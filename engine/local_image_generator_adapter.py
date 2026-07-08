from __future__ import annotations

import time
import logging
from pathlib import Path
from typing import Any
from controllers.generation_job import GenerationJob
from engine.generation_response import GenerationResponse
from engine.runtime_model import RuntimeModel

logger = logging.getLogger("LocalImageGeneratorAdapter")


class LocalImageGeneratorAdapter:
    """
    Adapter for local image generation. Resolves the target backend and delegates to the InferenceBackend.
    """

    def __init__(self, backend_adapter: Any = None) -> None:
        self.backend_adapter = backend_adapter

    def get_backend_name(self) -> str:
        if self.backend_adapter:
            return self.backend_adapter.get_backend_name()
        return "Local CPU (Stub)"

    def generate(self, job: GenerationJob, runtime_model: RuntimeModel | None = None) -> GenerationResponse:
        backend_name = self.get_backend_name()
        logger.info(f"[Adapter] Starting generate() on backend: {backend_name}")
        print(f"[Adapter] Starting generate() on backend: {backend_name}")

        # Retrieve backend from the factory, passing the runtime_model
        from engine.inference_backend_factory import InferenceBackendFactory
        backend = InferenceBackendFactory.get_backend(backend_name, runtime_model=runtime_model)

        logger.info(f"[Adapter] Delegating to InferenceBackend: {backend.__class__.__name__}")
        print(f"[Adapter] Delegating to InferenceBackend: {backend.__class__.__name__}")
        
        return backend.generate(job)

