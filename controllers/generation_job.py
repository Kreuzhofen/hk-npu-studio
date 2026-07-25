from __future__ import annotations

from datetime import datetime
from uuid import uuid4, UUID
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event

from controllers.generation_session import GenerationSessionModel


@dataclass
class GenerationJob:
    """
    Represents a single generative pipeline execution task.
    Tracks execution status, progress, target parameters and output paths.
    """
    session: GenerationSessionModel
    job_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "QUEUED"  # QUEUED, RUNNING, FINISHED, FAILED, CANCELLED
    progress: float = 0.0
    result_path: Path | None = None
    error_message: str | None = None
    cancel_requested: Event = field(default_factory=Event, repr=False, compare=False)
    progress_callback: Any = None
