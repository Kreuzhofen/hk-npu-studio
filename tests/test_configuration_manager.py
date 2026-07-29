from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.configuration_manager import (
    CURRENT_SCHEMA_VERSION,
    ConfigurationManager,
)
from app.settings_manager import SettingsManager


class ConfigurationManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary_directory.name) / "preferences.json"
        self.manager = ConfigurationManager(self.path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_missing_configuration_uses_validated_defaults(self) -> None:
        values = self.manager.load()
        self.assertEqual(CURRENT_SCHEMA_VERSION, values["schema_version"])
        self.assertEqual("Auto", values["thread_count"])
        self.assertEqual("QNN EP", values["execution_provider"])

    def test_legacy_flat_configuration_is_migrated_and_persisted(self) -> None:
        self.path.write_text(
            json.dumps(
                {
                    "model_id": "legacy_model",
                    "hf_access_token": "secret",
                    "thread_count": 8,
                    "hardware_accel": True,
                    "custom_key": "erhalten",
                }
            ),
            encoding="utf-8",
        )

        values = self.manager.load()
        persisted = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(CURRENT_SCHEMA_VERSION, persisted["schema_version"])
        self.assertEqual("legacy_model", values["active_model_id"])
        self.assertEqual("secret", values["hf_token"])
        self.assertEqual("8", values["thread_count"])
        self.assertEqual("True", values["hardware_accel"])
        self.assertEqual("erhalten", values["custom_key"])

    def test_nested_legacy_settings_are_flattened(self) -> None:
        self.path.write_text(
            json.dumps(
                {
                    "settings": {
                        "theme": "Hell",
                        "language": "English",
                    }
                }
            ),
            encoding="utf-8",
        )
        values = self.manager.load()
        self.assertEqual("Hell", values["theme"])
        self.assertEqual("English", values["language"])
        self.assertNotIn("settings", values)

    def test_invalid_values_fall_back_without_dropping_unknown_keys(self) -> None:
        validation = self.manager.validate(
            {
                "thread_count": "999",
                "execution_provider": "Ungültig",
                "hardware_accel": "vielleicht",
                "output_dir": "",
                "models_dir": "",
                "theme": "Neon",
                "language": "Esperanto",
                "future_option": 42,
            }
        )
        self.assertFalse(validation.is_valid)
        self.assertEqual("Auto", validation.values["thread_count"])
        self.assertEqual("QNN EP", validation.values["execution_provider"])
        self.assertEqual("True", validation.values["hardware_accel"])
        self.assertEqual(42, validation.values["future_option"])

    def test_atomic_merge_preserves_existing_values(self) -> None:
        self.assertTrue(self.manager.save({"theme": "Hell"}, merge=False))
        self.assertTrue(self.manager.save({"language": "English"}))
        values = self.manager.load()
        self.assertEqual("Hell", values["theme"])
        self.assertEqual("English", values["language"])
        self.assertFalse(self.path.with_suffix(".json.tmp").exists())

    def test_settings_manager_uses_central_manager(self) -> None:
        with patch.object(SettingsManager, "get_preferences_path", return_value=self.path):
            self.assertTrue(
                SettingsManager.save_settings(
                    {
                        "thread_count": "4",
                        "execution_provider": "CPU EP",
                        "hardware_accel": "False",
                    }
                )
            )
            values = SettingsManager.load_settings()
        self.assertEqual(CURRENT_SCHEMA_VERSION, values["schema_version"])
        self.assertEqual("4", values["thread_count"])
        self.assertEqual("CPU EP", values["execution_provider"])
        self.assertEqual("False", values["hardware_accel"])


if __name__ == "__main__":
    unittest.main()
