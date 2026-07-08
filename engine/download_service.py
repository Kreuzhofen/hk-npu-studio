from __future__ import annotations

import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from config import TEMP_DIR

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
    ) -> DownloadResult:
        self.reset_cancel()
        try:
            return self._download(url, filename, progress_callback, overwrite)
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

        if partial_path.exists():
            partial_path.unlink()

        request = urllib.request.Request(url, headers={"User-Agent": "SnapdragonAIStudio/2.0"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                total_bytes = self._read_content_length(response)
                bytes_downloaded = 0

                with open(partial_path, "wb") as out_file:
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
            self._cleanup_partial(partial_path)
            raise DownloadError(DownloadErrorCode.TIMEOUT, f"Download timed out: {url}") from exc
        except urllib.error.URLError as exc:
            self._cleanup_partial(partial_path)
            if isinstance(exc.reason, TimeoutError):
                raise DownloadError(DownloadErrorCode.TIMEOUT, f"Download timed out: {url}") from exc
            raise DownloadError(
                DownloadErrorCode.NETWORK_ERROR,
                f"Network error while downloading {url}: {exc}",
            ) from exc
        except OSError as exc:
            self._cleanup_partial(partial_path)
            raise DownloadError(
                DownloadErrorCode.NETWORK_ERROR,
                f"File or network error while downloading {url}: {exc}",
            ) from exc
        except DownloadError:
            self._cleanup_partial(partial_path)
            raise

        if not partial_path.exists() or partial_path.stat().st_size <= 0:
            self._cleanup_partial(partial_path)
            raise DownloadError(
                DownloadErrorCode.INVALID_FILE,
                "Downloaded file is missing or empty.",
            )

        final_size = partial_path.stat().st_size
        if total_bytes is not None and final_size != total_bytes:
            self._cleanup_partial(partial_path)
            raise DownloadError(
                DownloadErrorCode.INCOMPLETE_DOWNLOAD,
                f"Incomplete download: expected {total_bytes} bytes, got {final_size} bytes.",
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
            message=f"Downloaded package to {target_path}",
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
