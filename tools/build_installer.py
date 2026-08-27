from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.release_config import RELEASE


INSTALLER_SCRIPT = PROJECT_ROOT / "installer" / "snapdragon_ai_studio.iss"
RELEASE_STAGING_DIR = PROJECT_ROOT / "dist" / "HKNPUStudio"


def validate_release_staging(staging_dir: Path = RELEASE_STAGING_DIR) -> None:
    """Reject runtime output from the installer staging tree."""
    runtime_output = staging_dir / "output"
    if runtime_output.exists():
        raise RuntimeError(
            f"Release-Staging darf keinen Runtime-Ausgabeordner enthalten: {runtime_output}"
        )


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
    candidates = (
        shutil.which("ISCC.exe"),
        shutil.which("iscc"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    )
    iscc = next(
        (candidate for candidate in candidates if candidate and Path(candidate).is_file()),
        None,
    )
    if not iscc:
        raise RuntimeError("Inno Setup Compiler (ISCC.exe) wurde nicht gefunden.")
    executable = RELEASE_STAGING_DIR / RELEASE.executable_name
    if not executable.is_file():
        raise FileNotFoundError(f"Release-Build fehlt: {executable}")
    validate_release_staging()
    return subprocess.run(build_command(iscc), cwd=PROJECT_ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
