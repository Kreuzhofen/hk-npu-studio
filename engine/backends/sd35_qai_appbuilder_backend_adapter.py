from __future__ import annotations

from controllers.generation_job import GenerationJob
from engine.backends.backend_adapter import BackendAdapter
from engine.sd35_qai_appbuilder_backend import BACKEND_NAME, MODEL_ID, get_shared_backend


class StableDiffusion35QaiAppBuilderBackendAdapter(BackendAdapter):
    """Adapter retaining one persistent, serial SD3.5 QAI worker."""

    def __init__(self) -> None:
        self._backend = get_shared_backend()

    def initialize(self) -> None:
        return None

    def shutdown(self) -> None:
        self._backend.close()

    def is_available(self) -> bool:
        return self._backend.is_available()

    def get_backend_name(self) -> str:
        return BACKEND_NAME

    def get_backend_version(self) -> str:
        return self._backend.get_backend_version()

    def get_supported_models(self) -> list[str]:
        return [MODEL_ID]

    def generate(self, job: GenerationJob):
        return self._backend.generate(job)

    def cancel(self, job: GenerationJob) -> str:
        return self._backend.cancel(job)
