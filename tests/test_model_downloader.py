from __future__ import annotations

import io
import hashlib
import unittest
import zipfile
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch, MagicMock

from app.model_downloader import ModelDownloader


class ModelDownloaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)
        
        # Patch the target dirs in ModelDownloader to write inside self.temp_dir
        self.downloader = ModelDownloader()
        self.downloader.download_dir = self.temp_dir / "downloads"
        self.downloader.MODEL_TARGETS = {
            "stable_diffusion_v1_5_qnn": self.temp_dir / "sd15",
            "controlnet_canny_qnn": self.temp_dir / "controlnet",
            "stable_diffusion_v2_1_qnn": self.temp_dir / "sd21",
            "sdxl_base": self.temp_dir / "sdxl",
        }

    def tearDown(self) -> None:
        self.temp_dir_obj.cleanup()

    def _create_dummy_zip(self) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("metadata.json", '{"name": "test"}')
            z.writestr("unet.onnx", "dummy weight")
        return buf.getvalue()

    @patch("urllib.request.urlopen")
    def test_successful_download_and_extract(self, mock_urlopen: MagicMock) -> None:
        dummy_zip = self._create_dummy_zip()
        checksum = hashlib.sha256(dummy_zip).hexdigest()

        # Mock the network response
        class MockResponse:
            def __init__(self, data: bytes) -> None:
                self.data = io.BytesIO(data)
                self.headers = {"Content-Length": str(len(data))}
            def read(self, amt: int | None = None) -> bytes:
                return self.data.read(amt)
            def __enter__(self) -> MockResponse:
                return self
            def __exit__(self, *args: Any) -> None:
                pass

        mock_urlopen.return_value = MockResponse(dummy_zip)

        progress_reports = []
        def callback(report: dict[str, Any]) -> None:
            progress_reports.append(report.copy())

        self.downloader.start_download(
            model_id="stable_diffusion_v1_5_qnn",
            progress_callback=callback,
            url="http://example.com/sd15.zip",
            checksum=checksum
        )

        # Wait for thread to finish
        thread = self.downloader._active_threads.get("stable_diffusion_v1_5_qnn")
        if thread:
            thread.join(timeout=5.0)

        self.assertFalse(self.downloader.is_downloading("stable_diffusion_v1_5_qnn"))
        
        # Verify status progression
        statuses = [r["status"] for r in progress_reports]
        self.assertIn("downloading", statuses)
        self.assertIn("verifying", statuses)
        self.assertIn("extracting", statuses)
        self.assertIn("completed", statuses)

        # Verify target files are extracted
        extracted_dir = self.downloader.MODEL_TARGETS["stable_diffusion_v1_5_qnn"]
        self.assertTrue((extracted_dir / "metadata.json").exists())
        self.assertTrue((extracted_dir / "unet.onnx").exists())

    @patch("urllib.request.urlopen")
    def test_checksum_mismatch(self, mock_urlopen: MagicMock) -> None:
        dummy_zip = self._create_dummy_zip()
        incorrect_checksum = "wrong_checksum_value"

        class MockResponse:
            def __init__(self, data: bytes) -> None:
                self.data = io.BytesIO(data)
                self.headers = {"Content-Length": str(len(data))}
            def read(self, amt: int | None = None) -> bytes:
                return self.data.read(amt)
            def __enter__(self) -> MockResponse:
                return self
            def __exit__(self, *args: Any) -> None:
                pass

        mock_urlopen.return_value = MockResponse(dummy_zip)

        progress_reports = []
        def callback(report: dict[str, Any]) -> None:
            progress_reports.append(report.copy())

        self.downloader.start_download(
            model_id="stable_diffusion_v1_5_qnn",
            progress_callback=callback,
            url="http://example.com/sd15.zip",
            checksum=incorrect_checksum
        )

        thread = self.downloader._active_threads.get("stable_diffusion_v1_5_qnn")
        if thread:
            thread.join(timeout=5.0)

        statuses = [r["status"] for r in progress_reports]
        self.assertIn("failed", statuses)
        
        # Make sure extraction did NOT happen or files do not exist
        extracted_dir = self.downloader.MODEL_TARGETS["stable_diffusion_v1_5_qnn"]
        self.assertFalse((extracted_dir / "metadata.json").exists())

    @patch("urllib.request.urlopen")
    def test_cancel_download(self, mock_urlopen: MagicMock) -> None:
        # Mock connection reading that yields chunks slowly so we can cancel it
        class SlowResponse:
            def __init__(self) -> None:
                self.headers = {"Content-Length": "1000000"}
                self.read_count = 0
            def read(self, amt: int | None = None) -> bytes:
                self.read_count += 1
                if self.read_count > 5:
                    return b""
                time.sleep(0.01)
                return b"a" * 1024
            def __enter__(self) -> SlowResponse:
                return self
            def __exit__(self, *args: Any) -> None:
                pass

        mock_urlopen.return_value = SlowResponse()

        progress_reports = []
        def callback(report: dict[str, Any]) -> None:
            progress_reports.append(report.copy())
            if report["status"] == "downloading" and len(progress_reports) == 2:
                self.downloader.cancel_download("stable_diffusion_v1_5_qnn")

        self.downloader.start_download(
            model_id="stable_diffusion_v1_5_qnn",
            progress_callback=callback,
            url="http://example.com/sd15.zip"
        )

        thread = self.downloader._active_threads.get("stable_diffusion_v1_5_qnn")
        if thread:
            thread.join(timeout=5.0)

        statuses = [r["status"] for r in progress_reports]
        self.assertIn("cancelled", statuses)

    @patch("urllib.request.urlopen")
    @patch.dict("os.environ", {"HF_TOKEN": "my_secret_token"})
    def test_authorization_header_sent(self, mock_urlopen: MagicMock) -> None:
        class MockResponse:
            def __init__(self) -> None:
                self.headers = {"Content-Length": "10"}
            def read(self, amt: int | None = None) -> bytes:
                return b""
            def __enter__(self) -> MockResponse:
                return self
            def __exit__(self, *args: Any) -> None:
                pass

        mock_urlopen.return_value = MockResponse()

        def callback(report: dict[str, Any]) -> None:
            pass

        self.downloader.start_download(
            model_id="stable_diffusion_v1_5_qnn",
            progress_callback=callback,
            url="http://example.com/sd15.zip"
        )

        thread = self.downloader._active_threads.get("stable_diffusion_v1_5_qnn")
        if thread:
            thread.join(timeout=5.0)

        # Inspect the Request object passed to urlopen
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.headers["Authorization"], "Bearer my_secret_token")

    @patch("urllib.request.urlopen")
    def test_401_unauthorized_error(self, mock_urlopen: MagicMock) -> None:
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://example.com/sd15.zip",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=io.BytesIO(b"")
        )

        progress_reports = []
        def callback(report: dict[str, Any]) -> None:
            progress_reports.append(report.copy())

        self.downloader.start_download(
            model_id="stable_diffusion_v1_5_qnn",
            progress_callback=callback,
            url="http://example.com/sd15.zip"
        )

        thread = self.downloader._active_threads.get("stable_diffusion_v1_5_qnn")
        if thread:
            thread.join(timeout=5.0)

        # Check that it failed
        statuses = [r["status"] for r in progress_reports]
        self.assertIn("failed", statuses)
        
        # Verify the custom/localized error message
        final_report = progress_reports[-1]
        msg = final_report["error_message"]
        self.assertTrue(
            "Authentifizierung fehlgeschlagen" in msg or "Authentication failed" in msg,
            f"Expected auth failed message, got: {msg}"
        )

    @patch("urllib.request.urlopen")
    def test_404_not_found_error(self, mock_urlopen: MagicMock) -> None:
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://example.com/sdxl.zip",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=io.BytesIO(b"")
        )

        progress_reports = []
        def callback(report: dict[str, Any]) -> None:
            progress_reports.append(report.copy())

        self.downloader.start_download(
            model_id="sdxl_base",
            progress_callback=callback,
            url="http://example.com/sdxl.zip"
        )

        thread = self.downloader._active_threads.get("sdxl_base")
        if thread:
            thread.join(timeout=5.0)

        # Check that it failed
        statuses = [r["status"] for r in progress_reports]
        self.assertIn("failed", statuses)
        
        # Verify the custom/localized error message
        final_report = progress_reports[-1]
        msg = final_report["error_message"]
        self.assertTrue(
            "Modell nicht gefunden" in msg or "Model not found" in msg,
            f"Expected model not found message, got: {msg}"
        )

    @patch("urllib.request.urlopen")
    def test_single_file_download_success(self, mock_urlopen: MagicMock) -> None:
        dummy_safetensors = b"dummy safetensors bytes"
        checksum = hashlib.sha256(dummy_safetensors).hexdigest()

        # Mock the network response
        class MockResponse:
            def __init__(self, data: bytes) -> None:
                self.data = io.BytesIO(data)
                self.headers = {"Content-Length": str(len(data))}
            def read(self, amt: int | None = None) -> bytes:
                return self.data.read(amt)
            def __enter__(self) -> MockResponse:
                return self
            def __exit__(self, *args: Any) -> None:
                pass

        mock_urlopen.return_value = MockResponse(dummy_safetensors)

        # Temporarily override checksum mapping
        original_checksum = self.downloader.MODEL_CHECKSUMS.get("sdxl_base")
        self.downloader.MODEL_CHECKSUMS["sdxl_base"] = checksum

        progress_reports = []
        def callback(report: dict[str, Any]) -> None:
            progress_reports.append(report.copy())

        self.downloader.start_download(
            model_id="sdxl_base",
            progress_callback=callback,
            url="http://example.com/sd_xl_base_1.0.safetensors"
        )

        thread = self.downloader._active_threads.get("sdxl_base")
        if thread:
            thread.join(timeout=5.0)

        # Verify completion
        statuses = [r["status"] for r in progress_reports]
        self.assertIn("completed", statuses)
        self.assertNotIn("failed", statuses)

        # Restore original checksum mapping
        if original_checksum:
            self.downloader.MODEL_CHECKSUMS["sdxl_base"] = original_checksum

        # Check that file was moved to target directory
        expected_file = self.downloader.MODEL_TARGETS["sdxl_base"] / "sd_xl_base_1.0.safetensors"
        self.assertTrue(expected_file.exists())
        self.assertEqual(expected_file.read_bytes(), dummy_safetensors)

    @patch("urllib.request.urlopen")
    def test_resume_uses_range_and_preserves_existing_bytes(self, mock_urlopen: MagicMock) -> None:
        complete = self._create_dummy_zip()
        split = len(complete) // 2
        partial = complete[:split]
        remainder = complete[split:]
        self.downloader.download_dir.mkdir(parents=True)
        partial_path = self.downloader.download_dir / "sd15.zip.part"
        partial_path.write_bytes(partial)

        class PartialResponse:
            status = 206
            headers = {"Content-Length": str(len(remainder))}

            def __init__(self):
                self.data = io.BytesIO(remainder)

            def read(self, amount=None):
                return self.data.read(amount)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        mock_urlopen.return_value = PartialResponse()
        reports = []
        self.downloader.start_download(
            "stable_diffusion_v1_5_qnn",
            reports.append,
            url="https://example.com/sd15.zip",
            checksum=hashlib.sha256(complete).hexdigest(),
        )
        self.downloader._active_threads["stable_diffusion_v1_5_qnn"].join(5)

        request = mock_urlopen.call_args[0][0]
        self.assertEqual(request.headers["Range"], f"bytes={split}-")
        self.assertEqual(reports[-1]["status"], "completed")
        self.assertFalse(partial_path.exists())

    @patch("urllib.request.urlopen")
    def test_cancel_keeps_partial_file_for_resume(self, mock_urlopen: MagicMock) -> None:
        class Response:
            headers = {"Content-Length": "4096"}

            def read(self, amount=None):
                self_downloader.cancel_download("sdxl_base")
                return b"x" * 1024

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        self_downloader = self.downloader
        mock_urlopen.return_value = Response()
        reports = []
        self.downloader.start_download(
            "sdxl_base",
            reports.append,
            url="https://example.com/model.safetensors",
        )
        self.downloader._active_threads["sdxl_base"].join(5)

        self.assertEqual(reports[-1]["status"], "cancelled")
        partial = self.downloader.download_dir / "model.safetensors.part"
        self.assertTrue(partial.exists())
        self.assertGreater(partial.stat().st_size, 0)

    @patch("urllib.request.urlopen")
    def test_unsafe_archive_is_rejected_before_extraction(self, mock_urlopen: MagicMock) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("../escape.txt", "unsafe")
        payload = buffer.getvalue()

        class Response:
            headers = {"Content-Length": str(len(payload))}

            def __init__(self):
                self.data = io.BytesIO(payload)

            def read(self, amount=None):
                return self.data.read(amount)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        mock_urlopen.return_value = Response()
        reports = []
        self.downloader.start_download(
            "stable_diffusion_v1_5_qnn",
            reports.append,
            url="https://example.com/unsafe.zip",
            checksum=hashlib.sha256(payload).hexdigest(),
        )
        self.downloader._active_threads["stable_diffusion_v1_5_qnn"].join(5)

        self.assertEqual(reports[-1]["status"], "failed")
        self.assertIn("Unsafe archive member", reports[-1]["error_message"])
        self.assertFalse((self.temp_dir / "escape.txt").exists())


if __name__ == "__main__":
    unittest.main()
