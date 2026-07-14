from __future__ import annotations

import unittest
from unittest.mock import MagicMock
import tkinter as tk

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


class QualityPresetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        self.controller = PromptWorkspaceController()
        self.view = PhoenixPromptView(self.root, controller=self.controller)

    def tearDown(self) -> None:
        self.view.destroy()

    def test_preset_toggles_correct_steps_values(self) -> None:
        # Select Schnell preset
        self.view._select_steps_preset("Schnell")
        self.assertEqual(self.view.active_steps_preset, "Schnell")
        self.assertEqual(self.view.steps_scale.get(), 10)

        # Select Standard preset
        self.view._select_steps_preset("Standard")
        self.assertEqual(self.view.active_steps_preset, "Standard")
        self.assertEqual(self.view.steps_scale.get(), 20)

        # Select Beste Qualität preset
        self.view._select_steps_preset("Beste Qualität")
        self.assertEqual(self.view.active_steps_preset, "Beste Qualität")
        self.assertEqual(self.view.steps_scale.get(), 30)

    def test_apply_generation_contract_toggles_visibility(self) -> None:
        # Mock contracts
        locked_contract = {"resolution_locked": True, "steps": {"default": 20, "min": 1, "max": 100}}
        unlocked_contract = {"resolution_locked": False, "steps": {"default": 20, "min": 1, "max": 100}}

        # Stub select_model to return locked contract
        self.controller.select_model = lambda mid: locked_contract
        self.view._apply_generation_contract("stable_diffusion_v1_5_qnn")

        # Verify preset frame is visible and scale is hidden
        self.assertTrue(self.view.steps_preset_frame.winfo_manager() != "")
        self.assertTrue(self.view.steps_scale.winfo_manager() == "")

        # Stub select_model to return unlocked contract
        self.controller.select_model = lambda mid: unlocked_contract
        self.view._apply_generation_contract("sdxl_base")

        # Verify scale is visible and preset frame is hidden
        self.assertTrue(self.view.steps_preset_frame.winfo_manager() == "")
        self.assertTrue(self.view.steps_scale.winfo_manager() != "")


if __name__ == "__main__":
    unittest.main()
