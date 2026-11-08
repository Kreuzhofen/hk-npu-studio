"""
HK NPU STUDIO – Phoenix Architecture
Sprint 94: Isolated MobileSAM Qualcomm Hexagon HTP Backend Adapter

Provides hardware-accelerated semantic segmentation using official MobileSAM
(TinyViT image encoder + lightweight prompt mask decoder) running strictly on
Qualcomm Hexagon HTP V73 NPU with 0 CPU fallbacks.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logger = logging.getLogger(__name__)

# Default model directory
DEFAULT_LOCALAPPDATA_SAM_DIR = (
    Path(os.environ.get("LOCALAPPDATA", "")) / "HK NPU STUDIO" / "models" / "mobilesam_qnn" / "onnx"
)
DEFAULT_REPO_SAM_DIR = REPO_ROOT / "models" / "mobilesam_qnn" / "onnx"

def _resolve_default_sam_path(filename: str) -> Path:
    candidates = []
    try:
        import config
        candidates.append(config.resolve_model_path(Path("mobilesam_qnn") / "onnx" / filename))
    except Exception:
        pass
    candidates.append(DEFAULT_LOCALAPPDATA_SAM_DIR / filename)
    candidates.append(DEFAULT_REPO_SAM_DIR / filename)
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]

DEFAULT_MOBILESAM_DIR = DEFAULT_REPO_SAM_DIR
DEFAULT_ENCODER_PATH = _resolve_default_sam_path("encoder.onnx")
DEFAULT_DECODER_PATH = _resolve_default_sam_path("decoder.onnx")


def _configure_qnn_runtime_env() -> None:
    """Ensure onnxruntime_qnn library directory is present on PATH and DLL search."""
    try:
        spec = importlib.util.find_spec("onnxruntime_qnn")
        if spec is None or spec.origin is None:
            return
        qnn_dir = Path(spec.origin).resolve().parent
        os.environ["PATH"] = str(qnn_dir) + os.pathsep + os.environ.get("PATH", "")
        os.environ["ADSP_LIBRARY_PATH"] = str(qnn_dir)
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(str(qnn_dir))
            except OSError:
                pass
    except Exception:
        logger.exception("Failed to configure QNN runtime search path.")


_configure_qnn_runtime_env()


@dataclass
class MobileSamBenchmarkStats:
    """Performance metrics for Qualcomm Hexagon HTP MobileSAM execution."""
    encoder_coldstart_ms: float = 0.0
    encoder_warmstart_ms: float = 0.0
    decoder_coldstart_ms: float = 0.0
    decoder_warmstart_avg_ms: float = 0.0
    decoder_warmstart_min_ms: float = 0.0
    decoder_warmstart_max_ms: float = 0.0
    memory_rss_mb: float = 0.0
    hardware_target: str = "Qualcomm Hexagon NPU (HTP V73)"
    cpu_fallbacks: int = 0


class MobileSamQnnAdapter:
    """
    Isolated backend adapter for MobileSAM semantic segmentation on Qualcomm Hexagon NPU.
    
    Architecture:
    - Preprocessing: Resize image to 1024x1024, normalize to RGB float32 [0.0, 1.0].
    - Encoder: TinyViT backbone on HTP V73 produces [1, 256, 64, 64] image embedding.
      Cached in memory for instant interactive repeat queries.
    - Decoder: Lightweight two-way transformer on HTP V73 converts point prompts
      into high-resolution instance masks in ~10-20 ms.
    """

    def __init__(
        self,
        encoder_path: Optional[Union[str, Path]] = None,
        decoder_path: Optional[Union[str, Path]] = None,
        performance_mode: str = "burst",
    ) -> None:
        self.encoder_path = Path(encoder_path or DEFAULT_ENCODER_PATH)
        self.decoder_path = Path(decoder_path or DEFAULT_DECODER_PATH)
        self.performance_mode = performance_mode

        self._encoder_session: Optional[Any] = None
        self._decoder_session: Optional[Any] = None
        self._cached_embeddings: Optional[np.ndarray] = None
        self._orig_size: Optional[Tuple[int, int]] = None  # (width, height)
        self._ort: Optional[Any] = None
        self._qnn: Optional[Any] = None

    def initialize(self) -> None:
        """Initialize QNN Execution Provider and load HTP inference sessions."""
        if self._encoder_session is not None and self._decoder_session is not None:
            return

        _configure_qnn_runtime_env()
        import onnxruntime as ort
        import onnxruntime_qnn as qnn

        self._ort = ort
        self._qnn = qnn

        try:
            ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
        except Exception as reg_err:
            if "already registered" not in str(reg_err).lower():
                raise reg_err
        devices = [d for d in ort.get_ep_devices() if d.ep_name == "QNNExecutionProvider"]
        if not devices:
            raise RuntimeError("No QNNExecutionProvider devices available for Qualcomm Hexagon HTP.")

        if not self.encoder_path.exists():
            raise FileNotFoundError(f"MobileSAM encoder model not found: {self.encoder_path}")
        if not self.decoder_path.exists():
            raise FileNotFoundError(f"MobileSAM decoder model not found: {self.decoder_path}")

        logger.info(f"Loading MobileSAM decoder on Hexagon HTP: {self.decoder_path}")
        self._decoder_session = self._create_htp_session(self.decoder_path, devices)

        logger.info(f"Loading MobileSAM encoder on Hexagon HTP: {self.encoder_path}")
        self._encoder_session = self._create_htp_session(self.encoder_path, devices)
        logger.info("MobileSAM encoder and decoder loaded successfully on Hexagon HTP.")

    def _create_htp_session(self, model_path: Path, devices: list) -> Any:
        """Create an ONNX Runtime InferenceSession strictly bound to Hexagon HTP."""
        opts = self._ort.SessionOptions()
        # Strictly disable CPU fallback to satisfy Phoenix Architecture safety gate
        opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        prov_opts = {
            "backend_path": self._qnn.get_qnn_htp_path(),
            "htp_performance_mode": self.performance_mode,
        }
        opts.add_provider_for_devices(devices, prov_opts)
        return self._ort.InferenceSession(str(model_path), opts)

    def set_image(self, image: Union[Image.Image, np.ndarray]) -> np.ndarray:
        """
        Encode input image using Hexagon HTP TinyViT backbone.
        Caches feature embeddings for subsequent zero-overhead interactive queries.
        
        Args:
            image: PIL Image or numpy array (RGB)
            
        Returns:
            np.ndarray: Image embedding tensor with shape [1, 256, 64, 64]
        """
        self.initialize()

        if isinstance(image, np.ndarray):
            pil_img = Image.fromarray(image).convert("RGB")
        else:
            pil_img = image.convert("RGB")

        self._orig_size = pil_img.size  # (width, height)
        orig_w, orig_h = self._orig_size

        # Preprocess: resize to 1024x1024, normalize to [0.0, 1.0] RGB float32
        resized = pil_img.resize((1024, 1024), Image.Resampling.BILINEAR)
        arr = np.array(resized, dtype=np.float32) / 255.0
        # Transpose to NCHW [1, 3, 1024, 1024]
        tensor = np.transpose(arr, (2, 0, 1))[None, ...]

        logger.info(f"Encoding image ({orig_w}x{orig_h}) on Hexagon HTP...")
        t0 = time.perf_counter()
        embeddings = self._encoder_session.run(None, {"image": tensor})[0]
        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(f"Image encoded on HTP in {elapsed:.2f} ms. Embedding shape: {embeddings.shape}")

        self._cached_embeddings = embeddings
        return embeddings

    def predict_mask(
        self,
        point_coords: List[Tuple[float, float]],
        point_labels: Optional[List[int]] = None,
        mask_threshold: float = 0.0,
    ) -> Tuple[np.ndarray, float]:
        """
        Predict semantic mask for specified interactive point prompts on Hexagon HTP.
        
        Args:
            point_coords: List of (x, y) coordinates in original image space.
            point_labels: List of labels (1 = foreground, 0 = background). Defaults to all 1.
            mask_threshold: Logit threshold for binary segmentation (default: 0.0).
            
        Returns:
            Tuple[np.ndarray, float]:
                - Binary mask array of shape (height, width) with dtype bool.
                - Confidence score (float, between 0.0 and 1.0+).
        """
        if self._cached_embeddings is None or self._orig_size is None:
            raise RuntimeError("No image has been encoded yet. Call set_image() first.")

        orig_w, orig_h = self._orig_size

        if not point_coords:
            raise ValueError("point_coords list cannot be empty.")

        if point_labels is None:
            point_labels = [1] * len(point_coords)

        if len(point_coords) != len(point_labels):
            raise ValueError("point_coords and point_labels must have the same length.")

        # Map original image coordinates (x, y) to MobileSAM 1024x1024 coordinate space
        pts_1024 = []
        for x, y in point_coords:
            x_1024 = float(x) * 1024.0 / float(orig_w)
            y_1024 = float(y) * 1024.0 / float(orig_h)
            pts_1024.append([x_1024, y_1024])

        pts_array = np.array([pts_1024], dtype=np.float32)  # shape [1, N, 2]
        lbls_array = np.array([point_labels], dtype=np.float32)  # shape [1, N]

        # Decoder inference on Hexagon HTP
        t0 = time.perf_counter()
        outputs = self._decoder_session.run(
            None,
            {
                "image_embeddings": self._cached_embeddings,
                "point_coords": pts_array,
                "point_labels": lbls_array,
            },
        )
        elapsed = (time.perf_counter() - t0) * 1000
        masks, scores = outputs[0], outputs[1]

        score = float(scores[0, 0])
        mask_logits_256 = masks[0, 0]  # shape [256, 256]

        # Threshold logits to uint8 binary mask [0, 255]
        bin_mask_256 = (mask_logits_256 > mask_threshold).astype(np.uint8) * 255

        # Resize mask back to original resolution
        mask_pil = Image.fromarray(bin_mask_256).resize((orig_w, orig_h), Image.Resampling.BILINEAR)
        final_binary_mask = np.array(mask_pil) > 127

        logger.debug(
            f"Point prompt prediction completed in {elapsed:.2f} ms: "
            f"score={score:.3f}, foreground_pixels={final_binary_mask.sum()}"
        )
        return final_binary_mask, score

    def clear_cache(self) -> None:
        """Clear cached image embeddings."""
        self._cached_embeddings = None
        self._orig_size = None
