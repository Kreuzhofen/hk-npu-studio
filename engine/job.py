"""
Snapdragon AI Studio

Job

Created by Holger Kreuzhofen
Phoenix Engine
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from engine.job_lifecycle import JobStatus, fail_job, set_job_progress, set_job_status


@dataclass
class Job:
    """
    Repräsentiert einen einzelnen KI-Auftrag der Phoenix Engine.
    """

    skill: str
    kwargs: dict[str, Any]

    status: str = JobStatus.QUEUED.value
    progress: float = 0.0

    result: Any = None
    error: str | None = None

    created: datetime = field(default_factory=datetime.now)
    started: datetime | None = None
    finished: datetime | None = None

    def start(self):
        """Markiert den Job als gestartet."""
        set_job_status(self, JobStatus.RUNNING)
        self.started = datetime.now()

    def finish(self, result: Any):
        """Markiert den Job als erfolgreich beendet."""
        set_job_status(self, JobStatus.FINISHED)
        set_job_progress(self, 1.0, notify=False)
        self.result = result
        self.finished = datetime.now()

    def fail(self, error: str):
        """Markiert den Job als fehlgeschlagen."""
        fail_job(self, error)
        self.error = str(error)
        self.finished = datetime.now()
