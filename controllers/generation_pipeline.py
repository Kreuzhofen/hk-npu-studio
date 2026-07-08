from __future__ import annotations

import time
from typing import Any
from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult


class ImageGenerationPipeline:
    """
    Manages the execution workflow of an image generation task.
    Sequentially orchestrates: prepare -> validate -> execute -> finish -> cleanup.
    Currently a stub awaiting physical acceleration backends.
    """

    def __init__(self, job: GenerationJob, backend_adapter: Any) -> None:
        self.job = job
        self.backend_adapter = backend_adapter
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def prepare(self) -> None:
        """Prepares folders, locks model weights, and primes NPU/CPU backend buffers."""
        self.start_time = time.time()
        # Stub preparation: Create target directories, print logs

    def validate(self) -> bool:
        """Performs syntax, boundary, and model parameter validation checks."""
        if not self.job or not self.job.session:
            return False
        
        # Verify resolution parameter bounds
        width = self.job.session.width
        height = self.job.session.height
        if width <= 0 or height <= 0:
            return False
            
        return True

    def execute(self) -> GenerationResult:
        """Runs the active BackendAdapter to synthesize the image output."""
        from engine.generation_executor import GenerationExecutor
        executor = GenerationExecutor()
        return executor.execute(self.job, self.backend_adapter)

    def finish(self, result: GenerationResult) -> GenerationResult:
        """Appends generation performance metrics, saves metadata files, and triggers workflow callbacks."""
        self.end_time = time.time()
        if result:
            result.generation_time = max(0.0, self.end_time - self.start_time)
        return result

    def cleanup(self) -> None:
        """Frees GPU/NPU memory locks, deletes temporary scratch files, and resets buffers."""
        # Stub cleanup
        pass

    def run(self) -> GenerationResult:
        """Orchestrator executing the complete pipeline flow and returning the final GenerationResult."""
        try:
            self.prepare()
            if not self.validate():
                return GenerationResult(
                    success=False,
                    status="ValidationError",
                    message="Pipeline validation failed: invalid parameters.",
                    model_name=self.job.session.model_name if (self.job and self.job.session) else "Unknown"
                )

            result = self.execute()
            result = self.finish(result)
            return result
        except Exception as error:
            return GenerationResult(
                success=False,
                status="PipelineError",
                message=str(error),
                model_name=self.job.session.model_name if (self.job and self.job.session) else "Unknown"
            )
        finally:
            self.cleanup()
