from __future__ import annotations

from app.i18n import tr
from pathlib import Path
from typing import Any
from controllers.generation_session import GenerationSessionModel
from controllers.generation_job import GenerationJob
from controllers.generation_queue import GenerationQueue
from controllers.generation_result import GenerationResult
from controllers.model_repository import ModelRepository
from engine.backends.backend_manager import BackendManager
from engine.job_lifecycle import JobStatus, get_job_status, set_job_status
from engine.logging_config import get_logger
from engine.model_loader_service import ModelLoaderService


logger = get_logger("GenerationController")

def log_abort(event_name, error=None, model_id=None, model_path=None):
    import os
    import sys
    import traceback
    from pathlib import Path
    import datetime

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        local_app_data = str(Path.home() / "AppData" / "Local")
    log_file = Path(local_app_data) / "Snapdragon AI Studio" / "logs" / "early_generation_abort.log"
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().isoformat()
        if error is not None:
            tb = traceback.extract_tb(sys.exc_info()[2])
            if tb:
                filename, line_no, func_name, text = tb[-1]
            else:
                filename, line_no = "unknown", 0
            
            stacktrace = "".join(traceback.format_exception(type(error), error, sys.exc_info()[2]))
            
            log_line = (
                f"[{timestamp}] ERROR: {event_name}\n"
                f"Exception-Type: {type(error).__name__}\n"
                f"Message: {str(error)}\n"
                f"File: {filename}\n"
                f"Line: {line_no}\n"
                f"Model-ID: {model_id or 'Unknown'}\n"
                f"Modelpath: {model_path or 'Unknown'}\n"
                f"Stacktrace:\n{stacktrace}"
                f"{'='*80}\n"
            )
        else:
            log_line = f"[{timestamp}] EVENT: {event_name}\n"
            if model_id:
                log_line += f"Model-ID: {model_id}\n"
            if model_path:
                log_line += f"Modelpath: {model_path}\n"
            log_line += f"{'='*80}\n"
            
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print(f"Failed to write to early abort log: {e}", file=sys.stderr)



