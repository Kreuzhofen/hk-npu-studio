from __future__ import annotations

import http.client
import logging
import hashlib
import os
import shutil
import threading
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import FIRST_EXCEPTION, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from config import (
    DOWNLOAD_SEGMENT_MIN_BYTES,
    DOWNLOAD_SEGMENT_RETRIES,
    DOWNLOAD_SEGMENTS,
    TEMP_DIR,
)
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

    Large files from servers that accept byte ranges are fetched as parallel segments:
    segment 0 is written to the regular .part file and segments 1..n to .part.1 .. .part.n,
    which are appended in order once all are complete. The .part file therefore always
    holds a valid prefix of the download, so single-stream resume keeps working.
    """

    _PROGRESS_INTERVAL_SECONDS = 0.5
    _RETRY_DELAY_SECONDS = 1.0

    def __init__(
        self,
        download_dir: Path | None = None,
        timeout: float = 30.0,
        segments: int = DOWNLOAD_SEGMENTS,
        segment_min_bytes: int = DOWNLOAD_SEGMENT_MIN_BYTES,
        segment_retries: int = DOWNLOAD_SEGMENT_RETRIES,
    ) -> None:
        self.download_dir = download_dir or (TEMP_DIR / "downloads")
        self.timeout = timeout
        self.segments = segments
        self.segment_min_bytes = segment_min_bytes
        self.segment_retries = segment_retries
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
        authorization_token: str | None = None,
    ) -> DownloadResult:
        self.reset_cancel()
        try:
            return self._download(
                url, filename, progress_callback, overwrite, expected_sha256, resume,
                require_checksum,
                authorization_token,
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
        authorization_token: str | None,
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

        headers = {"User-Agent": "HKNPUStudio/2.0"}
        if authorization_token:
            headers["Authorization"] = f"Bearer {authorization_token}"

        if target_path.exists() and not overwrite:
            return self._reuse_existing_target(
                target_path,
                urllib.request.Request(url, headers=headers),
                progress_callback,
                expected_sha256,
                require_checksum,
            )

        if partial_path.exists() and not resume:
            partial_path.unlink()
            self._cleanup_segments(partial_path)

        existing_bytes = partial_path.stat().st_size if partial_path.exists() else 0
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

                if self._can_segment(response, status, existing_bytes, total_bytes):
                    self._download_segments(
                        url, headers, response, partial_path, existing_bytes, total_bytes,
                        progress_callback,
                    )
                else:
                    self._cleanup_segments(partial_path)
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

    def _reuse_existing_target(
        self,
        target_path: Path,
        request: urllib.request.Request,
        progress_callback: ProgressCallback | None,
        expected_sha256: str | None,
        require_checksum: bool,
    ) -> DownloadResult:
        try:
            target_path.resolve().relative_to(self.download_dir.resolve())
        except (OSError, ValueError) as exc:
            raise DownloadError(
                DownloadErrorCode.INVALID_FILE,
                f"Existing download target is outside managed staging: {target_path}",
            ) from exc
        if target_path.parent.resolve() != self.download_dir.resolve() or not target_path.is_file():
            raise DownloadError(
                DownloadErrorCode.INVALID_FILE,
                f"Existing download target is not a managed staging file: {target_path}",
            )

        file_size = target_path.stat().st_size
        if self._valid_sha256(expected_sha256):
            actual_sha256 = self._sha256(target_path)
            if actual_sha256 != expected_sha256.lower():
                raise DownloadError(
                    DownloadErrorCode.INVALID_FILE,
                    f"SHA-256 mismatch: expected {expected_sha256.lower()}, got {actual_sha256}.",
                )
            total_bytes = file_size
        elif require_checksum:
            raise DownloadError(
                DownloadErrorCode.INVALID_FILE,
                "A valid SHA-256 checksum is required before registration.",
            )
        else:
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    total_bytes = self._read_content_length(response)
            except TimeoutError as exc:
                raise DownloadError(DownloadErrorCode.TIMEOUT, f"Download timed out: {request.full_url}") from exc
            except urllib.error.URLError as exc:
                code = DownloadErrorCode.TIMEOUT if isinstance(exc.reason, TimeoutError) else DownloadErrorCode.NETWORK_ERROR
                raise DownloadError(code, f"Unable to validate existing download {request.full_url}: {exc}") from exc
            except OSError as exc:
                raise DownloadError(
                    DownloadErrorCode.NETWORK_ERROR,
                    f"Unable to validate existing download {request.full_url}: {exc}",
                ) from exc
            if total_bytes is None or file_size <= 0 or file_size != total_bytes:
                raise DownloadError(
                    DownloadErrorCode.FILE_EXISTS,
                    f"Existing download could not be verified as complete: {target_path}",
                )

        logger.info("Reusing existing completed download: %s", target_path)
        self._emit_progress(progress_callback, file_size, total_bytes)
        return DownloadResult(
            success=True,
            path=target_path,
            bytes_downloaded=file_size,
            total_bytes=total_bytes,
            message=tr(
                "package_downloaded_to",
                "Paket heruntergeladen nach {path}",
                path=target_path,
            ),
        )

    def _can_segment(
        self,
        response: object,
        status: int | None,
        existing_bytes: int,
        total_bytes: int | None,
    ) -> bool:
        if self.segments < 2 or total_bytes is None or total_bytes < self.segment_min_bytes:
            return False
        if status == 206:
            ranges_supported = existing_bytes > 0
        else:
            try:
                accept_ranges = response.headers.get("Accept-Ranges") or ""  # type: ignore[attr-defined]
            except AttributeError:
                accept_ranges = ""
            ranges_supported = not existing_bytes and accept_ranges.strip().lower() == "bytes"
        # An existing .part can only be adopted while it still fits into segment 0.
        return ranges_supported and existing_bytes <= self._segment_ranges(total_bytes)[0][1]

    def _segment_ranges(self, total_bytes: int) -> list[tuple[int, int]]:
        """Return [start, end) byte ranges; the layout only depends on the total size."""
        segment_size = -(-total_bytes // self.segments)
        return [
            (start, min(start + segment_size, total_bytes))
            for start in range(0, total_bytes, segment_size)
        ]

    @staticmethod
    def _segment_paths(partial_path: Path, count: int) -> list[Path]:
        return [partial_path] + [
            partial_path.with_name(f"{partial_path.name}.{index}") for index in range(1, count)
        ]

    @staticmethod
    def _cleanup_segments(partial_path: Path) -> None:
        if not partial_path.parent.is_dir():
            return
        prefix = partial_path.name + "."
        for path in partial_path.parent.iterdir():
            if path.name.startswith(prefix) and path.name[len(prefix):].isdigit():
                DownloadService._cleanup_partial(path)

    def _download_segments(
        self,
        url: str,
        headers: dict[str, str],
        first_response: object,
        partial_path: Path,
        existing_bytes: int,
        total_bytes: int,
        progress_callback: ProgressCallback | None,
    ) -> None:
        ranges = self._segment_ranges(total_bytes)
        paths = self._segment_paths(partial_path, len(ranges))
        for (start, end), path in zip(ranges[1:], paths[1:]):
            if path.exists() and path.stat().st_size > end - start:
                path.unlink()

        downloaded = existing_bytes + sum(path.stat().st_size for path in paths[1:] if path.exists())
        downloaded_lock = threading.Lock()
        stop = threading.Event()
        logger.info(
            "Downloading %s in %d parallel segments (%d of %d bytes already present).",
            url, len(ranges), downloaded, total_bytes,
        )

        def on_chunk(size: int) -> None:
            nonlocal downloaded
            with downloaded_lock:
                downloaded += size

        # Progress is emitted from this thread only, so callers keep a single-threaded callback.
        with ThreadPoolExecutor(max_workers=len(ranges), thread_name_prefix="DownloadSegment") as pool:
            futures = [
                pool.submit(
                    self._download_segment, url, headers, path, start, end, on_chunk, stop,
                    first_response if index == 0 else None,
                )
                for index, ((start, end), path) in enumerate(zip(ranges, paths))
            ]
            try:
                pending = set(futures)
                while pending:
                    done, pending = wait(
                        pending, timeout=self._PROGRESS_INTERVAL_SECONDS, return_when=FIRST_EXCEPTION
                    )
                    self._emit_progress(progress_callback, downloaded, total_bytes)
                    for future in done:
                        future.result()
            finally:
                stop.set()

        for (start, end), path in zip(ranges, paths):
            size = path.stat().st_size if path.exists() else 0
            if size != end - start:
                raise DownloadError(
                    DownloadErrorCode.INCOMPLETE_DOWNLOAD,
                    f"Incomplete download segment {path.name}: expected {end - start} bytes, got {size} bytes.",
                )
        # Appending in order keeps .part a valid prefix even if this step is interrupted.
        with open(partial_path, "ab") as out_file:
            for path in paths[1:]:
                with open(path, "rb") as segment_file:
                    shutil.copyfileobj(segment_file, out_file, 1024 * 1024)
        for path in paths[1:]:
            path.unlink()

    def _download_segment(
        self,
        url: str,
        headers: dict[str, str],
        path: Path,
        start: int,
        end: int,
        on_chunk: Callable[[int], None],
        stop: threading.Event,
        response: object | None = None,
    ) -> None:
        failures = 0
        while not stop.is_set():
            offset = start + (path.stat().st_size if path.exists() else 0)
            if offset >= end:
                return
            try:
                if response is None:
                    response = self._open_range(url, headers, offset, end)
                with response, open(path, "ab") as out_file:  # type: ignore[union-attr]
                    while offset < end and not stop.is_set():
                        if self._cancel_requested:
                            raise DownloadError(
                                DownloadErrorCode.CANCELLED,
                                f"Download cancelled: {url}",
                            )
                        chunk = response.read(min(1024 * 1024, end - offset))  # type: ignore[union-attr]
                        if not chunk:
                            break
                        out_file.write(chunk)
                        offset += len(chunk)
                        on_chunk(len(chunk))
                if offset < end and not stop.is_set():
                    raise http.client.IncompleteRead(b"", end - offset)
            except (OSError, http.client.HTTPException) as exc:
                failures += 1
                if failures > self.segment_retries:
                    if isinstance(exc, http.client.HTTPException):
                        raise DownloadError(
                            DownloadErrorCode.NETWORK_ERROR,
                            f"Network error while downloading {url}: {exc!r}",
                        ) from exc
                    raise
                logger.warning(
                    "Download segment %d-%d interrupted at byte %d (%s); retrying (%d/%d).",
                    start, end - 1, offset, exc, failures, self.segment_retries,
                )
                stop.wait(self._RETRY_DELAY_SECONDS)
            finally:
                response = None

    def _open_range(self, url: str, headers: dict[str, str], offset: int, end: int) -> object:
        request = urllib.request.Request(url, headers={**headers, "Range": f"bytes={offset}-{end - 1}"})
        response = urllib.request.urlopen(request, timeout=self.timeout)
        try:
            content_range = response.headers.get("Content-Range") or ""
        except AttributeError:
            content_range = ""
        if getattr(response, "status", None) != 206 or not content_range.startswith(f"bytes {offset}-"):
            response.close()
            raise DownloadError(
                DownloadErrorCode.NETWORK_ERROR,
                f"Server did not honour the byte range request for {url}.",
            )
        return response

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
