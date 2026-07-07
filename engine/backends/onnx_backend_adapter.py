from __future__ import annotations

from engine.backends.backend_adapter import BackendAdapter
from controllers.generation_job import GenerationJob


class ONNXBackendAdapter(BackendAdapter):
    """
    ONNX Runtime local execution adapter.
    Supports CPU, GPU (CUDA), and DirectML acceleration execution targets.
    
    Future Integration:
    - Acceleration Providers: CPUExecutionProvider, DmlExecutionProvider (DirectML for AMD/Intel/Nvidia on Windows)
    - Pipelines: Stable Diffusion 1.5, SDXL, and ControlNet ONNX models
    - Optimizations: ORT model quantization and execution graph optimizations
    """

    def initialize(self) -> None:
        print("[ONNXBackendAdapter] Loading ONNX Runtime sessions...")
        # TODO: import onnxruntime as ort

    def shutdown(self) -> None:
        print("[ONNXBackendAdapter] Shutting down ONNX Runtime sessions...")

    def is_available(self) -> bool:
        # TODO: Verify onnxruntime package availability
        return True

    def get_backend_name(self) -> str:
        return "ONNX Runtime (Stub)"

    def get_backend_version(self) -> str:
        return "1.18.0-stub"

    def get_supported_models(self) -> list[str]:
        return ["sd_xl_base_1.0_onnx", "sd_1.5_onnx"]

    def generate(self, job: GenerationJob) -> str:
        print(f"[ONNXBackendAdapter] Executing ONNX pipeline for job {job.job_id}...")
        job.status = "RUNNING"
        # TODO: Execute ORT session.run loop over UNet/VAE models
        return "Generation running on ORT (stub)"

    def cancel(self, job: GenerationJob) -> str:
        print(f"[ONNXBackendAdapter] Signalling cancellation to ONNX session for job {job.job_id}...")
        job.status = "CANCELLED"
        return "Generation cancelled on ORT (stub)"

    def get_progress(self, job: GenerationJob) -> float:
        return job.progress

    def health_check(self) -> bool:
        return True
