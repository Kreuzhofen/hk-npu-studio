from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any


class ModelScanner:
    """Scans and verifies local QNN/ONNX model installations on disk."""

    def __init__(self, temp_dir: str | Path | None = None, models_dir: str | Path | None = None) -> None:
        if temp_dir is None:
            try:
                import config
                temp_dir = config.TEMP_DIR
            except ImportError:
                temp_dir = "C:/SnapdragonAI/temp"
        if models_dir is None:
            try:
                import config
                models_dir = config.MODELS_DIR
            except ImportError:
                models_dir = "C:/SnapdragonAI/models"
        self.temp_dir = Path(temp_dir)
        self.models_dir = Path(models_dir)

    def scan_models(self) -> list[dict[str, Any]]:
        """Scans, verifies completeness, and computes folder sizes for local models."""
        model_configs = [
            {
                "id": "stable_diffusion_v1_5_qnn",
                "display_name": "Stable Diffusion 1.5 QNN",
                "path": self.temp_dir / "stable_diffusion_v1_5_qnn_inspection" / "stable_diffusion_v1_5-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite",
                "expected_files": ["text_encoder.onnx", "unet.onnx", "vae.onnx", "metadata.json"],
                "quantization": "w8a16",
                "backend_status": "HTP V73",
                "default_sampler": "Euler"
            },
            {
                "id": "stable_diffusion_v2_1_qnn",
                "display_name": "Stable Diffusion 2.1 QNN",
                "path": self.models_dir / "stable_diffusion_v2_1",
                "expected_files": ["text_encoder.onnx", "unet.onnx", "vae.onnx", "metadata.json"],
                "quantization": "w8a16",
                "backend_status": "HTP V73",
                "default_sampler": "DDIM"
            },
            {
                "id": "controlnet_canny_qnn",
                "display_name": "ControlNet Canny QNN",
                "path": self.temp_dir / "controlnet_canny_gate" / "controlnet_canny-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite",
                "expected_files": ["text_encoder.onnx", "controlnet.onnx", "unet.onnx", "vae.onnx", "metadata.json"],
                "quantization": "w8a16",
                "backend_status": "HTP V73",
                "default_sampler": "DDIM"
            },
            {
                "id": "sdxl_base",
                "display_name": "Stable Diffusion XL Base",
                "path": self.models_dir / "sdxl_base",
                "expected_files": ["text_encoder.onnx", "text_encoder_2.onnx", "unet.onnx", "vae_decoder.onnx", "metadata.json"],
                "quantization": "w8a16",
                "backend_status": "ONNX Runtime",
                "default_sampler": "Euler"
            }
        ]

        results = []
        for cfg in model_configs:
            path = Path(cfg["path"])
            exists = path.exists() and path.is_dir()
            
            missing_files = []
            if exists:
                for f in cfg["expected_files"]:
                    if not (path / f).exists():
                        missing_files.append(f)
                is_complete = len(missing_files) == 0
            else:
                is_complete = False
                
            size_bytes = 0
            if exists:
                size_bytes = self._get_dir_size(path)
            
            status = "missing"
            if exists:
                status = "complete" if is_complete else "incomplete"

            results.append({
                "id": cfg["id"],
                "display_name": cfg["display_name"],
                "path": str(path),
                "exists": exists,
                "is_complete": is_complete,
                "missing_files": missing_files,
                "size_bytes": size_bytes,
                "size_str": self._format_size(size_bytes),
                "quantization": cfg["quantization"],
                "backend_status": cfg["backend_status"],
                "default_sampler": cfg["default_sampler"],
                "status": status
            })
            
        return results

    def _get_dir_size(self, path: Path) -> int:
        total_size = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass
        return total_size

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"
