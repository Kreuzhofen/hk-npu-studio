from __future__ import annotations

from engine.backends.backend_adapter import BackendAdapter
from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult


class ControlNetCannyQnnBackendAdapter(BackendAdapter):
    """
    Qualcomm Hexagon HTP Backend adapter for ControlNet Canny.
    """

    def __init__(self) -> None:
        self._running_backend = None

    def set_running_backend(self, backend) -> None:
        """Bind the physical backend instance currently executing this adapter's job."""
        self._running_backend = backend

    def initialize(self) -> None:
        print("[ControlNetCannyQnnBackendAdapter] Running on Qualcomm Hexagon HTP")

    def shutdown(self) -> None:
        pass

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

    def generate(self, job: GenerationJob) -> GenerationResult:
        # Route to physical QNN backend
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
        return True
