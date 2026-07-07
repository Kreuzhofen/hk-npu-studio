from __future__ import annotations

from typing import Any
from controllers.model_repository import ModelRepository


class ModelManagerModel:
    """
    Model representing the state of the Model Manager.
    Delegates all metadata storage and retrieval to ModelRepository.
    """

    def __init__(self, repository: ModelRepository | None = None) -> None:
        self.repository = repository or ModelRepository()

    def get_models(self) -> list[dict[str, Any]]:
        """Retrieve all models from the repository."""
        return self.repository.get_all_models()

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        """Retrieve a single model by ID."""
        return self.repository.get_model(model_id)

    def update_model_status(self, model_id: str, installed: bool, path: str, status: str) -> bool:
        """Update model installation state."""
        return self.repository.update_model(
            model_id,
            installed=installed,
            path=path,
            status=status
        )
