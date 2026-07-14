from __future__ import annotations

from pathlib import Path

from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult
from engine.backends.backend_adapter import BackendAdapter


class StableDiffusion21QnnBackendAdapter(BackendAdapter):
    """Product routing adapter for the dedicated SD2.1 QNN backend."""

    MODEL_DIR = Path(r"C:\SnapdragonAI\models\stable_diffusion_v2_1")

    def __init__(self) -> None:
        self._running_backend = None

    def set_running_backend(self, backend) -> None:
        """Bind the physical backend instance currently executing this adapter's job."""
        self._running_backend = backend

    def initialize(self) -> None:
        print("[StableDiffusion21QnnBackendAdapter] Running on Qualcomm Hexagon HTP")

    def shutdown(self) -> None:
        pass

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

    def generate(self, job: GenerationJob) -> GenerationResult:
        from engine.inference_backend_factory import InferenceBackendFactory
        backend = InferenceBackendFactory.get_backend(self.get_backend_name())
        self._running_backend = backend
        try:
            return backend.generate(job)
        finally:
            if self._running_backend is backend:
                self._running_backend = None

    def cancel(self, job: GenerationJob) -> str:
        job.cancel_requested.set()
        job.status = "CANCELLED"
        backend = self._running_backend
        if backend is not None:
            backend.cancel(job)
        return "Generation cancelled"

    def get_progress(self, job: GenerationJob) -> float:
        return job.progress

    def health_check(self) -> bool:
        return self.is_available()
