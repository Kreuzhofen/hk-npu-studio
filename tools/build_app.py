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


BUILD_ROOT = PROJECT_ROOT / "build" / "release"
DIST_ROOT = PROJECT_ROOT / "dist"
APP_DIST = DIST_ROOT / "SnapdragonAIStudio"


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
      StringStruct('InternalName', 'SnapdragonAIStudio'),
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

    required_files = [
        "onnxruntime_providers_qnn.dll",
        "QnnHtp.dll",
        "QnnSystem.dll",
        "QnnHtpV73Stub.dll",
        "libQnnHtpV73Skel.so",
    ]
    for filename in required_files:
        filepath = qnn_path / filename
        if not filepath.is_file():
            raise FileNotFoundError(
                f"Die benötigte QNN-Datei fehlt im Verzeichnis des onnxruntime_qnn-Pakets: {filename}"
            )

    version_file = _write_version_file()
    data_directories = {
        resources: "resources",
        PROJECT_ROOT / "assets": "assets",
        PROJECT_ROOT / "locales": "locales",
        plugins: "plugins",
        PROJECT_ROOT / "workflows": "workflows",
        PROJECT_ROOT / "presets": "presets",
        qnn_path: "onnxruntime_qnn",
    }
    arguments = [
        str(PROJECT_ROOT / "gui_v2.py"),
        "--name",
        "SnapdragonAIStudio",
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
        "--add-data",
        f"{PROJECT_ROOT / 'release.json'}{os.pathsep}.",
    ]
    for source, destination in data_directories.items():
        if source.exists():
            arguments.extend(
                ["--add-data", f"{source}{os.pathsep}{destination}"]
            )
    return arguments


def main() -> int:
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
