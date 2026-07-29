from __future__ import annotations

from typing import Any
from controllers.generation_job import GenerationJob
from controllers.model_repository import ModelRepository
from engine.model_loader_service import ModelLoaderService
from engine.generation_response import GenerationResponse
from engine.local_image_generator_adapter import LocalImageGeneratorAdapter
from engine.logging_config import get_logger

logger = get_logger("GenerationExecutor")


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

        # 1. Resolve, validate, and acquire the shared model/backend lifecycle.
        load_result = self.loader_service.load_model(model_name)
        if not load_result.success or load_result.loaded_model is None:
            logger.error(f"[Executor] Model loading failed: {load_result.message}")
            print(f"[Executor] Model loading failed: {load_result.message}")
            return GenerationResponse(
                success=False,
                status="LoadError",
                message=load_result.message,
                model_name=model_name
            )

        try:
            runtime_model = load_result.loaded_model.runtime_model
            if backend_adapter is None:
                backend_adapter = load_result.loaded_model.backend_adapter

            adapter = LocalImageGeneratorAdapter(backend_adapter)
            backend_name = adapter.get_backend_name()
            logger.info(f"[Executor] Selected Model: {model_name}")
            logger.info(f"[Executor] Runtime Model: ID={runtime_model.model_id}, Path={runtime_model.model_path}, Backend={runtime_model.backend}")
            logger.info(f"[Executor] Target Backend: {backend_name}")
            print(f"[Executor] Selected Model: {model_name}")
            print(f"[Executor] Runtime Model: ID={runtime_model.model_id}, Path={runtime_model.model_path}, Backend={runtime_model.backend}")
            print(f"[Executor] Target Backend: {backend_name}")
            logger.info(f"[Executor] Dispatching to LocalImageGeneratorAdapter with backend: {backend_name}")
            print(f"[Executor] Dispatching to LocalImageGeneratorAdapter with backend: {backend_name}")
            response = adapter.generate(job, runtime_model=runtime_model)
        finally:
            self.loader_service.unload_model(model_name)
        
        logger.info(f"[Executor] Generation finished. Success: {response.success}, Backend: {response.backend_name}")
        print(f"[Executor] Generation finished. Success: {response.success}, Backend: {response.backend_name}")

        return response
