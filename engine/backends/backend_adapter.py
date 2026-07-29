from __future__ import annotations

from abc import ABC, abstractmethod

from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult
from engine.inference_backend import InferenceBackend


class BackendAdapter(InferenceBackend, ABC):
    """Routing-Erweiterung des gemeinsamen Inferenz-Backend-Vertrags."""

    @abstractmethod
    def is_available(self) -> bool:
        """Prüft die Verfügbarkeit des Routing-Ziels."""
        raise NotImplementedError

    @abstractmethod
    def get_backend_name(self) -> str:
        """Liefert den stabilen Registrierungsnamen."""
        raise NotImplementedError

    @abstractmethod
    def get_backend_version(self) -> str:
        """Liefert die bekannte Laufzeitversion."""
        raise NotImplementedError

    @abstractmethod
    def get_supported_models(self) -> list[str]:
        """Liefert die unterstützten Modellkennungen."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, job: GenerationJob) -> GenerationResult:
        """Delegiert einen Generierungsauftrag an das konkrete Backend."""
        raise NotImplementedError
