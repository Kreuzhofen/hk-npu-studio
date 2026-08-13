from __future__ import annotations

from config import MODELS_DIR
from engine.backends.qnn_product_backend_adapter import QnnProductBackendAdapter


class ControlNetCannyQnnBackendAdapter(QnnProductBackendAdapter):
    """
    Qualcomm Hexagon HTP Backend adapter for ControlNet Canny.
    """

    INITIALIZE_MESSAGE = (
        "[ControlNetCannyQnnBackendAdapter] Running on Qualcomm Hexagon HTP"
    )

    def is_available(self) -> bool:
        model_dir = MODELS_DIR / "controlnet_canny_qnn"
        required = (
            "metadata.json",
            "text_encoder.onnx",
            "text_encoder_qairt_context.bin",
            "controlnet.onnx",
            "controlnet_qairt_context.bin",
            "unet.onnx",
            "unet_qairt_context.bin",
            "vae.onnx",
            "vae_qairt_context.bin",
            "tokenizer/vocab.json",
            "tokenizer/merges.txt",
        )
        return all((model_dir / relative).is_file() for relative in required)

    def get_backend_name(self) -> str:
        return "Qualcomm ControlNet Canny (HTP V73)"

    def get_backend_version(self) -> str:
        return "2.45.41"

    def get_supported_models(self) -> list[str]:
        return ["controlnet_canny_qnn"]

    def health_check(self) -> bool:
        return True
