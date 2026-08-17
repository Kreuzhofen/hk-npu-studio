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
        self.assertIn("Ollama installieren", texts)
        self.assertIn("Sampler:", texts)
        self.assertIn("Scheduler:", texts)
        self.assertFalse(any("{sampler}" in text or "{scheduler}" in text for text in texts))
        self.assertIn(
            "Installieren Sie zuerst Ollama. Die offizielle Downloadseite wird geöffnet; "
            "Ihre Bildgenerierung bleibt weiterhin verfügbar.",
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
        self.assertEqual(self.view._boost_install_btn.cget("text"), "Qwen2.5 3B installieren")
        self.assertEqual(self.view._boost_model_status_lbl.cget("text"), "Qwen2.5 3B: nicht installiert")
        self.assertIn("benötigte Qwen-Modell", self.view._boost_ai_info_lbl.cget("text"))

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
    def test_regression_qwen_pull_success(self, mock_which, mock_popen, mock_thread) -> None:
        from dialogs.qwen_setup_dialog import QwenSetupDialog
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())

        process = MagicMock()
        process.wait.return_value = 0
        process.stdout.read.side_effect = [c for c in "pulling manifest\rdownloading 50%\rsuccess\r"] + [""]
        mock_popen.return_value = process

        success_called = False
        def on_success():
            nonlocal success_called
            success_called = True

        def mock_after(ms, func, *args, **kwargs):
            func(*args, **kwargs)

        with patch.object(QwenSetupDialog, "wait_window"), patch.object(QwenSetupDialog, "after", side_effect=mock_after):
            dialog = QwenSetupDialog(self.root, on_success=on_success)
            # Verify no technical output is shown in the detail label
            self.assertNotIn("pulling", dialog._detail_lbl.cget("text"))
            self.assertNotIn("downloading", dialog._detail_lbl.cget("text"))
            self.assertNotIn("MB/s", dialog._detail_lbl.cget("text"))
            self.assertNotIn("GB", dialog._detail_lbl.cget("text"))
            dialog._finish_success()

        self.assertTrue(dialog._success)
        self.assertTrue(success_called)

    @patch("dialogs.qwen_setup_dialog.threading.Thread")
    @patch("dialogs.qwen_setup_dialog.subprocess.Popen")
    @patch("dialogs.qwen_setup_dialog.shutil.which", return_value="C:/Ollama/ollama.exe")
    def test_regression_qwen_pull_failure(self, mock_which, mock_popen, mock_thread) -> None:
        from dialogs.qwen_setup_dialog import QwenSetupDialog
        mock_thread.side_effect = lambda target, *args, **kwargs: MagicMock(start=lambda: target())

        process = MagicMock()
        process.wait.return_value = 1
        process.stdout.read.side_effect = [c for c in "pulling manifest\rerror: model not found\r"] + [""]
        mock_popen.return_value = process

        success_called = False
        def on_success():
            nonlocal success_called
            success_called = True

        def mock_after(ms, func, *args, **kwargs):
            func(*args, **kwargs)

        with patch.object(QwenSetupDialog, "wait_window"), patch.object(QwenSetupDialog, "after", side_effect=mock_after):
            dialog = QwenSetupDialog(self.root, on_success=on_success)

        self.assertFalse(dialog._success)
        self.assertFalse(success_called)
        # Verify the friendly error is shown, not the raw error
        self.assertIn("konnte nicht installiert werden", dialog._detail_lbl.cget("text"))
        self.assertNotIn("error: model not found", dialog._detail_lbl.cget("text"))

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
        mock_detect.return_value = OllamaStatus(installed=True, reachable=True) # Available!

        detected_called = False
        def on_detected():
            nonlocal detected_called
            detected_called = True

        def mock_after(ms, func, *args, **kwargs):
            func(*args, **kwargs)

        with patch.object(OllamaSetupDialog, "wait_window"), patch.object(OllamaSetupDialog, "after", side_effect=mock_after):
            dialog = OllamaSetupDialog(self.root, on_detected=on_detected)
            # Verify status label changed
            self.assertEqual(dialog._status_lbl.cget("text"), "✓ Ollama ist bereit")
            # Verify button changed to "Weiter"
            self.assertEqual(dialog._close_btn.text, "Weiter")
            # Simulate clicking "Weiter"
            dialog._close_btn.command()

        self.assertTrue(detected_called)

    @patch("widgets.phoenix.views.prompt_view.OllamaStatusService.detect")
    def test_regression_status_refresh_after_successful_installation(self, mock_detect) -> None:
        mock_detect.return_value = OllamaStatus(installed=True, reachable=True, model_available=False)
        self.view._update_ollama_install_button(mock_detect.return_value)
        self.assertFalse(self.view._ollama_status.model_available)

        mock_detect.return_value = OllamaStatus(installed=True, reachable=True, model_available=True)
        self.view._on_qwen_installed_success()
        self.assertTrue(self.view._ollama_status.model_available)


if __name__ == "__main__":
    unittest.main()
