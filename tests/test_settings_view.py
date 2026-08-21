from __future__ import annotations

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import tkinter as tk

from widgets.phoenix.views.settings_view import PhoenixSettingsView
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import set_language
from app.settings_manager import SettingsManager


class SettingsViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        set_language("de_DE")
        
        # Patch messagebox calls to prevent blocking
        self.showinfo_patcher = patch("tkinter.messagebox.showinfo")
        self.showwarning_patcher = patch("tkinter.messagebox.showwarning")
        self.mock_showinfo = self.showinfo_patcher.start()
        self.mock_showwarning = self.showwarning_patcher.start()

        # Patch load_settings to avoid loading real configs
        with patch.object(SettingsManager, "get_hf_token", return_value="dummy_saved_token"):
            self.view = PhoenixSettingsView(self.root)

    def tearDown(self) -> None:
        self.view.destroy()
        self.root.update_idletasks()
        
        self.showinfo_patcher.stop()
        self.showwarning_patcher.stop()

    def test_settings_view_build(self) -> None:
        # Assert components are created
        self.assertIsNotNone(self.view.token_entry)
        self.assertIsNotNone(self.view.toggle_btn)
        self.assertIsNotNone(self.view.save_btn)
        self.assertIsNotNone(self.view.test_btn)
        self.assertEqual(
            self.view.ui_language_save_hint.cget("text"),
            "Hinweis: Änderungen an Sprache und Benutzeroberfläche werden erst nach dem Speichern übernommen.",
        )
        self.assertEqual(self.view.ui_language_save_hint.cget("wraplength"), 440)
        self.assertEqual(
            self.view.system_npu_hint.cget("text"),
            "Hinweis: Snapdragon AI Studio wählt die passende Verarbeitung für das verwendete Modell automatisch aus. Sie müssen hier normalerweise nichts einstellen.",
        )
        self.assertEqual(self.view.system_npu_hint.cget("wraplength"), 440)
        
        # Verify initial token matches the patched get_hf_token value
        self.assertEqual(self.view.token_entry.get(), "dummy_saved_token")

    def test_ui_language_save_hint_is_complete_in_all_languages(self) -> None:
        expected = {
            "de_DE": (
                "Hinweis: Änderungen an Sprache und Benutzeroberfläche werden erst nach dem Speichern übernommen.",
                "Hinweis: Snapdragon AI Studio wählt die passende Verarbeitung für das verwendete Modell automatisch aus. Sie müssen hier normalerweise nichts einstellen.",
            ),
            "en_US": (
                "Note: Changes to the language and user interface are applied after you save the settings.",
                "Note: Snapdragon AI Studio automatically selects the appropriate processing method for the model you are using. You normally do not need to change anything here.",
            ),
            "es_ES": (
                "Nota: Los cambios de idioma y de la interfaz se aplican después de guardar la configuración.",
                "Nota: Snapdragon AI Studio selecciona automáticamente el procesamiento adecuado para el modelo que está utilizando. Normalmente no necesita cambiar nada aquí.",
            ),
        }
        root = Path(__file__).resolve().parents[1]
        for locale, texts in expected.items():
            data = json.loads((root / "locales" / f"{locale}.json").read_text(encoding="utf-8"))
            self.assertEqual(data["settings_ui_language_save_hint"], texts[0], locale)
            self.assertEqual(data["settings_system_npu_hint"], texts[1], locale)
            self.assertNotIn("{", "".join(texts))

    def test_toggle_token_visibility(self) -> None:
        # Initial state should be masked (show="*")
        self.assertEqual(self.view.token_entry.cget("show"), "*")
        self.assertIn(self.view.toggle_btn.cget("text"), {"Anzeigen", "Show"})

        # Toggle to show
        self.view._toggle_token_visibility()
        self.assertEqual(self.view.token_entry.cget("show"), "")
        self.assertIn(self.view.toggle_btn.cget("text"), {"Verbergen", "Hide"})

        # Toggle back to hide
        self.view._toggle_token_visibility()
        self.assertEqual(self.view.token_entry.cget("show"), "*")
        self.assertIn(self.view.toggle_btn.cget("text"), {"Anzeigen", "Show"})

    @patch.object(SettingsManager, "save_settings")
    def test_save_settings_triggers_manager(self, mock_save: MagicMock) -> None:
        mock_save.return_value = True
        
        # Modify token input
        self.view.token_entry.delete(0, tk.END)
        self.view.token_entry.insert(0, "new_secret_token")
        
        # Trigger save
        self.view._save_settings()
        
        # Verify save_settings called with correct argument
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][0]
        self.assertEqual(saved_data.get("hf_token"), "new_secret_token")
        self.assertNotIn("output_dir", saved_data)
        self.assertNotIn("models_dir", saved_data)
        status_text = self.view.status_lbl.cget("text")
        self.assertTrue(
            "erfolgreich gespeichert" in status_text or "Settings saved successfully" in status_text,
            f"Expected save success message, got: {status_text}"
        )

    def test_path_fields_show_configured_runtime_paths_and_are_readonly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "configured-output"
            models_dir = Path(temp_dir) / "configured-models"
            with patch("widgets.phoenix.views.settings_view.OUTPUT_DIR", output_dir), \
                 patch("widgets.phoenix.views.settings_view.MODELS_DIR", models_dir):
                self.view._load_values()

            self.assertEqual(self.view.out_dir_entry.get(), str(output_dir))
            self.assertEqual(self.view.models_dir_entry.get(), str(models_dir))
        self.assertEqual(str(self.view.out_dir_entry.cget("state")), "readonly")
        self.assertEqual(str(self.view.models_dir_entry.cget("state")), "readonly")
        self.assertEqual(self.view.out_dir_entry.cget("readonlybackground"), PHOENIX_THEME.elevated_bg)
        self.assertEqual(self.view.models_dir_entry.cget("readonlybackground"), PHOENIX_THEME.elevated_bg)
        self.assertFalse(hasattr(self.view, "out_dir_btn"))
        self.assertFalse(hasattr(self.view, "models_dir_btn"))

    @patch("app.settings_manager.SettingsManager.test_hf_token")
    def test_test_token_successful(self, mock_test: MagicMock) -> None:
        mock_test.return_value = (True, "Token ist gültig.")

        self.view.token_entry.delete(0, tk.END)
        self.view.token_entry.insert(0, "valid_token")

        # Directly run worker method to avoid thread-join waiting in test
        self.view._test_token_worker("valid_token")
        
        # Force idle tasks to run after_idle scheduled calls
        self.root.update_idletasks()

        mock_test.assert_called_once_with("valid_token")
        self.assertEqual(self.view.status_lbl.cget("text"), "Token ist gültig.")
        
        # Check that showinfo was called with either localized version of 'Test Token'
        self.assertTrue(self.mock_showinfo.called)
        call_args = self.mock_showinfo.call_args[0]
        self.assertIn(call_args[0], {"Token testen", "Test Token"})
        self.assertEqual(call_args[1], "Token ist gültig.")


if __name__ == "__main__":
    unittest.main()
