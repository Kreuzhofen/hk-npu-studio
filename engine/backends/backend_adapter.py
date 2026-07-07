from __future__ import annotations

from abc import ABC, abstractmethod
from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult


class BackendAdapter(ABC):
    """
    Abstract base class for all AI inference engine adapters.
    Ensures a standardized interface for various local (NPU, CPU, GPU) and remote backends.
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the backend, loading hardware runtimes or SDK configurations."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the backend, releasing resources, memory, or network sockets."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend adapter is available on the current hardware/platform."""
        pass

    @abstractmethod
    def get_backend_name(self) -> str:
        """Get the human-readable name of the backend."""
        pass

    @abstractmethod
    def get_backend_version(self) -> str:
        """Get the version string of the backend engine."""
        pass

    @abstractmethod
    def get_supported_models(self) -> list[str]:
        """Get a list of models supported by this backend."""
        pass

    @abstractmethod
    def generate(self, job: GenerationJob) -> GenerationResult:
        """
        Execute an image/video generation job.
        Returns a GenerationResult instance.
        """
        pass

    @abstractmethod
    def cancel(self, job: GenerationJob) -> str:
        """Cancel a running generation job."""
        pass

    @abstractmethod
    def get_progress(self, job: GenerationJob) -> float:
        """Get the current progress (0.0 to 1.0) of a running job."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Perform a diagnosis check to ensure the backend is fully operational."""
        pass
