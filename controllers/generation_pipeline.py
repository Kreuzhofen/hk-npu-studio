from __future__ import annotations

import time
from typing import Any
from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult
from engine.error_diagnostics import diagnose_exception
from engine.job_lifecycle import JobStatus, get_job_status, set_job_progress, set_job_status
from engine.logging_config import get_logger


logger = get_logger("ImageGenerationPipeline")


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
        set_job_status(self.job, JobStatus.RUNNING)
        set_job_progress(self.job, self.job.progress, "Pipeline gestartet", notify=False)
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

            if result.success and result.image_path:
                try:
                    import json
                    from pathlib import Path
                    from controllers.model_repository import ModelRepository

                    image_path = Path(result.image_path)
                    sidecar_path = image_path.with_suffix(".json")

                    # Read repository to find if active model supports ControlNet
                    model_name = self.job.session.model_name
                    repo = ModelRepository()
                    model_meta = repo.get_model(model_name)
                    controlnet_enabled = False
                    if model_meta:
                        capabilities = model_meta.get("capabilities", {})
                        controlnet_enabled = capabilities.get("controlnet", False)

                    # Prepare ControlNet fields
                    controlnet_model = "canny" if controlnet_enabled else None
                    canny_low_threshold = int(self.job.session.canny_low_threshold) if controlnet_enabled else None
                    canny_high_threshold = int(self.job.session.canny_high_threshold) if controlnet_enabled else None
                    controlnet_conditioning_scale = float(self.job.session.controlnet_conditioning_scale) if controlnet_enabled else None
                    reference_image_path = self.job.session.input_image_path if controlnet_enabled else None

                    # If sidecar exists, load it, modify it, and save it back.
                    # If it doesn't exist, we can create one!
                    data = {}
                    if sidecar_path.is_file():
                        with open(sidecar_path, "r", encoding="utf-8") as f:
                            data = json.load(f)

                    data["controlnet_enabled"] = controlnet_enabled
                    data["controlnet_model"] = controlnet_model
                    data["canny_low_threshold"] = canny_low_threshold
                    data["canny_high_threshold"] = canny_high_threshold
                    data["controlnet_conditioning_scale"] = controlnet_conditioning_scale
                    data["reference_image_path"] = reference_image_path

                    # Write back to sidecar
                    with open(sidecar_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    # Update result metadata dict
                    result.metadata.update({
                        "controlnet_enabled": controlnet_enabled,
                        "controlnet_model": controlnet_model,
                        "canny_low_threshold": canny_low_threshold,
                        "canny_high_threshold": canny_high_threshold,
                        "controlnet_conditioning_scale": controlnet_conditioning_scale,
                        "reference_image_path": reference_image_path
                    })

                except Exception as error:
                    diagnose_exception(
                        logger,
                        error,
                        category="pipeline",
                        context="sidecar_postprocessing",
                    )
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
                self.job.fail("Pipeline validation failed: invalid parameters.")
                return GenerationResult(
                    success=False,
                    status="ValidationError",
                    message="Pipeline validation failed: invalid parameters.",
                    model_name=self.job.session.model_name if (self.job and self.job.session) else "Unknown"
                )

            result = self.execute()
            result = self.finish(result)
            if get_job_status(self.job) != JobStatus.CANCELLED:
                if result.success:
                    set_job_status(self.job, JobStatus.FINISHED)
                    set_job_progress(self.job, 1.0, "Pipeline abgeschlossen", notify=False)
                else:
                    self.job.fail(result.message)
            return result
        except Exception as error:
            diagnose_exception(
                logger,
                error,
                category="pipeline",
                context="pipeline_run",
                job=self.job,
            )
            return GenerationResult(
                success=False,
                status="PipelineError",
                message=str(error),
                model_name=self.job.session.model_name if (self.job and self.job.session) else "Unknown"
            )
        finally:
            self.cleanup()
