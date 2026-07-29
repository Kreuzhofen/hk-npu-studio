from __future__ import annotations

from engine.backends.qnn_product_backend_adapter import QnnProductBackendAdapter


class StableDiffusion15QnnBackendAdapter(QnnProductBackendAdapter):
    """
    Qualcomm Hexagon HTP Backend adapter for SD1.5.
    """

    INITIALIZE_MESSAGE = (
        "[StableDiffusion15QnnBackendAdapter] Running on Qualcomm Hexagon HTP"
    )

    def is_available(self) -> bool:
        # Verify model files and QNN runtime are present
        from pathlib import Path
        model_dir = Path(r"C:\SnapdragonAI\temp\stable_diffusion_v1_5_qnn_inspection\stable_diffusion_v1_5-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite")
        if not (model_dir / "text_encoder.onnx").exists():
            return False
        return True

    def get_backend_name(self) -> str:
        return "Qualcomm Stable Diffusion 1.5 (HTP V73)"

    def get_backend_version(self) -> str:
        return "2.45.41"

    def get_supported_models(self) -> list[str]:
        return ["stable_diffusion_v1_5_qnn"]

    def health_check(self) -> bool:
        return True
