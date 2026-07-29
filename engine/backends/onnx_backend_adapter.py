from __future__ import annotations

from engine.backends.stub_backend_adapter import StubBackendAdapter


class ONNXBackendAdapter(StubBackendAdapter):
    """Routing-Adapter für lokale ONNX-Runtime-Ausführung."""

    BACKEND_NAME = "ONNX Runtime (Stub)"
    BACKEND_VERSION = "1.18.0-stub"
    SUPPORTED_MODELS = ("sd_xl_base_1.0_onnx", "sd_1.5_onnx")
    INITIALIZE_MESSAGE = "[ONNXBackendAdapter] Loading ONNX Runtime sessions..."
    SHUTDOWN_MESSAGE = "[ONNXBackendAdapter] Shutting down ONNX Runtime sessions..."
    GENERATE_MESSAGE = "[ONNXBackendAdapter] Executing ONNX pipeline for job {job_id}..."
    SUCCESS_MESSAGE = "Bildgenerierung über ONNX Runtime erfolgreich (Stub)."
    CANCEL_LOG_MESSAGE = (
        "[ONNXBackendAdapter] Signalling cancellation to ONNX session for job {job_id}..."
    )
    CANCEL_MESSAGE = "Generation cancelled on ORT (stub)"
