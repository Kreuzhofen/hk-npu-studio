from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
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
        self.view.neg_prompt_text.delete("1.0", "end")
        self.view.neg_prompt_text.insert("1.0", "No blur")

        # Open popup
        self.view._open_expandable_prompt_popup()
        self.assertTrue(hasattr(self.view, "_prompt_popup"))
        self.assertTrue(self.view._prompt_popup.winfo_exists())

        # Verify initial text was synchronized
        popup_text_content = self.view._prompt_popup_text.get("1.0", "end-1c")
        self.assertEqual(popup_text_content, "Hello Test")
        negative_popup_content = self.view._negative_prompt_popup_text.get("1.0", "end-1c")
        self.assertEqual(negative_popup_content, "No blur")

        # Update popup text and verify main text updates via direct sync method invocation
        self.view._prompt_popup_text.insert("end", " Extra")
        self.view._negative_prompt_popup_text.insert("end", ", no artifacts")
        self.view._sync_popup_prompt_to_main()

        main_text_content = self.view.prompt_text.get("1.0", "end-1c")
        self.assertEqual(main_text_content, "Hello Test Extra")
        self.assertEqual(
            self.view.neg_prompt_text.get("1.0", "end-1c"),
            "No blur, no artifacts",
        )

        # Update main prompt text and verify popup text updates via direct sync method invocation
        self.view.prompt_text.insert("end", " More")
        self.view._sync_main_prompt_to_popup()

        popup_text_content = self.view._prompt_popup_text.get("1.0", "end-1c")
        self.assertEqual(popup_text_content, "Hello Test Extra More")

        self.view.neg_prompt_text.insert("end", ", no noise")
        self.view._sync_main_prompt_to_popup()
        self.assertEqual(
            self.view._negative_prompt_popup_text.get("1.0", "end-1c"),
            "No blur, no artifacts, no noise",
        )

        # Close popup
        self.view._prompt_popup.destroy()
        self.assertFalse(self.view._prompt_popup.winfo_exists())

    def test_escape_applies_both_prompt_values(self) -> None:
        self.view._open_expandable_prompt_popup()
        self.view._prompt_popup_text.delete("1.0", "end")
        self.view._prompt_popup_text.insert("1.0", "Applied prompt")
        self.view._negative_prompt_popup_text.delete("1.0", "end")
        self.view._negative_prompt_popup_text.insert("1.0", "Applied negative")

        self.view._prompt_popup.focus_force()
        self.root.update()
        self.view._prompt_popup.event_generate("<Escape>")
        self.root.update()

        self.assertEqual(self.view.prompt_text.get("1.0", "end-1c"), "Applied prompt")
        self.assertEqual(
            self.view.neg_prompt_text.get("1.0", "end-1c"), "Applied negative"
        )
        self.assertFalse(self.view._prompt_popup.winfo_exists())

    def test_old_preset_uses_model_defaults_for_missing_fields(self) -> None:
        self.view.seed_var.set("987")
        self.view.batch_var.set("8")
        self.view.neg_prompt_text.delete("1.0", "end")
        self.view.neg_prompt_text.insert("1.0", "stale negative")

        self.view.apply_generation_settings({"prompt": "Legacy prompt"})

        contract = self.controller.get_generation_parameters(self.view.model_var.get())
        self.assertEqual(self.view.prompt_text.get("1.0", "end-1c"), "Legacy prompt")
        self.assertEqual(self.view.neg_prompt_text.get("1.0", "end-1c"), "")
        self.assertEqual(self.view.seed_var.get(), str(contract["seed"]["default"]))
        self.assertEqual(self.view.batch_var.get(), "1")
        self.assertEqual(self.view.steps_var.get(), contract["steps"]["default"])
        self.assertEqual(self.view.cfg_var.get(), contract["cfg"]["default"])

    def test_existing_preset_is_not_overwritten_when_declined(self) -> None:
        manager = MagicMock()
        manager.preset_exists.return_value = True
        self.view.preset_manager = manager

        with patch("tkinter.simpledialog.askstring", return_value="Existing"), patch(
            "tkinter.messagebox.askyesno", return_value=False
        ) as ask_overwrite:
            self.view._on_save_preset()

        ask_overwrite.assert_called_once()
        manager.save_preset.assert_not_called()

    def test_complete_preset_is_collected_and_loaded(self) -> None:
        manager = MagicMock()
        manager.preset_exists.return_value = False
        manager.save_preset.return_value = True
        manager.list_presets.return_value = ["complete"]
        manager.preset_key.return_value = "complete"
        self.view.preset_manager = manager

        self.view.prompt_text.delete("1.0", "end")
        self.view.prompt_text.insert("1.0", "Complete prompt")
        self.view.neg_prompt_text.delete("1.0", "end")
        self.view.neg_prompt_text.insert("1.0", "Complete negative")
        self.view.seed_var.set("12345")
        self.view.width_var.set("512")
        self.view.height_var.set("512")
        self.view.steps_var.set(33)
        self.view.cfg_var.set(7.5)
        self.view.sampler_var.set("Euler")
        self.view.scheduler_var.set("Euler")
        self.view.batch_var.set("4")
        self.view.canny_supported = True
        self.view.active_tab = "canny"
        self.view.canny_low_var.set(40)
        self.view.canny_high_var.set(140)
        self.view.conditioning_strength_var.set(0.75)
        self.view._ref_image_path = "C:/images/reference.png"

        with patch("tkinter.simpledialog.askstring", return_value="Complete"), patch(
            "tkinter.messagebox.showinfo"
        ) as success_popup:
            self.view._on_save_preset()

        success_popup.assert_not_called()
        saved = manager.save_preset.call_args.args[1]
        expected_keys = {
            "prompt", "negative_prompt", "model_name", "backend", "seed",
            "width", "height", "steps", "cfg_scale", "sampler", "scheduler",
            "batch", "controlnet_enabled", "canny_low_threshold",
            "canny_high_threshold", "controlnet_conditioning_scale",
            "reference_image_path",
        }
        self.assertEqual(set(saved), expected_keys)
        self.assertEqual(saved["prompt"], "Complete prompt")
        self.assertEqual(saved["negative_prompt"], "Complete negative")
        self.assertEqual(saved["seed"], 12345)
        self.assertEqual(saved["batch"], 4)
        self.assertEqual(saved["canny_low_threshold"], 40)
        self.assertEqual(saved["canny_high_threshold"], 140)
        self.assertEqual(saved["controlnet_conditioning_scale"], 0.75)

        self.view.apply_generation_settings(saved)
        self.assertEqual(self.view.prompt_text.get("1.0", "end-1c"), "Complete prompt")
        self.assertEqual(
            self.view.neg_prompt_text.get("1.0", "end-1c"), "Complete negative"
        )
        self.assertEqual(self.view.seed_var.get(), "12345")
        self.assertEqual(self.view.batch_var.get(), "4")


if __name__ == "__main__":
    unittest.main()
