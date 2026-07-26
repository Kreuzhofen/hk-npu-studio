from __future__ import annotations

import io
import hashlib
import unittest
import zipfile
import tempfile
import time
from pathlib import Path
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
        self.assertIn("Authentifizierung fehlgeschlagen", final_report["error_message"])


if __name__ == "__main__":
    unittest.main()
