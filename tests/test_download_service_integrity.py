from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
