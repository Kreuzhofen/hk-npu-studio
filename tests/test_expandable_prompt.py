from __future__ import annotations

import unittest
import json
from pathlib import Path
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
from engine.boost_engine import PhoenixBoostEngine
from engine.ollama_status import OllamaStatus, OllamaStatusService
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
        if hasattr(self.view, "_boost_popup") and self.view._boost_popup.winfo_exists():
            self.view._boost_popup.destroy()
        self.view.destroy()
        if hasattr(self.view, "_prompt_popup") and self.view._prompt_popup.winfo_exists():
            self.view._prompt_popup.destroy()

    def test_maximize_button_exists(self) -> None:
        self.assertTrue(hasattr(self.view, "maximize_btn"))
        self.assertTrue(self.view.maximize_btn.winfo_manager() != "")

    def test_boost_button_uses_snapdragon_green(self) -> None:
        self.assertEqual(self.view.boost_btn.cget("bg"), PHOENIX_THEME.success)
        self.assertEqual(self.view.boost_btn.cget("fg"), PHOENIX_THEME.text_on_accent)

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

    def test_boost_languages_and_model_profiles(self) -> None:
        cases = (
            ("Ein Porträt einer Frau mit natürlichem Licht", "sd15", "de", "portrait"),
            ("A product photograph of a red shoe", "stable-diffusion-2.1", "en", "product"),
            ("Un paisaje de montaña con luz natural", "sdxl_base", "es", "landscape"),
        )
        for prompt, model, language, motif in cases:
            suggestion = PhoenixBoostEngine.suggest(prompt, "", model, 20, 6.0, 512, 512)
            self.assertEqual(suggestion.language, language)
            self.assertEqual(suggestion.motif, motif)
            self.assertTrue(suggestion.optimized_prompt)
        self.assertEqual(PhoenixBoostEngine.suggest("photo", "", "sd15", 20, 7, 512, 512).model_profile, "sd15")
        self.assertEqual(PhoenixBoostEngine.suggest("photo", "", "sd2.1", 20, 7, 512, 512).model_profile, "sd21")
        self.assertEqual(PhoenixBoostEngine.suggest("photo", "", "sdxl", 20, 7, 512, 512).model_profile, "sdxl")

    def test_boost_empty_prompt_and_existing_negative(self) -> None:
        with self.assertRaisesRegex(ValueError, "prompt_empty"):
            PhoenixBoostEngine.suggest("  ", "", "sdxl", 20, 7, 512, 512)
        suggestion = PhoenixBoostEngine.suggest("A portrait", "grain", "sdxl", 20, 7, 512, 512)
        self.assertEqual(suggestion.existing_negative_prompt, "grain")
        self.assertTrue(suggestion.recommended_negative_prompt.startswith("grain, "))

    @patch("engine.ollama_status.urlopen")
    @patch("engine.ollama_status.shutil.which", return_value="C:/Ollama/ollama.exe")
    def test_ollama_available(self, _which, open_url) -> None:
        response = MagicMock(status=200)
        open_url.return_value.__enter__.return_value = response
        status = OllamaStatusService.detect()
        self.assertTrue(status.installed)
        self.assertTrue(status.available)

    @patch("engine.ollama_status.urlopen")
    @patch("engine.ollama_status.shutil.which", return_value=None)
    def test_ollama_missing_keeps_standard_boost_available(self, _which, open_url) -> None:
        open_url.side_effect = OSError("not reachable")
        status = OllamaStatusService.detect()
        self.assertFalse(status.available)
        open_url.assert_called_once()
        suggestion = PhoenixBoostEngine.suggest("one red car", "", "sdxl", 20, 7, 512, 512)
        self.assertTrue(suggestion.optimized_prompt)

    def test_missing_ollama_hint_is_visible_and_boost_still_works(self) -> None:
        self.view.prompt_text.delete("1.0", "end")
        self.view.prompt_text.insert("1.0", "one red car")
        with patch.object(
            OllamaStatusService, "detect", return_value=OllamaStatus(False, False)
        ):
            self.view._open_boost_preview()

        def widget_texts(widget):
            values = []
            try:
                values.append(str(widget.cget("text")))
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                values.extend(widget_texts(child))
            return values

        texts = widget_texts(self.view._boost_popup)
        self.assertIn("Phoenix Boost AI", texts)
        self.assertIn("Ollama nicht installiert", texts)
        self.assertIn("Ollama installieren", texts)
        self.assertTrue(self.view._boost_suggestion.optimized_prompt)

    def test_boost_cancel_changes_nothing(self) -> None:
        self.view.prompt_text.insert("1.0", "A mountain landscape")
        before = self.view.prompt_text.get("1.0", "end-1c")
        self.view._open_boost_preview()
        self.view._boost_popup.destroy()
        self.assertEqual(self.view.prompt_text.get("1.0", "end-1c"), before)

    def test_boost_apply_preserves_seed_and_requires_negative_confirmation(self) -> None:
        self.view.prompt_text.delete("1.0", "end")
        self.view.neg_prompt_text.delete("1.0", "end")
        self.view.prompt_text.insert("1.0", "A portrait photograph")
        self.view.neg_prompt_text.insert("1.0", "existing negative")
        self.view.seed_var.set("12345")
        self.view._open_boost_preview()
        self.view._boost_apply_negative_var.set(False)
        self.view._apply_boost_suggestion()
        self.assertEqual(self.view.seed_var.get(), "12345")
        self.assertEqual(self.controller.model.state.seed, 12345)
        self.assertEqual(self.view.neg_prompt_text.get("1.0", "end-1c"), "existing negative")
        self.assertIn("realistic photography", self.view.prompt_text.get("1.0", "end-1c"))

    def test_boost_extracts_giraffe_relationships_in_three_languages(self) -> None:
        prompts = (
            "Eine Giraffe hält einen roten Heliumballon im Maul.",
            "One giraffe holds the string of a red helium balloon in its mouth.",
            "Una jirafa sostiene la cuerda de un globo de helio rojo en la boca.",
        )
        for prompt in prompts:
            suggestion = PhoenixBoostEngine.suggest(prompt, "", "sdxl", 20, 7, 512, 512)
            self.assertEqual(suggestion.analysis.main_object, "giraffe")
            self.assertEqual(suggestion.analysis.count, 1)
            self.assertIn("holding", suggestion.analysis.actions)
            self.assertIn("red", suggestion.analysis.colors)
            self.assertIn("one giraffe in the foreground", suggestion.optimized_prompt)
            self.assertIn("holding the string in its mouth", suggestion.optimized_prompt)
            self.assertIn("one red helium balloon floating above", suggestion.optimized_prompt)

    def test_boost_preserves_multiple_objects_and_background_relation(self) -> None:
        prompt = "One giraffe holds a red balloon, two people laughing in the background."
        suggestion = PhoenixBoostEngine.suggest(prompt, "", "sdxl", 20, 7, 512, 512)
        self.assertIn("one giraffe in the foreground", suggestion.optimized_prompt)
        self.assertIn("two people laughing in the background", suggestion.optimized_prompt)
        self.assertIn("people laughing in the background", suggestion.analysis.relationships)
        self.assertEqual(suggestion.analysis.environment, "in the background")
        self.assertEqual(suggestion.analysis.style, "realistic photography")

    def test_controlnet_prevents_boost_resolution_change(self) -> None:
        self.view.prompt_text.insert("1.0", "A landscape photograph")
        self.view.canny_supported = True
        self.view.active_tab = "canny"
        self.view._open_boost_preview()
        self.view._boost_apply_resolution_var.set(True)
        self.view._apply_boost_suggestion()
        self.assertEqual((self.view.width_var.get(), self.view.height_var.get()), ("512", "512"))

    def test_boost_locale_keys_are_complete(self) -> None:
        root = Path(__file__).resolve().parents[1]
        required = {
            "boost_button", "boost_tooltip", "boost_title", "boost_preview_title",
            "boost_empty_prompt", "boost_original_prompt", "boost_optimized_prompt",
            "boost_existing_negative", "boost_negative_addition", "boost_none",
            "boost_current", "boost_recommended", "boost_model_hint",
            "boost_steps", "boost_cfg", "boost_resolution",
            "boost_apply_negative", "boost_apply_resolution",
            "boost_resolution_controlnet_locked", "boost_resolution_model_locked",
            "boost_ai_available", "boost_ai_info", "boost_install_ollama",
            "boost_ai_title", "boost_ollama_not_installed", "boost_ollama_not_available",
        }
        for locale in ("de_DE.json", "en_US.json", "es_ES.json"):
            data = json.loads((root / "locales" / locale).read_text(encoding="utf-8"))
            self.assertTrue(required.issubset(data), locale)


if __name__ == "__main__":
    unittest.main()
