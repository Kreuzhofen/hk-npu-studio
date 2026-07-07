from __future__ import annotations

from typing import Any
from controllers.model_manager_model import ModelManagerModel
from engine.backends.backend_manager import BackendManager
from engine.backends.discovery_result import DiscoveryResult


class ModelManagerController:
    """
    Controller coordinating interactions between the Model Manager View,
    the ModelManagerModel, and the BackendManager.
    """

    def __init__(
        self,
        model: ModelManagerModel | None = None,
        backend_manager: BackendManager | None = None
    ) -> None:
        self.model = model or ModelManagerModel()
        self.backend_manager = backend_manager or BackendManager()

    def get_all_models(self) -> list[dict[str, Any]]:
        """Get all model definitions from the repository."""
        return self.model.get_models()

    def get_model_details(self, model_id: str) -> dict[str, Any] | None:
        """Get details of a specific model by ID."""
        return self.model.get_model(model_id)

    def get_available_backends(self) -> list[str]:
        """Query available backends from the BackendManager."""
        return self.backend_manager.get_available_backends()

    def get_active_backend_name(self) -> str:
        """Query active backend name from BackendManager."""
        active = self.backend_manager.get_active_backend()
        if active:
            return active.get_backend_name()
        return "None"

    def refresh_repository(self) -> None:
        """Triggers scanning/re-loading model files from disk."""
        self.model.repository.load_repository()

    def get_active_model_id(self) -> str | None:
        """Get the active model ID from single source of truth."""
        return self.model.repository.get_active_model_id()

    def set_active_model_id(self, model_id: str | None) -> None:
        """Set the active model ID in the single source of truth."""
        self.model.repository.set_active_model_id(model_id)

    def get_discovery_result(self) -> DiscoveryResult:
        """Run or query system environment discovery diagnostics."""
        return self.backend_manager.get_discovery_result()

Class = ModelManagerController
