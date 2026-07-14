from __future__ import annotations

from uuid import UUID
from controllers.generation_job import GenerationJob


class GenerationQueue:
    """
    Manages a queue of GenerationJobs in FIFO order.
    Tracks both pending and executing jobs.
    """

    def __init__(self) -> None:
        self._jobs: list[GenerationJob] = []

    def enqueue(self, job: GenerationJob) -> None:
        """Add a job to the queue."""
        self._jobs.append(job)

    def dequeue(self) -> GenerationJob | None:
        """Retrieve and return the next queued job, setting status to RUNNING."""
        for job in self._jobs:
            if job.status == "QUEUED":
                job.status = "RUNNING"
                return job
        return None

    def current_job(self) -> GenerationJob | None:
        """Get the currently executing job if any."""
        for job in self._jobs:
            if job.status == "RUNNING":
                return job
        return None

    def cancel(self, job_id: UUID) -> bool:
        """Cancel a job in the queue by its ID."""
        for job in self._jobs:
            if job.job_id == job_id:
                job.cancel_requested.set()
                job.status = "CANCELLED"
                return True
        return False

    def clear_finished(self) -> None:
        """Remove jobs that are FINISHED, FAILED, or CANCELLED from the queue."""
        self._jobs = [job for job in self._jobs if job.status in ("QUEUED", "RUNNING")]

    def get_all_jobs(self) -> list[GenerationJob]:
        """Return all jobs in the queue."""
        return self._jobs

    def get_queued_count(self) -> int:
        """Count jobs that are currently QUEUED."""
        return sum(1 for job in self._jobs if job.status == "QUEUED")

    def get_total_count(self) -> int:
        """Count all active/history jobs currently in the queue."""
        return len(self._jobs)
