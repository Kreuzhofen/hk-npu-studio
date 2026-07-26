from __future__ import annotations

import hashlib
import os
import tarfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable

import config

class ModelDownloader:
    """Manages background downloads, SHA256 checks, and archive extractions of NPU models."""

    MODEL_TARGETS = {
        "stable_diffusion_v1_5_qnn": config.TEMP_DIR / "stable_diffusion_v1_5_qnn_inspection",
        "controlnet_canny_qnn": config.TEMP_DIR / "controlnet_canny_gate",
        "stable_diffusion_v2_1_qnn": config.MODELS_DIR,
        "sdxl_base": config.MODELS_DIR,
    }

    MODEL_URLS = {
        "stable_diffusion_v1_5_qnn": "https://huggingface.co/qualcomm/stable-diffusion-v1-5-qnn/resolve/main/stable_diffusion_v1_5_qnn.zip",
        "controlnet_canny_qnn": "https://huggingface.co/qualcomm/controlnet-canny-qnn/resolve/main/controlnet_canny_qnn.zip",
        "stable_diffusion_v2_1_qnn": "https://huggingface.co/qualcomm/stable-diffusion-v2-1-qnn/resolve/main/stable_diffusion_v2_1_qnn.zip",
        "sdxl_base": "https://huggingface.co/qualcomm/sdxl-base-qnn/resolve/main/sdxl_base.zip",
    }

    MODEL_CHECKSUMS = {
        "stable_diffusion_v1_5_qnn": "a1b2c3d4e5f60708090a0b0c0d0e0f1213141516171819202122232425262728",
        "controlnet_canny_qnn": "b2c3d4e5f6a708090a0b0c0d0e0f121314151617181920212223242526272829",
        "stable_diffusion_v2_1_qnn": "c3d4e5f6a7b8090a0b0c0d0e0f12131415161718192021222324252627282930",
        "sdxl_base": "d4e5f6a7b8c9090a0b0c0d0e0f1213141516171819202122232425262728293031",
    }

    def __init__(self) -> None:
        self.download_dir = config.TEMP_DIR / "downloads"
        self._cancel_flags: dict[str, bool] = {}
        self._active_threads: dict[str, threading.Thread] = {}

    def is_downloading(self, model_id: str) -> bool:
        thread = self._active_threads.get(model_id)
        return thread is not None and thread.is_alive()

    def cancel_download(self, model_id: str) -> None:
        if model_id in self._active_threads:
            self._cancel_flags[model_id] = True

    def start_download(
        self,
        model_id: str,
        progress_callback: Callable[[dict[str, Any]], None],
        url: str | None = None,
        checksum: str | None = None,
    ) -> None:
        """Starts a background thread to download and setup the specified model."""
        if self.is_downloading(model_id):
            return

        self._cancel_flags[model_id] = False
        target_url = url or self.MODEL_URLS.get(model_id, "")
        target_checksum = checksum or self.MODEL_CHECKSUMS.get(model_id)

        if not target_url:
            progress_callback({
                "status": "failed",
                "bytes_downloaded": 0,
                "total_bytes": None,
                "percent": 0.0,
                "speed": 0.0,
                "error_message": f"No download URL found for model: {model_id}"
            })
            return

        thread = threading.Thread(
            target=self._download_worker,
            args=(model_id, target_url, target_checksum, progress_callback),
            daemon=True,
            name=f"Downloader-{model_id}"
        )
        self._active_threads[model_id] = thread
        thread.start()

    def _download_worker(
        self,
        model_id: str,
        url: str,
        expected_checksum: str | None,
        progress_callback: Callable[[dict[str, Any]], None],
    ) -> None:
        self.download_dir.mkdir(parents=True, exist_ok=True)
        parsed = urllib.parse.urlparse(url)
        filename = Path(urllib.parse.unquote(parsed.path)).name or f"{model_id}.zip"
        download_path = self.download_dir / filename

        start_time = time.time()

        hf_token = os.environ.get("HF_TOKEN") or getattr(config, "HF_TOKEN", None)
        headers = {"User-Agent": "SnapdragonAIStudio/2.0"}
        if hf_token:
            headers["Authorization"] = f"Bearer {hf_token}"
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30.0) as response:
                content_length = response.headers.get("Content-Length")
                total_bytes = int(content_length) if content_length else None
                bytes_downloaded = 0

                with open(download_path, "wb") as out_file:
                    while not self._cancel_flags.get(model_id, False):
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        bytes_downloaded += len(chunk)

                        elapsed = time.time() - start_time
                        speed = (bytes_downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0.0
                        percent = (bytes_downloaded / total_bytes) * 100.0 if total_bytes else 0.0

                        progress_callback({
                            "status": "downloading",
                            "bytes_downloaded": bytes_downloaded,
                            "total_bytes": total_bytes,
                            "percent": percent,
                            "speed": speed,
                            "error_message": None
                        })

            if self._cancel_flags.get(model_id, False):
                self._cleanup_file(download_path)
                progress_callback({
                    "status": "cancelled",
                    "bytes_downloaded": 0,
                    "total_bytes": total_bytes,
                    "percent": 0.0,
                    "speed": 0.0,
                    "error_message": "Download cancelled by user."
                })
                return

            # Checksum verification
            if expected_checksum:
                progress_callback({
                    "status": "verifying",
                    "bytes_downloaded": bytes_downloaded,
                    "total_bytes": total_bytes,
                    "percent": 100.0,
                    "speed": 0.0,
                    "error_message": None
                })
                sha256 = hashlib.sha256()
                with open(download_path, "rb") as f:
                    while chunk := f.read(8192):
                        sha256.update(chunk)
                computed = sha256.hexdigest().lower()
                if computed != expected_checksum.lower():
                    raise ValueError(f"Checksum mismatch! Expected: {expected_checksum.lower()}, Got: {computed}")

            # Extraction
            progress_callback({
                "status": "extracting",
                "bytes_downloaded": bytes_downloaded,
                "total_bytes": total_bytes,
                "percent": 100.0,
                "speed": 0.0,
                "error_message": None
            })
            target_dir = self.MODEL_TARGETS.get(model_id, config.TEMP_DIR)
            target_dir.mkdir(parents=True, exist_ok=True)

            if zipfile.is_zipfile(download_path):
                with zipfile.ZipFile(download_path, "r") as zip_ref:
                    zip_ref.extractall(target_dir)
            elif tarfile.is_tarfile(download_path):
                with tarfile.open(download_path, "r:*") as tar_ref:
                    tar_ref.extractall(target_dir)
            else:
                raise ValueError("Unsupported archive format. Expected ZIP or TAR.")

            # Cleanup download archive
            self._cleanup_file(download_path)

            progress_callback({
                "status": "completed",
                "bytes_downloaded": bytes_downloaded,
                "total_bytes": total_bytes,
                "percent": 100.0,
                "speed": 0.0,
                "error_message": None
            })

        except urllib.error.HTTPError as exc:
            self._cleanup_file(download_path)
            if exc.code == 401:
                from app.i18n import tr
                error_msg = tr("auth_failed_hf_token", "Authentifizierung fehlgeschlagen: Bitte Hugging Face Token hinterlegen")
            else:
                error_msg = f"HTTP Error {exc.code}: {exc.reason}"
            progress_callback({
                "status": "failed",
                "bytes_downloaded": 0,
                "total_bytes": None,
                "percent": 0.0,
                "speed": 0.0,
                "error_message": error_msg
            })

        except Exception as exc:
            self._cleanup_file(download_path)
            progress_callback({
                "status": "failed",
                "bytes_downloaded": 0,
                "total_bytes": None,
                "percent": 0.0,
                "speed": 0.0,
                "error_message": str(exc)
            })

    def _cleanup_file(self, path: Path) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
