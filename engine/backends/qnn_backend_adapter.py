from __future__ import annotations

from engine.backends.stub_backend_adapter import StubBackendAdapter


class QNNBackendAdapter(StubBackendAdapter):
    """Routing-Adapter für generische Qualcomm-QNN-NPU-Ausführung."""

    BACKEND_NAME = "Qualcomm QNN NPU (Stub)"
    BACKEND_VERSION = "2.23.0-NPU"
    SUPPORTED_MODELS = ("sd_xl_base_1.0_qnn_int8", "flux_dev_qnn_int4")
    INITIALIZE_MESSAGE = "[QNNBackendAdapter] Initializing Qualcomm Hexagon HTP Backend driver..."
    SHUTDOWN_MESSAGE = "[QNNBackendAdapter] Releasing Qualcomm NPU contexts..."
    GENERATE_MESSAGE = "[QNNBackendAdapter] Enqueuing job {job_id} onto Snapdragon HTP..."
    SUCCESS_MESSAGE = "Bildgenerierung auf Snapdragon NPU (QNN) abgeschlossen (Stub)."
    CANCEL_LOG_MESSAGE = "[QNNBackendAdapter] Terminating QNN NPU context for job {job_id}..."
    CANCEL_MESSAGE = "Generation cancelled on NPU (stub)"

    _cached_is_available: bool | None = None

    def is_available(self) -> bool:
        if QNNBackendAdapter._cached_is_available is None:
            try:
                from engine.backends.backend_discovery_service import BackendDiscoveryService

                result = BackendDiscoveryService.discover()
                QNNBackendAdapter._cached_is_available = bool(
                    result.qnn_sdk_found and result.qnn_tools_found
                )
            except Exception:
                QNNBackendAdapter._cached_is_available = False
        return QNNBackendAdapter._cached_is_available
