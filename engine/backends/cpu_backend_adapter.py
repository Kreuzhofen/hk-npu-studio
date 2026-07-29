from __future__ import annotations

from engine.backends.stub_backend_adapter import StubBackendAdapter


class CPUBackendAdapter(StubBackendAdapter):
    """Lokaler CPU-Referenzadapter und garantierter Rückfallpfad."""

    BACKEND_NAME = "CPU (Stub)"
    BACKEND_VERSION = "0.1.0-stub"
    SUPPORTED_MODELS = ("sd_xl_base_1.0", "sd_1.5_resnet")
    INITIALIZE_MESSAGE = "[CPUBackendAdapter] Initializing CPU inference context..."
    SHUTDOWN_MESSAGE = "[CPUBackendAdapter] Cleaning up CPU inference context..."
    GENERATE_MESSAGE = "[CPUBackendAdapter] Starting generation stub for job {job_id}..."
    SUCCESS_MESSAGE = "Bildgenerierung auf CPU erfolgreich abgeschlossen (Stub)."
    CANCEL_LOG_MESSAGE = "[CPUBackendAdapter] Cancelling job {job_id}..."
    CANCEL_MESSAGE = "Generation cancelled (stub)"
