from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from engine.release_config import RELEASE


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_SCRIPT = PROJECT_ROOT / "installer" / "snapdragon_ai_studio.iss"


def build_command(iscc_path: str | Path) -> list[str]:
    return [
        str(iscc_path),
        f"/DAppName={RELEASE.app_name}",
        f"/DAppVersion={RELEASE.package_version}",
        f"/DPublisher={RELEASE.publisher}",
        f"/DExecutableName={RELEASE.executable_name}",
        str(INSTALLER_SCRIPT),
    ]


def main() -> int:
    iscc = shutil.which("ISCC.exe") or shutil.which("iscc")
    if not iscc:
        raise RuntimeError("Inno Setup Compiler (ISCC.exe) wurde nicht gefunden.")
    executable = PROJECT_ROOT / "dist" / "SnapdragonAIStudio" / RELEASE.executable_name
    if not executable.is_file():
        raise FileNotFoundError(f"Release-Build fehlt: {executable}")
    return subprocess.run(build_command(iscc), cwd=PROJECT_ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
