from __future__ import annotations

import tempfile
import unittest
import subprocess
from pathlib import Path
from unittest.mock import patch

from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel
from engine.backends.backend_adapter import BackendAdapter
from engine.backends.cpu_backend_adapter import CPUBackendAdapter
from engine.backends.onnx_backend_adapter import ONNXBackendAdapter
from engine.backends.qnn_backend_adapter import QNNBackendAdapter
from engine.backends.backend_manager import BackendManager
from engine.backends.sd15_qnn_backend_adapter import StableDiffusion15QnnBackendAdapter
from engine.backends.sd21_qnn_backend_adapter import StableDiffusion21QnnBackendAdapter
from engine.backends.controlnet_canny_backend_adapter import ControlNetCannyQnnBackendAdapter
from engine.backends.sd35_qai_appbuilder_backend_adapter import StableDiffusion35QaiAppBuilderBackendAdapter
from engine.inference_backend import InferenceBackend
from engine.inference_backend_factory import InferenceBackendFactory
from engine.onnx_image_backend import OnnxImageBackend
from engine.runtime_model import RuntimeModel
from engine import sd35_qai_appbuilder_backend as sd35_backend
from engine.sd35_qai_appbuilder_backend import (
    BACKEND_NAME as SD35_BACKEND_NAME,
    StableDiffusion35QaiAppBuilderBackend,
)


class BackendContractTests(unittest.TestCase):
    def test_default_registry_contains_only_executable_local_backend_routes(self):
        names = BackendManager().get_all_backend_names()

        self.assertNotIn("Remote Cloud API (Stub)", names)
        self.assertFalse(any("Remote" in name for name in names))

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
            (ONNXBackendAdapter, "ONNX Runtime CPU"),
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

    def test_onnx_backend_uses_dynamic_diagnostic_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log_dir = Path(directory) / "logs"
            with patch("engine.onnx_image_backend.LOG_DIR", log_dir):
                path = OnnxImageBackend()._build_save_diagnostic_log_path(self.job)
            self.assertEqual(log_dir / "diagnostics", path.parent)
            self.assertTrue(path.parent.is_dir())

    def test_onnx_model_discovery_uses_dynamic_models_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            models_dir = Path(directory) / "models"
            model = models_dir / "custom" / "model.onnx"
            model.parent.mkdir(parents=True)
            model.write_bytes(b"onnx")
            with patch("engine.onnx_image_backend.MODELS_DIR", models_dir), patch(
                "engine.onnx_image_backend.BASE", Path(directory) / "app"
            ):
                discovered = OnnxImageBackend.discover_onnx_models()
            self.assertEqual(str(model.resolve().as_posix()), discovered[0]["path"])

    @patch("app.settings_manager.SettingsManager.get_execution_provider", return_value="QNNExecutionProvider")
    def test_sd35_routes_only_to_sd35_qai_backend(self, _provider) -> None:
        manager = BackendManager()
        sd35 = manager.get_backend(SD35_BACKEND_NAME)
        sd15 = next(
            adapter
            for adapter in manager._backends.values()
            if isinstance(adapter, StableDiffusion15QnnBackendAdapter)
        )
        model = {
            "id": "stable_diffusion_v3_5_qai",
            "backend": SD35_BACKEND_NAME,
            "recommended_backend": SD35_BACKEND_NAME,
        }

        with patch.object(sd35, "is_available", return_value=True), patch.object(
            sd15, "is_available", return_value=True
        ):
            selected = manager.get_best_backend(model)

        self.assertIs(selected, sd35)
        self.assertIsInstance(selected, StableDiffusion35QaiAppBuilderBackendAdapter)
        self.assertNotIsInstance(selected, StableDiffusion15QnnBackendAdapter)

        runtime = RuntimeModel(
            model_id="stable_diffusion_v3_5_qai",
            model_path="C:/models/stable_diffusion_v3_5_qai",
            files=[],
            backend=SD35_BACKEND_NAME,
            load_plan=None,
        )
        delegated = InferenceBackendFactory.get_backend(
            selected.get_backend_name(), runtime_model=runtime
        )
        self.assertIsInstance(delegated, StableDiffusion35QaiAppBuilderBackend)

    @patch("app.settings_manager.SettingsManager.get_execution_provider", return_value="QNNExecutionProvider")
    def test_sd35_unavailable_never_falls_back_to_sd15(self, _provider) -> None:
        manager = BackendManager()
        sd35 = manager.get_backend(SD35_BACKEND_NAME)
        sd15 = next(
            adapter
            for adapter in manager._backends.values()
            if isinstance(adapter, StableDiffusion15QnnBackendAdapter)
        )
        model = {
            "id": "stable_diffusion_v3_5_qai",
            "backend": SD35_BACKEND_NAME,
            "recommended_backend": SD35_BACKEND_NAME,
        }

        with patch.object(sd35, "is_available", return_value=False), patch.object(
            sd15, "is_available", return_value=True
        ):
            selected = manager.get_best_backend(model)

        self.assertIsNone(selected)

    @patch("app.settings_manager.SettingsManager.get_execution_provider", return_value="QNNExecutionProvider")
    def test_existing_qnn_product_routes_remain_model_specific(self, _provider) -> None:
        cases = (
            (
                "stable_diffusion_v1_5_qnn",
                "Qualcomm Stable Diffusion 1.5 (HTP V73)",
                StableDiffusion15QnnBackendAdapter,
            ),
            (
                "stable_diffusion_v2_1_qnn",
                "Qualcomm Stable Diffusion 2.1 (HTP V73)",
                StableDiffusion21QnnBackendAdapter,
            ),
            (
                "controlnet_canny_qnn",
                "Qualcomm ControlNet Canny (HTP V73)",
                ControlNetCannyQnnBackendAdapter,
            ),
        )
        for model_id, backend_name, adapter_type in cases:
            with self.subTest(model=model_id):
                manager = BackendManager()
                target = manager.get_backend(backend_name)
                with patch.object(target, "is_available", return_value=True):
                    selected = manager.get_best_backend(
                        {
                            "id": model_id,
                            "backend": backend_name,
                            "recommended_backend": backend_name,
                        }
                    )
                self.assertIsInstance(selected, adapter_type)

    def test_sd35_frozen_availability_uses_packaged_probe_and_model_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            worker = root / "HKNPUStudio.exe"
            worker.write_bytes(b"frozen")
            model_dir = root / "models" / "stable_diffusion_v3_5_qai"
            for relative_path in sd35_backend._MODEL_FILES:
                path = model_dir / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"model")
            for tokenizer_name in ("tokenizer", "tokenizer_2"):
                tokenizer = model_dir / tokenizer_name
                tokenizer.mkdir(parents=True)
                for filename in ("tokenizer_config.json", "vocab.json", "merges.txt"):
                    (tokenizer / filename).write_text("{}", encoding="utf-8")

            completed = subprocess.CompletedProcess(
                [str(worker), "--qai-appbuilder-probe"], 0, "", ""
            )
            backend = StableDiffusion35QaiAppBuilderBackend()
            with patch.object(sd35_backend, "_worker_python", return_value=worker), patch.object(
                sd35_backend, "_model_dir", return_value=model_dir
            ), patch.object(sd35_backend.sys, "frozen", True, create=True), patch.object(
                sd35_backend.subprocess, "run", return_value=completed
            ) as run:
                self.assertTrue(backend.is_available())

            self.assertEqual(
                [str(worker), "--qai-appbuilder-probe"], run.call_args.args[0]
            )


if __name__ == "__main__":
    unittest.main()
