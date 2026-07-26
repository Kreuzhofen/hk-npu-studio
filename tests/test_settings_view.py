from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk

from widgets.phoenix.views.settings_view import PhoenixSettingsView
from app.settings_manager import SettingsManager


class SettingsViewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()  # Withdraw to prevent rendering actual window
        
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
        self.root.destroy()  # Reliably destroy the root window
        
        self.showinfo_patcher.stop()
        self.showwarning_patcher.stop()

    def test_settings_view_build(self) -> None:
        # Assert components are created
        self.assertIsNotNone(self.view.token_entry)
        self.assertIsNotNone(self.view.toggle_btn)
        self.assertIsNotNone(self.view.save_btn)
        self.assertIsNotNone(self.view.test_btn)
        
        # Verify initial token matches the patched get_hf_token value
        self.assertEqual(self.view.token_entry.get(), "dummy_saved_token")

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
        status_text = self.view.status_lbl.cget("text")
        self.assertTrue(
            "erfolgreich gespeichert" in status_text or "Settings saved successfully" in status_text,
            f"Expected save success message, got: {status_text}"
        )

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
