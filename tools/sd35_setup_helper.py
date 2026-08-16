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

from config import TEMP_DIR
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

            emit("sd35_extracting", 10.0)
            if extracted_root.exists() and allow_redownload:
                shutil.rmtree(extracted_root)
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
            state_path.write_text(
                json.dumps({"attempted": True, "script": str(script_path)}), encoding="utf-8"
            )

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
            # Install python requirements
            pip_cmd = [
                python_executable, "-m", "pip", "install",
                "transformers", "diffusers", "qai-appbuilder", "qai-hub", "py3-wget"
            ]
            logger.info("Running: %s", " ".join(pip_cmd))

            # Set up environment variables with PYTHONPATH pointing to the isolated dependencies
            env = os.environ.copy()
            bundled_torch_path = None
            is_frozen = getattr(sys, "frozen", False)

            if is_frozen:
                candidate = Path(sys.executable).parent
                if (candidate / "torch").is_dir():
                    bundled_torch_path = candidate
            else:
                dev_candidate = Path(__file__).resolve().parent.parent / "dist" / "SnapdragonAIStudio"
                if (dev_candidate / "torch").is_dir():
                    bundled_torch_path = dev_candidate

            if bundled_torch_path:
                if is_frozen:
                    logger.info("Using bundled torch in frozen environment from: %s", bundled_torch_path)
                    isolated_deps_dir = workspace / "isolated_deps"
                    # Safe cleanup of any existing junctions
                    if isolated_deps_dir.exists():
                        failed_junctions = []
                        for item in isolated_deps_dir.iterdir():
                            if item.is_dir():
                                try:
                                    os.rmdir(item)
                                except Exception as e:
                                    logger.error("SAFETY ALERT: Could not rmdir junction %s during initialization: %s. Aborting recursive cleanup of this path to protect source directories.", item, e)
                                    failed_junctions.append(item)
                        if failed_junctions:
                            logger.warning("Junction cleanup failed for: %s. Skipping rmtree of isolated_deps to prevent accidental deletion of source files.", failed_junctions)
                        else:
                            try:
                                shutil.rmtree(isolated_deps_dir)
                            except Exception as e:
                                logger.warning("Could not rmtree isolated_deps_dir %s during initialization: %s", isolated_deps_dir, e)

                    isolated_deps_dir.mkdir(parents=True, exist_ok=True)

                    try:
                        import _winapi
                    except ImportError:
                        _winapi = None

                    for name in ("torch", "torchgen", "functorch"):
                        src = Path(bundled_torch_path) / name
                        dst = isolated_deps_dir / name
                        if src.is_dir():
                            try:
                                if _winapi:
                                    _winapi.CreateJunction(str(src), str(dst))
                                else:
                                    subprocess.run(
                                        ["cmd", "/c", "mklink", "/j", str(dst), str(src)],
                                        capture_output=True,
                                        check=True
                                    )
                                logger.info("Junction created for %s", name)
                            except Exception as ex:
                                logger.error("Failed to create junction for %s: %s", name, ex)

                    env["PYTHONPATH"] = str(isolated_deps_dir)
                    logger.info("Isolated PYTHONPATH configured (exclusive): %s", env["PYTHONPATH"])
                else:
                    # Keep dev/non-frozen behavior compatible and minimally changed
                    logger.info("Using bundled torch in dev/non-frozen environment from: %s", bundled_torch_path)
                    existing_pythonpath = env.get("PYTHONPATH", "")
                    if existing_pythonpath:
                        env["PYTHONPATH"] = f"{bundled_torch_path}{os.pathsep}{existing_pythonpath}"
                    else:
                        env["PYTHONPATH"] = str(bundled_torch_path)

            startupinfo = None
            creationflags = 0
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                creationflags = subprocess.CREATE_NO_WINDOW

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

            # Read stdout line by line
            pip_output_buffer = []
            pip_error_lines = []
            keywords = ["error", "failed", "no matching distribution", "could not", "requirement", "traceback"]

            while True:
                line = process.stdout.readline()
                if not line:
                    break
                striped = line.strip()
                logger.info("[pip] %s", striped)

                # Keep last 15 lines of general output
                pip_output_buffer.append(striped)
                if len(pip_output_buffer) > 15:
                    pip_output_buffer.pop(0)

                # Check for keywords to collect specific error lines (case-insensitive)
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

            # Runtime preflight check immediately before launching stable_diffusion_v3_5.py
            if bundled_torch_path and is_frozen:
                logger.info("Running runtime preflight check...")
                preflight_code = (
                    "import sys\n"
                    "import numpy\n"
                    "import torch\n"
                    "import torchgen\n"
                    "import functorch\n"
                    "import requests\n"
                    "import yaml\n"
                    "import diffusers\n"
                    "import transformers\n"
                    "import qai_appbuilder\n"
                    "assert hasattr(numpy, 'ndarray'), 'numpy.ndarray is missing'\n"
                    "print('PREFLIGHT_OK')\n"
                )
                try:
                    preflight_process = subprocess.run(
                        [python_executable, "-c", preflight_code],
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
                        logger.error("Preflight check failed: %s", preflight_error)
                        return fail(
                            "preflight_failed",
                            f"Preflight check failed: {preflight_error or 'Unknown import error'}",
                            50.0,
                            3
                        )
                    logger.info("Preflight check passed.")
                except Exception as preflight_exc:
                    logger.exception("Preflight check exception: %s", preflight_exc)
                    return fail(
                        "preflight_failed",
                        f"Preflight check exception: {preflight_exc}",
                        50.0,
                        3
                    )

            emit("sd35_downloading_weights", 50.0)
            run_cmd = [python_executable, "stable_diffusion_v3_5.py"]
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
    def safe_cleanup_temp_dir(path_str: str) -> None:
        try:
            path = Path(path_str).resolve()
            if not path.exists() or not path.is_dir():
                return

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
            if isolated_deps.is_dir():
                failed_junctions = []
                for item in isolated_deps.iterdir():
                    if item.is_dir():
                        try:
                            os.rmdir(item)
                        except Exception as e:
                            logger.error("SAFETY ALERT: Failed to safely rmdir junction %s: %s. Skipping recursive cleanup of %s to protect source directories.", item, e, path)
                            failed_junctions.append(item)
                if failed_junctions:
                    logger.warning("Junction cleanup failed for: %s. Aborting clean up of workspace %s to protect source folders.", failed_junctions, path)
                    return
                try:
                    shutil.rmtree(isolated_deps)
                except Exception as e:
                    logger.warning("Failed to remove isolated_deps dir %s: %s", isolated_deps, e)

            shutil.rmtree(path)
        except Exception as exc:
            logger.error("Failed to clean up temp dir %s: %s", path_str, exc)
