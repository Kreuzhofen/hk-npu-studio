from __future__ import annotations

import os
import sys
import shutil
import tempfile
import zipfile
import subprocess
import logging
import json
import inspect
from pathlib import Path
from typing import Callable, Any

import re

from config import TEMP_DIR, USER_BASE
from engine.model_install_service import SD35InstallState, SD35SourceInspection

logger = logging.getLogger("SD35SetupHelper")


def sanitize_pip_line(line: str) -> str:
    """Mask URLs with credentials/tokens and clean whitespace."""
    line = line.strip()
    if not line:
        return ""
    # Mask credentials: http://user:pass@host -> http://***@host
    line = re.sub(r'(https?://)[^:\s/]+:[^@\s/]+@', r'\1***@', line)
    # Mask token: http://token@host -> http://***@host
    line = re.sub(r'(https?://)[^@\s/]+@', r'\1***@', line)
    # Mask key=value parameters: token=foo -> token=***
    line = re.sub(r'(token|api_key|password|secret|auth|key)=[a-zA-Z0-9_\-\.]+', r'\1=***', line, flags=re.IGNORECASE)
    return line


def resolve_python_executable() -> str:
    """Return a real Python interpreter, never the frozen Studio executable."""
    current = Path(sys.executable)
    python_names = {"python.exe", "pythonw.exe", "python", "python3"}
    if not getattr(sys, "frozen", False) and current.name.lower() in python_names:
        return str(current)

    candidates: list[Path] = []
    override = os.environ.get("SNAPDRAGON_AI_PYTHON", "").strip()
    if override:
        candidates.append(Path(override))
    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
    candidates.extend((
        program_files / "Python311-arm64" / "python.exe",
        local_app_data / "Programs" / "Python" / "Python311-arm64" / "python.exe",
        local_app_data / "Programs" / "Python" / "Python311" / "python.exe",
    ))
    for command in ("python3.11", "python"):
        resolved = shutil.which(command)
        if resolved:
            candidates.append(Path(resolved))
    for candidate in candidates:
        if (
            candidate.name.lower() in python_names
            and candidate.is_file()
            and "windowsapps" not in str(candidate).lower()
            and candidate.stat().st_size > 0
        ):
            return str(candidate.resolve())
    raise RuntimeError("A real Python 3.11 interpreter is required for SD3.5 setup.")


