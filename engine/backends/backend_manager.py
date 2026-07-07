from __future__ import annotations

from engine.backends.backend_adapter import BackendAdapter
from engine.backends.cpu_backend_adapter import CPUBackendAdapter
from engine.backends.qnn_backend_adapter import QNNBackendAdapter
from engine.backends.onnx_backend_adapter import ONNXBackendAdapter
from engine.backends.remote_backend_adapter import RemoteBackendAdapter
from engine.backends.discovery_result import DiscoveryResult


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
        self.register_backend(RemoteBackendAdapter())

        # Set default active backend to CPU fallback stub
        self.set_active_backend("CPU (Stub)")

    def register_backend(self, adapter: BackendAdapter) -> None:
        """Register an inference backend adapter."""
        name = adapter.get_backend_name()
        self._backends[name] = adapter

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
                backend.initialize()

    def shutdown_all(self) -> None:
        """Shutdown all registered backends, freeing resources."""
        for backend in self._backends.values():
            backend.shutdown()

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
