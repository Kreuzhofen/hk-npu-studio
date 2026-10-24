from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_default_directory_uses_central_writable_path(self) -> None:
        default_dir = Path(self.temp_dir) / "data" / "presets"
        with patch("config.PRESETS_DIR", default_dir):
            manager = PresetManager()
            self.assertTrue(manager.save_preset("Portable", {"prompt": "test"}))

        self.assertEqual(default_dir, manager.preset_dir)
        self.assertTrue((default_dir / "portable.json").is_file())

    def test_frozen_app_copies_missing_bundled_presets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundled_dir = root / "bundle" / "data" / "presets"
            target_dir = root / "user" / "data" / "presets"
            bundled_dir.mkdir(parents=True)
            expected_bytes = b'{"name":"Bundled only","prompt":"kept exactly"}\n'
            (bundled_dir / "bundled_only.json").write_bytes(expected_bytes)

            with patch.object(sys, "frozen", True, create=True), \
                 patch("config.BASE", root / "bundle"):
                PresetManager(preset_dir=target_dir)

            self.assertEqual((target_dir / "bundled_only.json").read_bytes(), expected_bytes)

    def test_frozen_app_never_overwrites_existing_or_custom_presets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundled_dir = root / "bundle" / "data" / "presets"
            target_dir = root / "user" / "data" / "presets"
            bundled_dir.mkdir(parents=True)
            target_dir.mkdir(parents=True)
            (bundled_dir / "shared.json").write_bytes(b'{"name":"Bundled"}\n')
            existing_bytes = b'{"name":"User custom","prompt":"do not overwrite"}\n'
            (target_dir / "shared.json").write_bytes(existing_bytes)
            (target_dir / "my_custom.json").write_bytes(b'{"name":"My custom"}\n')

            with patch.object(sys, "frozen", True, create=True), \
                 patch("config.BASE", root / "bundle"):
                PresetManager(preset_dir=target_dir)

            self.assertEqual((target_dir / "shared.json").read_bytes(), existing_bytes)
            self.assertEqual(
                (target_dir / "my_custom.json").read_bytes(), b'{"name":"My custom"}\n'
            )

    def test_missing_frozen_bundle_keeps_default_initialization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target_dir = root / "user" / "data" / "presets"

            with patch.object(sys, "frozen", True, create=True), \
                 patch("config.BASE", root / "missing_bundle"):
                manager = PresetManager(preset_dir=target_dir)

            self.assertIn("default", manager.list_presets())

    def test_identical_bundle_and_writable_directories_do_not_copy_to_self(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target_dir = root / "data" / "presets"
            target_dir.mkdir(parents=True)
            (target_dir / "bundle.json").write_text('{"name":"Bundled"}\n', encoding="utf-8")

            with patch.object(sys, "frozen", True, create=True), \
                 patch("config.BASE", root), \
                 patch("app.preset_manager.shutil.copyfile") as copy_file:
                PresetManager(preset_dir=target_dir)

            copy_file.assert_not_called()

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

    def test_complete_generation_preset_round_trip(self) -> None:
        preset_data = {
            "prompt": "Mountain road",
            "negative_prompt": "blurry",
            "model_name": "sdxl_base",
            "backend": "CPUExecutionProvider",
            "seed": 12345,
            "width": 512,
            "height": 512,
            "steps": 30,
            "cfg_scale": 7.0,
            "sampler": "Euler a",
            "scheduler": "Normal",
            "batch": 4,
            "controlnet_enabled": True,
            "canny_low_threshold": 40,
            "canny_high_threshold": 140,
            "controlnet_conditioning_scale": 0.75,
            "reference_image_path": "C:/images/reference.png",
        }

        self.assertTrue(self.manager.save_preset("Complete", preset_data))
        self.assertEqual(self.manager.get_preset("complete"), {"name": "Complete", **preset_data})

    def test_preset_exists_uses_normalized_name(self) -> None:
        self.assertTrue(self.manager.save_preset("My Preset", {"prompt": "first"}))
        self.assertTrue(self.manager.preset_exists("My Preset"))
        self.assertTrue(self.manager.preset_exists("my_preset"))
        self.assertFalse(self.manager.preset_exists("Missing"))

    def test_delete_preset_removes_from_disk(self) -> None:
        """4. delete_preset löscht das Preset-File vom Dateisystem."""
        presets_before = self.manager.list_presets()
        self.assertIn("cyberpunk", presets_before)
        
        success = self.manager.delete_preset("cyberpunk")
        self.assertTrue(success)
        
        presets_after = self.manager.list_presets()
        self.assertNotIn("cyberpunk", presets_after)
        self.assertFalse((Path(self.temp_dir) / "cyberpunk.json").exists())
