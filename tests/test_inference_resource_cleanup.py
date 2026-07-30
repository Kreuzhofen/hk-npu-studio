from __future__ import annotations

from io import StringIO
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel
from engine.generation_response import GenerationResponse
from engine.local_image_generator_adapter import LocalImageGeneratorAdapter
from engine.onnx_provider_service import OnnxProviderService
from engine.unet_service import UNetService
from engine.sd15_qnn_backend import StableDiffusion15QnnBackend
from engine.sd21_qnn_backend import StableDiffusion21QnnBackend
from engine.controlnet_canny_backend import ControlNetCannyQnnBackend


class FakeProcess:
    def __init__(self) -> None:
        self.stdout = StringIO()
        self.returncode = None
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        self.returncode = -15 if self.terminated else 0
        return self.returncode

    def kill(self):
        self.returncode = -9


class InferenceResourceCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.job = GenerationJob(
            GenerationSessionModel(prompt="test", model_name="demo")
        )

    def test_physical_backend_shutdown_runs_after_success(self):
        physical = MagicMock()
        physical.generate.return_value = GenerationResponse(
            True, "FINISHED", "done", model_name="demo"
        )
        routing = MagicMock()
        routing.get_backend_name.return_value = "Test Backend"

        with patch(
            "engine.inference_backend_factory.InferenceBackendFactory.get_backend",
            return_value=physical,
        ):
            result = LocalImageGeneratorAdapter(routing).generate(self.job)

        self.assertTrue(result.success)
        physical.shutdown.assert_called_once_with()
        routing.set_running_backend.assert_any_call(None)

    def test_physical_backend_shutdown_runs_after_error(self):
        physical = MagicMock()
        physical.generate.side_effect = RuntimeError("inference failed")
        routing = MagicMock()
        routing.get_backend_name.return_value = "Test Backend"

        with patch(
            "engine.inference_backend_factory.InferenceBackendFactory.get_backend",
            return_value=physical,
        ), self.assertRaisesRegex(RuntimeError, "inference failed"):
            LocalImageGeneratorAdapter(routing).generate(self.job)

        physical.shutdown.assert_called_once_with()
        routing.set_running_backend.assert_any_call(None)

    def test_shutdown_error_does_not_mask_generation_result(self):
        physical = MagicMock()
        physical.generate.return_value = GenerationResponse(
            True, "FINISHED", "done", model_name="demo"
        )
        physical.shutdown.side_effect = RuntimeError("cleanup failed")
        routing = MagicMock()
        routing.get_backend_name.return_value = "Test Backend"

        with patch(
            "engine.inference_backend_factory.InferenceBackendFactory.get_backend",
            return_value=physical,
        ):
            result = LocalImageGeneratorAdapter(routing).generate(self.job)

        self.assertTrue(result.success)
        routing.set_running_backend.assert_any_call(None)

    def test_onnx_session_release_is_used_on_inference_failure(self):
        package = MagicMock()
        package.is_fully_ready.return_value = True
        package.get_component_path.return_value = "C:/models/unet.onnx"
        session = MagicMock()
        session.get_inputs.return_value = []
        session.run.side_effect = RuntimeError("run failed")
        service = UNetService(package)

        with patch("pathlib.Path.is_file", return_value=True), patch.object(
            OnnxProviderService, "create_session", return_value=session
        ), patch.object(
            OnnxProviderService, "release_session"
        ) as release:
            with self.assertRaisesRegex(RuntimeError, "Reale CPU-Ausführung"):
                service.predict_noise(
                    np.zeros((1, 4, 8, 8), dtype=np.float32),
                    1,
                    np.zeros((1, 77, 768), dtype=np.float32),
                )

        release.assert_called_once_with(session)

    def test_qnn_shutdown_terminates_worker_and_closes_pipe(self):
        for backend in (
            StableDiffusion15QnnBackend(),
            StableDiffusion21QnnBackend(),
            ControlNetCannyQnnBackend(),
        ):
            with self.subTest(backend=type(backend).__name__):
                process = FakeProcess()
                backend._active_process = process

                backend.shutdown()

                self.assertTrue(process.terminated)
                self.assertTrue(process.stdout.closed)
                self.assertIsNone(backend._active_process)


if __name__ == "__main__":
    unittest.main()
