from __future__ import annotations

from engine.backends.backend_adapter import BackendAdapter
from controllers.generation_job import GenerationJob


class CPUBackendAdapter(BackendAdapter):
    """
    CPU-based local inference reference adapter.
    Uses pure PyTorch (CPU) or NumPy fallbacks for testing and model evaluation.
    
    Future Integration:
    - Text Encoders: CLIP ViT-L, T5-XXL (run on CPU for RAM saving)
    - VAE: AutoencoderKL decoding steps
    - Models: SDXL Base, Stable Diffusion 3 Medium, Flux.1 Dev
    - Schedulers: DPMSolverMultistepScheduler, EulerDiscreteScheduler
    """

    def initialize(self) -> None:
        print("[CPUBackendAdapter] Initializing CPU inference context...")

    def shutdown(self) -> None:
        print("[CPUBackendAdapter] Cleaning up CPU inference context...")

    def is_available(self) -> bool:
        return True  # CPU is always available as fallback

    def get_backend_name(self) -> str:
        return "CPU (Stub)"

    def get_backend_version(self) -> str:
        return "0.1.0-stub"

    def get_supported_models(self) -> list[str]:
        return ["sd_xl_base_1.0", "sd_1.5_resnet"]

    def generate(self, job: GenerationJob) -> str:
        print(f"[CPUBackendAdapter] Starting generation stub for job {job.job_id}...")
        job.status = "RUNNING"
        job.progress = 0.1
        # TODO: Implement local CPU pipeline scheduler loop:
        # 1. Encode prompt using Text Encoder (CLIP/T5)
        # 2. Iterate scheduler denoising steps over latent noise tensor
        # 3. Decode latents using VAE decoder
        # 4. Save result image and update job.result_path
        job.status = "FINISHED"
        job.progress = 1.0
        return "Generation finished (stub)"

    def cancel(self, job: GenerationJob) -> str:
        print(f"[CPUBackendAdapter] Cancelling job {job.job_id}...")
        job.status = "CANCELLED"
        return "Generation cancelled (stub)"

    def get_progress(self, job: GenerationJob) -> float:
        return job.progress

    def health_check(self) -> bool:
        return True
