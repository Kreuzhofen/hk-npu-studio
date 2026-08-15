from __future__ import annotations

import config

from engine.backends.qnn_product_backend_adapter import QnnProductBackendAdapter


class StableDiffusion21QnnBackendAdapter(QnnProductBackendAdapter):
    """Product routing adapter for the dedicated SD2.1 QNN backend."""

    MODEL_DIR = config.MODELS_DIR / "stable_diffusion_v2_1_qnn"

    INITIALIZE_MESSAGE = (
        "[StableDiffusion21QnnBackendAdapter] Running on Qualcomm Hexagon HTP"
    )

    def is_available(self) -> bool:
        required = (
            "text_encoder.onnx", "text_encoder.bin",
            "unet.onnx", "unet.bin",
            "vae.onnx", "vae.bin",
        )
        return all((self.MODEL_DIR / name).is_file() for name in required)

    def get_backend_name(self) -> str:
        return "Qualcomm Stable Diffusion 2.1 (HTP V73)"

    def get_backend_version(self) -> str:
        return "2.45"

    def get_supported_models(self) -> list[str]:
        return ["stable_diffusion_v2_1_qnn"]

    def health_check(self) -> bool:
        return self.is_available()
