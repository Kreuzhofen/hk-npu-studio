from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from app.preset_manager import PresetManager


class PresetManagerTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PresetManager(preset_dir=self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    def test_default_presets_created_on_init(self) -> None:
        """1. Standard-Presets werden bei der Initialisierung erstellt."""
        presets = self.manager.list_presets()
        self.assertIn("default", presets)
        self.assertIn("cyberpunk", presets)
        self.assertIn("photorealistic", presets)

    def test_get_preset_loads_correct_data(self) -> None:
        """2. get_preset lädt die korrekten Parameterdaten eines Presets."""
        default_preset = self.manager.get_preset("default")
        self.assertIsNotNone(default_preset)
        self.assertEqual(default_preset["name"], "Default")
        self.assertEqual(default_preset["cfg_scale"], 7.5)
        self.assertEqual(default_preset["steps"], 20)

    def test_save_preset_saves_successfully(self) -> None:
        """3. save_preset speichert ein neues Custom-Preset mit bereinigtem Dateinamen."""
        preset_data = {
            "prompt": "Hyperdetailed futuristic city",
            "cfg_scale": 12.0,
            "steps": 50,
            "controlnet_enabled": False
        }
        
        success = self.manager.save_preset("My Custom Preset", preset_data)
        self.assertTrue(success)
        
        self.assertTrue((Path(self.temp_dir) / "my_custom_preset.json").is_file())
        
        loaded = self.manager.get_preset("my_custom_preset")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["name"], "My Custom Preset")
        self.assertEqual(loaded["prompt"], "Hyperdetailed futuristic city")
        self.assertEqual(loaded["cfg_scale"], 12.0)
        self.assertEqual(loaded["steps"], 50)

    def test_delete_preset_removes_from_disk(self) -> None:
        """4. delete_preset löscht das Preset-File vom Dateisystem."""
        presets_before = self.manager.list_presets()
        self.assertIn("cyberpunk", presets_before)
        
        success = self.manager.delete_preset("cyberpunk")
        self.assertTrue(success)
        
        presets_after = self.manager.list_presets()
        self.assertNotIn("cyberpunk", presets_after)
        self.assertFalse((Path(self.temp_dir) / "cyberpunk.json").exists())
