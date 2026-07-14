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


class AdvancedPopupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        self.controller = PromptWorkspaceController()
        # Ensure COMPACT_PREVIEW_MODE is True
        PhoenixPromptView.COMPACT_PREVIEW_MODE = True
        self.view = PhoenixPromptView(self.root, controller=self.controller)

    def tearDown(self) -> None:
        self.view.destroy()
        if hasattr(self.view, "_advanced_popup") and self.view._advanced_popup.winfo_exists():
            self.view._advanced_popup.destroy()

    def test_compact_mode_grids_correctly(self) -> None:
        # Re-apply contract with compact mode True
        self.view._apply_generation_contract("stable_diffusion_v1_5_qnn")

        # Verify advanced widgets are hidden
        self.assertTrue(self.view.size_frame.winfo_manager() == "")
        self.assertTrue(self.view.dropdown_frame.winfo_manager() == "")
        self.assertTrue(self.view.output_frame.winfo_manager() == "")
        self.assertTrue(self.view.cfg_scale.winfo_manager() == "")

        # Verify advanced button is visible
        self.assertTrue(self.view.adv_settings_btn.winfo_manager() != "")

    def test_open_and_close_popup(self) -> None:
        # Open popup
        self.view._open_advanced_settings_popup()
        self.assertTrue(hasattr(self.view, "_advanced_popup"))
        self.assertTrue(self.view._advanced_popup.winfo_exists())

        # Verify it has some child widgets
        children = self.view._advanced_popup.winfo_children()
        self.assertTrue(len(children) > 0)

        # Close popup
        self.view._advanced_popup.destroy()
        self.assertFalse(self.view._advanced_popup.winfo_exists())

    def test_legacy_mode_grids_correctly(self) -> None:
        # Switch to legacy layout mode
        self.view.COMPACT_PREVIEW_MODE = False
        self.view._apply_generation_contract("stable_diffusion_v1_5_qnn")

        # Verify advanced widgets are visible
        self.assertTrue(self.view.size_frame.winfo_manager() != "")
        self.assertTrue(self.view.dropdown_frame.winfo_manager() != "")
        self.assertTrue(self.view.output_frame.winfo_manager() != "")

        # Verify advanced button is hidden
        self.assertTrue(self.view.adv_settings_btn.winfo_manager() == "")


if __name__ == "__main__":
    unittest.main()
