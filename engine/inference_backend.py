from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from controllers.generation_job import GenerationJob
from engine.generation_response import GenerationResponse


class InferenceBackend(ABC):
    """
    Abstract base class for physical local inference backends.
    Allows decoupling model loaders and generation adapters from specific runtimes (QNN, ONNX, CPU, etc.).
    """

    @abstractmethod
    def generate(self, job: GenerationJob) -> GenerationResponse:
        """
        Execute image/asset generation for the given job.
        Returns a GenerationResponse.
        """
        pass
