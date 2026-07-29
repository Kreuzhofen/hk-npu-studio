from __future__ import annotations

import unittest
from unittest.mock import patch

from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel
from engine.backends.backend_adapter import BackendAdapter
from engine.backends.cpu_backend_adapter import CPUBackendAdapter
from engine.backends.onnx_backend_adapter import ONNXBackendAdapter
from engine.backends.qnn_backend_adapter import QNNBackendAdapter
from engine.inference_backend import InferenceBackend
from engine.onnx_image_backend import OnnxImageBackend


class BackendContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.job = GenerationJob(
            session=GenerationSessionModel(model_name="contract_test_model")
        )

    def test_routing_adapters_share_inference_contract(self) -> None:
        for adapter_type in (CPUBackendAdapter, ONNXBackendAdapter, QNNBackendAdapter):
            with self.subTest(adapter=adapter_type.__name__):
                adapter = adapter_type()
                self.assertIsInstance(adapter, BackendAdapter)
                self.assertIsInstance(adapter, InferenceBackend)
                self.assertTrue(callable(adapter.generate))
                self.assertTrue(callable(adapter.cancel))
                self.assertTrue(callable(adapter.health_check))

    def test_stub_adapters_preserve_generation_result(self) -> None:
        expected = (
            (CPUBackendAdapter, "CPU (Stub)"),
            (ONNXBackendAdapter, "ONNX Runtime (Stub)"),
            (QNNBackendAdapter, "Qualcomm QNN NPU (Stub)"),
        )
        for adapter_type, backend_name in expected:
            with self.subTest(adapter=adapter_type.__name__):
                job = GenerationJob(
                    session=GenerationSessionModel(model_name="contract_test_model")
                )
                result = adapter_type().generate(job)
                self.assertTrue(result.success)
                self.assertEqual("FINISHED", result.status)
                self.assertEqual("FINISHED", job.status)
                self.assertEqual(1.0, job.progress)
                self.assertEqual(backend_name, result.backend_name)
                self.assertEqual("contract_test_model", result.model_name)

    def test_common_cancel_sets_event_and_status(self) -> None:
        result = CPUBackendAdapter().cancel(self.job)
        self.assertEqual("Generation cancelled (stub)", result)
        self.assertEqual("CANCELLED", self.job.status)
        self.assertTrue(self.job.cancel_requested.is_set())

    def test_onnx_backend_exposes_boolean_availability(self) -> None:
        backend = OnnxImageBackend()
        with patch.object(
            backend,
            "check_availability",
            return_value=(True, "verfügbar"),
        ):
            self.assertIs(backend.is_available(), True)


if __name__ == "__main__":
    unittest.main()
