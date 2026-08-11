from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engine.download_service import DownloadErrorCode, DownloadService


class Response:
    status = 200

    def __init__(self, payload: bytes):
        self.payload = io.BytesIO(payload)
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


if __name__ == "__main__":
    unittest.main()
