from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import config
from controllers.model_manager_model import ModelManagerModel
from engine.backends.backend_manager import BackendManager
from engine.backends.discovery_result import DiscoveryResult
from engine.model_install_service import ModelInstallService
from engine.qnn_dlc_diagnostic_runner import QnnDlcDiagnosticRunner


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
        if model_id is not None and not self.model.repository.is_selectable_model(model_id):
            return
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

    def download_and_install_package(
        self,
        model_id: str,
        source_url: str,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> bool:
        """Download, validate, install, and activate one DIRECT package."""
        def emit(phase: str, percent: float) -> None:
            if progress_callback:
                progress_callback({"phase": phase, "percent": percent})

        model = self.model.repository.get_model(model_id)
        if not model or model.get("installed") is True:
            return False
        if model.get("source_type") != "direct" or source_url != model.get("source_url"):
            return False
        if (Path(config.MODELS_DIR) / model_id).exists():
            emit("install_failed", 0.0)
            return False

        original_state = {
            key: model.get(key) for key in ("installed", "downloaded", "path", "status")
        }
        previous_active = self.get_active_model_id()
        staged_path = ""
        installed = False
        try:
            if not self.install_service.start_download(
                model_id,
                source_url,
                lambda percent: emit("downloading", min(70.0, float(percent) * 0.7)),
            ):
                emit("download_failed", 0.0)
                self.model.repository.update_model(model_id, **original_state)
                return False

            staged = self.model.repository.get_model(model_id)
            staged_path = str((staged or {}).get("path") or "")
            emit("download_complete", 70.0)
            emit("checking", 75.0)
            validation = self.install_service.validate_package_source(model_id, staged_path)
            if not validation.get("success"):
                emit("validation_failed", 75.0)
                self.model.repository.update_model(model_id, **original_state)
                return False

            emit("installing", 82.0)
            if not self.install_service.install_package(
                model_id, staged_path, replace_existing=False
            ):
                emit("install_failed", 82.0)
                self.model.repository.update_model(model_id, **original_state)
                return False
            installed = True

            emit("activating", 95.0)
            self.set_active_model_id(model_id)
            if self.get_active_model_id() != model_id:
                if self.get_active_model_id() != previous_active:
                    self.set_active_model_id(previous_active)
                emit("activation_failed", 95.0)
                return False
            emit("ready", 100.0)
            return True
        except Exception:
            emit("activation_failed" if installed else "install_failed", 95.0 if installed else 82.0)
            if not installed:
                self.model.repository.update_model(model_id, **original_state)
            elif self.get_active_model_id() != previous_active:
                self.set_active_model_id(previous_active)
            return False
        finally:
            if staged_path:
                self.install_service.cleanup_staged_download(staged_path)

    def list_available_packages(self) -> list[dict[str, Any]]:
        """List package catalog entries with locally derived PackageStatus."""
        return self.install_service.list_available_packages()

    def reconcile_installed_packages(self) -> list[dict[str, Any]]:
        """Compare installed packages with the local package catalog."""
        return self.install_service.reconcile_installed_packages()

    def get_package_status(self, model_id: str) -> str:
        """Retrieve the detailed PackageStatus string for a model."""
        return str(self.model.repository.get_package_status(model_id))

    def run_npu_diagnostic(self) -> dict[str, Any]:
        """Run the local QNN DLC smoke test and return the diagnostic report."""
        return QnnDlcDiagnosticRunner().run()

    def scan_npu_models(self) -> list[dict[str, Any]]:
        """Scan local directories for preinstalled NPU models."""
        from app.model_scanner import ModelScanner
        import config
        scanner = ModelScanner(temp_dir=config.TEMP_DIR, models_dir=config.MODELS_DIR)
        return scanner.scan_models()

Class = ModelManagerController

