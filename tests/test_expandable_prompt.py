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


class ExpandablePromptTests(unittest.TestCase):
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
        if hasattr(self.view, "_prompt_popup") and self.view._prompt_popup.winfo_exists():
            self.view._prompt_popup.destroy()

    def test_maximize_button_exists(self) -> None:
        self.assertTrue(hasattr(self.view, "maximize_btn"))
        self.assertTrue(self.view.maximize_btn.winfo_manager() != "")

    def test_open_expandable_prompt_popup(self) -> None:
        # Initial text in main prompt
        self.view.prompt_text.delete("1.0", "end")
        self.view.prompt_text.insert("1.0", "Hello Test")

        # Open popup
        self.view._open_expandable_prompt_popup()
        self.assertTrue(hasattr(self.view, "_prompt_popup"))
        self.assertTrue(self.view._prompt_popup.winfo_exists())

        # Verify initial text was synchronized
        popup_text_content = self.view._prompt_popup_text.get("1.0", "end-1c")
        self.assertEqual(popup_text_content, "Hello Test")

        # Update popup text and verify main text updates via direct sync method invocation
        self.view._prompt_popup_text.insert("end", " Extra")
        self.view._sync_popup_prompt_to_main()

        main_text_content = self.view.prompt_text.get("1.0", "end-1c")
        self.assertEqual(main_text_content, "Hello Test Extra")

        # Update main prompt text and verify popup text updates via direct sync method invocation
        self.view.prompt_text.insert("end", " More")
        self.view._sync_main_prompt_to_popup()

        popup_text_content = self.view._prompt_popup_text.get("1.0", "end-1c")
        self.assertEqual(popup_text_content, "Hello Test Extra More")

        # Close popup
        self.view._prompt_popup.destroy()
        self.assertFalse(self.view._prompt_popup.winfo_exists())


if __name__ == "__main__":
    unittest.main()
