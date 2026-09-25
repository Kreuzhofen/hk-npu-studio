from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.release_config import RELEASE
from engine.backends.backend_discovery_service import BackendDiscoveryService


BUILD_ROOT = PROJECT_ROOT / "build" / "release"
DIST_ROOT = PROJECT_ROOT / "dist"
APP_DIST = DIST_ROOT / "HKNPUStudio"
REALESRGAN_PRODUCT_MODEL = PROJECT_ROOT / "models" / "real_esrgan_x4plus.bin"
FIDESR_PRODUCT_FILES = (
    (
        PROJECT_ROOT / "models" / "photo_restore_context" / "fidesr_vae_encoder" / "fidesr_vae_encoder.serialized.bin.bin",
        "models/photo_restore_context/fidesr_vae_encoder",
    ),
    (
        PROJECT_ROOT / "models" / "photo_restore_context" / "fidesr_unet" / "fidesr_unet_merged.serialized.bin.bin",
        "models/photo_restore_context/fidesr_unet",
    ),
    (
        PROJECT_ROOT / "models" / "photo_restore_context" / "fidesr_lrrb" / "fidesr_lrrb.serialized.bin.bin",
        "models/photo_restore_context/fidesr_lrrb",
    ),
    (
        PROJECT_ROOT / "models" / "photo_restore_context" / "fidesr_vae_decoder" / "fidesr_vae_decoder.serialized.bin.bin",
        "models/photo_restore_context/fidesr_vae_decoder",
    ),
    (
        PROJECT_ROOT / "models" / "photo_restore" / "fidesr_empty_prompt_embeds.bin",
        "models/photo_restore",
    ),
    (
        PROJECT_ROOT / "models" / "photo_restore" / "fidesr_epsilon_seed231.bin",
        "models/photo_restore",
    ),
    (
        PROJECT_ROOT / "engine" / "backends" / "fidesr_strong_runner_template.py",
        "engine/backends",
    ),
)
RELEASE_DOCUMENTS = (
    (PROJECT_ROOT / "README.md", "."),
    (PROJECT_ROOT / "LICENSE", "."),
    (PROJECT_ROOT / "docs" / "user-guide" / "USER_GUIDE_DE.md", "docs/user-guide"),
    (PROJECT_ROOT / "docs" / "user-guide" / "USER_GUIDE_EN.md", "docs/user-guide"),
    (PROJECT_ROOT / "docs" / "user-guide" / "USER_GUIDE_ES.md", "docs/user-guide"),
    (PROJECT_ROOT / "docs" / "releases" / "RC3_RELEASE_NOTES.md", "docs/releases"),
)


def _resolve_fidesr_qnn_runtime_files() -> tuple[tuple[Path, str], ...]:
    discovery = BackendDiscoveryService.discover()
    runner_text = discovery.qnn_net_run_path if discovery.qnn_tools_found else None
    backend_text = discovery.qnn_htp_backend_path
    runner = Path(runner_text) if runner_text else None
    backend = Path(backend_text) if backend_text else None
    skeleton = next(
        (
            Path(path) for path in discovery.qnn_htp_skeleton_dirs
            if (Path(path) / "libQnnHtpV73Skel.so").is_file()
            and (Path(path) / "libqnnhtpv73.cat").is_file()
        ),
        None,
    )
    if runner is None or backend is None or skeleton is None:
        raise FileNotFoundError(
            "FiDeSR QNN/HTP runtime discovery is incomplete; no packaged runtime can be built."
        )
    files = (
        (runner, "qnn_runtime/bin"),
        (backend.parent / "QnnHtp.dll", "qnn_runtime/lib"),
        (backend.parent / "QnnSystem.dll", "qnn_runtime/lib"),
        (backend.parent / "QnnHtpV73Stub.dll", "qnn_runtime/lib"),
        (skeleton / "libQnnHtpV73Skel.so", "qnn_runtime/hexagon"),
        (skeleton / "libqnnhtpv73.cat", "qnn_runtime/hexagon"),
    )
    missing = [path for path, _destination in files if not path.is_file() or path.stat().st_size <= 0]
    if missing:
        raise FileNotFoundError(
            "FiDeSR QNN/HTP runtime files missing: "
            + ", ".join(str(path) for path in missing)
        )
    return files


