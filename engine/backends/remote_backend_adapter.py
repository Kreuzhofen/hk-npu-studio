from __future__ import annotations

from engine.backends.backend_adapter import BackendAdapter
from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult
from engine.job_lifecycle import JobStatus, cancel_job, set_job_progress, set_job_status
from engine.logging_config import get_logger


logger = get_logger("RemoteBackendAdapter")


class RemoteBackendAdapter(BackendAdapter):
    """
    Remote Cloud API backend adapter.
    Dispatches generation jobs to cloud providers (e.g. Hugging Face, Replicate, AWS) via web APIs.
    
    Future Integration:
    - Protocol: REST / gRPC API clients using requests / aiohttp
    - Services: Stable Diffusion 3, Flux.1 Ultra, Wan2.1 Video Generation APIs
    - Features: Real-time progress webhooks, batch scheduling, and cloud storage download helpers
    """

    def initialize(self) -> None:
        print("[RemoteBackendAdapter] Initializing cloud API connection handlers...")

    def shutdown(self) -> None:
        print("[RemoteBackendAdapter] Terminating active HTTP sessions...")

    def is_available(self) -> bool:
        # TODO: Ping API endpoint to check internet connectivity and server availability
        return True

    def get_backend_name(self) -> str:
        return "Remote Cloud API (Stub)"

    def get_backend_version(self) -> str:
        return "v1-api-stub"

    def get_supported_models(self) -> list[str]:
        return ["flux_1_ultra_api", "sd_3_medium_api"]

    def generate(self, job: GenerationJob) -> GenerationResult:
        logger.info("Remote-Generierung gestartet | job_id=%s", job.job_id)
        print(f"[RemoteBackendAdapter] Sending API post request for job {job.job_id}...")
        set_job_status(job, JobStatus.RUNNING)
        # TODO: Send request and await generation webhook/response
        set_job_status(job, JobStatus.FINISHED)
        set_job_progress(job, 1.0, notify=False)
        return GenerationResult(
            success=True,
            status="FINISHED",
            message="Bildgenerierung via Cloud-API erfolgreich (Stub).",
            image_path=None,
            thumbnail_path=None,
            backend_name=self.get_backend_name(),
            model_name=job.session.model_name if (job and job.session) else "Unknown",
        )

    def cancel(self, job: GenerationJob) -> str:
        logger.warning("Remote-Abbruch angefordert | job_id=%s", job.job_id)
        print(f"[RemoteBackendAdapter] Sending cancel signal to API server for job {job.job_id}...")
        cancel_job(job)
        return "Generation cancelled on cloud API (stub)"

    def get_progress(self, job: GenerationJob) -> float:
        return job.progress

    def health_check(self) -> bool:
        # TODO: Perform cloud API ping request
        return True
