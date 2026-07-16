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


if __name__ == "__main__":
    unittest.main()
