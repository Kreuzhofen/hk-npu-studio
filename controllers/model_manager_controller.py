from __future__ import annotations

from typing import Any
from controllers.model_manager_model import ModelManagerModel
from engine.backends.backend_manager import BackendManager
from engine.backends.discovery_result import DiscoveryResult
from engine.model_install_service import ModelInstallService


class ModelManagerController:
    """
    Controller coordinating interactions between the Model Manager View,
    the ModelManagerModel, the BackendManager, and the ModelInstallService.
    """

    def __init__(
        self,
        model: ModelManagerModel | None = None,
        backend_manager: BackendManager | None = None,
        install_service: ModelInstallService | None = None
    ) -> None:
        self.model = model or ModelManagerModel()
        self.backend_manager = backend_manager or BackendManager()
        self.install_service = install_service or ModelInstallService(self.model.repository)

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

    def install_model(self, model_id: str, source_path: str) -> bool:
        """Install a model locally from source_path."""
        return self.install_service.install_model(model_id, source_path)

    def uninstall_model(self, model_id: str) -> bool:
        """Uninstall a model and delete files."""
        return self.install_service.uninstall_model(model_id)

    def validate_package(self, model_id: str) -> dict[str, Any]:
        """Validate package components and return verification results."""
        return self.install_service.validate_package(model_id)

    def update_package(self, model_id: str, new_source_path: str) -> bool:
        """Update an existing package with new components."""
        return self.install_service.update_package(model_id, new_source_path)

    def remove_package(self, model_id: str) -> bool:
        """Remove model package and delete files."""
        return self.install_service.remove_package(model_id)

    def install_package(self, model_id: str, source_path: str) -> bool:
        """Install a new SMP package from source path."""
        return self.install_service.install_package(model_id, source_path)

    def get_package_status(self, model_id: str) -> str:
        """Retrieve the detailed PackageStatus string for a model."""
        return str(self.model.repository.get_package_status(model_id))

Class = ModelManagerController
