from __future__ import annotations

import logging
from typing import Any
from engine.inference_backend import InferenceBackend
from engine.runtime_model import RuntimeModel

logger = logging.getLogger("InferenceBackendFactory")


class InferenceBackendFactory:
    """
    Factory for retrieving and registering InferenceBackend implementations.
    Allows dynamic plugin registration for CPU, QNN, ONNX, and remote backends.
    """

    _registry: dict[str, type[InferenceBackend]] = {}

    @classmethod
    def register_backend(cls, name: str, backend_cls: type[InferenceBackend]) -> None:
        cls._registry[name] = backend_cls
        logger.info(f"[Factory] Registered backend class '{backend_cls.__name__}' under name '{name}'")
        print(f"[Factory] Registered backend class '{backend_cls.__name__}' under name '{name}'")

    @classmethod
    def get_backend(cls, name: str, runtime_model: RuntimeModel | None = None) -> InferenceBackend:
        # Resolve backend class by matching name
        backend_cls = cls._registry.get(name)
        if not backend_cls:
            # Fallback mapping
            if "ONNX" in name:
                backend_cls = cls._registry.get("ONNX Runtime CPU")
            else:
                backend_cls = cls._registry.get("Stub")
                
        if not backend_cls:
            raise ValueError(f"No inference backend registered for name '{name}'")
            
        # Instantiate with runtime_model passed to constructor
        from engine.stub_image_backend import StubImageBackend
        from engine.onnx_image_backend import OnnxImageBackend
        from engine.sd15_qnn_backend import StableDiffusion15QnnBackend
        
        if issubclass(backend_cls, StubImageBackend):
            return backend_cls(backend_name=name, runtime_model=runtime_model)
        elif issubclass(backend_cls, OnnxImageBackend):
            return backend_cls(runtime_model=runtime_model)
        elif issubclass(backend_cls, StableDiffusion15QnnBackend):
            return backend_cls()
            
        return backend_cls()


# Dynamic registration of the backends
from engine.stub_image_backend import StubImageBackend
from engine.onnx_image_backend import OnnxImageBackend
from engine.sd15_qnn_backend import StableDiffusion15QnnBackend

InferenceBackendFactory.register_backend("Stub", StubImageBackend)
InferenceBackendFactory.register_backend("Local CPU (Stub)", StubImageBackend)
InferenceBackendFactory.register_backend("Qualcomm QNN NPU (Stub)", StubImageBackend)
InferenceBackendFactory.register_backend("ONNX Runtime CPU", OnnxImageBackend)
InferenceBackendFactory.register_backend("ONNX Runtime (Stub)", OnnxImageBackend)
InferenceBackendFactory.register_backend("Qualcomm Stable Diffusion 1.5 (HTP V73)", StableDiffusion15QnnBackend)
