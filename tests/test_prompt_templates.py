from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock
import tkinter as tk
from tkinter import ttk

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

# Restore original palette function to avoid polluting other tests
ThemeManager.palette = original_palette_func


class PromptTemplatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        self.controller = PromptWorkspaceController()
        # Stub the controller to return test categories
        self.controller.load_prompt_templates = lambda: {
            "Portrait": [{"name": "Test Portrait", "prompt": "Portrait prompt content"}],
            "Landschaft": [{"name": "Test Landschaft", "prompt": "Landschaft prompt content"}]
        }
        self.view = PhoenixPromptView(self.root, controller=self.controller)

    def tearDown(self) -> None:
        self.view.destroy()

    def test_load_templates_controller(self) -> None:
        templates = self.controller.load_prompt_templates()
        self.assertIn("Portrait", templates)
        self.assertEqual(templates["Portrait"][0]["prompt"], "Portrait prompt content")

    def test_load_template_prompt_view(self) -> None:
        # Initial values
        self.view.prompt_text.delete("1.0", "end")
        self.view.prompt_text.insert("1.0", "Original Prompt")
        self.view.neg_prompt_text.delete("1.0", "end")
        self.view.neg_prompt_text.insert("1.0", "Original Negative Prompt")

        # Load template
        self.view._load_template_prompt("New Template Prompt")

        # Check that main prompt is loaded, and negative prompt is untouched
        self.assertEqual(self.view.prompt_text.get("1.0", "end-1c"), "New Template Prompt")
        self.assertEqual(self.view.neg_prompt_text.get("1.0", "end-1c"), "Original Negative Prompt")

    def test_ensure_progress_style(self) -> None:
        # Call the style enforcement method
        self.view._ensure_progress_style()
        style = ttk.Style(self.root)

        # Check that the custom layout exists
        layout = style.layout("Phoenix.Horizontal.TProgressbar")
        self.assertTrue(len(layout) > 0)

        # Check that configure options match PHOENIX_THEME.success
        background = style.lookup("Phoenix.Horizontal.TProgressbar", "background")
        self.assertEqual(background, PHOENIX_THEME.success)


if __name__ == "__main__":
    unittest.main()
