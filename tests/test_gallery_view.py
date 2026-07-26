from __future__ import annotations

import unittest
import tkinter as tk
from pathlib import Path

from controllers.gallery_model import GalleryImage
from widgets.phoenix.gallery.inspector import GalleryInspector
from app.i18n import set_language


class GalleryInspectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        set_language("de_DE")
        self.apply_callback_args = []
        self.inspector = GalleryInspector(
            self.root,
            on_apply_settings=lambda s: self.apply_callback_args.append(s)
        )

    def test_default_state_hides_apply_button(self) -> None:
        """1. Standardzustand (keine Auswahl) blendet Übernahme-Button aus."""
        self.inspector.update_selection([])
        self.assertEqual(self.inspector.apply_btn.grid_info(), {})

    def test_multiple_selection_hides_apply_button(self) -> None:
        """2. Mehrfachauswahl blendet Übernahme-Button aus."""
        img1 = GalleryImage(Path("img1.png"), "img1.png", ".png", 512, 512, 1024)
        img2 = GalleryImage(Path("img2.png"), "img2.png", ".png", 512, 512, 1024)
        
        self.inspector.update_selection([img1, img2])
        self.assertEqual(self.inspector.apply_btn.grid_info(), {})

    def test_single_selection_shows_apply_button_and_populates_inspector(self) -> None:
        """3. Einzelbildauswahl blendet Übernahme-Button ein und befüllt Details."""
        metadata = {
            "prompt": "Test Prompt",
            "negative_prompt": "Test Neg Prompt",
            "model": "controlnet_canny_qnn",
            "steps": 20,
            "cfg_scale": 7.5,
            "sampler": "Euler",
            "scheduler": "Euler",
            "controlnet_enabled": True,
            "canny_low_threshold": 50,
            "canny_high_threshold": 150,
            "controlnet_conditioning_scale": 1.0,
            "reference_image_path": "ref.png"
        }
        image = GalleryImage(
            path=Path("img1.png"),
            filename="img1.png",
            extension=".png",
            width=512,
            height=512,
            file_size=1024,
            prompt="Test Prompt",
            model_id="controlnet_canny_qnn",
            seed=42,
            metadata=metadata
        )

        self.inspector.update_selection([image])
        self.assertNotEqual(self.inspector.apply_btn.grid_info(), {})

        self.inspector.apply_btn.invoke()

        self.assertEqual(len(self.apply_callback_args), 1)
        settings = self.apply_callback_args[0]
        self.assertEqual(settings["prompt"], "Test Prompt")
        self.assertEqual(settings["negative_prompt"], "Test Neg Prompt")
        self.assertEqual(settings["model"], "controlnet_canny_qnn")
        self.assertEqual(settings["steps"], 20)
        self.assertEqual(settings["cfg_scale"], 7.5)
        self.assertEqual(settings["controlnet_enabled"], True)
        self.assertEqual(settings["canny_low_threshold"], 50)
        self.assertEqual(settings["canny_high_threshold"], 150)
        self.assertEqual(settings["controlnet_conditioning_scale"], 1.0)
        self.assertEqual(settings["reference_image_path"], "ref.png")
        self.assertEqual(settings["seed"], 42)

    def test_english_translation_lookup_on_inspector(self) -> None:
        """4. Sprachumstellung (de -> en) aktualisiert Inspector-Labels."""
        set_language("en_US")
        inspector_en = GalleryInspector(self.root)
        self.assertEqual(inspector_en.apply_btn.cget("text"), "Open in AI Generate")