def _required_add_data_files() -> tuple[tuple[Path, str], ...]:
    required = (*FIDESR_PRODUCT_FILES, *RELEASE_DOCUMENTS)
    missing = [path for path, _destination in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Required RC3 release files missing: "
            + ", ".join(str(path) for path in missing)
        )
    return required


def _find_optional_qai_appbuilder() -> tuple[Path, Path] | None:
    configured = os.environ.get("SNAPDRAGON_QAI_APPBUILDER_PACKAGE", "").strip()
    candidates = [
        Path(configured).expanduser() if configured else None,
        PROJECT_ROOT.parent
        / "QAI-AppBuilder-Test"
        / ".venv"
        / "Lib"
        / "site-packages"
        / "qai_appbuilder",
    ]
    package = next((path.resolve() for path in candidates if path and path.is_dir()), None)
    if package is None:
        return None
    required = (
        "__init__.py",
        "appbuilder.cp311-win_arm64.pyd",
        "libappbuilder.dll",
        "QAIAppSvc.exe",
        "libs/QnnHtp.dll",
        "libs/QnnSystem.dll",
        "libs/QnnHtpV73Stub.dll",
        "libs/libQnnHtpV73Skel.so",
    )
    missing = [name for name in required if not (package / name).is_file()]
    if missing:
        raise FileNotFoundError(
            "QAI AppBuilder package is incomplete: " + ", ".join(missing)
        )
    common = package.parents[2] / "samples" / "common"
    if not (common / "_stable_diffusion.py").is_file():
        common = PROJECT_ROOT.parent / "QAI-AppBuilder-Test" / "samples" / "common"
    if not (common / "_stable_diffusion.py").is_file():
        raise FileNotFoundError("QAI Stable Diffusion helper '_stable_diffusion.py' is missing")
    return package, common.resolve()


