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


class PromptCounterTests(unittest.TestCase):
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

    def test_main_counter_updates(self) -> None:
        # Initial check
        self.view.prompt_text.delete("1.0", "end")
        self.view.prompt_text.insert("1.0", "Hello World")
        self.view._update_prompt_counters()

        # Check label text
        self.assertEqual(self.view.prompt_counter_lbl.cget("text"), "Zeichen: 11 | Wörter: 2")

        # Update text
        self.view.prompt_text.insert("end", " Test python")
        self.view._update_prompt_counters()
        self.assertEqual(self.view.prompt_counter_lbl.cget("text"), "Zeichen: 23 | Wörter: 4")

    def test_popup_counter_updates_and_syncs(self) -> None:
        self.view.prompt_text.delete("1.0", "end")
        self.view.prompt_text.insert("1.0", "Popup Sync")
        self.view._update_prompt_counters()

        # Open popup
        self.view._open_expandable_prompt_popup()

        # Verify popup counter text matches initial
        self.assertEqual(self.view.popup_counter_lbl.cget("text"), "Zeichen: 10 | Wörter: 2")

        # Simulate typing in popup text area
        self.view._prompt_popup_text.insert("end", " Extra words")
        self.view._sync_popup_prompt_to_main()

        # Verify both counters sync to the new count
        self.assertEqual(self.view.prompt_counter_lbl.cget("text"), "Zeichen: 22 | Wörter: 4")
        self.assertEqual(self.view.popup_counter_lbl.cget("text"), "Zeichen: 22 | Wörter: 4")


if __name__ == "__main__":
    unittest.main()
