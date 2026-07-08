from __future__ import annotations
from typing import Any
from controllers.generation_result import GenerationResult

class GenerationResponse(GenerationResult):
    """
    Response object returned by generator adapters.
    Subclasses GenerationResult for seamless compatibility with the pipeline.
    Ensures image_path and output_path are consistently exposed.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.output_path: str | None = self.image_path
