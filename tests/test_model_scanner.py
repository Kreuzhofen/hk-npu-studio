from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from app.model_scanner import ModelScanner


class ModelScannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.models_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)
        self.models_dir = Path(self.models_dir_obj.name)
        self.scanner = ModelScanner(temp_dir=str(self.temp_dir), models_dir=str(self.models_dir))

    def tearDown(self) -> None:
        self.temp_dir_obj.cleanup()
        self.models_dir_obj.cleanup()

    def test_missing_model_detection(self) -> None:
        # None of the models are created yet, so all should be marked as exists=False, status="missing", size_bytes=0
        results = self.scanner.scan_models()
        self.assertEqual(len(results), 4)
        for r in results:
            self.assertFalse(r["exists"])
            self.assertFalse(r["is_complete"])
            self.assertEqual(r["status"], "missing")
            self.assertEqual(r["size_bytes"], 0)

    def test_complete_model_detection(self) -> None:
        # Create a complete model: Stable Diffusion 2.1 QNN under models_dir / stable_diffusion_v2_1
        sd21_dir = self.models_dir / "stable_diffusion_v2_1"
        sd21_dir.mkdir(parents=True)
        
        # Create expected files
        for f in ["text_encoder.onnx", "unet.onnx", "vae.onnx", "metadata.json"]:
            (sd21_dir / f).write_text("dummy content")

        results = self.scanner.scan_models()
        sd21_res = next(r for r in results if r["id"] == "stable_diffusion_v2_1_qnn")
        self.assertTrue(sd21_res["exists"])
        self.assertTrue(sd21_res["is_complete"])
        self.assertEqual(sd21_res["status"], "complete")
        self.assertGreater(sd21_res["size_bytes"], 0)
        self.assertEqual(sd21_res["quantization"], "w8a16")
        self.assertEqual(sd21_res["backend_status"], "HTP V73")

    def test_incomplete_model_detection(self) -> None:
        # Create an incomplete model: Stable Diffusion XL Base under models_dir / sdxl_base
        sdxl_dir = self.models_dir / "sdxl_base"
        sdxl_dir.mkdir(parents=True)
        
        # Write only some of the expected files (missing text_encoder_2.onnx and vae_decoder.onnx)
        for f in ["text_encoder.onnx", "unet.onnx", "metadata.json"]:
            (sdxl_dir / f).write_text("dummy")

        results = self.scanner.scan_models()
        sdxl_res = next(r for r in results if r["id"] == "sdxl_base")
        self.assertTrue(sdxl_res["exists"])
        self.assertFalse(sdxl_res["is_complete"])
        self.assertEqual(sdxl_res["status"], "incomplete")
        self.assertIn("text_encoder_2.onnx", sdxl_res["missing_files"])
        self.assertIn("vae_decoder.onnx", sdxl_res["missing_files"])

    def test_fallback_initialization(self) -> None:
        # Test fallback initialization works without parameters
        scanner = ModelScanner()
        self.assertIsNotNone(scanner.temp_dir)
        self.assertIsNotNone(scanner.models_dir)


if __name__ == "__main__":
    unittest.main()