class GenerationController:
    """
    Central controller responsible for validating, scheduling and orchestrating AI generations.
    Decoupled from GUI views and direct backend implementations.
    Now leverages a FIFO GenerationQueue for pipeline scheduling and BackendManager for adapter routing.
    """

    def __init__(
        self,
        session: GenerationSessionModel | None = None,
        repository: ModelRepository | None = None,
    ) -> None:
        self.session = session or GenerationSessionModel()
        self.queue = GenerationQueue()
        self.backend_manager = BackendManager()
        self.repository = repository or ModelRepository()
        self.model_loader = ModelLoaderService(self.repository)
        self.is_generating = False

    @staticmethod
    def discard_cancelled_output(result: GenerationResult, job: GenerationJob) -> GenerationResult:
        """Remove any output that raced with cancellation and return the canonical result."""
        output_paths = {result.image_path, result.thumbnail_path}
        output_dir = Path(job.session.output_directory or "output")
        if output_dir.is_dir():
            job_token = str(job.job_id)[:8]
            output_paths.update(str(path) for path in output_dir.glob(f"*{job_token}*.png"))
        for output_path in output_paths:
            if not output_path:
                continue
            path = Path(output_path)
            path.unlink(missing_ok=True)
            path.with_suffix(".json").unlink(missing_ok=True)
        return GenerationResult(
            success=False,
            status="CANCELLED",
            message=tr("generation_cancelled", "Generierung abgebrochen."),
            model_name=job.session.model_name,
        )

    def update_session(self, **kwargs: Any) -> None:
        """Update active generation session settings."""
        self.session.update(**kwargs)

    def validate_session(self) -> tuple[bool, str]:
        """
        Validate that the session contains sufficient and correct parameters.
        Returns a tuple of (is_valid, error_message).
        """
        if not self.session.prompt.strip():
            return False, "Prompt darf nicht leer sein."

        model_meta = self.repository.get_model(self.session.model_name)
        if model_meta and self.session.controlnet_enabled:
            capabilities = model_meta.get("capabilities", {})
            if not capabilities.get("controlnet", False):
                return False, "Das ausgewählte Modell unterstützt ControlNet nicht."
            else:
                img_path = self.session.input_image_path
                if not img_path:
                    return False, "Eingabebild für ControlNet Canny fehlt oder ist ungültig."
                path = Path(img_path)
                if not path.exists() or not path.is_file():
                    return False, "Eingabebild für ControlNet Canny fehlt oder ist ungültig."

                # Check extension/format
                ext = path.suffix.lower()
                if ext not in (".png", ".jpg", ".jpeg", ".webp"):
                    return False, "Es werden nur Bilddateien in den Formaten PNG, JPG, JPEG und WebP unterstützt."

                # Check file size (no empty files allowed)
                if path.stat().st_size == 0:
                    return False, "Das ausgewählte Referenzbild ist leer (0 Byte)."

                # Check readability and loading in the preprocessing path
                try:
                    from PIL import Image
                    with Image.open(path) as img:
                        img.verify()
                    with Image.open(path) as img:
                        img.convert('L')
                except Exception as e:
                    return False, f"Das Referenzbild ist beschädigt oder ungültig: {e}"

                # Check Canny thresholds and conditioning scale (Sprint CN-004)
                low = getattr(self.session, "canny_low_threshold", 50)
                high = getattr(self.session, "canny_high_threshold", 150)
                cond_scale = getattr(self.session, "controlnet_conditioning_scale", 1.0)

                if not (0 <= low <= 255) or not (0 <= high <= 255):
                    return False, "Canny-Schwellenwerte müssen zwischen 0 und 255 liegen."
                if low >= high:
                    return False, "Der untere Schwellenwert (Low Threshold) muss kleiner als der obere Schwellenwert (High Threshold) sein."
                if not (0.0 <= cond_scale <= 2.0):
                    return False, "Die ControlNet-Stärke (Conditioning Strength) muss zwischen 0.0 und 2.0 liegen."

        
        return self.repository.validate_generation_parameters(
            self.session.model_name,
            {
                "width": self.session.width,
                "height": self.session.height,
                "steps": self.session.steps,
                "cfg": self.session.cfg_scale,
                "seed": self.session.seed,
                "sampler": self.session.sampler,
                "scheduler": self.session.scheduler,
            },
        )



    def queue_generation(self, notify_workflow: bool = True, progress_callback: Any = None) -> GenerationResult:
        """
        Queue the generation based on the active session parameters.
        Validates parameters first, creates a GenerationJob and adds it to the queue.
        Executes the job using the ImageGenerationPipeline and returns a GenerationResult.
        """
        is_valid, msg = self.validate_session()
        if not is_valid:
            logger.warning("Validierung fehlgeschlagen: %s", msg)
            print(f"Validation failed: {msg}")
            return GenerationResult(
                success=False,
                status="ValidationError",
                message=msg,
                model_name=self.session.model_name
            )

        # Create a parameter snapshot for this job
        job_session = GenerationSessionModel(**self.session.to_dict())
        job = GenerationJob(session=job_session, progress_callback=progress_callback)
        self.queue.enqueue(job)
        self.queue.dequeue()
        logger.info("Job eingereiht | job_id=%s | model=%s", job.job_id, job_session.model_name)
        
        # LOG EVENT: job_created
        model_path = None
        try:
            model_path = self.model_loader.get_model_path(job_session.model_name)
        except Exception:
            pass
        log_abort("job_created", model_id=job_session.model_name, model_path=model_path)

        self.is_generating = True
        print("--- [GenerationController: Job Enqueued] ---")
        print(f"Job ID: {job.job_id}")
        for key, val in job_session.to_dict().items():
            print(f"  {key}: {val}")
        print("--------------------------------------------")

        # Resolve model metadata
        repo = self.repository
        # Verify model installation prior to execution
        try:
            load_result = self.model_loader.load_model(
                job_session.model_name, self.backend_manager
            )
            if not load_result.success or load_result.loaded_model is None:
                raise RuntimeError(load_result.message)
            
            # LOG EVENT: model_resolved
            log_abort("model_resolved", model_id=job_session.model_name, model_path=load_result.loaded_model.runtime_model.model_path)
        except Exception as error:
            log_abort("model_resolved", error=error, model_id=job_session.model_name, model_path=model_path)
            job.fail(str(error))
            logger.error(
                "Modellauflösung fehlgeschlagen | job_id=%s | model=%s | message=%s",
                job.job_id,
                job_session.model_name,
                str(error),
            )
            self.queue.clear_finished()
            self.is_generating = False
            return GenerationResult(
                success=False,
                status="LoadError",
                message=str(error),
                model_name=job_session.model_name
            )

        selected_backend = None
        try:
            # Route through the backend atomically bound by the shared loader.
            selected_backend = load_result.loaded_model.backend_adapter
            self.backend_manager.set_active_backend(
                selected_backend.get_backend_name()
            )
            logger.info(
                "Backend ausgewählt | job_id=%s | backend=%s",
                job.job_id,
                selected_backend.get_backend_name(),
            )
            from controllers.generation_pipeline import ImageGenerationPipeline
            pipeline = ImageGenerationPipeline(
                job=job,
                backend_adapter=selected_backend,
                runtime_model=load_result.loaded_model.runtime_model,
            )
            
            # LOG EVENT: backend_called
            log_abort("backend_called", model_id=job_session.model_name, model_path=load_result.loaded_model.runtime_model.model_path)
            
            result = pipeline.run()
        except Exception as error:
            log_abort("backend_called", error=error, model_id=job_session.model_name, model_path=load_result.loaded_model.runtime_model.model_path)
            raise error
        finally:
            self.model_loader.unload_model(job_session.model_name)

        if job.cancel_requested.is_set():
            result = self.discard_cancelled_output(result, job)

        # Update result metadata so AI Generate can show the routed backend
        if selected_backend:
            result.backend_name = selected_backend.get_backend_name()
            result.metadata["routed_backend"] = selected_backend.get_backend_name()

        # Finalize and remove the active queue item.
        if get_job_status(job) != JobStatus.CANCELLED:
            set_job_status(
                job,
                JobStatus.FINISHED if result.success else JobStatus.FAILED,
            )
        self.queue.clear_finished()
        self.is_generating = False

        # Notify the WorkflowController that the generation finished.
        # Worker-thread callers can defer this to the Tk main thread.
        if notify_workflow:
            from controllers.workflow_controller import WorkflowController
            WorkflowController.get_instance().on_generation_finished(result)

        return result

    def cancel_generation(self) -> str:
        """
        Cancel any running or queued generation.
        """
        current = self.queue.current_job()
        if current is not None:
            self.queue.cancel(current.job_id)
            
        # Cancel all queued jobs as well
        for job in self.queue.get_all_jobs():
            if get_job_status(job) == JobStatus.QUEUED:
                self.queue.cancel(job.job_id)

        # Notify active backend of cancel
        active_backend = self.backend_manager.get_active_backend()
        if active_backend is not None and current is not None:
            active_backend.cancel(current)

        print("--- [GenerationController: Cancel Generation] ---")
        logger.info(
            "Generierungsabbruch angefordert | active_job=%s",
            getattr(current, "job_id", None),
        )
        print("All jobs in queue cancelled.")
        print("--------------------------------------------------")
        
        return "CANCELLED"
