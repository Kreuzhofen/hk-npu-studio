from __future__ import annotations

from engine.backends.qnn_product_backend_adapter import QnnProductBackendAdapter


class ControlNetCannyQnnBackendAdapter(QnnProductBackendAdapter):
    """
    Qualcomm Hexagon HTP Backend adapter for ControlNet Canny.
    """

    INITIALIZE_MESSAGE = (
        "[ControlNetCannyQnnBackendAdapter] Running on Qualcomm Hexagon HTP"
    )

    def is_available(self) -> bool:
        from pathlib import Path
        model_dir = Path(r"C:\SnapdragonAI\temp\controlnet_canny_gate\controlnet_canny-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite")
        if not (model_dir / "controlnet.onnx").exists():
            return False
        return True

    def get_backend_name(self) -> str:
        return "Qualcomm ControlNet Canny (HTP V73)"

    def get_backend_version(self) -> str:
        return "2.45.41"

    def get_supported_models(self) -> list[str]:
        return ["controlnet_canny_qnn"]

    def health_check(self) -> bool:
        return True
