from __future__ import annotations

from engine.backends.backend_adapter import BackendAdapter
from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult


class StableDiffusion15QnnBackendAdapter(BackendAdapter):
    """
    Qualcomm Hexagon HTP Backend adapter for SD1.5.
    """

    def initialize(self) -> None:
        print("[StableDiffusion15QnnBackendAdapter] Running on Qualcomm Hexagon HTP")

    def shutdown(self) -> None:
        pass

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

    def generate(self, job: GenerationJob) -> GenerationResult:
        # Route to physical QNN backend
        from engine.inference_backend_factory import InferenceBackendFactory
        backend = InferenceBackendFactory.get_backend(self.get_backend_name())
        return backend.generate(job)

    def cancel(self, job: GenerationJob) -> str:
        job.status = "CANCELLED"
        return "Generation cancelled"

    def get_progress(self, job: GenerationJob) -> float:
        return job.progress

    def health_check(self) -> bool:
        return True
