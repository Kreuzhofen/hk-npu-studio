from __future__ import annotations

from typing import Any
from controllers.generation_session import GenerationSessionModel
from controllers.generation_job import GenerationJob
from controllers.generation_queue import GenerationQueue


# Geplante Backend Adapter (Zukünftige Integration):
#
# class QNNBackendAdapter:
#     """NPU-beschleunigte Inferenz über das Qualcomm QNN SDK."""
#     pass
#
# class ONNXBackendAdapter:
#     """Lokaler Fallback über ONNX Runtime."""
#     pass
#
# class CPUBackendAdapter:
#     """Reine CPU-Referenzimplementierung über NumPy / PyTorch CPU."""
#     pass
#
# class RemoteBackendAdapter:
#     """Cloud-Generierung über REST-API-Schnittstellen."""
#     pass


class GenerationController:
    """
    Central controller responsible for validating, scheduling and orchestrating AI generations.
    Decoupled from GUI views and direct backend implementations.
    Now leverages a FIFO GenerationQueue for pipeline scheduling.
    """

    def __init__(self, session: GenerationSessionModel | None = None) -> None:
        self.session = session or GenerationSessionModel()
        self.queue = GenerationQueue()
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

        self.is_generating = False
        print("--- [GenerationController: Cancel Generation] ---")
        print("All jobs in queue cancelled.")
        print("--------------------------------------------------")
        
        return "Generation cancelled (stub)"
