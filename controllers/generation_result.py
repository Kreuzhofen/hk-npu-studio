from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GenerationResult:
    """
    Data class representing the result of an AI model image generation job.
    Encapsulates state, output paths, performance metrics, and metadata without UI dependencies.
    """
    success: bool
    status: str
    message: str
    image_path: str | None = None
    thumbnail_path: str | None = None
    generation_time: float = 0.0
    backend_name: str = "Unknown"
    model_name: str = "Unknown"
    metadata: dict[str, Any] = field(default_factory=dict)
