from __future__ import annotations

from typing import Any
from controllers.generation_session import GenerationSessionModel
from controllers.generation_job import GenerationJob
from controllers.generation_queue import GenerationQueue
from controllers.generation_result import GenerationResult
from engine.backends.backend_manager import BackendManager


class GenerationController:
    """
    Central controller responsible for validating, scheduling and orchestrating AI generations.
    Decoupled from GUI views and direct backend implementations.
    Now leverages a FIFO GenerationQueue for pipeline scheduling and BackendManager for adapter routing.
    """

    def __init__(self, session: GenerationSessionModel | None = None) -> None:
        self.session = session or GenerationSessionModel()
        self.queue = GenerationQueue()
        self.backend_manager = BackendManager()
        self.is_generating = False

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
        
        if self.session.steps < 1 or self.session.steps > 150:
            return False, "Steps müssen zwischen 1 und 150 liegen."
            
        if self.session.cfg_scale < 1.0 or self.session.cfg_scale > 30.0:
            return False, "CFG Scale muss zwischen 1.0 und 30.0 liegen."

        if self.session.width <= 0 or self.session.height <= 0:
            return False, "Breite und Höhe müssen positive Werte sein."

        return True, "Validierung erfolgreich."

    def queue_generation(self) -> GenerationResult:
        """
        Queue the generation based on the active session parameters.
        Validates parameters first, creates a GenerationJob and adds it to the queue.
        Executes the job using the ImageGenerationPipeline and returns a GenerationResult.
        """
        is_valid, msg = self.validate_session()
        if not is_valid:
            print(f"Validation failed: {msg}")
            return GenerationResult(
                success=False,
                status="ValidationError",
                message=msg,
                model_name=self.session.model_name
            )

        # Create a parameter snapshot for this job
        job_session = GenerationSessionModel(**self.session.to_dict())
        job = GenerationJob(session=job_session)
        self.queue.enqueue(job)

        self.is_generating = True
        
        # Log active session setup to stdout
        print("--- [GenerationController: Job Enqueued] ---")
        print(f"Job ID: {job.job_id}")
        for key, val in job_session.to_dict().items():
            print(f"  {key}: {val}")
        print("--------------------------------------------")

        # Route job through the pipeline to the active backend adapter
        active_backend = self.backend_manager.get_active_backend()
        
        from controllers.generation_pipeline import ImageGenerationPipeline
        pipeline = ImageGenerationPipeline(job=job, backend_adapter=active_backend)
        result = pipeline.run()

        # Dequeue since execution finished
        self.queue.dequeue()
        self.is_generating = False

        # Notify the WorkflowController that the generation finished
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
            if job.status == "QUEUED":
                self.queue.cancel(job.job_id)

        # Notify active backend of cancel
        active_backend = self.backend_manager.get_active_backend()
        if active_backend is not None and current is not None:
            active_backend.cancel(current)

        self.is_generating = False
        print("--- [GenerationController: Cancel Generation] ---")
        print("All jobs in queue cancelled.")
        print("--------------------------------------------------")
        
        return "Generation cancelled (stub)"
