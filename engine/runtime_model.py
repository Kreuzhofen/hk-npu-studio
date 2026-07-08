from __future__ import annotations

from typing import Any


class RuntimeModel:
    """
    Represents the loaded model metadata and plan at runtime.
    Decoupled from physical weight tensors in memory.
    """

    def __init__(
        self,
        model_id: str,
        model_path: str,
        files: list[str],
        backend: str,
        load_plan: dict[str, Any] | None = None
    ) -> None:
        self.model_id = model_id
        self.model_path = model_path
        self.files = files
        self.backend = backend
        self.load_plan = load_plan or {}
