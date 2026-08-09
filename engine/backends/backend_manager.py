from __future__ import annotations

from typing import Any
from engine.backends.backend_adapter import BackendAdapter
from engine.backends.cpu_backend_adapter import CPUBackendAdapter
from engine.backends.qnn_backend_adapter import QNNBackendAdapter
from engine.backends.onnx_backend_adapter import ONNXBackendAdapter
from engine.backends.sd15_qnn_backend_adapter import StableDiffusion15QnnBackendAdapter
from engine.backends.sd21_qnn_backend_adapter import StableDiffusion21QnnBackendAdapter
from engine.backends.controlnet_canny_backend_adapter import ControlNetCannyQnnBackendAdapter
from engine.backends.sd15_qai_appbuilder_backend_adapter import StableDiffusion15QaiAppBuilderBackendAdapter
from engine.backends.discovery_result import DiscoveryResult
from engine.error_diagnostics import diagnose_exception
from engine.logging_config import get_logger


logger = get_logger("BackendManager")


class BackendManager:
    """
    Central registry and manager for AI inference backend adapters.
    Handles selection and life-cycle events of active backends.
    """

    def __init__(self) -> None:
        self._backends: dict[str, BackendAdapter] = {}
        self._active_backend_name: str | None = None
        self._discovery_result: DiscoveryResult | None = None

        # Auto-register default pipeline adapters
        self.register_backend(CPUBackendAdapter())
        self.register_backend(QNNBackendAdapter())
        self.register_backend(ONNXBackendAdapter())
        self.register_backend(StableDiffusion15QnnBackendAdapter())
        self.register_backend(StableDiffusion21QnnBackendAdapter())
        self.register_backend(ControlNetCannyQnnBackendAdapter())
        self.register_backend(StableDiffusion15QaiAppBuilderBackendAdapter())

        # Initialize status from the persisted provider. Actual model routing still
        # happens in get_best_backend() and is intentionally unchanged.
        from app.settings_manager import SettingsManager

        if SettingsManager.get_execution_provider() == SettingsManager.CPU_EXECUTION_PROVIDER:
            self.set_active_backend(ONNXBackendAdapter.BACKEND_NAME)
        else:
            self.set_active_backend(QNNBackendAdapter.BACKEND_NAME)

    def register_backend(self, adapter: BackendAdapter) -> None:
        """Register an inference backend adapter."""
        name = adapter.get_backend_name()
        self._backends[name] = adapter
        logger.debug("Backend registriert | backend=%s", name)

    def get_backend(self, name: str) -> BackendAdapter | None:
        """Get registered backend adapter by name."""
        return self._backends.get(name)

    def get_active_backend(self) -> BackendAdapter | None:
        """Get the currently active backend adapter."""
        if self._active_backend_name is None:
            return None
        return self.get_backend(self._active_backend_name)

    def set_active_backend(self, name: str) -> bool:
        """Set the active backend adapter by name."""
        if name in self._backends:
            self._active_backend_name = name
            return True
        return False

    def initialize_all(self) -> None:
        """Initialize all registered backends that are supported on local hardware."""
        for backend in self._backends.values():
            if backend.is_available():
                try:
                    backend.initialize()
                except Exception as error:
                    diagnose_exception(
                        logger,
                        error,
                        category="backend",
                        context="initialize_all",
                        backend_name=backend.get_backend_name(),
                    )
                    raise

    def shutdown_all(self) -> None:
        """Shutdown all registered backends, freeing resources."""
        for backend in self._backends.values():
            try:
                backend.shutdown()
            except Exception as error:
                diagnose_exception(
                    logger,
                    error,
                    category="backend",
                    context="shutdown_all",
                    backend_name=backend.get_backend_name(),
                )
                raise

    def get_available_backends(self) -> list[str]:
        """List names of registered backends that are available on this hardware."""
        return [name for name, b in self._backends.items() if b.is_available()]

    def get_all_backend_names(self) -> list[str]:
        """List names of all registered backends regardless of availability."""
        return list(self._backends.keys())

    def run_discovery(self) -> DiscoveryResult:
        """Run system diagnostics to scan system hardware, OS, Python runtime and QNN paths."""
        from engine.backends.backend_discovery_service import BackendDiscoveryService
        self._discovery_result = BackendDiscoveryService.discover()
        return self._discovery_result

    def get_discovery_result(self) -> DiscoveryResult:
        """Retrieve the last cached discovery run result, or run discovery dynamically if empty."""
        if self._discovery_result is None:
            self.run_discovery()
        assert self._discovery_result is not None
        return self._discovery_result

    def get_backend_status_summary(self) -> str:
        """Returns a high-level summary string detailing QNN and ONNX availability status."""
        res = self.get_discovery_result()
        qnn_status = "Gefunden" if res.qnn_sdk_found else "Nicht gefunden"
        onnx_status = f"Installiert ({res.onnx_version})" if res.onnx_available else "Nicht installiert"
        return f"QNN NPU: {qnn_status} | ONNX: {onnx_status}"

    def get_active_execution_provider_label(self) -> str:
        """Return the EP represented by the active routed adapter."""
        from app.settings_manager import SettingsManager

        active = self.get_active_backend()
        if isinstance(active, (ONNXBackendAdapter, CPUBackendAdapter)):
            return "CPU EP"
        if isinstance(
            active,
            (
                QNNBackendAdapter,
                StableDiffusion15QnnBackendAdapter,
                StableDiffusion21QnnBackendAdapter,
                ControlNetCannyQnnBackendAdapter,
                StableDiffusion15QaiAppBuilderBackendAdapter,
            ),
        ):
            return "QNN EP"
        return SettingsManager.get_execution_provider_label()

    def get_best_backend(self, model: dict[str, Any] | str | None = None) -> BackendAdapter | None:
        """
        Selects the best available backend based on model preferences and system capability.
        Priority:
        1. Model's preferred backend if available.
        2. Qualcomm QNN NPU if available.
        3. ONNX Runtime if available.
        4. CPU (Stub) as fallback.
        """
        from app.settings_manager import SettingsManager

        configured_provider = SettingsManager.get_execution_provider()
        if configured_provider == SettingsManager.CPU_EXECUTION_PROVIDER:
            for adapter in self._backends.values():
                if isinstance(adapter, ONNXBackendAdapter) and adapter.is_available():
                    self._active_backend_name = adapter.get_backend_name()
                    logger.info(
                        "Gespeicherte Provider-Auswahl angewendet | provider=%s backend=%s",
                        configured_provider,
                        adapter.get_backend_name(),
                    )
                    return adapter

        target_backend_name = None
        preferred = None

        active = self.get_active_backend()
        if isinstance(active, StableDiffusion15QaiAppBuilderBackendAdapter):
            model_id = model.get("id") if isinstance(model, dict) else model
            if model_id in active.get_supported_models() and active.is_available():
                return active

        if model is not None:
            import os

            model_id = model.get("id") if isinstance(model, dict) else model
            qai_requested = os.environ.get("SNAPDRAGON_SD15_QAI_APPBUILDER", "").strip() == "1"
            if model_id == "stable_diffusion_v1_5_qnn" and qai_requested:
                qai_adapter = next(
                    (
                        adapter
                        for adapter in self._backends.values()
                        if isinstance(adapter, StableDiffusion15QaiAppBuilderBackendAdapter)
                    ),
                    None,
                )
                if qai_adapter is not None and qai_adapter.is_available():
                    self._active_backend_name = qai_adapter.get_backend_name()
                    return qai_adapter
        
        if model is not None:
            if isinstance(model, dict):
                preferred = model.get("recommended_backend") or model.get("backend")
            elif isinstance(model, str):
                try:
                    from controllers.model_repository import ModelRepository
                    repo = ModelRepository()
                    model_dict = repo.get_model(model)
                    if model_dict:
                        preferred = model_dict.get("recommended_backend") or model_dict.get("backend")
                except Exception as error:
                    diagnose_exception(
                        logger,
                        error,
                        category="backend",
                        context="resolve_model_preference",
                    )
            
            if preferred and preferred in self._backends:
                target_backend_name = preferred

        # Generic fallback priority by adapter capability/type.  Keep CPU last;
        # registry insertion order must not affect execution priority.
        def fallback_priority(adapter: BackendAdapter) -> int:
            from engine.backends.controlnet_canny_backend_adapter import ControlNetCannyQnnBackendAdapter
            if isinstance(adapter, (StableDiffusion15QnnBackendAdapter, StableDiffusion21QnnBackendAdapter, ControlNetCannyQnnBackendAdapter)):
                return 0
            if isinstance(adapter, StableDiffusion15QaiAppBuilderBackendAdapter):
                return 6
            if isinstance(adapter, QNNBackendAdapter):
                return 1
            if isinstance(adapter, ONNXBackendAdapter):
                return 2
            if isinstance(adapter, CPUBackendAdapter):
                return 5
            return 3

        general_order = sorted(
            self._backends,
            key=lambda name: fallback_priority(self._backends[name]),
        )

        # Put preferred backend first if it is registered
        order = []
        if target_backend_name and target_backend_name in self._backends:
            order.append(target_backend_name)
        for b in general_order:
            if b not in order:
                order.append(b)

        # Return the first available backend in the order list
        for name in order:
            adapter = self.get_backend(name)
            if adapter and adapter.is_available():
                self._active_backend_name = name
                return adapter

        return None

    @staticmethod
    def get_configured_provider_name() -> str:
        from app.settings_manager import SettingsManager

        return SettingsManager.get_execution_provider()
