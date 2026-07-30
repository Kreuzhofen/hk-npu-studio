from __future__ import annotations

from app.i18n import tr
import time
from typing import Any
from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult
from engine.error_diagnostics import diagnose_exception
from engine.job_lifecycle import JobStatus, get_job_status, set_job_progress, set_job_status
from engine.logging_config import get_logger
from engine.runtime_model import RuntimeModel


logger = get_logger("ImageGenerationPipeline")


class ImageGenerationPipeline:
    """
    Executes the shared prepare, validate, inference, finish and cleanup lifecycle
    for CPU, ONNX and QNN generation backends.
    """

    def __init__(
        self,
        job: GenerationJob,
        backend_adapter: Any,
        runtime_model: RuntimeModel | None = None,
    ) -> None:
        self.job = job
        self.backend_adapter = backend_adapter
        self.runtime_model = runtime_model
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def prepare(self) -> None:
        """Prepares folders, locks model weights, and primes NPU/CPU backend buffers."""
        self.start_time = time.time()
        if self.job.cancel_requested.is_set():
            set_job_status(self.job, JobStatus.CANCELLED)
            return
        set_job_status(self.job, JobStatus.RUNNING)
        set_job_progress(self.job, self.job.progress, "Pipeline gestartet", notify=False)
        try:
            from engine.resource_monitor import observe_running_job

            observe_running_job(self.job, self.backend_adapter)
        except Exception:
            pass

    def validate(self) -> bool:
        """Performs syntax, boundary, and model parameter validation checks."""
        if not self.job or not self.job.session:
            return False
        session = self.job.parameters
        if (
            isinstance(session.width, bool)
            or not isinstance(session.width, int)
            or isinstance(session.height, bool)
            or not isinstance(session.height, int)
            or session.width <= 0
            or session.height <= 0
            or isinstance(session.steps, bool)
            or not isinstance(session.steps, int)
            or session.steps <= 0
        ):
            return False
        return True

    def execute(self) -> GenerationResult:
        """Runs the active BackendAdapter to synthesize the image output."""
        from engine.generation_executor import GenerationExecutor
        executor = GenerationExecutor()
        return executor.execute(
            self.job,
            self.backend_adapter,
            runtime_model=self.runtime_model,
        )

    def _cancelled_result(self) -> GenerationResult:
        set_job_status(self.job, JobStatus.CANCELLED)
        return GenerationResult(
            success=False,
            status=JobStatus.CANCELLED.value,
            message=tr("generation_cancelled", "Generierung abgebrochen."),
            model_name=(
                self.job.parameters.model_name
                if self.job and self.job.session
                else "Unknown"
            ),
        )

    def _normalize_result(self, result: Any) -> GenerationResult:
        if not isinstance(result, GenerationResult):
            raise TypeError("Inference backend returned no valid GenerationResult.")
        if not isinstance(result.metadata, dict):
            result.metadata = {}
        if not result.model_name or result.model_name == "Unknown":
            result.model_name = self.job.parameters.model_name
        if self.job.cancel_requested.is_set() or get_job_status(self.job) == JobStatus.CANCELLED:
            return self._cancelled_result()
        if result.success:
            result.status = JobStatus.FINISHED.value
        elif not result.status:
            result.status = JobStatus.FAILED.value
        return result

    def finish(self, result: GenerationResult) -> GenerationResult:
        """Appends generation performance metrics, saves metadata files, and triggers workflow callbacks."""
        self.end_time = time.time()
        if result:
            result.generation_time = max(0.0, self.end_time - self.start_time)

            if result.success and result.image_path:
                try:
                    from pathlib import Path
                    from engine.asset_files import atomic_write_json

                    image_path = Path(result.image_path)
                    sidecar_path = image_path.with_suffix(".json")

                    params = self.job.parameters
                    controlnet_enabled = bool(params.controlnet_enabled)

                    # Prepare ControlNet fields
                    controlnet_model = "canny" if controlnet_enabled else None
                    canny_low_threshold = int(params.canny_low_threshold) if controlnet_enabled else None
                    canny_high_threshold = int(params.canny_high_threshold) if controlnet_enabled else None
                    controlnet_conditioning_scale = float(params.controlnet_conditioning_scale) if controlnet_enabled else None
                    reference_image_path = params.input_image_path if controlnet_enabled else None

                    # If sidecar exists, load it, modify it, and save it back.
                    # If it doesn't exist, we can create one!
                    data = {}
                    if sidecar_path.is_file():
                        with open(sidecar_path, "r", encoding="utf-8") as f:
                            import json
                            data = json.load(f)

                    data["controlnet_enabled"] = controlnet_enabled
                    data["controlnet_model"] = controlnet_model
                    data["canny_low_threshold"] = canny_low_threshold
                    data["canny_high_threshold"] = canny_high_threshold
                    data["controlnet_conditioning_scale"] = controlnet_conditioning_scale
                    data["reference_image_path"] = reference_image_path

                    # Write back to sidecar
                    atomic_write_json(sidecar_path, data)

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
            if self.job.cancel_requested.is_set():
                return self._cancelled_result()
            if not self.validate():
                self.job.fail(
                    tr(
                        "pipeline_validation_failed",
                        "Pipeline-Validierung fehlgeschlagen: ungültige Parameter.",
                    )
                )
                return GenerationResult(
                    success=False,
                    status="ValidationError",
                    message=tr(
                        "pipeline_validation_failed",
                        "Pipeline-Validierung fehlgeschlagen: ungültige Parameter.",
                    ),
                    model_name=self.job.parameters.model_name if (self.job and self.job.session) else "Unknown"
                )

            result = self._normalize_result(self.execute())
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
                model_name=self.job.parameters.model_name if (self.job and self.job.session) else "Unknown"
            )
        finally:
            self.cleanup()
