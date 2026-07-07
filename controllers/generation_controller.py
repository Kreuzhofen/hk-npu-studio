from __future__ import annotations

from typing import Any
from controllers.generation_session import GenerationSessionModel
from controllers.generation_job import GenerationJob
from controllers.generation_queue import GenerationQueue
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

    def queue_generation(self) -> str:
        """
        Queue the generation based on the active session parameters.
        Validates parameters first, creates a GenerationJob and adds it to the queue.
        Routes execution through BackendManager to the active BackendAdapter.
        """
        is_valid, msg = self.validate_session()
        if not is_valid:
            print(f"Validation failed: {msg}")
            return f"Fehler: {msg}"

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

        # Route job to the active backend adapter
        active_backend = self.backend_manager.get_active_backend()
        if active_backend is not None:
            backend_msg = active_backend.generate(job)
            print(f"[GenerationController] Active Backend ({active_backend.get_backend_name()}) returned: {backend_msg}")

        queued_count = self.queue.get_queued_count()
        if queued_count == 1:
            return "1 Job in Warteschlange"
        else:
            return f"{queued_count} Jobs in Warteschlange"

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
