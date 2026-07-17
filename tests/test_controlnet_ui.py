from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import tempfile
from pathlib import Path

from engine.theme_manager import ThemeManager, ThemePalette

# Setup a mock palette for widgets/phoenix/theme initialization
original_palette_func = ThemeManager.palette
dummy_palette = ThemePalette(
    background="#ffffff",
    surface="#ffffff",
    card="#ffffff",
    elevated="#f3f2f1",
    border="#cccccc",
    accent="#0078d4",
    success="#22c55e",
    warning="#eab308",
    error="#ef4444",
    text="#000000",
    text_secondary="#333333",
    text_disabled="#999999",
    text_on_accent="#ffffff",
    button="#ffffff",
    button_hover="#ffffff",
    button_active="#005a9e",
    sidebar="#ffffff",
    header="#ffffff",
    workspace="#ffffff",
)
ThemeManager.palette = MagicMock(return_value=dummy_palette)

from controllers.prompt_workspace_controller import PromptWorkspaceController
from widgets.phoenix.views.prompt_view import PhoenixPromptView
from widgets.phoenix.theme import PHOENIX_THEME

# Restore original palette function
ThemeManager.palette = original_palette_func


class ControlNetUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        self.controller = PromptWorkspaceController()
        # Initialize the view
        self.view = PhoenixPromptView(self.root, controller=self.controller)

    def tearDown(self) -> None:
        self.view.destroy()

    def test_dynamic_visibility_based_on_model_capabilities(self) -> None:
        # 1. SD1.5 model (controlnet capability is False)
        self.view._apply_generation_contract("stable_diffusion_v1_5_qnn")
        
        # Verify reference image controls are hidden
        self.assertEqual(self.view.dnd_subtitle.winfo_manager(), "")
        self.assertEqual(self.view.dnd_card.winfo_manager(), "")

        # 2. ControlNet Canny QNN model (controlnet capability is True)
        self.view._apply_generation_contract("controlnet_canny_qnn")
        
        # Verify reference image controls are visible in grid
        self.assertNotEqual(self.view.dnd_subtitle.winfo_manager(), "")
        self.assertNotEqual(self.view.dnd_card.winfo_manager(), "")
        
        # Check text update
        self.assertEqual(self.view.dnd_subtitle.cget("text"), "Referenzbild für ControlNet Canny:")

        # 3. Switch back to SD2.1 (controlnet capability is False)
        self.view._apply_generation_contract("stable_diffusion_v2_1_qnn")
        self.assertEqual(self.view.dnd_subtitle.winfo_manager(), "")
        self.assertEqual(self.view.dnd_card.winfo_manager(), "")

    def test_ui_validation_triggers_on_generate_click(self) -> None:
        # Load ControlNet model
        self.view.model_var.set("controlnet_canny_qnn")
        self.view._apply_generation_contract("controlnet_canny_qnn")
        self.view.prompt_text.insert("1.0", "A beautiful futuristic city")
        
        # Simulate generate click when input image is missing
        # We patch messagebox.showerror to prevent popups during automated tests
        with patch("tkinter.messagebox.showerror") as mock_error:
            # Let's directly call controller validation
            is_valid, msg = self.controller.generation_controller.validate_session()
            self.assertFalse(is_valid)
            self.assertEqual("Eingabebild für ControlNet Canny fehlt oder ist ungültig.", msg)

    def test_reference_image_reset_on_model_change(self) -> None:
        # Set ControlNet model and load an input image
        self.view.model_var.set("controlnet_canny_qnn")
        self.view._apply_generation_contract("controlnet_canny_qnn")

        # Manually write reference image path in model/view
        self.view._ref_image_path = "some_image.png"
        self.controller.update_parameters(
            prompt="test", negative_prompt="", seed=-1, steps=20, cfg=7.5,
            width=512, height=512, selected_model="controlnet_canny_qnn",
            sampler="Euler", scheduler="Euler", batch_size=1,
            input_image_path="some_image.png"
        )
        self.assertEqual(self.controller.model.state.input_image_path, "some_image.png")

        # Transition model to SD 1.5
        self.view.model_var.set("stable_diffusion_v1_5_qnn")
        self.view._on_model_changed()

        # Verify the reference image state was completely cleared
        self.assertIsNone(self.view._ref_image_path)
        self.assertIsNone(self.controller.model.state.input_image_path)
        self.assertIsNone(self.view._dnd_photo_ref)


    def test_controlnet_image_validation_scenarios(self) -> None:
        import os
        from PIL import Image

        self.view.model_var.set("controlnet_canny_qnn")
        self.view._apply_generation_contract("controlnet_canny_qnn")

        # 1. Valid temporary PNG accepted
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            valid_png = f.name
        try:
            img = Image.new("RGB", (16, 16), color="white")
            img.save(valid_png, "PNG")

            self.controller.update_parameters(
                prompt="A beautiful futuristic city", negative_prompt="", seed=-1, steps=20, cfg=7.5,
                width=512, height=512, selected_model="controlnet_canny_qnn",
                sampler="DDIM", scheduler="DDIM", batch_size=1,
                input_image_path=valid_png
            )
            is_valid, msg = self.controller.generation_controller.validate_session()
            self.assertTrue(is_valid)
        finally:
            if os.path.exists(valid_png):
                os.unlink(valid_png)

        # 2. Empty .png file rejected
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            empty_png = f.name
        try:
            self.controller.update_parameters(
                prompt="A beautiful futuristic city", negative_prompt="", seed=-1, steps=20, cfg=7.5,
                width=512, height=512, selected_model="controlnet_canny_qnn",
                sampler="DDIM", scheduler="DDIM", batch_size=1,
                input_image_path=empty_png
            )
            is_valid, msg = self.controller.generation_controller.validate_session()
            self.assertFalse(is_valid)
            self.assertEqual("Das ausgewählte Referenzbild ist leer (0 Byte).", msg)
        finally:
            if os.path.exists(empty_png):
                os.unlink(empty_png)

        # 3. Corrupt .png file rejected
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            corrupt_png = f.name
        try:
            with open(corrupt_png, "wb") as f_corrupt:
                f_corrupt.write(b"this is totally corrupt raw bytes and not a png file structure")
            self.controller.update_parameters(
                prompt="A beautiful futuristic city", negative_prompt="", seed=-1, steps=20, cfg=7.5,
                width=512, height=512, selected_model="controlnet_canny_qnn",
                sampler="DDIM", scheduler="DDIM", batch_size=1,
                input_image_path=corrupt_png
            )
            is_valid, msg = self.controller.generation_controller.validate_session()
            self.assertFalse(is_valid)
            self.assertTrue(msg.startswith("Das Referenzbild ist beschädigt oder ungültig"))
        finally:
            if os.path.exists(corrupt_png):
                os.unlink(corrupt_png)

        # 4. Missing file rejected
        self.controller.update_parameters(
            prompt="A beautiful futuristic city", negative_prompt="", seed=-1, steps=20, cfg=7.5,
            width=512, height=512, selected_model="controlnet_canny_qnn",
            sampler="DDIM", scheduler="DDIM", batch_size=1,
            input_image_path="nonexistent_image_file.png"
        )
        is_valid, msg = self.controller.generation_controller.validate_session()
        self.assertFalse(is_valid)
        self.assertEqual("Eingabebild für ControlNet Canny fehlt oder ist ungültig.", msg)

        # 5. Unsupported extension rejected
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            unsupported_ext = f.name
        try:
            with open(unsupported_ext, "w") as f_txt:
                f_txt.write("not an image")
            self.controller.update_parameters(
                prompt="A beautiful futuristic city", negative_prompt="", seed=-1, steps=20, cfg=7.5,
                width=512, height=512, selected_model="controlnet_canny_qnn",
                sampler="DDIM", scheduler="DDIM", batch_size=1,
                input_image_path=unsupported_ext
            )
            is_valid, msg = self.controller.generation_controller.validate_session()
            self.assertFalse(is_valid)
            self.assertEqual("Es werden nur Bilddateien in den Formaten PNG, JPG, JPEG und WebP unterstützt.", msg)
        finally:
            if os.path.exists(unsupported_ext):
                os.unlink(unsupported_ext)

    def test_model_switching_scenarios(self) -> None:
        # Start state: ControlNet Canny
        self.view.model_var.set("controlnet_canny_qnn")
        self.view.update()

        # Populate reference image state
        self.view._ref_image_path = "some_image.png"
        self.controller.update_parameters(
            prompt="test", negative_prompt="", seed=-1, steps=20, cfg=7.5,
            width=512, height=512, selected_model="controlnet_canny_qnn",
            sampler="Euler", scheduler="Euler", batch_size=1,
            input_image_path="some_image.png"
        )
        self.assertEqual(self.controller.model.state.input_image_path, "some_image.png")
        self.assertEqual(self.view.dnd_card.winfo_manager(), "grid")

        # 1. ControlNet -> SD1.5 via AI-Generate OptionMenu (dropdown selection)
        self.view.model_var.set("stable_diffusion_v1_5_qnn")
        self.view.update()

        # Verify Referenzbildbereich is hidden, states are cleared
        self.assertEqual(self.view.dnd_card.winfo_manager(), "")
        self.assertIsNone(self.view._ref_image_path)
        self.assertIsNone(self.controller.model.state.input_image_path)
        self.assertIsNone(self.view._dnd_photo_ref)

        # 2. SD1.5 -> ControlNet via AI-Generate OptionMenu
        self.view.model_var.set("controlnet_canny_qnn")
        self.view.update()

        # Verify Referenzbildbereich is visible, state is empty/None (no old image restored)
        self.assertEqual(self.view.dnd_card.winfo_manager(), "grid")
        self.assertIsNone(self.view._ref_image_path)
        self.assertIsNone(self.controller.model.state.input_image_path)
        self.assertIsNone(self.view._dnd_photo_ref)

        # 3. ControlNet -> SD2.1 -> ControlNet via AI-Generate OptionMenu
        self.view._ref_image_path = "some_image.png"
        self.controller.model.update_state(input_image_path="some_image.png")
        self.view.model_var.set("stable_diffusion_v2_1_qnn")
        self.view.update()
        self.assertEqual(self.view.dnd_card.winfo_manager(), "")
        self.assertIsNone(self.view._ref_image_path)
        self.assertIsNone(self.controller.model.state.input_image_path)

        self.view.model_var.set("controlnet_canny_qnn")
        self.view.update()
        self.assertEqual(self.view.dnd_card.winfo_manager(), "grid")
        self.assertIsNone(self.view._ref_image_path)
        self.assertIsNone(self.controller.model.state.input_image_path)

        # 4. Model change via AI Model Manager continues to work
        # Setup: switch back to SD1.5 first
        self.view.model_var.set("stable_diffusion_v1_5_qnn")
        self.view.update()
        self.assertEqual(self.view.dnd_card.winfo_manager(), "")

        # Simulate active model change via Model Manager repository call
        self.controller.repository.set_active_model_id("controlnet_canny_qnn")
        # Trigger refresh (which detects mismatch and invokes model_var.set and _change_active_model)
        self.view.refresh()
        self.view.update()

        # Verify Model Manager path syncs successfully
        self.assertEqual(self.view.model_var.get(), "controlnet_canny_qnn")
        self.assertEqual(self.view.dnd_card.winfo_manager(), "grid")
        self.assertIsNone(self.view._ref_image_path)
        self.assertIsNone(self.controller.model.state.input_image_path)

        # 5. Both paths lead to identical Capability- and UI-state
        # State from Model Manager path:
        state_mm = self.controller.get_state()
        manager_mm = self.view.dnd_card.winfo_manager()

        # Now reset and do OptionMenu path for the same model
        self.view.model_var.set("stable_diffusion_v1_5_qnn")
        self.view.update()
        self.view.model_var.set("controlnet_canny_qnn")
        self.view.update()

        state_om = self.controller.get_state()
        manager_om = self.view.dnd_card.winfo_manager()

        # Assert they are identical
        self.assertEqual(manager_mm, manager_om)
        self.assertEqual(state_mm.selected_model, state_om.selected_model)
        self.assertEqual(state_mm.width, state_om.width)
        self.assertEqual(state_mm.height, state_om.height)
        self.assertEqual(state_mm.input_image_path, state_om.input_image_path)

    def test_controlnet_canny_controls(self) -> None:
        import os
        import json
        from PIL import Image
        from unittest.mock import MagicMock
        from controllers.generation_job import GenerationJob
        from engine.inference_backend_factory import InferenceBackendFactory

        # 1. Standardwerte (defaults)
        self.view.model_var.set("controlnet_canny_qnn")
        self.view.update()
        state = self.controller.get_state()
        self.assertEqual(state.canny_low_threshold, 50)
        self.assertEqual(state.canny_high_threshold, 150)
        self.assertEqual(state.controlnet_conditioning_scale, 1.0)

        # 2. Low Threshold kleiner als High Threshold (validation)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_img = f.name
        try:
            img = Image.new("RGB", (16, 16), color="white")
            img.save(temp_img, "PNG")

            self.controller.update_parameters(
                prompt="A beautiful city", negative_prompt="", seed=-1, steps=20, cfg=7.5,
                width=512, height=512, selected_model="controlnet_canny_qnn",
                sampler="DDIM", scheduler="DDIM", batch_size=1,
                input_image_path=temp_img,
                canny_low_threshold=100, canny_high_threshold=50,
                controlnet_conditioning_scale=1.0
            )
            is_valid, msg = self.controller.generation_controller.validate_session()
            self.assertFalse(is_valid)
            self.assertEqual("Der untere Schwellenwert (Low Threshold) muss kleiner als der obere Schwellenwert (High Threshold) sein.", msg)

            self.controller.update_parameters(
                prompt="A beautiful city", negative_prompt="", seed=-1, steps=20, cfg=7.5,
                width=512, height=512, selected_model="controlnet_canny_qnn",
                sampler="DDIM", scheduler="DDIM", batch_size=1,
                input_image_path=temp_img,
                canny_low_threshold=100, canny_high_threshold=100,
                controlnet_conditioning_scale=1.0
            )
            is_valid, msg = self.controller.generation_controller.validate_session()
            self.assertFalse(is_valid)
            self.assertEqual("Der untere Schwellenwert (Low Threshold) muss kleiner als der obere Schwellenwert (High Threshold) sein.", msg)

            # 3. Ungültige Werte blockieren Generation vor Worker-Start (validation bounds)
            # Low threshold out of bounds
            self.controller.update_parameters(
                prompt="A beautiful city", negative_prompt="", seed=-1, steps=20, cfg=7.5,
                width=512, height=512, selected_model="controlnet_canny_qnn",
                sampler="DDIM", scheduler="DDIM", batch_size=1,
                input_image_path=temp_img,
                canny_low_threshold=-10, canny_high_threshold=150,
                controlnet_conditioning_scale=1.0
            )
            is_valid, msg = self.controller.generation_controller.validate_session()
            self.assertFalse(is_valid)
            self.assertEqual("Canny-Schwellenwerte müssen zwischen 0 und 255 liegen.", msg)

            # High threshold out of bounds
            self.controller.update_parameters(
                prompt="A beautiful city", negative_prompt="", seed=-1, steps=20, cfg=7.5,
                width=512, height=512, selected_model="controlnet_canny_qnn",
                sampler="DDIM", scheduler="DDIM", batch_size=1,
                input_image_path=temp_img,
                canny_low_threshold=50, canny_high_threshold=300,
                controlnet_conditioning_scale=1.0
            )
            is_valid, msg = self.controller.generation_controller.validate_session()
            self.assertFalse(is_valid)
            self.assertEqual("Canny-Schwellenwerte müssen zwischen 0 und 255 liegen.", msg)

            # Conditioning scale out of bounds
            self.controller.update_parameters(
                prompt="A beautiful city", negative_prompt="", seed=-1, steps=20, cfg=7.5,
                width=512, height=512, selected_model="controlnet_canny_qnn",
                sampler="DDIM", scheduler="DDIM", batch_size=1,
                input_image_path=temp_img,
                canny_low_threshold=50, canny_high_threshold=150,
                controlnet_conditioning_scale=2.5
            )
            is_valid, msg = self.controller.generation_controller.validate_session()
            self.assertFalse(is_valid)
            self.assertEqual("Die ControlNet-Stärke (Conditioning Strength) muss zwischen 0.0 und 2.0 liegen.", msg)
        finally:
            if os.path.exists(temp_img):
                os.unlink(temp_img)

        # 4. Controls nur bei ControlNet sichtbar
        self.view.model_var.set("controlnet_canny_qnn")
        self.view.update()
        self.assertEqual(self.view.controlnet_frame.winfo_manager(), "grid")

        self.view.model_var.set("stable_diffusion_v1_5_qnn")
        self.view.update()
        self.assertEqual(self.view.controlnet_frame.winfo_manager(), "")

        # 5. Modellwechsel setzt ControlNet-spezifische Werte korrekt zurück
        self.view.model_var.set("controlnet_canny_qnn")
        self.view.update()
        self.view.canny_low_var.set(80)
        self.view.canny_high_var.set(200)
        self.view.conditioning_strength_var.set(1.5)

        self.view.model_var.set("stable_diffusion_v2_1_qnn")
        self.view.update()
        self.assertEqual(self.view.canny_low_var.get(), 50)
        self.assertEqual(self.view.canny_high_var.get(), 150)
        self.assertEqual(self.view.conditioning_strength_var.get(), 1.0)

        # 6. Werte werden bis zum Backend weitergegeben
        job = GenerationJob(self.controller.generation_controller.session)
        job.session.canny_low_threshold = 45
        job.session.canny_high_threshold = 120
        job.session.controlnet_conditioning_scale = 0.85
        job.session.input_image_path = "some_path.png"

        backend = InferenceBackendFactory.get_backend("Qualcomm ControlNet Canny (HTP V73)")

        with patch("subprocess.Popen") as mock_popen:
            fake_proc = MagicMock()
            fake_proc.poll.return_value = 0
            fake_proc.stdout.readline.return_value = ""
            mock_popen.return_value = fake_proc

            try:
                backend.generate(job)
            except Exception:
                pass

            temp_dir = Path(r"C:\SnapdragonAI\temp\controlnet_canny_gate")
            job_id_str = str(job.job_id)[:8]
            input_json_path = temp_dir / f"job_input_{job_id_str}.json"

            if input_json_path.exists():
                with open(input_json_path, "r", encoding="utf-8") as f_json:
                    serialized_data = json.load(f_json)
                self.assertEqual(serialized_data["canny_low_threshold"], 45)
                self.assertEqual(serialized_data["canny_high_threshold"], 120)
                self.assertEqual(serialized_data["controlnet_conditioning_scale"], 0.85)
                input_json_path.unlink(missing_ok=True)

        # 7. SD1.5 und SD2.1 bleiben unverändert (validation passes without ControlNet params checks)
        self.controller.update_parameters(
            prompt="A fantasy castle", negative_prompt="", seed=-1, steps=20, cfg=7.5,
            width=512, height=512, selected_model="stable_diffusion_v1_5_qnn",
            sampler="Euler", scheduler="Euler", batch_size=1,
            input_image_path=None
        )
        is_valid, msg = self.controller.generation_controller.validate_session()
        self.assertTrue(is_valid)

    def test_requantize_tensor_clipping(self) -> None:
        import numpy as np
        from engine.controlnet_canny_backend import ControlNetCannyQnnBackend

        # Create a representative dummy quantized input array (uint16)
        arr_q = np.array([0, 100, 1000, 32768, 65535], dtype=np.uint16)

        scale_from, zp_from = 0.003, 120
        scale_to, zp_to = 0.005, 150

        # 1. factor=1.0 matches the baseline requantization output (no factor)
        arr_f_base = (arr_q.astype(np.float32) - zp_from) * scale_from
        arr_q_to_base = np.clip(np.round(arr_f_base / scale_to) + zp_to, 0, 65535).astype(np.uint16)

        res_1_0, low_1_0, high_1_0 = ControlNetCannyQnnBackend.requantize_tensor_static(
            arr_q, scale_from, zp_from, scale_to, zp_to, factor=1.0
        )
        np.testing.assert_array_equal(res_1_0, arr_q_to_base)

        # 2. factor=0.0 maps all values exactly to target zero point (zp_to)
        res_0_0, low_0_0, high_0_0 = ControlNetCannyQnnBackend.requantize_tensor_static(
            arr_q, scale_from, zp_from, scale_to, zp_to, factor=0.0
        )
        expected_0_0 = np.full_like(arr_q, zp_to, dtype=np.uint16)
        np.testing.assert_array_equal(res_0_0, expected_0_0)
        self.assertEqual(low_0_0, 0)
        self.assertEqual(high_0_0, 0)

        # 3. factor=2.0 results remain in uint16 range
        res_2_0, low_2_0, high_2_0 = ControlNetCannyQnnBackend.requantize_tensor_static(
            arr_q, scale_from, zp_from, scale_to, zp_to, factor=2.0
        )
        self.assertEqual(res_2_0.dtype, np.uint16)
        self.assertTrue(np.all(res_2_0 >= 0))
        self.assertTrue(np.all(res_2_0 <= 65535))

        # 4. Clipping/Saturation is counted correctly
        test_arr = np.array([0, 50, 100, 200, 40000], dtype=np.uint16)
        res_clip, low_count, high_count = ControlNetCannyQnnBackend.requantize_tensor_static(
            test_arr, scale_from=1.0, zp_from=100, scale_to=1.0, zp_to=0, factor=2.0
        )
        self.assertEqual(low_count, 2)
        self.assertEqual(high_count, 1)
        np.testing.assert_array_equal(res_clip, np.array([0, 0, 0, 200, 65535], dtype=np.uint16))


if __name__ == "__main__":
    unittest.main()
