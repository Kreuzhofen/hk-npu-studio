from __future__ import annotations

from datetime import datetime
from uuid import uuid4, UUID
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Any

from controllers.generation_session import GenerationSessionModel
from engine.job_lifecycle import (
    JobStatus,
    cancel_job,
    fail_job,
    set_job_progress,
    set_job_status,
)


@dataclass
class GenerationJob:
    """
    Represents a single generative pipeline execution task.
    Tracks execution status, progress, target parameters and output paths.
    """
    session: GenerationSessionModel
    job_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = JobStatus.QUEUED.value
    progress: float = 0.0
    progress_message: str = ""
    result_path: Path | None = None
    error_message: str | None = None
    cancel_requested: Event = field(default_factory=Event, repr=False, compare=False)
    progress_callback: Any = None

    def transition_to(self, status: JobStatus | str) -> JobStatus:
        return set_job_status(self, status)

    def report_progress(self, progress: float | int, message: str = "") -> float:
        return set_job_progress(self, progress, message)

    def cancel(self) -> None:
        cancel_job(self)

    def fail(self, error: BaseException | str) -> None:
        fail_job(self, error)
