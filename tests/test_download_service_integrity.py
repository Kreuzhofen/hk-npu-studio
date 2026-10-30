from __future__ import annotations

import hashlib
import io
import shutil
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

from engine.download_service import DownloadErrorCode, DownloadService


class Response:
    def __init__(self, payload: bytes, status: int = 200, headers: dict[str, str] | None = None):
        self.payload = io.BytesIO(payload)
        self.status = status
        self.headers = {"Content-Length": str(len(payload))}
        if headers:
            self.headers.update(headers)
        self.closed = False

    def read(self, amount=None):
        return self.payload.read(amount)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.closed = True


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
        self.active_responses: list[Response] = []

    def urlopen(self, request, timeout=None):
        header = request.get_header("Range")
        if not header or not self.honour_ranges:
            response = Response(self.payload)
            response.headers["Accept-Ranges"] = "bytes"
            self.active_responses.append(response)
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
        self.active_responses.append(response)
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
            "urllib.request.urlopen",
            return_value=Response(
                remainder,
                status=206,
                headers={"Content-Range": f"bytes {len(prefix)}-{len(complete) - 1}/{len(complete)}"},
            ),
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

    # =========================================================================
    # FEHLERFALL 1: Download-Abbruch und Segment-Zusammenführung
    # =========================================================================

    def test_merge_interruption_and_restart_produces_identical_file(self):
        """Simuliert Abbruch waehrend des Zusammenfuehrens: Neustart erzeugt keine Duplikate."""
        payload = bytes(range(256)) * 401
        server = RangeServer(payload)

        with tempfile.TemporaryDirectory() as directory:
            service = segmented_service(directory)
            original_copy = service._copy_segment_to_target
            aborted = False

            def aborting_copy(seg_path, out_file, u):
                nonlocal aborted
                if not aborted:
                    out_file.write(seg_path.read_bytes()[:100])
                    aborted = True
                    raise OSError("Disk write failed during merge simulation")
                return original_copy(seg_path, out_file, u)

            with patch("urllib.request.urlopen", side_effect=server.urlopen), patch.object(
                service, "_copy_segment_to_target", side_effect=aborting_copy
            ):
                result1 = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )
                self.assertFalse(result1.success)
                self.assertEqual(result1.error_code, DownloadErrorCode.NETWORK_ERROR)

            # Nach Abbruch muss .part auf Segment-0-Groesse zurueckgesetzt worden sein
            partial_path = Path(directory) / "model.zip.part"
            seg0_expected = -(-len(payload) // 4)
            self.assertTrue(partial_path.exists())
            self.assertEqual(partial_path.stat().st_size, seg0_expected)

            # Neustart: saubere Fertigstellung ohne doppelte/verschobene Bytes
            with patch("urllib.request.urlopen", side_effect=server.urlopen):
                result2 = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )
                self.assertTrue(result2.success, result2.message)
                self.assertEqual(result2.path.read_bytes(), payload)
                self.assertEqual(len(result2.path.read_bytes()), len(payload))

    def test_merge_crash_with_stale_partial_prefix_recovers_without_duplicates(self):
        """Ungraceful Crash: .part hat Bytes ueber Segment 0 hinaus, Segmentdateien vorhanden."""
        payload = bytes(range(256)) * 401
        server = RangeServer(payload)
        total = len(payload)
        seg_size = -(-total // 4)

        with tempfile.TemporaryDirectory() as directory:
            partial_path = Path(directory) / "model.zip.part"
            # Segment 0 + 50 Bytes von Segment 1 bereits im .part
            partial_path.write_bytes(payload[: seg_size + 50])
            # Vollstaendige Segmentdateien auf der Platte
            (Path(directory) / "model.zip.part.1").write_bytes(payload[seg_size : 2 * seg_size])
            (Path(directory) / "model.zip.part.2").write_bytes(payload[2 * seg_size : 3 * seg_size])
            (Path(directory) / "model.zip.part.3").write_bytes(payload[3 * seg_size :])

            service = segmented_service(directory)
            with patch("urllib.request.urlopen", side_effect=server.urlopen):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )
                self.assertTrue(result.success, result.message)
                self.assertEqual(result.path.read_bytes(), payload)

    def test_cancel_during_merge_aborts_and_cleans_partial(self):
        """Cancel waehrend des Zusammenfuehrens bricht sofort ab und kuerzt .part sauber."""
        payload = bytes(range(256)) * 401
        server = RangeServer(payload)

        with tempfile.TemporaryDirectory() as directory:
            service = segmented_service(directory)
            original_copy = service._copy_segment_to_target

            def cancel_on_copy(seg_path, out_file, u):
                service.cancel()
                original_copy(seg_path, out_file, u)

            with patch("urllib.request.urlopen", side_effect=server.urlopen), patch.object(
                service, "_copy_segment_to_target", side_effect=cancel_on_copy
            ):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )
                self.assertFalse(result.success)
                self.assertEqual(result.error_code, DownloadErrorCode.CANCELLED)

            seg0_expected = -(-len(payload) // 4)
            partial_path = Path(directory) / "model.zip.part"
            self.assertTrue(partial_path.exists())
            self.assertEqual(partial_path.stat().st_size, seg0_expected)

    # =========================================================================
    # FEHLERFALL 2: Content-Range Validierung
    # =========================================================================

    def test_content_range_invalid_start_rejected(self):
        """Server sendet 206 mit falscher Startposition: Ablehnung ohne Dateikorruption."""
        payload = bytes(range(256)) * 401
        total = len(payload)

        def bad_start_urlopen(request, timeout=None):
            header = request.get_header("Range")
            if not header:
                resp = Response(payload, status=200)
                resp.headers["Accept-Ranges"] = "bytes"
                return resp
            # Antwort mit falscher Startposition (0 statt requested)
            resp = Response(payload[:500], status=206)
            resp.headers["Content-Range"] = f"bytes 0-499/{total}"
            return resp

        with tempfile.TemporaryDirectory() as directory:
            service = segmented_service(directory)
            with patch("urllib.request.urlopen", side_effect=bad_start_urlopen):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )
                self.assertFalse(result.success)
                self.assertEqual(result.error_code, DownloadErrorCode.NETWORK_ERROR)
                self.assertIn("start mismatch", result.message)

    def test_content_range_invalid_end_rejected(self):
        """Server sendet 206 mit unvollstaendiger Endposition."""
        payload = bytes(range(256)) * 401
        total = len(payload)

        def bad_end_urlopen(request, timeout=None):
            header = request.get_header("Range")
            if not header:
                resp = Response(payload, status=200)
                resp.headers["Accept-Ranges"] = "bytes"
                return resp
            # Range requested start-end, but server returns smaller end
            start_text, _, end_text = header.removeprefix("bytes=").partition("-")
            start = int(start_text)
            resp = Response(payload[start : start + 50], status=206)
            resp.headers["Content-Range"] = f"bytes {start}-{start + 49}/{total}"
            return resp

        with tempfile.TemporaryDirectory() as directory:
            service = segmented_service(directory)
            with patch("urllib.request.urlopen", side_effect=bad_end_urlopen):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )
                self.assertFalse(result.success)
                self.assertEqual(result.error_code, DownloadErrorCode.NETWORK_ERROR)
                self.assertIn("end mismatch", result.message)

    def test_content_range_invalid_total_size_rejected(self):
        """Server meldet abweichende Gesamtgroesse im Content-Range."""
        payload = bytes(range(256)) * 401

        def bad_total_urlopen(request, timeout=None):
            header = request.get_header("Range")
            if not header:
                resp = Response(payload, status=200)
                resp.headers["Accept-Ranges"] = "bytes"
                return resp
            start_text, _, end_text = header.removeprefix("bytes=").partition("-")
            start = int(start_text)
            end = int(end_text) + 1 if end_text else len(payload)
            resp = Response(payload[start:end], status=206)
            # Falsche Gesamtgroesse 999999
            resp.headers["Content-Range"] = f"bytes {start}-{end - 1}/999999"
            return resp

        with tempfile.TemporaryDirectory() as directory:
            service = segmented_service(directory)
            with patch("urllib.request.urlopen", side_effect=bad_total_urlopen):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )
                self.assertFalse(result.success)
                self.assertEqual(result.error_code, DownloadErrorCode.NETWORK_ERROR)
                self.assertIn("total size mismatch", result.message)

    def test_content_range_wildcard_total_rejected(self):
        """Server meldet Wildcard-Gesamtgroesse (*) im Content-Range: Ablehnung."""
        payload = bytes(range(256)) * 401

        def wildcard_total_urlopen(request, timeout=None):
            header = request.get_header("Range")
            if not header:
                resp = Response(payload, status=200)
                resp.headers["Accept-Ranges"] = "bytes"
                return resp
            start_text, _, end_text = header.removeprefix("bytes=").partition("-")
            start = int(start_text)
            end = int(end_text) + 1 if end_text else len(payload)
            resp = Response(payload[start:end], status=206)
            resp.headers["Content-Range"] = f"bytes {start}-{end - 1}/*"
            return resp

        with tempfile.TemporaryDirectory() as directory:
            service = segmented_service(directory)
            with patch("urllib.request.urlopen", side_effect=wildcard_total_urlopen):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )
                self.assertFalse(result.success)
                self.assertEqual(result.error_code, DownloadErrorCode.NETWORK_ERROR)

    def test_content_range_missing_header_rejected(self):
        """Server liefert Status 206, laesst aber Content-Range Header weg: Ablehnung."""
        payload = bytes(range(256)) * 401

        def missing_header_urlopen(request, timeout=None):
            header = request.get_header("Range")
            if not header:
                resp = Response(payload, status=200)
                resp.headers["Accept-Ranges"] = "bytes"
                return resp
            resp = Response(b"some bytes", status=206)
            # Kein Content-Range Header
            return resp

        with tempfile.TemporaryDirectory() as directory:
            service = segmented_service(directory)
            with patch("urllib.request.urlopen", side_effect=missing_header_urlopen):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )
                self.assertFalse(result.success)
                self.assertEqual(result.error_code, DownloadErrorCode.NETWORK_ERROR)
                self.assertIn("Missing or invalid Content-Range", result.message)

    def test_content_range_malformed_rejected(self):
        """Server liefert fehlerhaft formatierten Content-Range Header: Ablehnung."""
        payload = bytes(range(256)) * 401

        def malformed_urlopen(request, timeout=None):
            header = request.get_header("Range")
            if not header:
                resp = Response(payload, status=200)
                resp.headers["Accept-Ranges"] = "bytes"
                return resp
            resp = Response(b"some bytes", status=206)
            resp.headers["Content-Range"] = "not-a-valid-content-range"
            return resp

        with tempfile.TemporaryDirectory() as directory:
            service = segmented_service(directory)
            with patch("urllib.request.urlopen", side_effect=malformed_urlopen):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )
                self.assertFalse(result.success)
                self.assertEqual(result.error_code, DownloadErrorCode.NETWORK_ERROR)

    def test_content_length_exceeding_content_range_rejected(self):
        """Content-Length groesser als die angegebene Range: Ablehnung."""
        payload = bytes(range(256)) * 401

        def bad_length_urlopen(request, timeout=None):
            header = request.get_header("Range")
            if not header:
                resp = Response(payload, status=200)
                resp.headers["Accept-Ranges"] = "bytes"
                return resp
            start_text, _, end_text = header.removeprefix("bytes=").partition("-")
            start = int(start_text)
            end = int(end_text) + 1 if end_text else len(payload)
            resp = Response(b"some bytes", status=206)
            resp.headers["Content-Range"] = f"bytes {start}-{end - 1}/{len(payload)}"
            resp.headers["Content-Length"] = str((end - start) + 100)  # Groesser als RangeLength
            return resp

        with tempfile.TemporaryDirectory() as directory:
            service = segmented_service(directory)
            with patch("urllib.request.urlopen", side_effect=bad_length_urlopen):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )
                self.assertFalse(result.success)
                self.assertEqual(result.error_code, DownloadErrorCode.NETWORK_ERROR)
                self.assertIn("Content-Length mismatch", result.message)

    # =========================================================================
    # FEHLERFALL 3: Cancel und Verbindungsabbau
    # =========================================================================

    def test_cancel_closes_all_parallel_connections(self):
        """cancel() schliesst alle aktiven parallelen Netzwerkverbindungen zuverlaessig."""
        payload = bytes(range(256)) * 401
        server = RangeServer(payload)

        with tempfile.TemporaryDirectory() as directory:
            service = segmented_service(directory)

            # Blockierendes Lesen simulieren, damit Verbindungen offen bleiben
            first_chunk_event = threading.Event()
            cancelled_event = threading.Event()

            original_urlopen = server.urlopen

            def controlled_urlopen(request, timeout=None):
                resp = original_urlopen(request, timeout)
                original_read = resp.read

                def slow_read(amount=None):
                    first_chunk_event.set()
                    # Warten bis cancel aufgerufen wurde
                    cancelled_event.wait(timeout=2.0)
                    return original_read(amount)

                resp.read = slow_read
                return resp

            def cancel_worker():
                first_chunk_event.wait(timeout=2.0)
                service.cancel()
                cancelled_event.set()

            canceller = threading.Thread(target=cancel_worker)
            canceller.start()

            with patch("urllib.request.urlopen", side_effect=controlled_urlopen):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )

            canceller.join()

            self.assertFalse(result.success)
            self.assertEqual(result.error_code, DownloadErrorCode.CANCELLED)
            # Sicherstellen, dass aktive Verbindungen geschlossen wurden
            self.assertTrue(len(server.active_responses) > 0)
            for resp in server.active_responses:
                self.assertTrue(resp.closed)

    def test_cancel_before_download_aborts_immediately(self):
        """Wird cancel() vor download() gerufen, startet erst gar keine Verbindung."""
        with tempfile.TemporaryDirectory() as directory, patch(
            "urllib.request.urlopen"
        ) as mock_urlopen:
            service = segmented_service(directory)
            service.cancel()

            # Note: download() resets cancel, but if cancel is set immediately or concurrently:
            # Here we test cancel requested during init or reset
            with patch.object(service, "reset_cancel"):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )

            self.assertFalse(result.success)
            self.assertEqual(result.error_code, DownloadErrorCode.CANCELLED)
            mock_urlopen.assert_not_called()

    def test_cancel_during_single_stream_download_closes_connection(self):
        """cancel() waehrend Single-Stream schliesst die Verbindung sofort."""
        payload = b"small payload"
        resp = Response(payload, status=200)

        with tempfile.TemporaryDirectory() as directory:
            service = DownloadService(Path(directory))
            first_read = threading.Event()

            def slow_read(amount=None):
                first_read.set()
                service.cancel()
                return b"chunk"

            resp.read = slow_read
            with patch("urllib.request.urlopen", return_value=resp):
                result = service.download(
                    "https://example.com/model.zip", require_checksum=False
                )

            self.assertFalse(result.success)
            self.assertEqual(result.error_code, DownloadErrorCode.CANCELLED)
            self.assertTrue(resp.closed)


if __name__ == "__main__":
    unittest.main()
