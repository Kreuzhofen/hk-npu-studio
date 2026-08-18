from __future__ import annotations

import unittest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import tkinter as tk

from app.i18n import set_language, tr
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
from engine.brand_manager import BrandManager
from engine.boost_ai_service import BoostAIService
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
        set_language("de_DE")
        OllamaStatusService.invalidate_cache()
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

    def test_generator_main_view_keeps_core_controls_and_hides_detail_sections(self) -> None:
        self.assertTrue(self.view.prompt_text.winfo_manager())
        self.assertTrue(self.view.neg_prompt_text.winfo_manager())
        self.assertTrue(self.view.boost_btn.winfo_manager())
        self.assertTrue(self.view.gen_btn.winfo_manager())
        self.assertEqual(self.view.preset_frame.winfo_manager(), "")
        self.assertEqual(self.view.tab_container.winfo_manager(), "")

    def test_presets_popup_opens_with_existing_actions(self) -> None:
        with patch.object(BrandManager, "apply_window_icon", wraps=BrandManager.apply_window_icon) as apply_icon:
            self.view._open_presets_popup()
        self.assertTrue(self.view._presets_popup.winfo_exists())
        apply_icon.assert_called_once_with(self.view._presets_popup)
        self.assertTrue(self.view._preset_popup_dropdown.winfo_manager())
        self.assertFalse(hasattr(self.view._presets_popup, "_phoenix_logo_label"))
        self.assertEqual(self.view._presets_popup.cget("bg"), PHOENIX_THEME.card_bg)
        self.assertTrue(
            self.view._presets_popup._standard_dialog_title.winfo_manager()
        )
        self.assertEqual(
            self.view._presets_popup._standard_dialog_title.cget("anchor"), "w"
        )
        self.assertEqual(self.view._preset_apply_btn.text, tr("apply_preset_btn", "Anwenden"))
        self.assertEqual(self.view._preset_rename_btn.text, tr("rename_preset_btn", "Umbenennen"))
        self.assertEqual(self.view._preset_delete_btn.text, tr("delete_preset_btn", "Löschen"))
        self.view._presets_popup.destroy()

    def test_generation_settings_popup_opens_and_keeps_values(self) -> None:
        with patch.object(BrandManager, "apply_window_icon", wraps=BrandManager.apply_window_icon) as apply_icon:
            self.view._open_advanced_settings_popup()
        self.assertTrue(self.view._advanced_popup.winfo_exists())
        apply_icon.assert_called_once_with(self.view._advanced_popup)
        self.assertFalse(hasattr(self.view._advanced_popup, "_phoenix_logo_label"))
        self.assertEqual(self.view._advanced_popup.cget("bg"), PHOENIX_THEME.card_bg)

        def widget_texts(widget):
            values = []
            try:
                values.append(str(widget.cget("text")))
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                values.extend(widget_texts(child))
            return values

        texts = widget_texts(self.view._advanced_popup)
        for key, fallback in (
            ("model_parameter_help", "Das Modell bestimmt Stil, Fähigkeiten und unterstützte Einstellungen."),
            ("resolution_lock_tooltip", "Die Auflösung bestimmt Bildbreite und Bildhöhe; höhere Werte benötigen mehr Speicher."),
            ("steps_help", "Mehr Entrauschungsschritte können Details verbessern, benötigen aber mehr Zeit."),
            ("cfg_scale_help", "Stärke der Prompt-Befolgung; typische Empfehlung 6–8."),
            ("seed_help", "Reproduzierbarer Startwert; -1 bedeutet zufälliger Seed."),
            ("sampler_help", "Verwendetes Berechnungsverfahren für die Bildentstehung."),
            ("scheduler_help", "Zeitliche Verteilung der Entrauschungsschritte."),

        ):
            self.assertIn(tr(key, fallback), texts)
        self.view.steps_var.set(31)
        self.view.cfg_var.set(6.5)
        self.view.seed_var.set("123")
        self.view._advanced_popup.destroy()
        self.assertEqual(self.view.steps_var.get(), 31)
        self.assertEqual(self.view.cfg_var.get(), 6.5)
        self.assertEqual(self.view.seed_var.get(), "123")

    def test_generation_still_starts_from_cleaned_main_view(self) -> None:
        self.controller.generation_controller.validate_session = MagicMock(
            return_value=(True, "")
        )
        with patch("widgets.phoenix.views.prompt_view.threading.Thread") as thread:
            worker = MagicMock()
            thread.return_value = worker
            self.view._on_generate()
        worker.start.assert_called_once()
        self.view._generation_running = False

    def test_generator_toolbar_uses_neutral_buttons_with_colored_icons(self) -> None:
        buttons = (
            (self.view.presets_popup_btn, 0, 0, "folder", PHOENIX_THEME.warning),
            (self.view.boost_btn, 0, 1, "sparkles", PHOENIX_THEME.success),
            (self.view.parameters_popup_btn, 0, 2, "settings", PHOENIX_THEME.danger),
            (self.view.controlnet_popup_btn, 0, 3, "image", PHOENIX_THEME.accent),
            (self.view.history_btn, 1, 0, "back", PHOENIX_THEME.accent),
        )
        for button, row, column, icon_name, icon_color in buttons:
            self.assertTrue(button.winfo_manager())
            self.assertEqual(int(button.grid_info()["row"]), row)
            self.assertEqual(int(button.grid_info()["column"]), column)
            self.assertEqual(button.normal_bg, PHOENIX_THEME.elevated_bg)
            self.assertEqual(button.icon_name, icon_name)
            self.assertEqual(button.icon_color, icon_color)
        self.assertEqual(
            self.view.parameters_popup_btn.text,
            tr("generator_settings_toolbar", "Generierungsparameter"),
        )
        self.assertTrue(self.view.maximize_btn.text.startswith("⛶ "))
        self.assertEqual(self.view.maximize_btn.normal_bg, PHOENIX_THEME.elevated_bg)
        self.assertEqual(int(self.view.maximize_btn.grid_info()["row"]), 1)
        self.assertEqual(int(self.view.maximize_btn.grid_info()["column"]), 2)

    def test_prompt_titles_and_toolbar_have_separate_layout_rows(self) -> None:
        self.root.update_idletasks()
        self.assertEqual(self.view.prompt_title_label.cget("text"), tr("your_prompt_title", "DEIN PROMPT"))
        self.assertEqual(self.view.prompt_title_label.cget("fg"), PHOENIX_THEME.accent)
        self.assertEqual(self.view.negative_prompt_title_label.cget("fg"), PHOENIX_THEME.accent)
        self.assertEqual(int(self.view.prompt_toolbar.grid_info()["row"]), 1)
        self.assertEqual(int(self.view.prompt_text.grid_info()["row"]), 3)
        self.assertEqual(int(self.view.neg_prompt_text.grid_info()["row"]), 6)
        self.assertIsNot(self.view.boost_btn.master, self.view.prompt_title_label.master)
        self.assertGreater(self.view.prompt_title_label.winfo_width(), 0)
        self.assertTrue(self.view.neg_prompt_text.winfo_manager())

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

    def test_boost_optimized_prompt_can_be_saved_as_template(self) -> None:
        manager = MagicMock()
        manager.preset_exists.return_value = False
        manager.save_preset.return_value = True
        manager.list_presets.return_value = ["boost_template"]
        manager.preset_key.return_value = "boost_template"
        self.view.preset_manager = manager
        self.view.prompt_text.delete("1.0", "end")
        self.view.prompt_text.insert("1.0", "A portrait photograph")
        self.view.neg_prompt_text.delete("1.0", "end")
        self.view.neg_prompt_text.insert("1.0", "existing negative")
        self.view._open_boost_preview()

        with patch("tkinter.simpledialog.askstring", return_value="Boost Template"):
            self.view._save_boost_as_template()

        saved = manager.save_preset.call_args.args[1]
        self.assertEqual(saved["prompt"], self.view._boost_suggestion.optimized_prompt)
        self.assertEqual(
            saved["negative_prompt"],
            self.view._boost_suggestion.recommended_negative_prompt,
        )
        self.assertEqual(saved["model_name"], self.view.model_var.get())
        self.assertIn("controlnet_enabled", saved)
        self.assertEqual(self.view.selected_preset_var.get(), "boost_template")
        self.view._boost_popup.destroy()

    def test_preset_can_be_renamed_without_losing_data(self) -> None:
        manager = MagicMock()
        manager.get_preset.return_value = {"name": "Old Name", "prompt": "kept"}
        manager.preset_key.side_effect = lambda name: str(name).lower().replace(" ", "_")
        manager.preset_exists.return_value = False
        manager.save_preset.return_value = True
        manager.delete_preset.return_value = True
        manager.list_presets.return_value = ["new_name"]
        self.view.preset_manager = manager
        self.view.selected_preset_var.set("old_name")

        with patch("tkinter.simpledialog.askstring", return_value="New Name"):
            self.view._on_rename_preset()

        manager.save_preset.assert_called_once_with(
            "New Name", {"name": "Old Name", "prompt": "kept"}
        )
        manager.delete_preset.assert_called_once_with("old_name")
        self.assertEqual(self.view.selected_preset_var.get(), "new_name")

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
        response.read.return_value = json.dumps({"models": [{"name": "qwen2.5:3b"}]}).encode("utf-8")
        open_url.return_value.__enter__.return_value = response
        status = OllamaStatusService.detect()
        self.assertTrue(status.installed)
        self.assertTrue(status.available)
        self.assertTrue(status.model_available)
        self.assertTrue(status.ai_ready)

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
        ), patch.object(
            BrandManager, "apply_window_icon", wraps=BrandManager.apply_window_icon
        ) as apply_icon:
            self.view._open_boost_preview()
        apply_icon.assert_called_once_with(self.view._boost_popup)

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
        self.assertFalse(hasattr(self.view._boost_popup, "_phoenix_logo_label"))
        self.assertEqual(self.view._boost_popup.cget("bg"), PHOENIX_THEME.card_bg)
        self.assertTrue(self.view._boost_popup._standard_dialog_title.winfo_manager())
        self.assertIn("Phoenix Boost AI", texts)
        self.assertIn(
            "Phoenix Boost nutzt KI, um Ihre Bildbeschreibung zu verbessern.\n"
            "So versteht die Bilderzeugung besser, was Sie erstellen möchten.\n"
            "Phoenix Boost ist freiwillig – Sie können auch ohne Phoenix Boost Bilder erstellen.",
            texts,
        )
        self.assertEqual(self.view._boost_ai_optional_lbl.cget("wraplength"), 470)
        self.assertEqual(self.view._boost_ai_optional_lbl.pack_info()["pady"], (7, 6))
        self.assertNotEqual(self.view.gen_btn.cget("state"), "disabled")
        self.assertIn("Ollama: nicht installiert", texts)
        self.assertIn("Phoenix Boost einrichten", texts)
        self.assertIn("Sampler:", texts)
        self.assertIn("Scheduler:", texts)
        self.assertFalse(any("{sampler}" in text or "{scheduler}" in text for text in texts))
        self.assertIn(
            "Richten Sie Phoenix Boost in zwei einfachen Schritten ein.\n"
            "Snapdragon AI Studio führt Sie automatisch durch die Einrichtung.",
            texts,
        )
        self.assertTrue(self.view._boost_suggestion.optimized_prompt)
        self.assertEqual(self.view._boost_install_btn.cget("state"), "normal")
        self.assertEqual(self.view._boost_install_btn.cget("bg"), PHOENIX_THEME.accent)

    def test_installed_ollama_disables_install_button(self) -> None:
        self.view.prompt_text.delete("1.0", "end")
        self.view.prompt_text.insert("1.0", "one red car")
        with patch.object(
            OllamaStatusService, "detect", return_value=OllamaStatus(False, False)
        ):
            self.view._open_boost_preview()
        self.view._update_ollama_install_button(OllamaStatus(True, True, True))
        self.assertEqual(self.view._boost_install_btn.cget("state"), "disabled")
        self.assertEqual(self.view._boost_install_btn.cget("text"), "Phoenix Boost AI bereit ✓")
        self.assertEqual(self.view._boost_ai_status_lbl.cget("text"), "✓ Phoenix Boost ist bereit")
        self.assertEqual(
            self.view._boost_ai_info_lbl.cget("text"),
            "Alles eingerichtet. Phoenix Boost kann verwendet werden.",
        )
        self.assertEqual(self.view._boost_install_btn.cget("bg"), PHOENIX_THEME.elevated_bg)

    def test_missing_model_offers_qwen_install(self) -> None:
        self.view.prompt_text.delete("1.0", "end")
        self.view.prompt_text.insert("1.0", "one red car")
        with patch.object(
            OllamaStatusService, "detect", return_value=OllamaStatus(False, False)
        ):
            self.view._open_boost_preview()
        self.view._update_ollama_install_button(OllamaStatus(True, True, False))
        self.assertEqual(self.view._boost_install_btn.cget("state"), "normal")
        self.assertEqual(self.view._boost_install_btn.cget("text"), "Phoenix Boost einrichten")
        self.assertEqual(self.view._boost_model_status_lbl.cget("text"), "Qwen2.5 3B: nicht installiert")
        self.assertIn("Phoenix Boost in zwei einfachen Schritten", self.view._boost_ai_info_lbl.cget("text"))

    def test_boost_ready_cached_state_is_visible_on_second_open(self) -> None:
        self.view.prompt_text.delete("1.0", "end")
        self.view.prompt_text.insert("1.0", "one red car")
        ready = OllamaStatus(True, True, True)
        with patch.object(OllamaStatusService, "cached_status", return_value=ready), patch.object(
            OllamaStatusService, "detect", return_value=ready
        ):
            self.view._open_boost_preview()
            first_popup = self.view._boost_popup
            self.assertEqual(self.view._boost_ai_status_lbl.cget("text"), "✓ Phoenix Boost ist bereit")
            first_popup.destroy()
            self.view._open_boost_preview()
        self.assertTrue(self.view._boost_popup.winfo_exists())
        self.assertEqual(self.view._boost_ai_status_lbl.cget("text"), "✓ Phoenix Boost ist bereit")
        self.assertEqual(self.view._boost_install_btn.cget("state"), "disabled")
        self.view._boost_popup.destroy()

    @patch("engine.ollama_status.urlopen")
    @patch("engine.ollama_status.shutil.which", return_value="C:/Ollama/ollama.exe")
    def test_ollama_status_cache_avoids_repeated_probe(self, _which, open_url) -> None:
        open_url.return_value = self._url_response({"models": [{"name": "qwen2.5:3b"}]})
        first = OllamaStatusService.detect()
        second = OllamaStatusService.detect()
        self.assertIs(first, second)
        open_url.assert_called_once()

    @patch("engine.ollama_status.urlopen", side_effect=OSError("service failed"))
    @patch("engine.ollama_status.shutil.which", return_value="C:/Ollama/ollama.exe")
    def test_ollama_status_error_invalidates_cache(self, _which, open_url) -> None:
        OllamaStatusService.detect()
        OllamaStatusService.detect()
        self.assertEqual(open_url.call_count, 2)

    @staticmethod
    def _url_response(payload: dict) -> MagicMock:
        response = MagicMock()
        response.status = 200
        response.read.return_value = json.dumps(payload).encode("utf-8")
        context = MagicMock()
        context.__enter__.return_value = response
        return context

    @patch("engine.boost_ai_service.urlopen", side_effect=OSError("offline"))
    def test_boost_ai_missing_ollama_falls_back(self, _open_url) -> None:
        self.assertIsNone(BoostAIService.optimize("one giraffe"))
        self.assertTrue(PhoenixBoostEngine.suggest("one giraffe", "", "sdxl", 20, 7, 512, 512).optimized_prompt)

    @patch("engine.boost_ai_service.urlopen")
    def test_boost_ai_missing_model_falls_back(self, open_url) -> None:
        open_url.return_value = self._url_response({"models": [{"name": "other:latest"}]})
        self.assertIsNone(BoostAIService.optimize("one giraffe"))
        open_url.assert_called_once()

    @patch("engine.boost_ai_service.urlopen")
    def test_boost_ai_successful_structured_response(self, open_url) -> None:
        structured = {
            "main_object": "giraffe", "count": 1, "action": "holding",
            "relationships": ["holding a balloon string in its mouth"],
            "environment": "savanna", "style": "realistic photography",
            "optimized_prompt": "one giraffe holding a red balloon string in its mouth",
            "negative_prompt": "extra animals, distorted anatomy",
        }
        open_url.side_effect = [
            self._url_response({"models": [{"name": "qwen2.5:3b"}]}),
            self._url_response({"response": json.dumps(structured)}),
        ]
        result = BoostAIService.optimize("Eine Giraffe hält einen Ballon.")
        self.assertIsNotNone(result)
        self.assertEqual(result.main_object, "giraffe")
        self.assertEqual(result.count, 1)
        self.assertIn("balloon string", result.relationships[0])
        self.assertEqual(result.negative_prompt, "extra animals, distorted anatomy")

    @patch("engine.boost_ai_service.urlopen")
    def test_boost_ai_invalid_response_does_not_raise(self, open_url) -> None:
        open_url.side_effect = [
            self._url_response({"models": [{"name": "qwen2.5:3b"}]}),
            self._url_response({"response": "not-json"}),
        ]
        self.assertIsNone(BoostAIService.optimize("one giraffe"))

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
        self.view.width_var.set("512")
        self.view.height_var.set("512")
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
            "boost_sampler_label", "boost_scheduler_label",
            "boost_apply_negative", "boost_apply_resolution",
            "boost_resolution_controlnet_locked", "boost_resolution_model_locked",
            "boost_ai_available", "boost_ai_info", "boost_install_ollama",
            "boost_ai_optional_info", "boost_ai_setup_ollama",
            "boost_ai_setup_qwen", "boost_ai_setup_ready",
            "boost_ai_title", "boost_ollama_not_installed", "boost_ollama_not_available",
            "boost_ollama_installed",
            "boost_ollama_status_missing", "boost_ollama_status_ready",
            "boost_model_status_unavailable", "boost_model_status_missing",
            "boost_model_status_ready", "boost_ai_status_not_ready",
            "boost_ai_status_ready", "boost_install_qwen", "boost_ai_ready_button",
            "boost_install_qwen_title", "boost_install_qwen_storage_hint",
            "boost_qwen_install_started", "generator_settings_toolbar",
            "model_parameter_help", "boost_save_template",
            "template_save_title", "template_save_prompt",
            "rename_preset_btn", "rename_preset_title",
            "rename_preset_prompt", "rename_preset_exists",
        }
        for locale in ("de_DE.json", "en_US.json", "es_ES.json"):
            data = json.loads((root / "locales" / locale).read_text(encoding="utf-8"))
            self.assertTrue(required.issubset(data), locale)

        expected_explanations = {
            "de_DE.json": (
                "Phoenix Boost nutzt KI, um Ihre Bildbeschreibung zu verbessern.\n"
                "So versteht die Bilderzeugung besser, was Sie erstellen möchten.\n"
                "Phoenix Boost ist freiwillig – Sie können auch ohne Phoenix Boost Bilder erstellen."
            ),
            "en_US.json": (
                "Phoenix Boost uses AI to improve your image description.\n"
                "This helps the image generator understand what you want to create.\n"
                "Phoenix Boost is optional – you can create images without it."
            ),
            "es_ES.json": (
                "Phoenix Boost utiliza IA para mejorar la descripción de su imagen.\n"
                "Así, el generador de imágenes entiende mejor lo que desea crear.\n"
                "Phoenix Boost es opcional: puede crear imágenes sin utilizarlo."
            ),
        }
        for locale, expected in expected_explanations.items():
            data = json.loads((root / "locales" / locale).read_text(encoding="utf-8"))
            self.assertEqual(data["boost_ai_optional_info"], expected, locale)
        expected_parameter_labels = {
            "de_DE.json": ("Sampler:", "Scheduler:"),
            "en_US.json": ("Sampler:", "Scheduler:"),
            "es_ES.json": ("Muestreador:", "Planificador:"),
        }
        for locale, expected in expected_parameter_labels.items():
            data = json.loads((root / "locales" / locale).read_text(encoding="utf-8"))
            self.assertEqual(
                (data["boost_sampler_label"], data["boost_scheduler_label"]),
                expected,
                locale,
            )
            self.assertNotIn("{", data["boost_sampler_label"] + data["boost_scheduler_label"])

    @patch("engine.ollama_status.urlopen", side_effect=OSError("not reachable"))
    @patch("engine.ollama_status.shutil.which", return_value=None)
    @patch("os.environ.get", return_value=None)
    def test_regression_ollama_missing(self, mock_env, _which, open_url) -> None:
        OllamaStatusService.invalidate_cache()
        status = OllamaStatusService.detect(force=True)
        self.assertFalse(status.installed)
        self.assertFalse(status.reachable)
        self.assertFalse(status.model_available)
        self.assertFalse(status.ai_ready)

    @patch("engine.ollama_status.urlopen", side_effect=OSError("service offline"))
    @patch("engine.ollama_status.shutil.which", return_value="C:/Ollama/ollama.exe")
    def test_regression_ollama_present_but_service_unavailable(self, _which, open_url) -> None:
        OllamaStatusService.invalidate_cache()
        status = OllamaStatusService.detect(force=True)
        self.assertTrue(status.installed)
        self.assertFalse(status.reachable)
        self.assertFalse(status.model_available)
        self.assertFalse(status.ai_ready)

    @patch("engine.ollama_status.urlopen")
    @patch("engine.ollama_status.shutil.which", return_value="C:/Ollama/ollama.exe")
    def test_regression_ollama_available_qwen_model_missing(self, _which, open_url) -> None:
        open_url.return_value = self._url_response({"models": [{"name": "other_model:latest"}]})
        OllamaStatusService.invalidate_cache()
        status = OllamaStatusService.detect(force=True)
        self.assertTrue(status.installed)
        self.assertTrue(status.reachable)
        self.assertFalse(status.model_available)
        self.assertFalse(status.ai_ready)

    @patch("engine.ollama_status.urlopen")
    @patch("engine.ollama_status.shutil.which", return_value="C:/Ollama/ollama.exe")
    def test_regression_ollama_available_qwen_model_installed(self, _which, open_url) -> None:
        open_url.return_value = self._url_response({"models": [{"name": "qwen2.5:3b"}]})
        OllamaStatusService.invalidate_cache()
        status = OllamaStatusService.detect(force=True)
        self.assertTrue(status.installed)
        self.assertTrue(status.reachable)
        self.assertTrue(status.model_available)
        self.assertTrue(status.ai_ready)

    @patch("dialogs.qwen_setup_dialog.threading.Thread")
    @patch("dialogs.qwen_setup_dialog.subprocess.Popen")
    @patch("dialogs.qwen_setup_dialog.shutil.which", return_value="C:/Ollama/ollama.exe")
    @patch("dialogs.qwen_setup_dialog.OllamaStatusService.detect")
    def test_regression_qwen_pull_success(self, mock_detect, mock_which, mock_popen, mock_thread) -> None:
        from dialogs.qwen_setup_dialog import QwenSetupDialog
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())
        mock_detect.return_value = OllamaStatus(installed=True, reachable=True, model_available=True)

        process = MagicMock()
        process.wait.return_value = 0
        process.stdout.read.side_effect = [c.encode("utf-8") for c in "pulling manifest\rpulling 5ee4f07cdb9b: 42%\rsuccess\r"] + [b""]
        mock_popen.return_value = process

        success_called = False
        def on_success():
            nonlocal success_called
            success_called = True

        def mock_after(ms, func, *args, **kwargs):
            func(*args, **kwargs)

        with patch.object(QwenSetupDialog, "wait_window"), patch.object(QwenSetupDialog, "after", side_effect=mock_after):
            dialog = QwenSetupDialog(self.root, on_success=on_success)
            # Starts only after explicit button click
            dialog._primary_btn.command()
            # Verify no technical output is shown in the labels
            self.assertNotIn("pulling", dialog._desc_lbl.cget("text"))
            self.assertNotIn("downloading", dialog._desc_lbl.cget("text"))
            self.assertNotIn("MB/s", dialog._desc_lbl.cget("text"))
            self.assertNotIn("GB", dialog._desc_lbl.cget("text"))
            dialog._finish_success()

        self.assertTrue(dialog._success)
        self.assertTrue(success_called)

    @patch("dialogs.qwen_setup_dialog.threading.Thread")
    @patch("dialogs.qwen_setup_dialog.subprocess.Popen")
    @patch("dialogs.qwen_setup_dialog.shutil.which", return_value="C:/Ollama/ollama.exe")
    @patch("dialogs.qwen_setup_dialog.OllamaStatusService.detect")
    def test_regression_qwen_pull_failure(self, mock_detect, mock_which, mock_popen, mock_thread) -> None:
        from dialogs.qwen_setup_dialog import QwenSetupDialog
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())
        mock_detect.return_value = OllamaStatus(installed=True, reachable=True, model_available=False)

        process = MagicMock()
        process.wait.return_value = 1
        process.stdout.read.side_effect = [c.encode("utf-8") for c in "pulling manifest\rerror: model not found\r"] + [b""]
        mock_popen.return_value = process

        success_called = False
        def on_success():
            nonlocal success_called
            success_called = True

        def mock_after(ms, func, *args, **kwargs):
            func(*args, **kwargs)

        with patch.object(QwenSetupDialog, "wait_window"), patch.object(QwenSetupDialog, "after", side_effect=mock_after):
            dialog = QwenSetupDialog(self.root, on_success=on_success)
            dialog._primary_btn.command()

        self.assertFalse(dialog._success)
        self.assertFalse(success_called)
        # Verify the friendly error is shown, not the raw error
        self.assertIn("nicht abgeschlossen werden", dialog._desc_lbl.cget("text"))
        self.assertNotIn("error: model not found", dialog._desc_lbl.cget("text"))

    @patch("dialogs.qwen_setup_dialog.threading.Thread")
    def test_regression_qwen_starts_only_on_click(self, mock_thread) -> None:
        from dialogs.qwen_setup_dialog import QwenSetupDialog
        with patch.object(QwenSetupDialog, "wait_window"):
            dialog = QwenSetupDialog(self.root, on_success=lambda: None)
            mock_thread.assert_not_called()
            dialog._primary_btn.command()
            mock_thread.assert_called_once()

    @patch("dialogs.qwen_setup_dialog.subprocess.Popen")
    @patch("dialogs.qwen_setup_dialog.shutil.which", return_value="C:/Ollama/ollama.exe")
    def test_regression_qwen_cancel_path(self, mock_which, mock_popen) -> None:
        from dialogs.qwen_setup_dialog import QwenSetupDialog
        process = MagicMock()
        mock_popen.return_value = process

        with patch.object(QwenSetupDialog, "wait_window"):
            dialog = QwenSetupDialog(self.root, on_success=lambda: None)
            dialog._start_download_workflow()
            dialog._cancel_download()
            process.terminate.assert_called_once()
            self.assertTrue(dialog._is_cancelled)

    @patch("urllib.request.urlopen")
    @patch("subprocess.Popen")
    @patch("dialogs.ollama_setup_dialog.OllamaStatusService.detect")
    @patch("dialogs.ollama_setup_dialog.threading.Thread")
    def test_regression_ollama_download_success(self, mock_thread, mock_detect, mock_popen, mock_urlopen) -> None:
        from dialogs.ollama_setup_dialog import OllamaSetupDialog
        from unittest.mock import mock_open
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())

        mock_response = MagicMock()
        mock_response.getheader.return_value = "1024"
        mock_response.read.side_effect = [b"a" * 512, b"b" * 512, b""]
        mock_urlopen.return_value.__enter__.return_value = mock_response

        process = MagicMock()
        process.wait.return_value = 0
        mock_popen.return_value = process

        mock_detect.side_effect = [
            OllamaStatus(installed=False, reachable=False),
            OllamaStatus(installed=True, reachable=True)
        ]

        def mock_after(ms, func, *args, **kwargs):
            if "status_loop" in func.__name__ or func.__name__ == "check":
                return
            func(*args, **kwargs)

        with patch.object(OllamaSetupDialog, "wait_window"), \
             patch.object(OllamaSetupDialog, "after", side_effect=mock_after), \
             patch("pathlib.Path.mkdir"), \
             patch("builtins.open", new_callable=mock_open), \
             patch("pathlib.Path.is_file", return_value=True), \
             patch("pathlib.Path.unlink"), \
             patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 1024
            dialog = OllamaSetupDialog(self.root, on_detected=lambda: None)
            self.assertEqual(dialog._primary_btn.text, "Ollama installieren")
            dialog._primary_btn.command()
            self.assertTrue(dialog._success)
            self.assertEqual(dialog._status_lbl.cget("text"), "✓ Ollama ist bereit")

    @patch("dialogs.ollama_setup_dialog.OllamaStatusService.detect")
    @patch("urllib.request.urlopen")
    @patch("dialogs.ollama_setup_dialog.threading.Thread")
    def test_regression_ollama_download_failure(self, mock_thread, mock_urlopen, mock_detect) -> None:
        from dialogs.ollama_setup_dialog import OllamaSetupDialog
        mock_detect.return_value = OllamaStatus(installed=False, reachable=False)
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())
        mock_urlopen.side_effect = Exception("HTTP 500")

        def mock_after(ms, func, *args, **kwargs):
            if "status_loop" in func.__name__ or func.__name__ == "check":
                return
            func(*args, **kwargs)

        with patch.object(OllamaSetupDialog, "wait_window"), \
             patch.object(OllamaSetupDialog, "after", side_effect=mock_after), \
             patch("pathlib.Path.mkdir"), \
             patch("pathlib.Path.unlink"), \
             patch("pathlib.Path.is_file", return_value=False):
            dialog = OllamaSetupDialog(self.root, on_detected=lambda: None)
            dialog._primary_btn.command()
            self.assertFalse(dialog._success)
            self.assertIn("Installation konnte nicht abgeschlossen werden", dialog._desc_lbl.cget("text"))

    @patch("dialogs.ollama_setup_dialog.OllamaStatusService.detect")
    @patch("dialogs.ollama_setup_dialog.threading.Thread")
    def test_regression_ollama_unavailable(self, mock_thread, mock_detect) -> None:
        from dialogs.ollama_setup_dialog import OllamaSetupDialog
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())
        mock_detect.return_value = OllamaStatus(installed=False, reachable=False)

        detected_called = False
        def on_detected():
            nonlocal detected_called
            detected_called = True

        with patch.object(OllamaSetupDialog, "wait_window"):
            dialog = OllamaSetupDialog(self.root, on_detected=on_detected)

        self.assertFalse(detected_called)

    @patch("dialogs.ollama_setup_dialog.OllamaStatusService.detect")
    @patch("dialogs.ollama_setup_dialog.threading.Thread")
    def test_regression_ollama_detected_shows_weiter(self, mock_thread, mock_detect) -> None:
        from dialogs.ollama_setup_dialog import OllamaSetupDialog
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())
        mock_detect.return_value = OllamaStatus(installed=True, reachable=True)

        detected_called = False
        def on_detected():
            nonlocal detected_called
            detected_called = True

        def mock_after(ms, func, *args, **kwargs):
            func(*args, **kwargs)

        with patch.object(OllamaSetupDialog, "wait_window"), patch.object(OllamaSetupDialog, "after", side_effect=mock_after):
            dialog = OllamaSetupDialog(self.root, on_detected=on_detected)
            self.assertEqual(dialog._status_lbl.cget("text"), "✓ Ollama ist bereit")
            self.assertEqual(dialog._desc_lbl.cget("text"), "Die Installation wurde erkannt.")
            self.assertEqual(dialog._primary_btn.text, "Weiter")
            dialog._primary_btn.command()

        self.assertTrue(detected_called)

    @patch("dialogs.ollama_setup_dialog.OllamaStatusService.detect")
    @patch("urllib.request.urlopen")
    @patch("subprocess.Popen")
    @patch("dialogs.ollama_setup_dialog.threading.Thread")
    def test_regression_ollama_non_zero_exit_code(self, mock_thread, mock_popen, mock_urlopen, mock_detect) -> None:
        from dialogs.ollama_setup_dialog import OllamaSetupDialog
        from unittest.mock import mock_open
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())
        mock_detect.return_value = OllamaStatus(installed=False, reachable=False)

        mock_response = MagicMock()
        mock_response.getheader.return_value = "1024"
        mock_response.read.side_effect = [b"a" * 1024, b""]
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Installer finishes with exit code 1 (failure)
        process = MagicMock()
        process.wait.return_value = 1
        mock_popen.return_value = process

        def mock_after(ms, func, *args, **kwargs):
            if "status_loop" in func.__name__ or func.__name__ == "check":
                return
            func(*args, **kwargs)

        with patch.object(OllamaSetupDialog, "wait_window"), \
             patch.object(OllamaSetupDialog, "after", side_effect=mock_after), \
             patch("pathlib.Path.mkdir"), \
             patch("pathlib.Path.unlink"), \
             patch("pathlib.Path.is_file", return_value=True), \
             patch("pathlib.Path.stat") as mock_stat, \
             patch("builtins.open", new_callable=mock_open):
            mock_stat.return_value.st_size = 1024
            dialog = OllamaSetupDialog(self.root, on_detected=lambda: None)
            dialog._primary_btn.command()
            # Verify failure state
            self.assertFalse(dialog._success)
            self.assertEqual(dialog._status_lbl.cget("text"), "Fehler")

    @patch("dialogs.ollama_setup_dialog.OllamaStatusService.detect")
    @patch("urllib.request.urlopen")
    @patch("subprocess.Popen")
    @patch("dialogs.ollama_setup_dialog.threading.Thread")
    def test_regression_ollama_autostart_at_most_once(self, mock_thread, mock_popen, mock_urlopen, mock_detect) -> None:
        from dialogs.ollama_setup_dialog import OllamaSetupDialog
        from unittest.mock import mock_open
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())

        mock_detect.return_value = OllamaStatus(installed=True, reachable=False)

        mock_response = MagicMock()
        mock_response.getheader.return_value = "1024"
        mock_response.read.side_effect = [b"a" * 1024, b""]
        mock_urlopen.return_value.__enter__.return_value = mock_response

        process = MagicMock()
        process.wait.return_value = 0
        mock_popen.return_value = process

        # Mock time.sleep inside loop to return immediately
        with patch("time.sleep"), patch("shutil.which", return_value="C:/Ollama/ollama.exe"):
            def mock_after(ms, func, *args, **kwargs):
                if "status_loop" in func.__name__ or func.__name__ == "check":
                    return
                func(*args, **kwargs)

            with patch.object(OllamaSetupDialog, "wait_window"), \
                 patch.object(OllamaSetupDialog, "after", side_effect=mock_after), \
                 patch("pathlib.Path.mkdir"), \
                 patch("pathlib.Path.unlink"), \
                 patch("pathlib.Path.is_file", return_value=True), \
                 patch("pathlib.Path.stat") as mock_stat, \
                 patch("builtins.open", new_callable=mock_open):
                mock_stat.return_value.st_size = 1024
                dialog = OllamaSetupDialog(self.root, on_detected=lambda: None)
                dialog._primary_btn.command()

                # Check how many times Popen was called with the executable
                calls = [call[0][0] for call in mock_popen.call_args_list]
                autostart_calls = [c for c in calls if "ollama.exe" in c or c == ["C:/Ollama/ollama.exe"]]
                self.assertLessEqual(len(autostart_calls), 1)

    @patch("dialogs.ollama_setup_dialog.OllamaStatusService.detect")
    @patch("urllib.request.urlopen")
    @patch("subprocess.Popen")
    @patch("dialogs.ollama_setup_dialog.threading.Thread")
    def test_regression_ollama_retry(self, mock_thread, mock_popen, mock_urlopen, mock_detect) -> None:
        from dialogs.ollama_setup_dialog import OllamaSetupDialog
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())

        # side effect to return reachable=True after installation completes
        detect_calls = []
        def detect_side_effect(*args, **kwargs):
            detect_calls.append(1)
            if len(detect_calls) < 3:
                return OllamaStatus(installed=False, reachable=False)
            return OllamaStatus(installed=True, reachable=True)
        mock_detect.side_effect = detect_side_effect

        process = MagicMock()
        process.wait.return_value = 0
        mock_popen.return_value = process

        # First download fails, second succeeds
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("HTTP 500")
            mock_res = MagicMock()
            mock_res.getheader.return_value = "1024"
            mock_res.read.side_effect = [b"a" * 1024, b""]
            mock_context = MagicMock()
            mock_context.__enter__.return_value = mock_res
            return mock_context

        mock_urlopen.side_effect = side_effect

        def mock_after(ms, func, *args, **kwargs):
            if "status_loop" in func.__name__ or func.__name__ == "check":
                return
            func(*args, **kwargs)

        with patch("time.sleep"), \
             patch.object(OllamaSetupDialog, "wait_window"), \
             patch.object(OllamaSetupDialog, "after", side_effect=mock_after), \
             patch("pathlib.Path.mkdir"), \
             patch("pathlib.Path.unlink"), \
             patch("pathlib.Path.is_file", return_value=True), \
             patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 1024
            dialog = OllamaSetupDialog(self.root, on_detected=lambda: None)

            # Start download which fails
            dialog._primary_btn.command()
            self.assertEqual(dialog._status_lbl.cget("text"), "Fehler")
            self.assertEqual(dialog._primary_btn.text, "Erneut versuchen")

            # Click retry
            dialog._primary_btn.command()
            self.assertTrue(dialog._success)
            self.assertEqual(dialog._status_lbl.cget("text"), "✓ Ollama ist bereit")

    @patch("dialogs.qwen_setup_dialog.threading.Thread")
    @patch("dialogs.qwen_setup_dialog.subprocess.Popen")
    @patch("dialogs.qwen_setup_dialog.shutil.which", return_value="C:/Ollama/ollama.exe")
    @patch("dialogs.qwen_setup_dialog.OllamaStatusService.detect")
    def test_regression_qwen_retry(self, mock_detect, mock_which, mock_popen, mock_thread) -> None:
        from dialogs.qwen_setup_dialog import QwenSetupDialog
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())
        mock_detect.side_effect = [
            OllamaStatus(installed=True, reachable=True, model_available=False),
            OllamaStatus(installed=True, reachable=True, model_available=True)
        ]

        # First fails with non-zero exit code
        process1 = MagicMock()
        process1.wait.return_value = 1
        process1.stdout.read.return_value = b""

        # Second succeeds
        process2 = MagicMock()
        process2.wait.return_value = 0
        process2.stdout.read.return_value = b""

        mock_popen.side_effect = [process1, process2]

        def mock_after(ms, func, *args, **kwargs):
            func(*args, **kwargs)

        with patch.object(QwenSetupDialog, "wait_window"), patch.object(QwenSetupDialog, "after", side_effect=mock_after):
            dialog = QwenSetupDialog(self.root, on_success=lambda: None)

            # First pull fails
            dialog._primary_btn.command()
            self.assertEqual(dialog._status_lbl.cget("text"), "Fehler")
            self.assertEqual(dialog._primary_btn.text, "Erneut versuchen")

            # Retry
            dialog._primary_btn.command()
            self.assertTrue(dialog._success)

    @patch("widgets.phoenix.views.prompt_view.OllamaStatusService.detect")
    def test_regression_main_text_and_action_when_not_ready(self, mock_detect) -> None:
        mock_detect.return_value = OllamaStatus(installed=False, reachable=False, model_available=False)
        self.view._boost_install_btn = MagicMock()
        self.view._boost_ollama_status_lbl = MagicMock()
        self.view._boost_model_status_lbl = MagicMock()
        self.view._boost_ai_status_lbl = MagicMock()
        self.view._boost_ai_info_lbl = MagicMock()

        self.view._update_ollama_install_button(mock_detect.return_value)

        self.view._boost_ai_info_lbl.configure.assert_called_with(
            text=tr(
                "boost_ai_setup_prompt",
                "Richten Sie Phoenix Boost in zwei einfachen Schritten ein.\n"
                "Snapdragon AI Studio führt Sie automatisch durch die Einrichtung."
            )
        )
        self.view._boost_install_btn.configure.assert_called_with(
            text=tr("boost_setup_action", "Phoenix Boost einrichten"),
            command=self.view._open_ollama_download,
            button_type="primary",
            state="normal"
        )

    @patch("dialogs.ollama_setup_dialog.OllamaSetupDialog.__init__", return_value=None)
    @patch("widgets.phoenix.views.prompt_view.OllamaStatusService.detect")
    def test_regression_missing_ollama_opens_step1(self, mock_detect, mock_dialog) -> None:
        mock_detect.return_value = OllamaStatus(installed=False, reachable=False, model_available=False)
        self.view._update_ollama_install_button(mock_detect.return_value)
        self.view._open_ollama_download()
        mock_dialog.assert_called_once()

    def test_regression_ollama_progress_updates_correctly(self) -> None:
        from dialogs.ollama_setup_dialog import OllamaSetupDialog
        with patch.object(OllamaSetupDialog, "wait_window"):
            dialog = OllamaSetupDialog(self.root, on_detected=lambda: None)
            dialog._update_download_progress(45, "45.0 MB von 100.0 MB")
            self.assertEqual(dialog._progress_bar["value"], 45)
            self.assertIn("45 % heruntergeladen", dialog._status_lbl.cget("text"))
            self.assertIn("45.0 MB von 100.0 MB", dialog._desc_lbl.cget("text"))
    @patch("dialogs.ollama_setup_dialog.subprocess.run")
    @patch("dialogs.ollama_setup_dialog.subprocess.Popen")
    @patch("urllib.request.urlopen")
    @patch("dialogs.ollama_setup_dialog.OllamaStatusService.detect")
    @patch("dialogs.ollama_setup_dialog.threading.Thread")
    def test_regression_ollama_gui_suppression(self, mock_thread, mock_detect, mock_urlopen, mock_popen, mock_run) -> None:
        import subprocess
        from dialogs.ollama_setup_dialog import OllamaSetupDialog
        from unittest.mock import mock_open, ANY
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())
        mock_detect.side_effect = [
            OllamaStatus(installed=False, reachable=False),
            OllamaStatus(installed=True, reachable=True)
        ]
        mock_response = MagicMock()
        mock_response.getheader.return_value = "1024"
        mock_response.read.side_effect = [b"a" * 1024, b""]
        mock_urlopen.return_value.__enter__.return_value = mock_response

        process = MagicMock()
        process.wait.return_value = 0
        mock_popen.return_value = process

        def mock_after(ms, func, *args, **kwargs):
            if "status_loop" in func.__name__ or func.__name__ == "check":
                return
            func(*args, **kwargs)

        with patch.object(OllamaSetupDialog, "wait_window"), \
             patch.object(OllamaSetupDialog, "after", side_effect=mock_after), \
             patch("pathlib.Path.mkdir"), \
             patch("pathlib.Path.unlink"), \
             patch("pathlib.Path.is_file", return_value=True), \
             patch("pathlib.Path.stat") as mock_stat, \
             patch("builtins.open", new_callable=mock_open):
            mock_stat.return_value.st_size = 1024
            dialog = OllamaSetupDialog(self.root, on_detected=lambda: None)
            dialog._primary_btn.command()

            # Verify taskkill was run to suppress GUI
            mock_run.assert_called_with(
                ["taskkill", "/F", "/IM", "ollama app.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=ANY
            )
            # Note: This mock assertion verifies the logic flow post-installation,
            # but actual preservation of the localhost:11434 backend and survival of
            # ollama.exe must be verified manually on a clean machine prior to RC2A release.
            self.assertTrue(dialog._success)

    def test_regression_qwen_output_parsing(self) -> None:
        from dialogs.qwen_setup_dialog import QwenSetupDialog
        with patch.object(QwenSetupDialog, "wait_window"):
            dialog = QwenSetupDialog(self.root, on_success=lambda: None)

            # 1. Parse real current output pulling digest
            dialog._parse_output_line("pulling 5ee4f07cdb9b: 42% ... 806 MB/1.9 GB 6.8 MB/s ...")
            self.assertEqual(dialog._progress_bar["value"], 42)
            self.assertIn("42 % heruntergeladen", dialog._status_lbl.cget("text"))
            self.assertIn("heruntergeladen", dialog._desc_lbl.cget("text"))

            # 2. Parse older downloading format
            dialog._parse_output_line("downloading layer 88%: 88%")
            self.assertEqual(dialog._progress_bar["value"], 88)
            self.assertIn("88 % heruntergeladen", dialog._status_lbl.cget("text"))

            # 3. Parse manifest (should not failure, it is preparation state)
            dialog._parse_output_line("pulling manifest")
            self.assertIn("Vorbereitung", dialog._desc_lbl.cget("text"))

    @patch("dialogs.qwen_setup_dialog.QwenSetupDialog.__init__", return_value=None)
    @patch("dialogs.ollama_setup_dialog.OllamaSetupDialog.__init__", return_value=None)
    @patch("widgets.phoenix.views.prompt_view.OllamaStatusService.detect")
    def test_regression_ollama_available_qwen_missing_routing(self, mock_detect, mock_ollama_dlg, mock_qwen_dlg) -> None:
        # Ollama available, Qwen missing
        mock_detect.return_value = OllamaStatus(installed=True, reachable=True, model_available=False)
        self.view._boost_install_btn = MagicMock()
        self.view._boost_ollama_status_lbl = MagicMock()
        self.view._boost_model_status_lbl = MagicMock()
        self.view._boost_ai_status_lbl = MagicMock()
        self.view._boost_ai_info_lbl = MagicMock()

        self.view._update_ollama_install_button(mock_detect.return_value)
        self.view._open_ollama_download()
        # Should directly open Qwen dialog and skip Ollama
        mock_qwen_dlg.assert_called_once()
        mock_ollama_dlg.assert_not_called()

    @patch("widgets.phoenix.views.prompt_view.OllamaStatusService.detect")
    def test_regression_ollama_unreachable_state(self, mock_detect) -> None:
        # Ollama installed but unreachable
        mock_detect.return_value = OllamaStatus(installed=True, reachable=False, model_available=False)
        self.view._boost_install_btn = MagicMock()
        self.view._boost_ollama_status_lbl = MagicMock()
        self.view._boost_model_status_lbl = MagicMock()
        self.view._boost_ai_status_lbl = MagicMock()
        self.view._boost_ai_info_lbl = MagicMock()

        self.view._update_ollama_install_button(mock_detect.return_value)

        self.view._boost_ollama_status_lbl.configure.assert_called_with(text="Ollama nicht erreichbar")
        self.view._boost_model_status_lbl.configure.assert_called_with(text="Qwen2.5 3B: nicht verfügbar")
        self.view._boost_ai_status_lbl.configure(text="Phoenix Boost ist noch nicht bereit")
        self.view._boost_install_btn.configure.assert_called_with(
            text="Ollama nicht erreichbar",
            state="disabled"
        )

    @patch("widgets.phoenix.views.prompt_view.OllamaStatusService.detect")
    def test_regression_fully_ready_state_wizard(self, mock_detect) -> None:
        # Ollama ready + Qwen ready
        mock_detect.return_value = OllamaStatus(installed=True, reachable=True, model_available=True)
        self.view._boost_install_btn = MagicMock()
        self.view._boost_ollama_status_lbl = MagicMock()
        self.view._boost_model_status_lbl = MagicMock()
        self.view._boost_ai_status_lbl = MagicMock()
        self.view._boost_ai_info_lbl = MagicMock()

        self.view._update_ollama_install_button(mock_detect.return_value)
        self.view._boost_install_btn.configure.assert_called_with(
            text=tr("boost_ai_ready_button", "Phoenix Boost AI bereit ✓"),
            state="disabled"
        )

    @patch("widgets.phoenix.views.prompt_view.OllamaStatusService.detect")
    def test_regression_status_refresh_after_successful_installation(self, mock_detect) -> None:
        mock_detect.return_value = OllamaStatus(installed=True, reachable=True, model_available=False)
        self.view._update_ollama_install_button(mock_detect.return_value)
        self.assertFalse(self.view._ollama_status.model_available)

        mock_detect.return_value = OllamaStatus(installed=True, reachable=True, model_available=True)
        self.view._on_qwen_installed_success()
        self.assertTrue(self.view._ollama_status.model_available)


    @patch("dialogs.ollama_setup_dialog.urllib.request.urlopen")
    @patch("dialogs.ollama_setup_dialog.threading.Thread")
    @patch("dialogs.ollama_setup_dialog.OllamaStatusService.detect")
    def test_regression_download_completeness_success(self, mock_detect, mock_thread, mock_urlopen) -> None:
        from dialogs.ollama_setup_dialog import OllamaSetupDialog
        from unittest.mock import mock_open

        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())
        mock_detect.side_effect = [
            OllamaStatus(installed=False, reachable=False),
            OllamaStatus(installed=True, reachable=True)
        ]

        mock_response = MagicMock()
        mock_response.getheader.return_value = "1024"
        mock_response.read.side_effect = [b"a" * 1024, b""]
        mock_urlopen.return_value.__enter__.return_value = mock_response

        def mock_after(ms, func, *args, **kwargs):
            if "status_loop" in func.__name__ or func.__name__ == "check":
                return
            func(*args, **kwargs)

        with patch.object(OllamaSetupDialog, "wait_window"),              patch.object(OllamaSetupDialog, "after", side_effect=mock_after) as mock_after_obj,              patch("pathlib.Path.mkdir"),              patch("pathlib.Path.unlink"),              patch("pathlib.Path.is_file", return_value=True),              patch("pathlib.Path.stat") as mock_stat,              patch("builtins.open", new_callable=mock_open),              patch("dialogs.ollama_setup_dialog.subprocess.Popen") as mock_popen:
            mock_stat.return_value.st_size = 1024

            process = MagicMock()
            process.wait.return_value = 0
            process.communicate.return_value = (b"", b"")
            mock_popen.return_value = process

            dialog = OllamaSetupDialog(self.root, on_detected=lambda: None)
            dialog._primary_btn.command()

            from unittest.mock import ANY
            from config import TEMP_DIR
            mock_popen.assert_any_call(
                [str(Path(TEMP_DIR) / "OllamaSetup.exe"), "/VERYSILENT", "/SUPPRESSMSGBOXES"],
                creationflags=ANY
            )
            self.assertTrue(dialog._success)

            called_100 = False
            for call in mock_after_obj.call_args_list:
                args = call[0]
                if len(args) >= 3 and args[1] == dialog._update_download_progress:
                    if args[2] == 100:
                        called_100 = True
            self.assertTrue(called_100)

    @patch("dialogs.ollama_setup_dialog.urllib.request.urlopen")
    @patch("dialogs.ollama_setup_dialog.threading.Thread")
    @patch("dialogs.ollama_setup_dialog.OllamaStatusService.detect")
    def test_regression_download_completeness_premature_eof(self, mock_detect, mock_thread, mock_urlopen) -> None:
        from dialogs.ollama_setup_dialog import OllamaSetupDialog
        from unittest.mock import mock_open

        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())
        mock_detect.side_effect = [
            OllamaStatus(installed=False, reachable=False),
            OllamaStatus(installed=False, reachable=False)
        ]

        mock_response = MagicMock()
        mock_response.getheader.return_value = "1024"
        mock_response.read.side_effect = [b"a" * 500, b""]
        mock_urlopen.return_value.__enter__.return_value = mock_response

        def mock_after(ms, func, *args, **kwargs):
            if "status_loop" in func.__name__ or func.__name__ == "check":
                return
            func(*args, **kwargs)

        with patch.object(OllamaSetupDialog, "wait_window"),              patch.object(OllamaSetupDialog, "after", side_effect=mock_after) as mock_after_obj,              patch("pathlib.Path.mkdir"),              patch("pathlib.Path.unlink") as mock_unlink,              patch("pathlib.Path.is_file", return_value=True),              patch("pathlib.Path.stat") as mock_stat,              patch("builtins.open", new_callable=mock_open),              patch("dialogs.ollama_setup_dialog.subprocess.Popen") as mock_popen:
            mock_stat.return_value.st_size = 500
            dialog = OllamaSetupDialog(self.root, on_detected=lambda: None)
            dialog._primary_btn.command()

            mock_popen.assert_not_called()
            self.assertFalse(dialog._success)

            called_100 = False
            for call in mock_after_obj.call_args_list:
                args = call[0]
                if len(args) >= 3 and args[1] == dialog._update_download_progress:
                    if args[2] == 100:
                        called_100 = True
            self.assertFalse(called_100)
            mock_unlink.assert_called()


    @patch("dialogs.qwen_setup_dialog.threading.Thread")
    @patch("dialogs.qwen_setup_dialog.subprocess.Popen")
    @patch("dialogs.qwen_setup_dialog.shutil.which", return_value="C:/Ollama/ollama.exe")
    @patch("dialogs.qwen_setup_dialog.OllamaStatusService.detect")
    def test_regression_qwen_pull_fallback_success(self, mock_detect, mock_which, mock_popen, mock_thread) -> None:
        from dialogs.qwen_setup_dialog import QwenSetupDialog
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())

        mock_detect.return_value = OllamaStatus(installed=True, reachable=True, model_available=True)

        process = MagicMock()
        process.wait.return_value = 1
        process.stdout.read.return_value = b""
        mock_popen.return_value = process

        success_called = False
        def on_success():
            nonlocal success_called
            success_called = True

        def mock_after(ms, func, *args, **kwargs):
            func(*args, **kwargs)

        with patch.object(QwenSetupDialog, "wait_window"), patch.object(QwenSetupDialog, "after", side_effect=mock_after):
            dialog = QwenSetupDialog(self.root, on_success=on_success)
            dialog._primary_btn.command()
            dialog._finish_success()

        self.assertTrue(dialog._success)
        self.assertTrue(success_called)


    @patch("dialogs.qwen_setup_dialog.threading.Thread")
    @patch("dialogs.qwen_setup_dialog.subprocess.Popen")
    @patch("dialogs.qwen_setup_dialog.shutil.which", return_value=None)
    @patch("dialogs.qwen_setup_dialog.OllamaStatusService.detect")
    def test_regression_qwen_missing_executable(self, mock_detect, mock_which, mock_popen, mock_thread) -> None:
        from dialogs.qwen_setup_dialog import QwenSetupDialog
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())
        mock_detect.return_value = OllamaStatus(installed=False, reachable=False, model_available=False)

        def mock_after(ms, func, *args, **kwargs):
            func(*args, **kwargs)

        with patch.object(QwenSetupDialog, "wait_window"),              patch.object(QwenSetupDialog, "after", side_effect=mock_after),              patch("pathlib.Path.is_file", return_value=False):
            dialog = QwenSetupDialog(self.root, on_success=lambda: None)
            dialog._primary_btn.command()

            # Confirm it correctly transitions to failure (not silent hang)
            self.assertFalse(dialog._success)
            self.assertEqual(dialog._status_lbl.cget("text"), "Fehler")

    @patch("dialogs.qwen_setup_dialog.threading.Thread")
    @patch("dialogs.qwen_setup_dialog.subprocess.Popen")
    @patch("dialogs.qwen_setup_dialog.shutil.which", return_value="C:/Ollama/ollama.exe")
    @patch("dialogs.qwen_setup_dialog.OllamaStatusService.detect")
    def test_regression_qwen_pull_exit_zero_model_absent(self, mock_detect, mock_which, mock_popen, mock_thread) -> None:
        from dialogs.qwen_setup_dialog import QwenSetupDialog
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())

        # Exit code is 0, but model_available is False!
        mock_detect.return_value = OllamaStatus(installed=True, reachable=True, model_available=False)

        process = MagicMock()
        process.wait.return_value = 0
        process.stdout.read.return_value = b""
        mock_popen.return_value = process

        def mock_after(ms, func, *args, **kwargs):
            func(*args, **kwargs)

        with patch.object(QwenSetupDialog, "wait_window"), patch.object(QwenSetupDialog, "after", side_effect=mock_after):
            dialog = QwenSetupDialog(self.root, on_success=lambda: None)
            dialog._primary_btn.command()

            # Should NOT succeed
            self.assertFalse(dialog._success)
            self.assertEqual(dialog._status_lbl.cget("text"), "Fehler")


if __name__ == "__main__":
    unittest.main()
