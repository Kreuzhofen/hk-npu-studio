from __future__ import annotations
from controllers.generation_result import GenerationResult

class GenerationResponse(GenerationResult):
    """
    Response object returned by generator adapters.
    Subclasses GenerationResult for seamless compatibility with the pipeline.
    """
    pass
