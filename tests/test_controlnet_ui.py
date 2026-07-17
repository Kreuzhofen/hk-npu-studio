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


if __name__ == "__main__":
    unittest.main()
