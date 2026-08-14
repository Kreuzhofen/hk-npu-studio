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
from engine.logging_config import get_logger


logger = get_logger("ModelDownloader")

class ModelDownloader:
    """Manages background downloads, SHA256 checks, and archive extractions of NPU models."""

    MODEL_TARGETS = {
        "stable_diffusion_v1_5_qnn": config.TEMP_DIR / "stable_diffusion_v1_5_qnn_inspection",
        "controlnet_canny_qnn": config.TEMP_DIR / "controlnet_canny_gate",
        "stable_diffusion_v2_1_qnn": config.MODELS_DIR,
        "sdxl_base": config.MODELS_DIR,
    }

    MODEL_URLS = {
        "stable_diffusion_v1_5_qnn": "https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/stable_diffusion_v1_5/releases/v0.50.0/stable_diffusion_v1_5-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite.zip",
        "controlnet_canny_qnn": "https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/controlnet_canny/releases/v0.58.0/controlnet_canny-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite.zip",
        "stable_diffusion_v2_1_qnn": "https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/stable_diffusion_v2_1/releases/v0.58.0/stable_diffusion_v2_1-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite.zip",
        "sdxl_base": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
    }

    MODEL_CHECKSUMS = {
        "stable_diffusion_v1_5_qnn": "a1b2c3d4e5f60708090a0b0c0d0e0f1213141516171819202122232425262728",
        "stable_diffusion_v2_1_qnn": "c3d4e5f6a7b8090a0b0c0d0e0f12131415161718192021222324252627282930",
        "sdxl_base": "31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b",
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
        if not self._valid_sha256(target_checksum):
            logger.error("Download abgelehnt: gültiger SHA-256 fehlt | model=%s", model_id)
            progress_callback({
                "status": "failed",
                "bytes_downloaded": 0,
                "total_bytes": None,
                "percent": 0.0,
                "speed": 0.0,
                "error_message": "A valid SHA-256 checksum is required before download registration."
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
        partial_path = download_path.with_suffix(download_path.suffix + ".part")

        start_time = time.time()

        hf_token = os.environ.get("HF_TOKEN") or getattr(config, "HF_TOKEN", None)
        headers = {"User-Agent": "SnapdragonAIStudio/2.0"}
        if hf_token:
            headers["Authorization"] = f"Bearer {hf_token}"
        existing_bytes = partial_path.stat().st_size if partial_path.exists() else 0
        if existing_bytes:
            headers["Range"] = f"bytes={existing_bytes}-"
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30.0) as response:
                content_length = response.headers.get("Content-Length")
                response_status = getattr(response, "status", None)
                if response_status is None:
                    getcode = getattr(response, "getcode", None)
                    response_status = getcode() if callable(getcode) else None
                resumed = bool(existing_bytes and response_status == 206)
                if existing_bytes and not resumed:
                    logger.warning("Server ignoriert Range; Teildownload wird neu gestartet | model=%s", model_id)
                bytes_downloaded = existing_bytes if resumed else 0
                response_bytes = int(content_length) if content_length else None
                total_bytes = (
                    bytes_downloaded + response_bytes
                    if resumed and response_bytes is not None
                    else response_bytes
                )

                with open(partial_path, "ab" if resumed else "wb") as out_file:
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
                progress_callback({
                    "status": "cancelled",
                    "bytes_downloaded": bytes_downloaded,
                    "total_bytes": total_bytes,
                    "percent": (bytes_downloaded / total_bytes) * 100.0 if total_bytes else 0.0,
                    "speed": 0.0,
                    "error_message": "Download cancelled by user."
                })
                return

            if total_bytes is not None and partial_path.stat().st_size != total_bytes:
                raise IOError(
                    f"Incomplete download: expected {total_bytes} bytes, got {partial_path.stat().st_size} bytes."
                )

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
                with open(partial_path, "rb") as f:
                    while chunk := f.read(8192):
                        sha256.update(chunk)
                computed = sha256.hexdigest().lower()
                if computed != expected_checksum.lower():
                    self._cleanup_file(partial_path)
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

            if zipfile.is_zipfile(partial_path):
                with zipfile.ZipFile(partial_path, "r") as zip_ref:
                    self._validate_archive_paths(target_dir, zip_ref.namelist())
                    if zip_ref.testzip() is not None:
                        raise ValueError("ZIP archive contains a corrupt file.")
                    zip_ref.extractall(target_dir)
                self._cleanup_file(partial_path)
            elif tarfile.is_tarfile(partial_path):
                with tarfile.open(partial_path, "r:*") as tar_ref:
                    self._validate_archive_paths(target_dir, [member.name for member in tar_ref.getmembers()])
                    tar_ref.extractall(target_dir)
                self._cleanup_file(partial_path)
            elif download_path.suffix.lower() in {".safetensors", ".bin", ".onnx", ".json"}:
                import shutil
                dest_path = target_dir / download_path.name
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                if dest_path.exists():
                    dest_path.unlink()
                shutil.move(str(partial_path), str(dest_path))
            else:
                raise ValueError("Unsupported archive format. Expected ZIP or TAR.")

            progress_callback({
                "status": "completed",
                "bytes_downloaded": bytes_downloaded,
                "total_bytes": total_bytes,
                "percent": 100.0,
                "speed": 0.0,
                "error_message": None
            })

        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                from app.i18n import tr
                error_msg = tr("auth_failed_hf_token", "Authentifizierung fehlgeschlagen: Bitte Hugging Face Token hinterlegen")
            elif exc.code == 404:
                from app.i18n import tr
                error_msg = tr("model_not_found_404", "Modell nicht gefunden: Die angeforderte Datei existiert nicht auf dem Server (404 Not Found).")
            else:
                error_msg = f"HTTP Error {exc.code}: {exc.reason}"
            logger.error(
                "Modelldownload HTTP-Fehler | model=%s status=%s error=%s",
                model_id,
                exc.code,
                error_msg,
            )
            progress_callback({
                "status": "failed",
                "bytes_downloaded": 0,
                "total_bytes": None,
                "percent": 0.0,
                "speed": 0.0,
                "error_message": error_msg
            })

        except Exception as exc:
            logger.error("Modelldownload fehlgeschlagen | model=%s error=%s", model_id, exc)
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

    @staticmethod
    def _valid_sha256(value: str | None) -> bool:
        if value is None or len(value) != 64:
            return False
        return all(character in "0123456789abcdefABCDEF" for character in value)

    @staticmethod
    def _validate_archive_paths(target_dir: Path, names: list[str]) -> None:
        root = target_dir.resolve()
        for name in names:
            try:
                (target_dir / name).resolve().relative_to(root)
            except ValueError as error:
                raise ValueError(f"Unsafe archive member path: {name}") from error
