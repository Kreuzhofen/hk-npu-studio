from __future__ import annotations

import inspect
from typing import Any
from engine.inference_backend import InferenceBackend
from engine.logging_config import get_logger
from engine.runtime_model import RuntimeModel

logger = get_logger("InferenceBackendFactory")


class InferenceBackendFactory:
    """
    Factory for retrieving and registering InferenceBackend implementations.
    Allows dynamic plugin registration for CPU, QNN, ONNX, and remote backends.
    """

    _registry: dict[str, type[InferenceBackend]] = {}
    _constructors: dict[str, Any] = {}

    @classmethod
    def register_backend(cls, name: str, backend_cls: type[InferenceBackend], constructor: Any = None) -> None:
        cls._registry[name] = backend_cls
        cls._constructors[name] = constructor
        logger.info(f"[Factory] Registered backend class '{backend_cls.__name__}' under name '{name}'")
        print(f"[Factory] Registered backend class '{backend_cls.__name__}' under name '{name}'")

    @classmethod
    def get_backend(cls, name: str, runtime_model: RuntimeModel | None = None) -> InferenceBackend:
        # Resolve backend class by matching name
        selected_name = name
        backend_cls = cls._registry.get(selected_name)
        if not backend_cls:
            # Fallback mapping
            if "ONNX" in name:
                selected_name = "ONNX Runtime CPU"
            else:
                selected_name = "Stub"
            backend_cls = cls._registry.get(selected_name)
                
        if not backend_cls:
            raise ValueError(f"No inference backend registered for name '{name}'")
            
        constructor = cls._constructors.get(selected_name)
        if constructor is not None:
            return constructor(runtime_model)

        signature = inspect.signature(backend_cls)
        try:
            signature.bind(runtime_model)
        except TypeError:
            signature.bind()
            return backend_cls()
        return backend_cls(runtime_model)


# Dynamic registration of the backends
from engine.stub_image_backend import StubImageBackend
from engine.onnx_image_backend import OnnxImageBackend
from engine.sd15_qnn_backend import StableDiffusion15QnnBackend
from engine.sd21_qnn_backend import StableDiffusion21QnnBackend
from engine.controlnet_canny_backend import ControlNetCannyQnnBackend
from engine.sd15_qai_appbuilder_backend import StableDiffusion15QaiAppBuilderBackend, get_shared_backend
from engine.sd21_qai_appbuilder_backend import StableDiffusion21QaiAppBuilderBackend, get_shared_backend as get_shared_sd21_qai_backend
from engine.sd35_qai_appbuilder_backend import StableDiffusion35QaiAppBuilderBackend, get_shared_backend as get_shared_sd35_qai_backend

InferenceBackendFactory.register_backend("Stub", StubImageBackend, lambda runtime: StubImageBackend("Stub", runtime))
InferenceBackendFactory.register_backend("Local CPU (Stub)", StubImageBackend, lambda runtime: StubImageBackend("Local CPU (Stub)", runtime))
InferenceBackendFactory.register_backend("Qualcomm QNN NPU (Stub)", StubImageBackend, lambda runtime: StubImageBackend("Qualcomm QNN NPU (Stub)", runtime))
InferenceBackendFactory.register_backend("ONNX Runtime CPU", OnnxImageBackend, lambda runtime: OnnxImageBackend(runtime))
InferenceBackendFactory.register_backend("ONNX Runtime (Stub)", OnnxImageBackend, lambda runtime: OnnxImageBackend(runtime))
InferenceBackendFactory.register_backend("Qualcomm Stable Diffusion 1.5 (HTP V73)", StableDiffusion15QnnBackend, lambda runtime: StableDiffusion15QnnBackend())
InferenceBackendFactory.register_backend("Qualcomm Stable Diffusion 2.1 (HTP V73)", StableDiffusion21QnnBackend, lambda runtime: StableDiffusion21QnnBackend())
InferenceBackendFactory.register_backend("Qualcomm ControlNet Canny (HTP V73)", ControlNetCannyQnnBackend, lambda runtime: ControlNetCannyQnnBackend())
InferenceBackendFactory.register_backend("Qualcomm SD1.5 QAI AppBuilder (HTP)", StableDiffusion15QaiAppBuilderBackend, lambda runtime: get_shared_backend())
InferenceBackendFactory.register_backend("Qualcomm SD2.1 QAI AppBuilder (HTP)", StableDiffusion21QaiAppBuilderBackend, lambda runtime: get_shared_sd21_qai_backend())
InferenceBackendFactory.register_backend("Qualcomm SD3.5 Medium QAI AppBuilder (HTP)", StableDiffusion35QaiAppBuilderBackend, lambda runtime: get_shared_sd35_qai_backend())