def _prepare_release_resources() -> Path:
    target = BUILD_ROOT / "release_data" / "resources"
    if target.parent.exists():
        shutil.rmtree(target.parent)
    shutil.copytree(
        PROJECT_ROOT / "resources",
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    for definition in (target / "models").glob("*.json"):
        data = json.loads(definition.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data["installed"] = False
            data["downloaded"] = False
            data["path"] = ""
            data["status"] = "Not Installed"
            definition.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    return target


def _write_version_file() -> Path:
    version_file = BUILD_ROOT / "version_info.txt"
    version_file.parent.mkdir(parents=True, exist_ok=True)
    numeric = (2, 0, 0, 0)
    version_file.write_text(
        f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={numeric}, prodvers={numeric}, mask=0x3f, flags=0x0,
    OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)
  ),
  kids=[
    StringFileInfo([StringTable('040704B0', [
      StringStruct('CompanyName', '{RELEASE.publisher}'),
      StringStruct('FileDescription', '{RELEASE.app_name}'),
      StringStruct('FileVersion', '{RELEASE.package_version}'),
      StringStruct('InternalName', 'HKNPUStudio'),
      StringStruct('OriginalFilename', '{RELEASE.executable_name}'),
      StringStruct('ProductName', '{RELEASE.app_name}'),
      StringStruct('ProductVersion', '{RELEASE.package_version}')
    ])]),
    VarFileInfo([VarStruct('Translation', [1031, 1200])])
  ]
)""",
        encoding="utf-8",
    )
    return version_file


def build_arguments() -> list[str]:
    if not REALESRGAN_PRODUCT_MODEL.is_file():
        raise FileNotFoundError(
            f"Produktgebundenes RealESRGAN-Modell fehlt: {REALESRGAN_PRODUCT_MODEL}"
        )
    required_files = _required_add_data_files()
    fidesr_qnn_runtime = _resolve_fidesr_qnn_runtime_files()
    resources = _prepare_release_resources()
    plugins = BUILD_ROOT / "release_data" / "plugins"
    shutil.copytree(
        PROJECT_ROOT / "plugins",
        plugins,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    # Dynamische Erkennung und Validierung des onnxruntime_qnn-Pakets
    try:
        import onnxruntime_qnn
        qnn_path = Path(onnxruntime_qnn.__file__).parent.resolve()
    except ImportError:
        raise RuntimeError("Das Paket 'onnxruntime_qnn' ist im aktuellen Python-Environment nicht installiert.")

    qnn_provider_required_files = [
        "onnxruntime_providers_qnn.dll",
        "QnnHtp.dll",
        "QnnSystem.dll",
        "QnnHtpV73Stub.dll",
        "libQnnHtpV73Skel.so",
    ]
    for filename in qnn_provider_required_files:
        filepath = qnn_path / filename
        if not filepath.is_file():
            raise FileNotFoundError(
                f"Die benötigte QNN-Datei fehlt im Verzeichnis des onnxruntime_qnn-Pakets: {filename}"
            )

    version_file = _write_version_file()
    qai_runtime = _find_optional_qai_appbuilder()
    data_directories = {
        resources: "resources",
        PROJECT_ROOT / "assets": "assets",
        PROJECT_ROOT / "locales": "locales",
        plugins: "plugins",
        PROJECT_ROOT / "workflows": "workflows",
        PROJECT_ROOT / "presets": "presets",
        qnn_path: "onnxruntime_qnn",
    }
    if qai_runtime is not None:
        qai_package, qai_common = qai_runtime
        data_directories[qai_package] = "qai_appbuilder"
        data_directories[qai_common] = "qai_appbuilder_common"
    arguments = [
        str(PROJECT_ROOT / "gui_v2.py"),
        "--name",
        "HKNPUStudio",
        "--onedir",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--contents-directory",
        ".",
        "--distpath",
        str(DIST_ROOT),
        "--workpath",
        str(BUILD_ROOT / "pyinstaller"),
        "--specpath",
        str(BUILD_ROOT),
        "--icon",
        str(PROJECT_ROOT / "assets" / "brand" / "icons" / "app.ico"),
        "--version-file",
        str(version_file),
        "--collect-submodules",
        "plugins",
        "--collect-submodules",
        "tkinterdnd2",
        "--collect-submodules",
        "setuptools._vendor.backports",
        "--add-data",
        f"{PROJECT_ROOT / 'release.json'}{os.pathsep}.",
        "--add-data",
        f"{REALESRGAN_PRODUCT_MODEL}{os.pathsep}models",
    ]
    for source, destination in (*required_files, *fidesr_qnn_runtime):
        arguments.extend(["--add-data", f"{source}{os.pathsep}{destination}"])
    if qai_runtime is not None:
        qai_package, _ = qai_runtime
        qai_site_packages = qai_package.parent
        arguments.extend(
            [
                "--paths",
                str(qai_site_packages),
                "--collect-all",
                "qai_appbuilder",
                "--collect-all",
                "torchgen",
                "--collect-all",
                "functorch",
                "--collect-all",
                "yaml",
                "--collect-all",
                "requests",
                "--collect-all",
                "filelock",
                "--collect-all",
                "tqdm",
                "--collect-all",
                "packaging",
                "--collect-all",
                "huggingface_hub",
                "--collect-all",
                "qai_hub",
                "--collect-all",
                "diffusers",
                "--collect-all",
                "py3_wget",
                "--hidden-import",
                "torch",
                "--hidden-import",
                "torchgen",
                "--hidden-import",
                "functorch",
                "--hidden-import",
                "yaml",
                "--hidden-import",
                "requests",
                "--hidden-import",
                "filelock",
                "--hidden-import",
                "tqdm",
                "--hidden-import",
                "packaging",
                "--hidden-import",
                "huggingface_hub",
                "--hidden-import",
                "qai_hub",
                "--hidden-import",
                "diffusers",
                "--hidden-import",
                "transformers",
                "--hidden-import",
                "py3_wget",
            ]
        )
        for distribution in (
            "requests",
            "filelock",
            "numpy",
            "tqdm",
            "regex",
            "packaging",
            "tokenizers",
            "huggingface-hub",
            "safetensors",
            "pyyaml",
            "torch",
            "qai-hub",
            "transformers",
            "diffusers",
            "qai_appbuilder",
            "py3_wget",
        ):
            arguments.extend(["--copy-metadata", distribution])
    for source, destination in data_directories.items():
        if source.exists():
            arguments.extend(
                ["--add-data", f"{source}{os.pathsep}{destination}"]
            )
    return arguments


def main() -> int:
    qai_runtime = _find_optional_qai_appbuilder()
    if qai_runtime is not None:
        qai_site_packages = str(qai_runtime[0].parent)
        if qai_site_packages not in sys.path:
            sys.path.insert(0, qai_site_packages)

    from PyInstaller.__main__ import run

    if APP_DIST.exists():
        shutil.rmtree(APP_DIST)
    run(build_arguments())
    executable = APP_DIST / RELEASE.executable_name
    if not executable.is_file():
        raise FileNotFoundError(f"PyInstaller-Ausgabe fehlt: {executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
