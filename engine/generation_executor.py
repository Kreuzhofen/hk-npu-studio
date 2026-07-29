from __future__ import annotations

from typing import Any
from controllers.generation_job import GenerationJob
from controllers.model_repository import ModelRepository
from engine.model_loader_service import ModelLoaderService
from engine.generation_response import GenerationResponse
from engine.local_image_generator_adapter import LocalImageGeneratorAdapter
from engine.logging_config import get_logger
from engine.runtime_model import RuntimeModel

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

        # 2. Build model load plan and instantiate RuntimeModel
        load_plan = self.loader_service.build_model_load_plan(model_name)
        runtime_model = RuntimeModel(
            model_id=resolve_result.model_id,
            model_path=resolve_result.model_path or "",
            files=resolve_result.files,
            backend=resolve_result.backend,
            load_plan=load_plan
        )

        # Retrieve backend name for logging
        adapter = LocalImageGeneratorAdapter(backend_adapter)
        backend_name = adapter.get_backend_name()

        # Extended logging: Selected Model, Runtime Model, Backend
        logger.info(f"[Executor] Selected Model: {model_name}")
        logger.info(f"[Executor] Runtime Model: ID={runtime_model.model_id}, Path={runtime_model.model_path}, Backend={runtime_model.backend}")
        logger.info(f"[Executor] Target Backend: {backend_name}")
        
        print(f"[Executor] Selected Model: {model_name}")
        print(f"[Executor] Runtime Model: ID={runtime_model.model_id}, Path={runtime_model.model_path}, Backend={runtime_model.backend}")
        print(f"[Executor] Target Backend: {backend_name}")

        # 3. Dispatch to the local image generator adapter passing the runtime model
        logger.info(f"[Executor] Dispatching to LocalImageGeneratorAdapter with backend: {backend_name}")
        print(f"[Executor] Dispatching to LocalImageGeneratorAdapter with backend: {backend_name}")

        response = adapter.generate(job, runtime_model=runtime_model)
        
        logger.info(f"[Executor] Generation finished. Success: {response.success}, Backend: {response.backend_name}")
        print(f"[Executor] Generation finished. Success: {response.success}, Backend: {response.backend_name}")

        return response
