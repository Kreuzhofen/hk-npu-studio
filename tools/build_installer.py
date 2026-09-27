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
INSTALLER_OUTPUT_DIR = PROJECT_ROOT / "dist" / "installer"
GITHUB_RELEASE_ASSET_LIMIT_BYTES = 2_147_483_648
TARGET_INSTALLER_MAX_BYTES = 2_100_000_000


def validate_release_staging(staging_dir: Path = RELEASE_STAGING_DIR) -> None:
    """Reject runtime output from the installer staging tree."""
    runtime_output = staging_dir / "output"
    if runtime_output.exists():
        raise RuntimeError(
            f"Release-Staging darf keinen Runtime-Ausgabeordner enthalten: {runtime_output}"
        )


def validate_installer_size_bytes(size_bytes: int) -> None:
    """Keep the release asset below GitHub's limit with an explicit margin."""
    if size_bytes > TARGET_INSTALLER_MAX_BYTES:
        raise RuntimeError(
            "Installer exceeds the RC3 release size gate: "
            f"{size_bytes} > {TARGET_INSTALLER_MAX_BYTES} bytes "
            f"(GitHub limit: {GITHUB_RELEASE_ASSET_LIMIT_BYTES} bytes)."
        )


def validate_installer_size(installer_path: Path) -> None:
    if not installer_path.is_file():
        raise FileNotFoundError(f"Installer-Ausgabe fehlt: {installer_path}")
    validate_installer_size_bytes(installer_path.stat().st_size)


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
    result = subprocess.run(build_command(iscc), cwd=PROJECT_ROOT, check=False)
    if result.returncode != 0:
        return result.returncode
    installer = (
        INSTALLER_OUTPUT_DIR
        / f"HKNPUStudio-{RELEASE.package_version}-ARM64-Setup.exe"
    )
    validate_installer_size(installer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
