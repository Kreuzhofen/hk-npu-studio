from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import TEMP_DIR
from engine.download_service import DownloadService
from engine.logging_config import get_logger
from engine.release_config import RELEASE


logger = get_logger("ApplicationUpdateService")
_SEMVER = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?$"
)
MAX_MANIFEST_BYTES = 1024 * 1024


@dataclass(frozen=True)
class ApplicationUpdateManifest:
    version: str
    architecture: str
    package_url: str
    sha256: str


@dataclass(frozen=True)
class ApplicationUpdateCheck:
    available: bool
    message: str
    manifest: ApplicationUpdateManifest | None = None


@dataclass(frozen=True)
class ApplicationUpdateStage:
    success: bool
    message: str
    installer_path: Path | None = None


class ApplicationUpdateService:
    """Fail-closed RC update checker and verified installer staging service."""

    def __init__(
        self,
        *,
        current_version: str = RELEASE.package_version,
        architecture: str = RELEASE.architecture,
        download_service: DownloadService | None = None,
        opener=urllib.request.urlopen,
    ) -> None:
        self.current_version = current_version
        self.architecture = architecture.casefold()
        self.download_service = download_service or DownloadService(
            TEMP_DIR / "application_updates"
        )
        self._opener = opener

    def fetch_and_check(self, manifest_url: str) -> ApplicationUpdateCheck:
        parsed = urllib.parse.urlparse(manifest_url)
        if parsed.scheme != "https":
            return ApplicationUpdateCheck(False, "Update-Manifest erfordert HTTPS.")
        try:
            request = urllib.request.Request(
                manifest_url,
                headers={"User-Agent": f"HKNPUStudio/{self.current_version}"},
            )
            with self._opener(request, timeout=15.0) as response:
                payload = response.read(MAX_MANIFEST_BYTES + 1)
            if len(payload) > MAX_MANIFEST_BYTES:
                raise ValueError("Update-Manifest ist zu groß.")
            raw = json.loads(payload.decode("utf-8"))
            return self.check_manifest(raw)
        except Exception as error:
            logger.warning("Update-Prüfung fehlgeschlagen | error=%s", error)
            return ApplicationUpdateCheck(
                False, f"Update-Prüfung fehlgeschlagen: {error}"
            )

    def check_manifest(self, raw: Any) -> ApplicationUpdateCheck:
        try:
            manifest = self._parse_manifest(raw)
            if manifest.architecture.casefold() != self.architecture:
                return ApplicationUpdateCheck(
                    False,
                    f"Update-Architektur '{manifest.architecture}' ist inkompatibel.",
                )
            if self._compare_versions(
                manifest.version, self.current_version
            ) <= 0:
                return ApplicationUpdateCheck(False, "Kein neueres Update verfügbar.")
            return ApplicationUpdateCheck(
                True, f"Update {manifest.version} ist verfügbar.", manifest
            )
        except ValueError as error:
            return ApplicationUpdateCheck(False, str(error))

    def stage_update(
        self,
        manifest: ApplicationUpdateManifest,
        progress_callback=None,
    ) -> ApplicationUpdateStage:
        check = self.check_manifest(
            {
                "version": manifest.version,
                "architecture": manifest.architecture,
                "package_url": manifest.package_url,
                "sha256": manifest.sha256,
            }
        )
        if not check.available:
            return ApplicationUpdateStage(False, check.message)
        filename = f"HKNPUStudio-{manifest.version}-ARM64-Setup.exe"
        result = self.download_service.download(
            manifest.package_url,
            filename=filename,
            progress_callback=progress_callback,
            overwrite=True,
            expected_sha256=manifest.sha256,
            resume=True,
        )
        if not result.success or result.path is None:
            return ApplicationUpdateStage(
                False, result.message or "Update-Download fehlgeschlagen."
            )
        return ApplicationUpdateStage(
            True,
            "Update-Installer wurde verifiziert und bereitgestellt.",
            result.path,
        )

    @staticmethod
    def _parse_manifest(raw: Any) -> ApplicationUpdateManifest:
        if not isinstance(raw, dict):
            raise ValueError("Update-Manifest muss ein JSON-Objekt sein.")
        required = ("version", "architecture", "package_url", "sha256")
        missing = [key for key in required if not str(raw.get(key, "")).strip()]
        if missing:
            raise ValueError("Update-Manifest unvollständig: " + ", ".join(missing))
        version = str(raw["version"]).strip()
        if _SEMVER.fullmatch(version) is None:
            raise ValueError(f"Ungültige Update-Version: {version}")
        package_url = str(raw["package_url"]).strip()
        parsed = urllib.parse.urlparse(package_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Update-Paket erfordert eine absolute HTTPS-URL.")
        if not parsed.path.casefold().endswith(".exe"):
            raise ValueError("Update-Paket muss ein Windows-Installer (.exe) sein.")
        sha256 = str(raw["sha256"]).strip().casefold()
        if len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
            raise ValueError("Update-Manifest benötigt eine gültige SHA-256-Prüfsumme.")
        return ApplicationUpdateManifest(
            version=version,
            architecture=str(raw["architecture"]).strip(),
            package_url=package_url,
            sha256=sha256,
        )

    @staticmethod
    def _compare_versions(left: str, right: str) -> int:
        def parse(value: str):
            match = _SEMVER.fullmatch(value)
            if match is None:
                raise ValueError(f"Ungültige Version: {value}")
            core = tuple(int(match.group(name)) for name in ("major", "minor", "patch"))
            pre = match.group("pre")
            identifiers = tuple(pre.split(".")) if pre else ()
            return core, identifiers

        left_core, left_pre = parse(left)
        right_core, right_pre = parse(right)
        if left_core != right_core:
            return 1 if left_core > right_core else -1
        if not left_pre and right_pre:
            return 1
        if left_pre and not right_pre:
            return -1
        for left_id, right_id in zip(left_pre, right_pre):
            if left_id == right_id:
                continue
            if left_id.isdigit() and right_id.isdigit():
                return 1 if int(left_id) > int(right_id) else -1
            if left_id.isdigit() != right_id.isdigit():
                return -1 if left_id.isdigit() else 1
            return 1 if left_id > right_id else -1
        return (len(left_pre) > len(right_pre)) - (len(left_pre) < len(right_pre))
