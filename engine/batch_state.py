"""
SnapdragonAI Studio

Batch State

Created by Holger Kreuzhofen
Phoenix Engine Layer
"""

from enum import Enum


class BatchState(str, Enum):
    """Defines the lifecycle states for batch processing."""

    IDLE = "idle"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    FINISHED = "finished"
    ERROR = "error"