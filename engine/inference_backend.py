from __future__ import annotations

from abc import ABC, abstractmethod

from controllers.generation_job import GenerationJob
from engine.generation_response import GenerationResponse
from engine.job_lifecycle import cancel_job


class InferenceBackend(ABC):
    """Gemeinsamer Vertrag für Routing-Adapter und physische Inferenz-Backends."""

    def initialize(self) -> None:
        """Initialisiert optionale Laufzeitressourcen."""

    def shutdown(self) -> None:
        """Gibt optionale Laufzeitressourcen frei."""

    def is_available(self) -> bool:
        """Meldet, ob das Backend in der aktuellen Umgebung nutzbar ist."""
        return True

    def get_backend_name(self) -> str:
        """Liefert den stabilen Anzeigenamen des Backends."""
        return self.__class__.__name__

    def get_backend_version(self) -> str:
        """Liefert die bekannte Backend-Version."""
        return "Unbekannt"

    def get_supported_models(self) -> list[str]:
        """Liefert die explizit unterstützten Modellkennungen."""
        return []

    @abstractmethod
    def generate(self, job: GenerationJob) -> GenerationResponse:
        """Führt einen Generierungsauftrag aus."""
        raise NotImplementedError

    def cancel(self, job: GenerationJob) -> str:
        """Markiert einen Auftrag über den gemeinsamen Abbruchpfad als abgebrochen."""
        cancel_job(job)
        return "Generation cancelled"

    def get_progress(self, job: GenerationJob) -> float:
        """Liefert den normalisierten Fortschritt des Auftrags."""
        return float(job.progress)

    def health_check(self) -> bool:
        """Verwendet standardmäßig die Verfügbarkeitsprüfung."""
        return self.is_available()
