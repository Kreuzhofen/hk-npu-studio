from __future__ import annotations

from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult
from engine.backends.backend_adapter import BackendAdapter
from engine.job_lifecycle import JobStatus, set_job_progress, set_job_status


class StubBackendAdapter(BackendAdapter):
    """Gemeinsame, zustandskompatible Basis der CPU-, ONNX- und QNN-Stubs."""

    BACKEND_NAME = "Unbekanntes Backend (Stub)"
    BACKEND_VERSION = "0.1.0-stub"
    SUPPORTED_MODELS: tuple[str, ...] = ()
    INITIALIZE_MESSAGE = ""
    SHUTDOWN_MESSAGE = ""
    GENERATE_MESSAGE = ""
    SUCCESS_MESSAGE = "Generierung erfolgreich abgeschlossen (Stub)."
    CANCEL_LOG_MESSAGE = ""
    CANCEL_MESSAGE = "Generation cancelled (stub)"

    def initialize(self) -> None:
        if self.INITIALIZE_MESSAGE:
            print(self.INITIALIZE_MESSAGE)

    def shutdown(self) -> None:
        if self.SHUTDOWN_MESSAGE:
            print(self.SHUTDOWN_MESSAGE)

    def is_available(self) -> bool:
        return True

    def get_backend_name(self) -> str:
        return self.BACKEND_NAME

    def get_backend_version(self) -> str:
        return self.BACKEND_VERSION

    def get_supported_models(self) -> list[str]:
        return list(self.SUPPORTED_MODELS)

    def generate(self, job: GenerationJob) -> GenerationResult:
        if self.GENERATE_MESSAGE:
            print(self.GENERATE_MESSAGE.format(job_id=job.job_id))
        set_job_status(job, JobStatus.RUNNING)
        set_job_progress(job, max(float(job.progress), 0.1), notify=False)
        set_job_status(job, JobStatus.FINISHED)
        set_job_progress(job, 1.0, notify=False)
        return GenerationResult(
            success=True,
            status="FINISHED",
            message=self.SUCCESS_MESSAGE,
            image_path=None,
            thumbnail_path=None,
            backend_name=self.get_backend_name(),
            model_name=job.session.model_name if (job and job.session) else "Unknown",
        )

    def cancel(self, job: GenerationJob) -> str:
        if self.CANCEL_LOG_MESSAGE:
            print(self.CANCEL_LOG_MESSAGE.format(job_id=job.job_id))
        super().cancel(job)
        return self.CANCEL_MESSAGE
