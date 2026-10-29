from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from engine.download_service import DownloadErrorCode, DownloadService


class Response:
    def __init__(self, payload: bytes, status: int = 200):
        self.payload = io.BytesIO(payload)
        self.status = status
        self.headers = {"Content-Length": str(len(payload))}

    def read(self, amount=None):
        return self.payload.read(amount)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def close(self):
        pass


class RangeServer:
    """Serves one payload and honours byte ranges like a static file server."""

    def __init__(
        self,
        payload: bytes,
        honour_ranges: bool = True,
        truncate_within: tuple[int, int] | None = None,
        truncate_times: int = 1,
    ):
        self.payload = payload
        self.honour_ranges = honour_ranges
        self.truncate_within = truncate_within
        self.truncate_times = truncate_times
        self.ranges = []

    def urlopen(self, request, timeout=None):
        header = request.get_header("Range")
        if not header or not self.honour_ranges:
            response = Response(self.payload)
            response.headers["Accept-Ranges"] = "bytes"
            return response
        start_text, _, end_text = header.removeprefix("bytes=").partition("-")
        start = int(start_text)
        end = int(end_text) + 1 if end_text else len(self.payload)
        self.ranges.append((start, end))
        body = self.payload[start:end]
        if self.truncate_within and self.truncate_times and self.truncate_within[0] <= start < self.truncate_within[1]:
            self.truncate_times -= 1
            body = body[: len(body) // 2]
        response = Response(body, status=206)
        response.headers["Content-Range"] = f"bytes {start}-{end - 1}/{len(self.payload)}"
        return response


def segmented_service(directory: str) -> DownloadService:
    return DownloadService(Path(directory), segments=4, segment_min_bytes=1)


class DownloadServiceIntegrityTests(unittest.TestCase):
    def test_hash_is_required_before_final_file_is_registered(self):
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", return_value=Response(b"package")
        ):
            service = DownloadService(Path(directory))
            result = service.download("https://example.com/model.bin")

            self.assertFalse(result.success)
            self.assertEqual(result.error_code, DownloadErrorCode.INVALID_FILE)
            self.assertFalse((Path(directory) / "model.bin").exists())

    def test_valid_hash_promotes_partial_file_atomically(self):
        payload = b"verified package"
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", return_value=Response(payload)
        ):
            service = DownloadService(Path(directory))
            result = service.download(
                "https://example.com/model.bin", expected_sha256=digest
            )

            self.assertTrue(result.success)
            self.assertEqual(result.path.read_bytes(), payload)
            self.assertFalse((Path(directory) / "model.bin.part").exists())

    def test_package_staging_can_defer_integrity_to_package_installer(self):
        payload = b"package validated by the model installer"
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", return_value=Response(payload)
        ):
            service = DownloadService(Path(directory))
            result = service.download(
                "https://example.com/model.zip", require_checksum=False
            )

            self.assertTrue(result.success)
            self.assertEqual(result.path.read_bytes(), payload)
            self.assertFalse((Path(directory) / "model.zip.part").exists())

    def test_optional_hf_token_is_forwarded_as_bearer_auth(self):
        payload = b"gated package"
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", return_value=Response(payload)
        ), patch("urllib.request.Request", wraps=urllib.request.Request) as request:
            service = DownloadService(Path(directory))
            result = service.download(
                "https://huggingface.co/model.zip",
                expected_sha256=digest,
                authorization_token="hf_verified",
            )
        self.assertTrue(result.success)
        self.assertEqual(request.call_args.kwargs["headers"]["Authorization"], "Bearer hf_verified")

    def test_hash_mismatch_removes_untrusted_partial(self):
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", return_value=Response(b"tampered")
        ):
            service = DownloadService(Path(directory))
            result = service.download(
                "https://example.com/model.bin", expected_sha256="0" * 64
            )

            self.assertFalse(result.success)
            self.assertEqual(result.error_code, DownloadErrorCode.INVALID_FILE)
            self.assertFalse((Path(directory) / "model.bin").exists())
            self.assertFalse((Path(directory) / "model.bin.part").exists())

    def test_existing_complete_staged_file_is_reused_by_remote_size(self):
        payload = b"complete staged package"
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", return_value=Response(payload)
        ):
            target = Path(directory) / "model.zip"
            target.write_bytes(payload)
            service = DownloadService(Path(directory))
            result = service.download(
                "https://example.com/model.zip", require_checksum=False
            )

            self.assertTrue(result.success)
            self.assertEqual(result.path, target)
            self.assertEqual(result.total_bytes, len(payload))
            self.assertEqual(target.read_bytes(), payload)

    def test_existing_file_with_wrong_checksum_is_not_reused(self):
        payload = b"untrusted existing package"
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen"
        ) as urlopen:
            target = Path(directory) / "model.bin"
            target.write_bytes(payload)
            service = DownloadService(Path(directory))
            result = service.download(
                "https://example.com/model.bin", expected_sha256="0" * 64
            )

            self.assertFalse(result.success)
            self.assertEqual(result.error_code, DownloadErrorCode.INVALID_FILE)
            self.assertEqual(target.read_bytes(), payload)
            urlopen.assert_not_called()

    def test_partial_download_still_resumes_with_range_request(self):
        complete = b"complete payload"
        prefix = complete[:8]
        remainder = complete[8:]
        digest = hashlib.sha256(complete).hexdigest()
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", return_value=Response(remainder, status=206)
        ), patch("urllib.request.Request", wraps=urllib.request.Request) as request:
            partial = Path(directory) / "model.bin.part"
            partial.write_bytes(prefix)
            service = DownloadService(Path(directory))
            result = service.download(
                "https://example.com/model.bin", expected_sha256=digest
            )

            self.assertTrue(result.success)
            self.assertEqual(result.path.read_bytes(), complete)
            self.assertEqual(request.call_args.kwargs["headers"]["Range"], f"bytes={len(prefix)}-")

    def test_existing_file_outside_managed_staging_is_not_reused(self):
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen"
        ) as urlopen:
            root = Path(directory)
            staging = root / "downloads"
            staging.mkdir()
            outside = root / "outside.bin"
            outside.write_bytes(b"external")
            service = DownloadService(staging)
            result = service.download(
                "https://example.com/outside.bin",
                filename="../outside.bin",
                require_checksum=False,
            )

            self.assertFalse(result.success)
            self.assertEqual(result.error_code, DownloadErrorCode.INVALID_FILE)
            urlopen.assert_not_called()

    def test_large_download_is_fetched_in_parallel_segments(self):
        payload = bytes(range(256)) * 401
        server = RangeServer(payload)
        progress = []
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", side_effect=server.urlopen
        ):
            result = segmented_service(directory).download(
                "https://example.com/model.zip",
                require_checksum=False,
                progress_callback=lambda done, total, percent: progress.append(done),
            )

            self.assertTrue(result.success, result.message)
            self.assertEqual(result.path.read_bytes(), payload)
            self.assertEqual(sorted(path.name for path in Path(directory).iterdir()), ["model.zip"])
        # Segment 0 continues on the initial response; the other three use range requests.
        self.assertEqual(len(server.ranges), 3)
        self.assertEqual(progress[-1], len(payload))

    def test_segmented_download_adopts_existing_partial_as_first_segment(self):
        payload = bytes(range(256)) * 401
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", side_effect=RangeServer(payload).urlopen
        ) as urlopen:
            (Path(directory) / "model.zip.part").write_bytes(payload[:1000])
            result = segmented_service(directory).download(
                "https://example.com/model.zip", require_checksum=False
            )

            self.assertTrue(result.success, result.message)
            self.assertEqual(result.path.read_bytes(), payload)
        self.assertEqual(urlopen.call_args_list[0].args[0].get_header("Range"), "bytes=1000-")

    def test_interrupted_segment_is_retried_from_its_offset(self):
        payload = bytes(range(256)) * 401
        segment_size = -(-len(payload) // 4)
        server = RangeServer(payload, truncate_within=(2 * segment_size, 3 * segment_size))
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", side_effect=server.urlopen
        ), patch.object(DownloadService, "_RETRY_DELAY_SECONDS", 0):
            result = segmented_service(directory).download(
                "https://example.com/model.zip", require_checksum=False
            )

            self.assertTrue(result.success, result.message)
            self.assertEqual(result.path.read_bytes(), payload)
        retried = [start for start, _ in server.ranges if 2 * segment_size < start < 3 * segment_size]
        self.assertEqual(retried, [2 * segment_size + segment_size // 2])

    def test_segment_that_keeps_progressing_is_not_limited_by_retry_count(self):
        payload = bytes(range(256)) * 401
        segment_size = -(-len(payload) // 4)
        server = RangeServer(
            payload, truncate_within=(2 * segment_size, 3 * segment_size), truncate_times=6
        )
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", side_effect=server.urlopen
        ), patch.object(DownloadService, "_RETRY_DELAY_SECONDS", 0):
            service = DownloadService(Path(directory), segments=4, segment_min_bytes=1, retries=3)
            result = service.download("https://example.com/model.zip", require_checksum=False)

            self.assertTrue(result.success, result.message)
            self.assertEqual(result.path.read_bytes(), payload)
        retried = [start for start, _ in server.ranges if 2 * segment_size < start < 3 * segment_size]
        self.assertEqual(len(retried), 6)

    def test_initial_request_is_retried_after_connect_timeout(self):
        payload = b"package behind a flaky connection"
        server = RangeServer(payload)
        failures = [urllib.error.URLError(TimeoutError("timed out"))]

        def flaky_urlopen(request, timeout=None):
            if failures:
                raise failures.pop()
            return server.urlopen(request, timeout)

        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", side_effect=flaky_urlopen
        ), patch.object(DownloadService, "_RETRY_DELAY_SECONDS", 0):
            result = DownloadService(Path(directory)).download(
                "https://example.com/model.zip", require_checksum=False
            )

            self.assertTrue(result.success, result.message)
            self.assertEqual(result.path.read_bytes(), payload)

    def test_client_errors_are_not_retried(self):
        not_found = urllib.error.HTTPError("https://example.com/model.zip", 404, "Not Found", {}, None)
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", side_effect=not_found
        ) as urlopen, patch.object(DownloadService, "_RETRY_DELAY_SECONDS", 0):
            result = DownloadService(Path(directory)).download(
                "https://example.com/model.zip", require_checksum=False
            )

            self.assertFalse(result.success)
            self.assertEqual(result.error_code, DownloadErrorCode.NETWORK_ERROR)
        self.assertEqual(urlopen.call_count, 1)

    def test_server_ignoring_segment_ranges_fails_without_corrupting_file(self):
        payload = bytes(range(256)) * 401
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", side_effect=RangeServer(payload, honour_ranges=False).urlopen
        ):
            result = segmented_service(directory).download(
                "https://example.com/model.zip", require_checksum=False
            )

            self.assertFalse(result.success)
            self.assertEqual(result.error_code, DownloadErrorCode.NETWORK_ERROR)
            self.assertFalse((Path(directory) / "model.zip").exists())

    def test_small_download_stays_single_stream(self):
        payload = b"small package"
        server = RangeServer(payload)
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen", side_effect=server.urlopen
        ):
            result = DownloadService(Path(directory)).download(
                "https://example.com/model.zip", require_checksum=False
            )

            self.assertTrue(result.success, result.message)
            self.assertEqual(result.path.read_bytes(), payload)
        self.assertEqual(server.ranges, [])


if __name__ == "__main__":
    unittest.main()
