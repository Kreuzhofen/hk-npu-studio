from __future__ import annotations

import logging
from typing import Any
from controllers.generation_job import GenerationJob
from controllers.model_repository import ModelRepository
from engine.model_loader_service import ModelLoaderService
from engine.generation_response import GenerationResponse
from engine.local_image_generator_adapter import LocalImageGeneratorAdapter

logger = logging.getLogger("GenerationExecutor")


class GenerationExecutor:
    """
    Orchestrates the resolution and dispatching of generation jobs to the correct adapter.
    Logs execution flow: Executor -> Adapter -> Result.
    """

    def __init__(self, repository: ModelRepository | None = None) -> None:
        self.repository = repository or ModelRepository()
        self.loader_service = ModelLoaderService(self.repository)

    def execute(self, job: GenerationJob, backend_adapter: Any = None) -> GenerationResponse:
        model_name = job.session.model_name
        logger.info(f"[Executor] Starting execution for job {job.job_id} using model '{model_name}'")
        print(f"[Executor] Starting execution for job {job.job_id} using model '{model_name}'")

        # 1. Verify model is installed
        resolve_result = self.loader_service.resolve_model(model_name)
        if not resolve_result.success:
            logger.error(f"[Executor] Model resolution failed: {resolve_result.message}")
            print(f"[Executor] Model resolution failed: {resolve_result.message}")
            return GenerationResponse(
                success=False,
                status="LoadError",
                message=resolve_result.message,
                model_name=model_name
            )

        # 2. Dispatch to the local image generator adapter
        adapter = LocalImageGeneratorAdapter(backend_adapter)
        logger.info(f"[Executor] Dispatching to LocalImageGeneratorAdapter with backend: {adapter.get_backend_name()}")
        print(f"[Executor] Dispatching to LocalImageGeneratorAdapter with backend: {adapter.get_backend_name()}")

        response = adapter.generate(job)
        
        logger.info(f"[Executor] Generation finished. Success: {response.success}, Backend: {response.backend_name}")
        print(f"[Executor] Generation finished. Success: {response.success}, Backend: {response.backend_name}")

        return response
