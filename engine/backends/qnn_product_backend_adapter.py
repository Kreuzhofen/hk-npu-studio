from __future__ import annotations

from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult
from engine.backends.backend_adapter import BackendAdapter


class QnnProductBackendAdapter(BackendAdapter):
    """Gemeinsame Routing- und Abbruchlogik produktiver QNN-Modelladapter."""

    INITIALIZE_MESSAGE = ""

    def __init__(self) -> None:
        self._running_backend = None

    def set_running_backend(self, backend) -> None:
        """Bindet die aktuell ausgeführte physische Backend-Instanz."""
        self._running_backend = backend

    def initialize(self) -> None:
        if self.INITIALIZE_MESSAGE:
            print(self.INITIALIZE_MESSAGE)

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
        super().cancel(job)
        backend = self._running_backend
        if backend is not None:
            backend.cancel(job)
        return "Generation cancelled"
