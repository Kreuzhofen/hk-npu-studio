from __future__ import annotations

import logging
import hashlib
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from config import TEMP_DIR
from app.i18n import tr

logger = logging.getLogger("DownloadService")

ProgressCallback = Callable[..., None]


class DownloadErrorCode:
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    FILE_EXISTS = "file_exists"
    INCOMPLETE_DOWNLOAD = "incomplete_download"
    INVALID_FILE = "invalid_file"
    CANCELLED = "cancelled"


class DownloadError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class DownloadResult:
    success: bool
    path: Path | None = None
    bytes_downloaded: int = 0
    total_bytes: int | None = None
    error_code: str | None = None
    message: str = ""


class DownloadService:
    """
    Small standard-library download helper for future AI package downloads.
    Downloads are staged in temp/downloads before ModelInstallService installs them.
    """

    def __init__(self, download_dir: Path | None = None, timeout: float = 30.0) -> None:
        self.download_dir = download_dir or (TEMP_DIR / "downloads")
        self.timeout = timeout
        self._cancel_requested = False

    def cancel(self) -> None:
        self._cancel_requested = True

    def reset_cancel(self) -> None:
        self._cancel_requested = False

    def download(
        self,
        url: str,
        filename: str | None = None,
        progress_callback: ProgressCallback | None = None,
        overwrite: bool = False,
        expected_sha256: str | None = None,
        resume: bool = True,
        require_checksum: bool = True,
    ) -> DownloadResult:
        self.reset_cancel()
        try:
            return self._download(
                url, filename, progress_callback, overwrite, expected_sha256, resume,
                require_checksum,
            )
        except DownloadError as exc:
            logger.error("Download failed: %s", exc.message)
            return DownloadResult(
                success=False,
                error_code=exc.code,
                message=exc.message,
            )

    def _download(
        self,
        url: str,
        filename: str | None,
        progress_callback: ProgressCallback | None,
        overwrite: bool,
        expected_sha256: str | None,
        resume: bool,
        require_checksum: bool,
    ) -> DownloadResult:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise DownloadError(
                DownloadErrorCode.INVALID_FILE,
                f"Unsupported download URL scheme: {parsed.scheme or '<empty>'}",
            )

        target_name = filename or Path(urllib.parse.unquote(parsed.path)).name
        if not target_name:
            raise DownloadError(
                DownloadErrorCode.INVALID_FILE,
                "Download URL does not contain a valid file name.",
            )

        self.download_dir.mkdir(parents=True, exist_ok=True)
        target_path = self.download_dir / target_name
        partial_path = target_path.with_suffix(target_path.suffix + ".part")

        if target_path.exists() and not overwrite:
            raise DownloadError(
                DownloadErrorCode.FILE_EXISTS,
                f"Download target already exists: {target_path}",
            )

        if partial_path.exists() and not resume:
            partial_path.unlink()

        existing_bytes = partial_path.stat().st_size if partial_path.exists() else 0
        headers = {"User-Agent": "SnapdragonAIStudio/2.0"}
        if existing_bytes:
            headers["Range"] = f"bytes={existing_bytes}-"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status = getattr(response, "status", None)
                resumed = bool(existing_bytes and status == 206)
                response_bytes = self._read_content_length(response)
                bytes_downloaded = existing_bytes if resumed else 0
                total_bytes = (
                    bytes_downloaded + response_bytes
                    if resumed and response_bytes is not None
                    else response_bytes
                )

                with open(partial_path, "ab" if resumed else "wb") as out_file:
                    while True:
                        if self._cancel_requested:
                            raise DownloadError(
                                DownloadErrorCode.CANCELLED,
                                f"Download cancelled: {url}",
                            )

                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break

                        out_file.write(chunk)
                        bytes_downloaded += len(chunk)
                        self._emit_progress(progress_callback, bytes_downloaded, total_bytes)

        except TimeoutError as exc:
            raise DownloadError(DownloadErrorCode.TIMEOUT, f"Download timed out: {url}") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise DownloadError(DownloadErrorCode.TIMEOUT, f"Download timed out: {url}") from exc
            raise DownloadError(
                DownloadErrorCode.NETWORK_ERROR,
                f"Network error while downloading {url}: {exc}",
            ) from exc
        except OSError as exc:
            raise DownloadError(
                DownloadErrorCode.NETWORK_ERROR,
                f"File or network error while downloading {url}: {exc}",
            ) from exc
        except DownloadError:
            raise

        if not partial_path.exists() or partial_path.stat().st_size <= 0:
            self._cleanup_partial(partial_path)
            raise DownloadError(
                DownloadErrorCode.INVALID_FILE,
                "Downloaded file is missing or empty.",
            )

        final_size = partial_path.stat().st_size
        if total_bytes is not None and final_size != total_bytes:
            raise DownloadError(
                DownloadErrorCode.INCOMPLETE_DOWNLOAD,
                f"Incomplete download: expected {total_bytes} bytes, got {final_size} bytes.",
            )

        if require_checksum and not self._valid_sha256(expected_sha256):
            self._cleanup_partial(partial_path)
            raise DownloadError(
                DownloadErrorCode.INVALID_FILE,
                "A valid SHA-256 checksum is required before registration.",
            )
        actual_sha256 = self._sha256(partial_path) if expected_sha256 else ""
        if expected_sha256 and actual_sha256 != expected_sha256.lower():
            self._cleanup_partial(partial_path)
            raise DownloadError(
                DownloadErrorCode.INVALID_FILE,
                f"SHA-256 mismatch: expected {expected_sha256.lower()}, got {actual_sha256}.",
            )

        if target_path.exists() and overwrite:
            if target_path.is_dir():
                raise DownloadError(
                    DownloadErrorCode.FILE_EXISTS,
                    f"Download target is an existing directory: {target_path}",
                )
            target_path.unlink()

        os.replace(partial_path, target_path)
        self._emit_progress(progress_callback, final_size, total_bytes)

        return DownloadResult(
            success=True,
            path=target_path,
            bytes_downloaded=final_size,
            total_bytes=total_bytes,
            message=tr(
                "package_downloaded_to",
                "Paket heruntergeladen nach {path}",
                path=target_path,
            ),
        )

    @staticmethod
    def _read_content_length(response: object) -> int | None:
        try:
            value = response.headers.get("Content-Length")  # type: ignore[attr-defined]
        except AttributeError:
            return None
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _emit_progress(
        progress_callback: ProgressCallback | None,
        bytes_downloaded: int,
        total_bytes: int | None,
    ) -> None:
        if not progress_callback:
            return
        percent = 0.0 if not total_bytes else min(100.0, (bytes_downloaded / total_bytes) * 100)
        try:
            progress_callback(bytes_downloaded, total_bytes, percent)
        except TypeError:
            progress_callback(percent)

    @staticmethod
    def _cleanup_partial(path: Path) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            logger.warning("Failed to remove partial download: %s", path)

    @staticmethod
    def _valid_sha256(value: str | None) -> bool:
        return bool(
            value
            and len(value) == 64
            and all(character in "0123456789abcdefABCDEF" for character in value)
        )

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