class SD35SetupHelper:
    """Automates finding, extracting, installing deps, and running Qualcomm sample for SD3.5."""

    WORKSPACE_NAME = "sd35-qai-setup"
    STATE_FILE = "setup_state.json"

    @staticmethod
    def locate_zip() -> str | None:
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        zip_path = os.path.join(downloads, "qai-appbuilder-main.zip")
        if os.path.exists(zip_path):
            return zip_path
        return None

    @staticmethod
    def run_setup(
        zip_path: str,
        installer: Any,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        *,
        allow_redownload: bool = False,
    ) -> bool:
        def emit(update_or_phase: str | dict[str, Any], percent: float | None = None) -> None:
            if progress_callback:
                if isinstance(update_or_phase, dict):
                    progress_callback(update_or_phase)
                else:
                    progress_callback({"phase": update_or_phase, "percent": percent or 0.0})

        workspace = Path(TEMP_DIR) / SD35SetupHelper.WORKSPACE_NAME
        extracted_root = workspace / "qai-appbuilder-main"
        state_path = workspace / SD35SetupHelper.STATE_FILE

        def fail(phase: str, message: str, percent: float, step: int) -> bool:
            logger.error("SD3.5 %s failed: %s", phase, message)
            emit({"phase": phase, "percent": percent, "failed_step": step, "error": message})
            return False

        def find_script() -> Path | None:
            expected_suffix = Path(
                "samples/models/generative_ai/image_generation/"
                "stable_diffusion_v3_5/python/stable_diffusion_v3_5.py"
            )
            exact = extracted_root / expected_suffix
            if exact.is_file():
                return exact
            matches = list(extracted_root.rglob("stable_diffusion_v3_5.py")) if extracted_root.exists() else []
            return matches[0] if len(matches) == 1 else None

        def inspect_source(search_root: Path) -> SD35SourceInspection:
            service = getattr(installer, "install_service", installer)
            if inspect.ismethod(installer):
                owner = installer.__self__
                service = getattr(owner, "install_service", owner)
            inspector = getattr(service, "inspect_sd35_qualcomm_source", None)
            if callable(inspector):
                return inspector(str(search_root))
            raise RuntimeError("SD3.5 source validator unavailable")

        workspace.mkdir(parents=True, exist_ok=True)
        try:
            previous_workspaces = [workspace]
            previous_workspaces.extend(
                path for path in Path(tempfile.gettempdir()).glob("qai-appbuilder-setup-*")
                if path.is_dir()
            )
            partial_source: SD35SourceInspection | None = None
            for previous_workspace in previous_workspaces:
                inspection = inspect_source(previous_workspace)
                if inspection.state is SD35InstallState.COMPLETE_SOURCE:
                    logger.info("Reusing complete Qualcomm SD3.5 output: %s", inspection.root)
                    emit("sd35_reusing_models", 75.0)
                    return SD35SetupHelper._install_existing_source(
                        inspection.root, installer, emit, previous_workspace
                    )
                if inspection.state is SD35InstallState.PARTIAL_DOWNLOAD:
                    partial_source = inspection

            if partial_source is not None and not allow_redownload:
                return fail(
                    "redownload_required",
                    "Existing Qualcomm model files are incomplete or damaged; explicit redownload required. "
                    f"Missing: {', '.join(partial_source.missing_files)}",
                    0.0,
                    3,
                )

            # Check if extracted_root corresponds to currently selected ZIP
            is_stale = False
            if extracted_root.exists():
                try:
                    current_mtime = os.path.getmtime(zip_path)
                    current_size = os.path.getsize(zip_path)
                    current_resolved = str(Path(zip_path).resolve())
                    if state_path.is_file():
                        state_data = json.loads(state_path.read_text(encoding="utf-8"))
                        if (state_data.get("zip_path") != current_resolved or
                            state_data.get("zip_mtime") != current_mtime or
                            state_data.get("zip_size") != current_size):
                            is_stale = True
                            logger.info("Workspace ZIP mismatch. Marking extracted_root as stale.")
                    else:
                        is_stale = True
                except Exception as e:
                    is_stale = True
                    logger.warning("Error checking workspace ZIP correspondence: %s", e)

            # Also check if find_script finds a valid unique script in the existing extracted_root
            if not is_stale and extracted_root.exists():
                if not find_script():
                    is_stale = True
                    logger.info("Unique stable_diffusion_v3_5.py not found in existing root. Marking as stale.")

            emit("sd35_extracting", 10.0)
            if extracted_root.exists() and (allow_redownload or is_stale):
                logger.info("Removing stale or requested extracted_root: %s", extracted_root)
                SD35SetupHelper._safe_purge_reparse_and_dir(extracted_root)

            if not extracted_root.exists():
                logger.info("Extracting %s to persistent workspace %s", zip_path, workspace)
                with zipfile.ZipFile(zip_path, "r") as ref:
                    ref.extractall(workspace)

            emit("checking", 20.0)
            script_path = find_script()
            if not script_path:
                return fail("validation_failed", "stable_diffusion_v3_5.py not found uniquely in archive", 20.0, 0)

            working_dir = script_path.parent
            logger.info("Found Qualcomm sample directory: %s", working_dir)

            try:
                current_mtime = os.path.getmtime(zip_path)
                current_size = os.path.getsize(zip_path)
                current_resolved = str(Path(zip_path).resolve())
                state_path.write_text(
                    json.dumps({
                        "attempted": True,
                        "script": str(script_path),
                        "zip_path": current_resolved,
                        "zip_mtime": current_mtime,
                        "zip_size": current_size
                    }), encoding="utf-8"
                )
            except Exception as e:
                logger.warning("Failed to write setup state: %s", e)

            emit("sd35_installing_deps", 30.0)
            try:
                python_executable = resolve_python_executable()
            except RuntimeError:
                return fail(
                    "dependency_failed",
                    "python_311_required",
                    40.0,
                    1,
                )

            # 1. Dedicated venv under USER_BASE (AppData area)
            venv_dir = USER_BASE / "sd35_venv"
            venv_python = venv_dir / "Scripts" / "python.exe"
            site_packages_dir = venv_dir / "Lib" / "site-packages"

            startupinfo = None
            creationflags = 0
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                creationflags = subprocess.CREATE_NO_WINDOW

            # Set up environment variables with PYTHONPATH cleared to prevent leakage
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)

            def run_preflight_check() -> tuple[bool, str]:
                logger.info("Running runtime preflight check...")
                preflight_code = (
                    "import sys\n"
                    "import numpy\n"
                    "import yaml\n"
                    "import requests\n"
                    "import torch\n"
                    "import torchgen\n"
                    "import functorch\n"
                    "import diffusers\n"
                    "import transformers\n"
                    "import huggingface_hub\n"
                    "import qai_hub\n"
                    "import qai_appbuilder\n"
                    "import py3_wget\n"
                    "assert hasattr(numpy, 'ndarray'), 'numpy.ndarray is missing'\n"
                    "assert getattr(numpy, '__file__', None) is not None, 'numpy.__file__ is missing/None'\n"
                    "assert hasattr(numpy, '__version__'), 'numpy.__version__ is missing'\n"
                    "assert hasattr(torch, '__version__') and torch.__version__, 'torch version cannot be read'\n"
                    "print('numpy_file:', getattr(numpy, '__file__', 'unknown'))\n"
                    "print('yaml_file:', getattr(yaml, '__file__', 'unknown'))\n"
                    "print('requests_file:', getattr(requests, '__file__', 'unknown'))\n"
                    "print('torch_file:', getattr(torch, '__file__', 'unknown'))\n"
                    "print('diffusers_file:', getattr(diffusers, '__file__', 'unknown'))\n"
                    "print('transformers_file:', getattr(transformers, '__file__', 'unknown'))\n"
                    "print('qai_hub_file:', getattr(qai_hub, '__file__', 'unknown'))\n"
                    "print('PREFLIGHT_OK')\n"
                )
                try:
                    preflight_process = subprocess.run(
                        [str(venv_python), "-c", preflight_code],
                        env=env,
                        capture_output=True,
                        text=True,
                        startupinfo=startupinfo,
                        creationflags=creationflags,
                        timeout=30.0
                    )
                    if preflight_process.returncode != 0:
                        err_lines = []
                        for line in preflight_process.stderr.splitlines():
                            line = line.strip()
                            if line:
                                err_lines.append(sanitize_pip_line(line))
                        preflight_error = "; ".join(err_lines[-3:]) or preflight_process.stdout.strip()
                        return False, preflight_error
                    logger.info("Preflight check passed. Output:\n%s", preflight_process.stdout)
                    return True, ""
                except Exception as preflight_exc:
                    logger.exception("Preflight check exception: %s", preflight_exc)
                    return False, str(preflight_exc)

            env_ready = False
            if venv_python.exists():
                logger.info("Existing venv python found. Running preflight verification...")
                passed, _ = run_preflight_check()
                if passed:
                    logger.info("Reuse existing validated isolated environment.")
                    env_ready = True

            if not env_ready:
                # 8. Retry/recovery: if the venv exists but is incomplete/broken, recreate it safely
                if venv_dir.exists():
                    logger.info("Cleaning up incomplete/broken virtual environment at %s", venv_dir)
                    try:
                        SD35SetupHelper.safe_remove_venv(venv_dir)
                    except Exception as clean_err:
                        return fail(
                            "dependency_failed",
                            f"Virtual environment cleanup failed: {clean_err}",
                            35.0,
                            1
                        )

                logger.info("Creating isolated virtual environment at %s", venv_dir)
                try:
                    subprocess.run(
                        [python_executable, "-m", "venv", str(venv_dir)],
                        check=True,
                        capture_output=True,
                        text=True,
                        startupinfo=startupinfo,
                        creationflags=creationflags
                    )
                except subprocess.CalledProcessError as err:
                    logger.error("Failed to create venv: %s\nStdout: %s\nStderr: %s", err, err.stdout, err.stderr)
                    return fail(
                        "dependency_failed",
                        f"Failed to create virtual environment: {err.stderr.strip() or err}",
                        35.0,
                        1
                    )

                if not venv_python.exists():
                    logger.error("Virtual environment Python executable not found at %s", venv_python)
                    return fail(
                        "dependency_failed",
                        f"Failed to create virtual environment: Python executable not found at {venv_python}",
                        35.0,
                        1
                    )

                # E. Make only the bundled Torch and non-pure dependencies (like PyYAML and NumPy) available
                # by physically copying them into venv site-packages.
                bundled_libs_path = None
                is_frozen = getattr(sys, "frozen", False)

                if is_frozen:
                    candidate = Path(sys.executable).parent
                    if (candidate / "torch").is_dir():
                        bundled_libs_path = candidate
                else:
                    dev_candidate = Path(__file__).resolve().parent.parent / "dist" / "SnapdragonAIStudio"
                    if (dev_candidate / "torch").is_dir():
                        bundled_libs_path = dev_candidate

                if is_frozen and not bundled_libs_path:
                    return fail(
                        "dependency_failed",
                        "Required bundled dependencies are missing in frozen installation folder",
                        40.0,
                        1
                    )

                if bundled_libs_path:
                    logger.info("Using bundled dependencies from: %s", bundled_libs_path)
                    try:
                        import _winapi
                    except ImportError:
                        _winapi = None

                    # Find the dist-info folders
                    torch_dist_info = None
                    pyyaml_dist_info = None
                    try:
                        for item in Path(bundled_libs_path).iterdir():
                            if item.is_dir():
                                if item.name.startswith("torch-") and item.name.endswith(".dist-info"):
                                    torch_dist_info = item
                                elif item.name.startswith("pyyaml-") and item.name.endswith(".dist-info"):
                                    pyyaml_dist_info = item
                    except Exception as e:
                        logger.error("Failed to list bundled directory: %s", e)

                    # Validate all required components exist in bundled_libs_path
                    missing_components = []
                    for name in ["torch", "torchgen", "functorch"]:
                        if not (Path(bundled_libs_path) / name).is_dir():
                            missing_components.append(name)
                    if not torch_dist_info:
                        missing_components.append("torch-*.dist-info")

                    for name in ["yaml"]:
                        if not (Path(bundled_libs_path) / name).is_dir():
                            missing_components.append(name)
                    if not pyyaml_dist_info:
                        missing_components.append("pyyaml-*.dist-info")

                    if missing_components:
                        return fail(
                            "dependency_failed",
                            f"Required bundled dependency component(s) missing: {', '.join(missing_components)}",
                            40.0,
                            1
                        )

                    components_to_copy = [
                        "torch", "torchgen", "functorch", torch_dist_info.name,
                        "yaml", pyyaml_dist_info.name
                    ]
                    import stat
                    for name in components_to_copy:
                        src = Path(bundled_libs_path) / name
                        dst = site_packages_dir / name
                        try:
                            # Safely clean up dst if it exists (junction, file, or directory)
                            try:
                                st = dst.lstat()
                                is_junction = bool(getattr(st, "st_file_attributes", 0) & 0x400)
                                if is_junction or stat.S_ISLNK(st.st_mode):
                                    os.rmdir(dst)
                                elif stat.S_ISDIR(st.st_mode):
                                    SD35SetupHelper._safe_purge_reparse_and_dir(dst)
                                else:
                                    dst.unlink()
                            except FileNotFoundError:
                                pass
                            except Exception as cleanup_err:
                                logger.warning("Could not remove existing target %s: %s", dst, cleanup_err)
                            
                            logger.info("Staging %s physically...", name)
                            if src.is_dir():
                                shutil.copytree(src, dst)
                            else:
                                shutil.copy2(src, dst)
                            logger.info("Staged %s physically successfully", name)
                            if not dst.exists():
                                raise RuntimeError(f"Physical copy of {name} to {dst} was not created successfully")
                        except Exception as ex:
                            logger.error("Failed to stage %s physically: %s", name, ex)
                            return fail(
                                "dependency_failed",
                                f"Failed to stage {name} physically: {ex}",
                                40.0,
                                1
                            )

                # Nested helper to run pip and capture errors
                def run_pip(pip_cmd: list[str]) -> bool:
                    logger.info("Running: %s", " ".join(pip_cmd))
                    process = subprocess.Popen(
                        pip_cmd,
                        cwd=str(working_dir),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        startupinfo=startupinfo,
                        creationflags=creationflags,
                        encoding="utf-8",
                        errors="replace",
                        env=env
                    )

                    pip_output_buffer = []
                    pip_error_lines = []
                    keywords = ["error", "failed", "no matching distribution", "could not", "requirement", "traceback"]

                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break
                        striped = line.strip()
                        logger.info("[pip] %s", striped)

                        pip_output_buffer.append(striped)
                        if len(pip_output_buffer) > 15:
                            pip_output_buffer.pop(0)

                        lowered = striped.lower()
                        if any(kw in lowered for kw in keywords):
                            sanitized = sanitize_pip_line(striped)
                            if sanitized and sanitized not in pip_error_lines:
                                pip_error_lines.append(sanitized)
                                if len(pip_error_lines) > 5:
                                    pip_error_lines.pop(0)

                    process.wait()
                    if process.returncode != 0:
                        if not pip_error_lines and pip_output_buffer:
                            fallback_lines = []
                            for line in pip_output_buffer[-3:]:
                                sanitized = sanitize_pip_line(line)
                                if sanitized and sanitized not in fallback_lines:
                                    fallback_lines.append(sanitized)
                            pip_error_lines = fallback_lines

                        if pip_error_lines:
                            error_cause = "; ".join(pip_error_lines)
                            error_msg = f"pip exited with code {process.returncode}: {error_cause}"
                        else:
                            error_msg = f"pip exited with code {process.returncode}"

                        return fail("dependency_failed", error_msg, 40.0, 1)
                    return True

                # Phase 0: upgrade pip first to ensure tag compatibility
                pip_upgrade_cmd = [
                    str(venv_python), "-m", "pip", "install", "--upgrade", "pip",
                    "--only-binary=:all:", "--prefer-binary"
                ]
                if not run_pip(pip_upgrade_cmd):
                    return False

                # Phase 1: install remaining required SD3.5 dependency set using --prefer-binary and --only-binary=:all:
                pip_cmd_1 = [
                    str(venv_python), "-m", "pip", "install",
                    "--prefer-binary",
                    "--only-binary=:all:",
                    "numpy==2.4.4", "transformers", "diffusers", "qai-appbuilder", "qai-hub", "py3-wget"
                ]
                if not run_pip(pip_cmd_1):
                    return False

                passed, error_msg = run_preflight_check()
                if not passed:
                    return fail(
                        "preflight_failed",
                        f"Preflight check failed: {error_msg or 'Unknown import error'}",
                        50.0,
                        3
                    )

            emit("sd35_downloading_weights", 50.0)
            run_cmd = [str(venv_python), "stable_diffusion_v3_5.py"]
            logger.info("Running Qualcomm sample script: %s", " ".join(run_cmd))

            process = subprocess.Popen(
                run_cmd,
                cwd=str(working_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo,
                creationflags=creationflags,
                encoding="utf-8",
                errors="replace",
                env=env
            )

            import re
            progress_pattern = re.compile(
                r"Download progress:\s*(\d+)%\s*\((\d+)/(\d+)\s*MB\)(?:\s*([\d.]+)\s*MB/s)?"
            )

            qualcomm_output_buffer = []
            qualcomm_error_lines = []
            qc_keywords = ["traceback", "error", "exception", "modulenotfounderror", "importerror", "failed", "could not", "no module", "requirement"]

            def process_qc_line(line_str: str) -> None:
                striped = line_str.strip()
                if not striped:
                    return
                logger.info("[Qualcomm] %s", striped)

                # Keep last 15 lines of general output
                qualcomm_output_buffer.append(striped)
                if len(qualcomm_output_buffer) > 15:
                    qualcomm_output_buffer.pop(0)

                # Check for keywords to collect specific error lines (case-insensitive)
                lowered = striped.lower()
                if any(kw in lowered for kw in qc_keywords):
                    sanitized = sanitize_pip_line(striped)
                    if sanitized and sanitized not in qualcomm_error_lines:
                        qualcomm_error_lines.append(sanitized)
                        if len(qualcomm_error_lines) > 5:
                            qualcomm_error_lines.pop(0)

                # Match progress
                match = progress_pattern.search(striped)
                if match:
                    percent = float(match.group(1))
                    downloaded_mb = float(match.group(2))
                    total_mb = float(match.group(3))
                    speed_mbs = match.group(4)
                    speed = float(speed_mbs) if speed_mbs else None

                    downloaded_bytes = downloaded_mb * 1024 * 1024
                    total_bytes = total_mb * 1024 * 1024
                    scaled_percent = 50.0 + (percent * 0.30)

                    emit({
                        "phase": "sd35_downloading_weights",
                        "percent": scaled_percent,
                        "download_percent": percent,
                        "downloaded_bytes": downloaded_bytes,
                        "total_bytes": total_bytes,
                        "speed": speed,
                    })

            buffer_chars = []
            while True:
                char = process.stdout.read(1)
                if not char:
                    break
                if char in ("\r", "\n"):
                    line = "".join(buffer_chars)
                    buffer_chars = []
                    process_qc_line(line)
                else:
                    buffer_chars.append(char)

            if buffer_chars:
                line = "".join(buffer_chars)
                process_qc_line(line)

            process.wait()
            logger.info("Qualcomm sample process finished with code: %d", process.returncode)

            # The official sample defines MODEL_ROOT as <python>/../models.
            models_dir = working_dir.parent / "models"
            source = inspect_source(models_dir)

            if process.returncode != 0:
                # Even if the script exited with a non-zero code, check if we got a complete source
                if source.state is SD35InstallState.COMPLETE_SOURCE:
                    logger.info("Qualcomm sample exited with code %d, but complete 11/11 source was found. Proceeding with installation.", process.returncode)
                else:
                    if not qualcomm_error_lines and qualcomm_output_buffer:
                        fallback_lines = []
                        for line in qualcomm_output_buffer[-3:]:
                            sanitized = sanitize_pip_line(line)
                            if sanitized and sanitized not in fallback_lines:
                                fallback_lines.append(sanitized)
                        qualcomm_error_lines = fallback_lines

                    if qualcomm_error_lines:
                        error_cause = "; ".join(qualcomm_error_lines)
                        error_msg = f"Qualcomm sample exited with code {process.returncode}: {error_cause}"
                    else:
                        error_msg = f"Qualcomm sample exited with code {process.returncode}"

                    return fail(
                        "download_failed",
                        error_msg,
                        70.0,
                        3,
                    )
            else:
                if source.state is not SD35InstallState.COMPLETE_SOURCE:
                    return fail(
                        "source_validation_failed",
                        f"incomplete Qualcomm output at {models_dir}; missing: {', '.join(source.missing_files)}",
                        75.0,
                        3,
                    )

            emit("sd35_importing", 80.0)
            return SD35SetupHelper._install_existing_source(source.root, installer, emit, workspace)

        except Exception as exc:
            logger.exception("Exception during SD3.5 automated setup: %s", exc)
            return fail("install_failed", str(exc), 50.0, 4)

    @staticmethod
    def _install_existing_source(
        source_root: Path,
        installer: Any,
        emit: Callable[[str | dict[str, Any], float | None], None],
        workspace: Path,
    ) -> bool:
        activation_failed = False

        def wrapped_callback(update: dict[str, Any]) -> None:
            nonlocal activation_failed
            forwarded = dict(update)
            forwarded["percent"] = 80.0 + (float(update.get("percent", 0.0)) * 0.20)
            if update.get("phase") == "activation_failed":
                activation_failed = True
                forwarded.setdefault("failed_step", 5)
            emit(forwarded)

        install_callable = getattr(installer, "install_sd35_qualcomm_folder", None)
        if not callable(install_callable) and callable(installer):
            install_callable = installer
        if not callable(install_callable):
            logger.error("SD3.5 import failed: installer callback unavailable")
            emit({"phase": "install_failed", "percent": 80.0, "failed_step": 4,
                  "error": "installer callback unavailable"})
            return False
        if not install_callable(str(source_root), wrapped_callback):
            logger.error("SD3.5 import failed: controlled import returned False | source=%s", source_root)
            emit({"phase": "install_failed", "percent": 90.0, "failed_step": 4,
                  "error": "controlled import returned False"})
            return False

        logger.info("Qualcomm SD3.5 model successfully staged, validated, and imported.")
        try:
            SD35SetupHelper.safe_cleanup_temp_dir(str(workspace))
        except Exception as cleanup_exc:
            logger.warning("Failed to remove temporary setup workspace: %s", cleanup_exc)
            emit("cleanup_warning", 100.0)
            return True
        if not activation_failed:
            emit("ready", 100.0)
        return True

    @staticmethod
    def _safe_purge_reparse_and_dir(target: Path) -> bool:
        """Safely removes a directory or reparse point without traversing untrusted junctions.
        Returns True if successfully removed or didn't exist, False if failed/aborted.
        """
        try:
            import stat
            try:
                st = target.lstat()
            except FileNotFoundError:
                return True
            except Exception as e:
                # If we cannot inspect, abort to be safe
                logger.error("Cannot inspect path %s: %s. Aborting cleanup for safety.", target, e)
                return False

            is_dir = stat.S_ISDIR(st.st_mode)
            is_reparse = bool(getattr(st, "st_file_attributes", 0) & 0x400)

            if is_reparse:
                logger.info("Removing reparse point/junction: %s", target)
                try:
                    os.rmdir(target)
                except Exception:
                    try:
                        target.unlink()
                    except Exception as e:
                        logger.error("Failed to remove reparse point %s: %s", target, e)
                        return False
                return True

            if is_dir:
                # It is a normal directory. We can iterate its children safely.
                try:
                    for item in target.iterdir():
                        if not SD35SetupHelper._safe_purge_reparse_and_dir(item):
                            logger.warning("Aborting cleanup of %s due to child failure on %s", target, item)
                            return False
                except Exception as e:
                    logger.error("Failed to iterate children of normal directory %s: %s", target, e)
                    return False

                # Now that all children are gone, we can remove the empty dir
                try:
                    os.rmdir(target)
                except Exception as e:
                    logger.error("Failed to remove directory %s: %s", target, e)
                    return False
                return True

            # Normal file
            try:
                target.unlink()
            except Exception as e:
                logger.error("Failed to delete file %s: %s", target, e)
                return False
            return True
        except Exception as exc:
            logger.error("Unexpected error in safe purge of %s: %s", target, exc)
            return False

    @staticmethod
    def safe_remove_venv(venv_dir: Path) -> None:
        try:
            st = venv_dir.lstat()
        except FileNotFoundError:
            return
        except Exception as e:
            logger.error("Cannot inspect venv_dir %s: %s. Aborting venv cleanup.", venv_dir, e)
            return

        import stat
        is_dir = stat.S_ISDIR(st.st_mode)
        is_reparse = bool(getattr(st, "st_file_attributes", 0) & 0x400)

        if is_reparse:
            SD35SetupHelper._safe_purge_reparse_and_dir(venv_dir)
            return

        if is_dir:
            site_packages = venv_dir / "Lib" / "site-packages"
            try:
                sp_st = site_packages.lstat()
                sp_is_dir = stat.S_ISDIR(sp_st.st_mode)
                sp_is_reparse = bool(getattr(sp_st, "st_file_attributes", 0) & 0x400)
            except FileNotFoundError:
                sp_is_dir = False
                sp_is_reparse = False
            except Exception as e:
                logger.error("Cannot inspect site-packages %s: %s. Aborting venv cleanup.", site_packages, e)
                return

            if sp_is_reparse:
                if not SD35SetupHelper._safe_purge_reparse_and_dir(site_packages):
                    raise RuntimeError(f"Failed to remove site-packages reparse point: {site_packages}")
            elif sp_is_dir:
                # 1. Identify and purge standard target junctions
                for name in ("torch", "torchgen", "functorch"):
                    item = site_packages / name
                    if not SD35SetupHelper._safe_purge_reparse_and_dir(item):
                        raise RuntimeError(f"Failed to remove junction: {item}")

                # 2. Identify and purge dist-info junctions
                try:
                    for item in site_packages.iterdir():
                        if item.name.startswith("torch-") and item.name.endswith(".dist-info"):
                            if not SD35SetupHelper._safe_purge_reparse_and_dir(item):
                                raise RuntimeError(f"Failed to remove junction: {item}")
                except Exception as e:
                    logger.warning("Failed to scan site-packages for dist-info junctions: %s", e)

        # Now that all junctions are confirmed absent, safely delete the venv
        if not SD35SetupHelper._safe_purge_reparse_and_dir(venv_dir):
            logger.warning("Failed to safely remove venv directory %s", venv_dir)

    @staticmethod
    def safe_cleanup_temp_dir(path_str: str) -> None:
        try:
            path = Path(path_str)
            try:
                st = path.lstat()
            except FileNotFoundError:
                return
            except Exception as e:
                logger.error("Cannot inspect path %s during temp dir cleanup: %s. Aborting.", path_str, e)
                return

            import stat
            is_dir = stat.S_ISDIR(st.st_mode)
            is_reparse = bool(getattr(st, "st_file_attributes", 0) & 0x400)

            if is_reparse:
                SD35SetupHelper._safe_purge_reparse_and_dir(path)
                return

            if not is_dir:
                try:
                    path.unlink()
                except Exception:
                    pass
                return

            # Resolve only after we confirm it is a normal directory
            path = path.resolve()

            if path.name != SD35SetupHelper.WORKSPACE_NAME and not path.name.startswith("qai-appbuilder-setup-"):
                logger.warning("Aborting cleanup: directory name %s does not match expected temporary pattern.", path.name)
                return

            invalid_names = {"models", "SnapdragonAI", "Downloads", "Users", "Documents", "Desktop"}
            if path.name.lower() in (name.lower() for name in invalid_names):
                return

            protected_paths = [
                Path("C:/"),
                Path("C:/SnapdragonAI"),
                Path("C:/SnapdragonAI/models"),
                Path(os.path.expanduser("~")),
                Path(os.path.expanduser("~")) / "Downloads",
            ]
            for p in protected_paths:
                try:
                    if path == p.resolve():
                        logger.warning("Aborting cleanup: directory matches protected path %s.", p)
                        return
                except OSError:
                    continue

            # Remove any isolated_deps junctions safely before workspace cleanup
            isolated_deps = path / "isolated_deps"
            if not SD35SetupHelper._safe_purge_reparse_and_dir(isolated_deps):
                logger.warning("Junction cleanup failed for isolated_deps. Aborting clean up of workspace %s to protect source folders.", path)
                return

            # Remove any venv site-packages junctions safely before workspace cleanup
            site_packages = path / "venv" / "Lib" / "site-packages"
            try:
                sp_st = site_packages.lstat()
                sp_is_dir = stat.S_ISDIR(sp_st.st_mode)
                sp_is_reparse = bool(getattr(sp_st, "st_file_attributes", 0) & 0x400)
            except FileNotFoundError:
                sp_is_dir = False
                sp_is_reparse = False
            except Exception as e:
                logger.error("Cannot inspect site-packages %s during temp dir cleanup: %s. Aborting.", site_packages, e)
                return

            if sp_is_reparse:
                if not SD35SetupHelper._safe_purge_reparse_and_dir(site_packages):
                    logger.warning("Junction cleanup failed for site-packages. Aborting clean up of workspace %s.", path)
                    return
            elif sp_is_dir:
                # 1. Identify and purge standard junctions
                for name in ("torch", "torchgen", "functorch"):
                    item = site_packages / name
                    if not SD35SetupHelper._safe_purge_reparse_and_dir(item):
                        logger.warning("Junction cleanup failed for %s. Aborting clean up of workspace %s.", item, path)
                        return
                # 2. Identify and purge dist-info junctions
                try:
                    for item in site_packages.iterdir():
                        if item.name.startswith("torch-") and item.name.endswith(".dist-info"):
                            if not SD35SetupHelper._safe_purge_reparse_and_dir(item):
                                logger.warning("Junction cleanup failed for %s. Aborting clean up of workspace %s.", item, path)
                                return
                except Exception as iter_exc:
                    logger.warning("Failed to iterate site-packages for dist-info cleanup: %s", iter_exc)

            if not SD35SetupHelper._safe_purge_reparse_and_dir(path):
                logger.error("Failed to safely clean up temp dir %s", path)
        except Exception as exc:
            logger.error("Failed to clean up temp dir %s: %s", path_str, exc)
