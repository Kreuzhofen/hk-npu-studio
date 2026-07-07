from __future__ import annotations

from engine.backends.backend_adapter import BackendAdapter
from engine.backends.cpu_backend_adapter import CPUBackendAdapter
from engine.backends.qnn_backend_adapter import QNNBackendAdapter
from engine.backends.onnx_backend_adapter import ONNXBackendAdapter
from engine.backends.remote_backend_adapter import RemoteBackendAdapter


class BackendManager:
    """
    Central registry and manager for AI inference backend adapters.
    Handles selection and life-cycle events of active backends.
    """

    def __init__(self) -> None:
        self._backends: dict[str, BackendAdapter] = {}
        self._active_backend_name: str | None = None

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
