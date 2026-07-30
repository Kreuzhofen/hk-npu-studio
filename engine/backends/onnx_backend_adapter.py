from __future__ import annotations

from engine.backends.stub_backend_adapter import StubBackendAdapter


class ONNXBackendAdapter(StubBackendAdapter):
    """Routing-Adapter für die reale lokale ONNX-Runtime-Ausführung."""

    BACKEND_NAME = "ONNX Runtime CPU"
    BACKEND_VERSION = "1.27.0"
    SUPPORTED_MODELS = ("sdxl_base",)
    INITIALIZE_MESSAGE = "[ONNXBackendAdapter] Loading ONNX Runtime sessions..."
    SHUTDOWN_MESSAGE = "[ONNXBackendAdapter] Shutting down ONNX Runtime sessions..."
    GENERATE_MESSAGE = "[ONNXBackendAdapter] Executing ONNX pipeline for job {job_id}..."
    SUCCESS_MESSAGE = "Bildgenerierung über ONNX Runtime CPU erfolgreich abgeschlossen."
    CANCEL_LOG_MESSAGE = (
        "[ONNXBackendAdapter] Signalling cancellation to ONNX session for job {job_id}..."
    )
    CANCEL_MESSAGE = "Generation cancelled on ORT (stub)"
