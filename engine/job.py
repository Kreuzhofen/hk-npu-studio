"""
SnapdragonAI Studio

Job

Created by Holger Kreuzhofen
Phoenix Engine
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Job:
    """
    Repräsentiert einen einzelnen KI-Auftrag der Phoenix Engine.
    """

    skill: str
    kwargs: dict[str, Any]

    status: str = "queued"
    progress: float = 0.0

    result: Any = None
    error: str | None = None

    created: datetime = field(default_factory=datetime.now)
    started: datetime | None = None
    finished: datetime | None = None

    def start(self):
        """Markiert den Job als gestartet."""
        self.status = "running"
        self.started = datetime.now()

    def finish(self, result: Any):
        """Markiert den Job als erfolgreich beendet."""
        self.status = "finished"
        self.progress = 100.0
        self.result = result
        self.finished = datetime.now()

    def fail(self, error: str):
        """Markiert den Job als fehlgeschlagen."""
        self.status = "failed"
        self.error = error
        self.finished = datetime.now()