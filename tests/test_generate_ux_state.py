from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from controllers.generation_controller import GenerationController
from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel
from controllers.model_repository import ModelRepository
from engine.theme_manager import ThemeManager


def _model_definition(model_id: str, installed: bool = True) -> dict:
    return {
        "id": model_id,
        "display_name": model_id,
        "author": "Test",
        "version": "1.0",
        "license": "Test",
        "description": "Test model",
        "category": "Text-to-Image",
        "backend": "Test",
        "recommended_backend": "Test",
        "minimum_ram_gb": 1,
        "recommended_ram_gb": 1,
        "supports": ["txt2img"],
        "installed": installed,
        "downloaded": installed,
        "path": "test",
        "status": "READY" if installed else "MISSING",
        "product_available": True,
        "capabilities": {"txt2img": True, "controlnet": "controlnet" in model_id},
        "generation_parameters": {
            "width": {"default": 512},
            "height": {"default": 512},
            "steps": {"default": 20},
            "cfg": {"default": 7.5},
            "seed": {"default": -1},
            "sampler": {"default": "Test"},
            "scheduler": {"default": "Test"},
        },
    }


class GenerateUxStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.models_dir = self.root / "models"
        self.models_dir.mkdir()
        self.preferences_path = self.root / "data" / "preferences.json"
        self.original_preferences_path = ModelRepository._preferences_path
        self.original_active_model = ModelRepository._active_model_id
        ModelRepository._preferences_path = self.preferences_path
        ModelRepository._active_model_id = None

    def tearDown(self) -> None:
        ModelRepository._preferences_path = self.original_preferences_path
        ModelRepository._active_model_id = self.original_active_model
        self.temporary_directory.cleanup()

    def _write_model(self, filename: str, model_id: str, installed: bool = True) -> None:
        (self.models_dir / filename).write_text(
            json.dumps(_model_definition(model_id, installed)), encoding="utf-8"
        )

    def test_last_selected_sd21_and_sd15_are_restored(self) -> None:
        self._write_model("a_sd15.json", "stable_diffusion_v1_5_qnn")
        self._write_model("b_sd21.json", "stable_diffusion_v2_1_qnn")
        repository = ModelRepository(str(self.models_dir))

        for model_id in ("stable_diffusion_v2_1_qnn", "stable_diffusion_v1_5_qnn"):
            repository.set_active_model_id(model_id)
            ModelRepository._active_model_id = None
            restarted_repository = ModelRepository(str(self.models_dir))
            self.assertEqual(model_id, restarted_repository.get_active_model_id())

    def test_invalid_or_unavailable_preference_falls_back_cleanly(self) -> None:
        self._write_model("a_sd15.json", "stable_diffusion_v1_5_qnn")
        self._write_model("b_sd21.json", "stable_diffusion_v2_1_qnn", installed=False)
        self.preferences_path.parent.mkdir(parents=True)
        self.preferences_path.write_text(
            json.dumps({"active_model_id": "stable_diffusion_v2_1_qnn"}), encoding="utf-8"
        )

        repository = ModelRepository(str(self.models_dir))
        self.assertEqual("stable_diffusion_v1_5_qnn", repository.get_active_model_id())
        saved = json.loads(self.preferences_path.read_text(encoding="utf-8"))
        self.assertEqual("stable_diffusion_v1_5_qnn", saved["active_model_id"])

    def test_progress_success_role_is_green_in_both_themes(self) -> None:
        original_theme = ThemeManager.active_theme()
        try:
            ThemeManager.set_active_theme("dark")
            self.assertEqual("#22C55E", ThemeManager.palette().success)
            ThemeManager.set_active_theme("light")
            self.assertEqual("#15803D", ThemeManager.palette().success)
        finally:
            ThemeManager.set_active_theme(original_theme)

    def test_existing_cancel_path_returns_explicit_cancelled_status(self) -> None:
        controller = GenerationController()
        job = GenerationJob(session=GenerationSessionModel())
        controller.queue.enqueue(job)
        controller.queue.dequeue()
        self.assertEqual("CANCELLED", controller.cancel_generation())
        self.assertEqual("CANCELLED", job.status)

    def test_input_image_path_mvc_propagation(self) -> None:
        from controllers.prompt_workspace_controller import PromptWorkspaceController
        from controllers.prompt_workspace_model import PromptWorkspaceModel

        # Test default is None
        session = GenerationSessionModel()
        self.assertIsNone(session.input_image_path)

        model = PromptWorkspaceModel()
        self.assertIsNone(model.state.input_image_path)

        # Test update_state updates it
        model.update_state(input_image_path="path/to/image.png")
        self.assertEqual("path/to/image.png", model.state.input_image_path)

        # Test reset sets it back to None
        session.update(input_image_path="path/to/image.png")
        self.assertEqual("path/to/image.png", session.input_image_path)
        session.reset()
        self.assertIsNone(session.input_image_path)

    def test_controlnet_input_image_validation(self) -> None:
        self._write_model("c_controlnet.json", "controlnet_canny_qnn")
        repository = ModelRepository(str(self.models_dir))
        session = GenerationSessionModel(
            prompt="Test prompt",
            model_name="controlnet_canny_qnn"
        )
        controller = GenerationController(session=session, repository=repository)

        # 1. Test missing reference image path
        is_valid, msg = controller.validate_session()
        self.assertFalse(is_valid)
        self.assertEqual("Eingabebild für ControlNet Canny fehlt oder ist ungültig.", msg)

        # 2. Test non-existent image path
        session.update(input_image_path="nonexistent_image.png")
        is_valid, msg = controller.validate_session()
        self.assertFalse(is_valid)
        self.assertEqual("Eingabebild für ControlNet Canny fehlt oder ist ungültig.", msg)

        # 3. Test valid image path
        from PIL import Image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_img_path = f.name
        try:
            img = Image.new("RGB", (16, 16), color="white")
            img.save(temp_img_path, "PNG")
            session.update(input_image_path=temp_img_path)
            is_valid, msg = controller.validate_session()
            # It should pass ControlNet check and proceed to validate_generation_parameters
            self.assertTrue(is_valid or "Eingabebild" not in msg)
        finally:
            import os
            try:
                os.unlink(temp_img_path)
            except Exception:
                pass



if __name__ == "__main__":
    unittest.main()
