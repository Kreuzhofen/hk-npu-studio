from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel
from engine.onnx_image_backend import OnnxImageBackend
from engine.runtime_model import RuntimeModel
from engine.text_embedding_service import TextEmbeddingService
from engine.unet_service import UNetService
from engine.vae_decoder_service import VAEDecoderService


class _IncompletePackage:
    def is_fully_ready(self) -> bool:
        return False

    def get_component_path(self, component: str) -> str:
        return f"C:/missing/{component}/model.onnx"


class CpuGenerationFailClosedTests(unittest.TestCase):
    def test_component_services_never_return_mock_results(self) -> None:
        package = _IncompletePackage()
        with self.assertRaisesRegex(RuntimeError, "Text-Encoder"):
            TextEmbeddingService(package)._run_encoder_component(
                "text_encoder", [0] * 77, 768
            )
        with self.assertRaisesRegex(RuntimeError, "UNet"):
            UNetService(package).predict_noise(
                np.zeros((1, 4, 64, 64), dtype=np.float32),
                1,
                np.zeros((1, 77, 2048), dtype=np.float32),
            )
        with self.assertRaisesRegex(RuntimeError, "VAE"):
            VAEDecoderService(package).decode_latents(
                np.zeros((1, 4, 64, 64), dtype=np.float32)
            )

    def test_incompatible_cpu_package_returns_failure_without_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            model_dir = Path(directory)
            (model_dir / "model.onnx").write_bytes(b"not-used")
            runtime = RuntimeModel(
                model_id="controlnet_canny_qnn",
                model_path=str(model_dir),
                files=[str(model_dir / "model.onnx")],
                backend="Qualcomm ControlNet Canny (HTP V73)",
            )
            session = GenerationSessionModel(
                model_name="controlnet_canny_qnn",
                output_directory=directory,
            )
            package = MagicMock()
            package.verify_components.return_value = {
                "text_encoder": "FALLBACK",
                "unet": "FALLBACK",
                "vae_decoder": "FALLBACK",
            }
            package.is_fully_ready.return_value = False
            package.get_component_path.side_effect = (
                lambda component: str(model_dir / component / "model.onnx")
            )

            with patch.object(
                OnnxImageBackend, "check_availability", return_value=(True, "ok")
            ), patch.object(
                OnnxImageBackend, "discover_onnx_models", return_value=[]
            ), patch(
                "controllers.model_repository.ModelRepository.build_runtime_package",
                return_value=package,
            ):
                response = OnnxImageBackend(runtime).generate(GenerationJob(session))

            self.assertFalse(response.success)
            self.assertIsNone(response.image_path)
            self.assertNotIn("Alpha Fallback", response.message)
            self.assertEqual([], list(model_dir.glob("*.png")))


if __name__ == "__main__":
    unittest.main()
