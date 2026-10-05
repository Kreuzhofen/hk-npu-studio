from __future__ import annotations

import hashlib
import json
import re
import subprocess
import urllib.error
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
GITHUB_RELEASES_URL = (
    "https://api.github.com/repos/Kreuzhofen/hk-npu-studio/releases"
)
_SEMVER = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?$"
)
_HISTORIC_RC = re.compile(
    r"^rc\.?(?P<number>\d+)(?P<suffix>[A-Za-z]*)$", re.IGNORECASE
)
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_RELEASES_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class ApplicationUpdateManifest:
    version: str
    architecture: str
    package_url: str
    sha256: str
    asset_name: str = ""
    asset_size: int = 0
    release_name: str = ""
    tag: str = ""
    prerelease: bool = False
    release_notes: str = ""
    release_url: str = ""


@dataclass(frozen=True)
class ApplicationUpdateCheck:
    available: bool
    message: str
    manifest: ApplicationUpdateManifest | None = None
    error_code: str | None = None


@dataclass(frozen=True)
class ApplicationUpdateStage:
    success: bool
    message: str
    installer_path: Path | None = None
    error_code: str | None = None


@dataclass(frozen=True)
class ApplicationUpdateLaunch:
    success: bool
    message: str
    error_code: str | None = None


class ApplicationUpdateService:
    """Fail-closed RC update checker and verified installer staging service."""

    def __init__(
        self,
        *,
        current_version: str = RELEASE.package_version,
        architecture: str = RELEASE.architecture,
        download_service: DownloadService | None = None,
        opener=urllib.request.urlopen,
        popen=subprocess.Popen,
    ) -> None:
        self.current_version = current_version
        self.architecture = architecture.casefold()
        self.download_service = download_service or DownloadService(
            TEMP_DIR / "application_updates"
        )
        self._opener = opener
        self._popen = popen
        self._verified_installers: dict[Path, str] = {}

    def fetch_latest_github_release(
        self, api_url: str = GITHUB_RELEASES_URL
    ) -> ApplicationUpdateCheck:
        parsed = urllib.parse.urlparse(api_url)
        if parsed.scheme != "https" or not parsed.netloc:
            return ApplicationUpdateCheck(
                False, "GitHub-Updateprüfung erfordert HTTPS.", error_code="https_required"
            )
        try:
            request = urllib.request.Request(
                api_url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": f"HKNPUStudio/{self.current_version}",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            with self._opener(request, timeout=15.0) as response:
                payload = response.read(MAX_RELEASES_BYTES + 1)
            if len(payload) > MAX_RELEASES_BYTES:
                raise ValueError("GitHub-Antwort ist zu groß.")
            return self.check_github_releases(json.loads(payload.decode("utf-8")))
        except urllib.error.HTTPError as error:
            rate_limited = error.code in (403, 429)
            message = (
                "GitHub API-Limit erreicht."
                if rate_limited
                else f"Verbindung zu GitHub fehlgeschlagen: HTTP {error.code}"
            )
            logger.warning("GitHub-Updateprüfung fehlgeschlagen | error=%s", error)
            return ApplicationUpdateCheck(
                False, message, error_code="rate_limit" if rate_limited else "network"
            )
        except (OSError, urllib.error.URLError) as error:
            logger.warning("GitHub-Updateprüfung fehlgeschlagen | error=%s", error)
            return ApplicationUpdateCheck(
                False,
                f"Verbindung zu GitHub fehlgeschlagen: {error}",
                error_code="network",
            )
        except (UnicodeError, json.JSONDecodeError, ValueError) as error:
            logger.warning("GitHub-Release-Antwort ungültig | error=%s", error)
            return ApplicationUpdateCheck(
                False,
                f"GitHub-Release-Antwort ist ungültig: {error}",
                error_code="invalid_response",
            )

    def check_github_releases(self, raw: Any) -> ApplicationUpdateCheck:
        if not isinstance(raw, list):
            return ApplicationUpdateCheck(
                False,
                "GitHub-Release-Antwort ist ungültig.",
                error_code="invalid_response",
            )

        candidates: list[tuple[str, dict[str, Any]]] = []
        for release in raw:
            if not isinstance(release, dict) or release.get("draft") is True:
                continue
            version = self._normalize_tag(release.get("tag_name"))
            if version and self._compare_versions(version, self.current_version) > 0:
                candidates.append((version, release))

        if not candidates:
            return ApplicationUpdateCheck(
                False, "HK NPU STUDIO ist auf dem neuesten Stand."
            )

        best_version, best_release = candidates[0]
        for version, release in candidates[1:]:
            if self._compare_versions(version, best_version) > 0:
                best_version, best_release = version, release

        asset = self._select_installer_asset(
            best_release.get("assets"), best_version
        )
        if asset is None:
            return ApplicationUpdateCheck(
                False,
                "Kein passender ARM64-Installer gefunden.",
                error_code="installer_missing",
            )

        package_url = str(asset.get("browser_download_url", "")).strip()
        parsed = urllib.parse.urlparse(package_url)
        if parsed.scheme != "https" or not parsed.netloc:
            return ApplicationUpdateCheck(
                False,
                "Update-Paket erfordert eine absolute HTTPS-URL.",
                error_code="https_required",
            )
        sha256 = self._parse_github_digest(str(asset.get("digest", "")).strip())
        if sha256 is None:
            return ApplicationUpdateCheck(
                False,
                "Der ARM64-Installer besitzt keinen gültigen SHA-256-Digest.",
                error_code="digest_missing",
            )

        manifest = ApplicationUpdateManifest(
            version=best_version,
            architecture=self.architecture,
            package_url=package_url,
            sha256=sha256,
            asset_name=str(asset.get("name", "")).strip(),
            asset_size=max(0, self._safe_int(asset.get("size"))),
            release_name=str(
                best_release.get("name")
                or best_release.get("tag_name")
                or best_version
            ),
            tag=str(best_release.get("tag_name", "")).strip(),
            prerelease=bool(best_release.get("prerelease")),
            release_notes=str(best_release.get("body") or "").strip(),
            release_url=str(best_release.get("html_url") or "").strip(),
        )
        return ApplicationUpdateCheck(
            True, f"Update {best_version} ist verfügbar.", manifest
        )

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
        filename = manifest.asset_name or (
            f"HKNPUStudio-{manifest.version}-ARM64-Setup.exe"
        )
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
                False,
                result.message or "Update-Download fehlgeschlagen.",
                error_code=getattr(result, "error_code", None),
            )
        resolved = result.path.resolve()
        self._verified_installers[resolved] = manifest.sha256.casefold()
        return ApplicationUpdateStage(
            True,
            "Update-Installer wurde verifiziert und bereitgestellt.",
            result.path,
        )

    def launch_installer(self, installer_path: str | Path) -> ApplicationUpdateLaunch:
        path = Path(installer_path).resolve()
        expected_sha256 = self._verified_installers.get(path)
        if expected_sha256 is None or not path.is_file():
            return ApplicationUpdateLaunch(
                False,
                "Installer ist nicht als verifizierter Download registriert.",
                "integrity",
            )
        try:
            if self._sha256(path) != expected_sha256:
                return ApplicationUpdateLaunch(
                    False,
                    "Integritätsprüfung vor Installerstart fehlgeschlagen.",
                    "integrity",
                )
            self._popen([str(path), "/SILENT"], shell=False)
            return ApplicationUpdateLaunch(True, "Installer wurde gestartet.")
        except OSError as error:
            logger.error("Installerstart fehlgeschlagen | error=%s", error)
            return ApplicationUpdateLaunch(
                False,
                f"Installer konnte nicht gestartet werden: {error}",
                "installer_launch",
            )

    def cancel_download(self) -> None:
        self.download_service.cancel()

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
    def _normalize_tag(value: Any) -> str | None:
        tag = str(value or "").strip()
        if tag[:1].casefold() == "v":
            tag = tag[1:]
        match = _SEMVER.fullmatch(tag)
        if match is None:
            return None
        pre = match.group("pre")
        rc = _HISTORIC_RC.fullmatch(pre or "")
        if rc is None:
            return tag
        core = ".".join(match.group(name) for name in ("major", "minor", "patch"))
        return f"{core}-rc.{int(rc.group('number'))}{rc.group('suffix').casefold()}"

    @staticmethod
    def _select_installer_asset(assets: Any, version: str) -> dict[str, Any] | None:
        if not isinstance(assets, list):
            return None
        by_name = {
            str(asset.get("name", "")).casefold(): asset
            for asset in assets
            if isinstance(asset, dict)
        }
        for expected in (
            f"HKNPUStudio-{version}-ARM64-Setup.exe",
            f"SnapdragonAIStudio-{version}-ARM64-Setup.exe",
        ):
            asset = by_name.get(expected.casefold())
            if asset is not None:
                return asset
        return None

    @staticmethod
    def _parse_github_digest(value: str) -> str | None:
        algorithm, separator, digest = value.partition(":")
        digest = digest.casefold()
        if algorithm.casefold() != "sha256" or separator != ":":
            return None
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            return None
        return digest

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _compare_versions(left: str, right: str) -> int:
        def parse(value: str):
            match = _SEMVER.fullmatch(value)
            if match is None:
                raise ValueError(f"Ungültige Version: {value}")
            core = tuple(int(match.group(name)) for name in ("major", "minor", "patch"))
            pre = match.group("pre")
            identifiers = tuple(pre.split(".")) if pre else ()
            rc_match = _HISTORIC_RC.fullmatch(pre or "")
            rc = (
                (int(rc_match.group("number")), rc_match.group("suffix").casefold())
                if rc_match is not None
                else None
            )
            return core, identifiers, rc

        left_core, left_pre, left_rc = parse(left)
        right_core, right_pre, right_rc = parse(right)
        if left_core != right_core:
            return 1 if left_core > right_core else -1
        if not left_pre and right_pre:
            return 1
        if left_pre and not right_pre:
            return -1
        if left_rc is not None and right_rc is not None:
            if left_rc[0] != right_rc[0]:
                return 1 if left_rc[0] > right_rc[0] else -1
            if left_rc[1] != right_rc[1]:
                return 1 if left_rc[1] > right_rc[1] else -1
            return 0
        for left_id, right_id in zip(left_pre, right_pre):
            if left_id == right_id:
                continue
            if left_id.isdigit() and right_id.isdigit():
                return 1 if int(left_id) > int(right_id) else -1
            if left_id.isdigit() != right_id.isdigit():
                return -1 if left_id.isdigit() else 1
            return 1 if left_id > right_id else -1
        return (len(left_pre) > len(right_pre)) - (len(left_pre) < len(right_pre))
