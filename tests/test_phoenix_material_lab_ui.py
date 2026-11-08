"""Unit and UI Tests for Phoenix Material Lab Integration."""
from __future__ import annotations

import tempfile
import unittest
import tkinter as tk
from pathlib import Path
from unittest.mock import MagicMock

from PIL import Image

from controllers.gallery_model import GalleryImage
from controllers.inpainting_controller import InpaintingController
from widgets.phoenix.gallery.inspector import GalleryInspector
from widgets.phoenix.views.inpainting_view import PhoenixInpaintingView

_SHARED_ROOT: tk.Tk | None = None
_TEST_TEMP_DIR: tempfile.TemporaryDirectory | None = None


def get_shared_root() -> tk.Tk:
    global _SHARED_ROOT
    if _SHARED_ROOT is None:
        _SHARED_ROOT = tk.Tk()
        _SHARED_ROOT.withdraw()
    return _SHARED_ROOT


def setUpModule() -> None:
    global _TEST_TEMP_DIR
    _TEST_TEMP_DIR = tempfile.TemporaryDirectory(prefix="mat_lab_ui_test_")


def tearDownModule() -> None:
    global _SHARED_ROOT, _TEST_TEMP_DIR
    if _TEST_TEMP_DIR is not None:
        try:
            _TEST_TEMP_DIR.cleanup()
        except Exception:
            pass
        _TEST_TEMP_DIR = None
    if _SHARED_ROOT is not None:
        try:
            _SHARED_ROOT.destroy()
        except Exception:
            pass
        _SHARED_ROOT = None


class PhoenixMaterialLabUITest(unittest.TestCase):
    """Test suite for Material Lab UI, Popup, Controller Integration and Gallery Inspector."""

    def setUp(self) -> None:
        self.root = get_shared_root()
        self.mock_controller = MagicMock(spec=InpaintingController)
        self.temp_path = Path(_TEST_TEMP_DIR.name)
        self.view = PhoenixInpaintingView(
            self.root,
            controller=self.mock_controller,
            output_dir=self.temp_path / "output",
            temp_dir=self.temp_path / "temp",
        )

    def tearDown(self) -> None:
        if hasattr(self.view, "_close_material_lab_popup"):
            self.view._close_material_lab_popup()
        self.view.destroy()

    def test_default_material_state(self) -> None:
        """Verify default state is disabled ('none') and existing inpainting is untouched."""
        self.assertEqual(self.view.material_preset_var.get(), "none")
        self.assertEqual(self.view.material_intensity_var.get(), 100)
        self.assertIn("Deaktiviert", self.view.material_status_label.cget("text"))
        self.assertEqual(self.view.material_popup_btn.text, "Material auswählen...")
        self.assertEqual(self.view.material_popup_btn.button_type, "neutral")

    def test_popup_lifecycle_and_selection(self) -> None:
        """Verify popup opens, presents all 5 options, updates selection, and applies."""
        self.view._open_material_lab_popup()
        popup = self.view._material_popup
        self.assertIsNotNone(popup)
        self.assertTrue(popup.winfo_exists())

        # Check all 5 presets buttons are present
        buttons = self.view._popup_material_buttons
        self.assertIn("none", buttons)
        self.assertIn("24k_gold", buttons)
        self.assertIn("antique_brass", buttons)
        self.assertIn("copper", buttons)
        self.assertIn("chrome", buttons)

        # Select 24k Gold
        self.view._set_popup_temp_preset("24k_gold")
        self.assertEqual(self.view._popup_temp_preset, "24k_gold")
        self.assertEqual(buttons["24k_gold"].button_type, "nav_active")
        self.assertEqual(buttons["none"].button_type, "neutral")

        # Adjust intensity to 85%
        self.view.material_intensity_var.set(85)

        # Apply popup
        self.view._apply_material_lab_popup()
        self.assertIsNone(self.view._material_popup)
        self.assertEqual(self.view.material_preset_var.get(), "24k_gold")
        self.assertEqual(self.view.material_intensity_var.get(), 85)
        self.assertIn("24k Gold (85%)", self.view.material_status_label.cget("text"))
        self.assertEqual(self.view.material_popup_btn.button_type, "nav_active")

    def test_reset_material_preset(self) -> None:
        """Verify resetting clears preset back to 'none'."""
        self.view.material_preset_var.set("copper")
        self.view.material_intensity_var.set(90)
        self.view._update_material_ui_indicators()
        self.assertEqual(self.view.material_popup_btn.button_type, "nav_active")

        # Reset
        self.view._reset_material_preset()
        self.assertEqual(self.view.material_preset_var.get(), "none")
        self.assertEqual(self.view.material_intensity_var.get(), 100)
        self.assertIn("Deaktiviert", self.view.material_status_label.cget("text"))
        self.assertEqual(self.view.material_popup_btn.button_type, "neutral")

    def test_prompt_suggestion_auto_fill(self) -> None:
        """Verify prompt suggestion populates recommended prompts."""
        self.view._open_material_lab_popup()
        self.view._set_popup_temp_preset("24k_gold")
        self.view._apply_material_prompt_suggestion()

        prompt_text = self.view.prompt.get("1.0", "end").strip()
        self.assertIn("24k gold", prompt_text.lower())
        self.assertIn("metallic", prompt_text.lower())

        neg_prompt_text = self.view.negative_prompt.get("1.0", "end").strip()
        self.assertIn("glass", neg_prompt_text.lower())
        self.assertEqual(self.view.steps.get(), 10)
        self.assertAlmostEqual(self.view.strength_var.get(), 0.40)
        self.view._close_material_lab_popup()

    def test_start_dispatches_material_preset_to_controller(self) -> None:
        """Verify start passes material_preset and intensity when selected."""
        img_path = self.temp_path / "test_input.png"
        Image.new("RGB", (64, 64), (100, 100, 100)).save(img_path)
        self.view.input_path = img_path
        self.view.canvas.mask = Image.new("L", (64, 64), 255)
        self.view.prompt.insert("1.0", "test prompt")

        # 1. Test unprimed (default)
        self.view.material_preset_var.set("none")
        self.view._start()
        self.mock_controller.start.assert_called_once()
        _, kwargs = self.mock_controller.start.call_args
        self.assertIsNone(kwargs["material_preset"])

        self.mock_controller.reset_mock()

        # 2. Test primed
        self.view.material_preset_var.set("24k_gold")
        self.view.material_intensity_var.set(90)
        self.view._start()
        self.mock_controller.start.assert_called_once()
        _, kwargs2 = self.mock_controller.start.call_args
        self.assertEqual(kwargs2["material_preset"], "24k_gold")
        self.assertAlmostEqual(kwargs2["material_priming_intensity"], 0.90)

    def test_gallery_inspector_material_priming_display(self) -> None:
        """Verify GalleryInspector formats Material Priming and remains backward compatible."""
        inspector = GalleryInspector(self.root)

        # 1. Image with Material Priming metadata
        img_with_mat = GalleryImage(
            path=self.temp_path / "img_mat.png",
            filename="img_mat.png",
            extension=".png",
            width=512,
            height=512,
            file_size=1024,
            prompt="golden sculpture",
            model_id="sd15",
            metadata={
                "feature": "Inpainting",
                "material_preset": "24k_gold",
                "material_priming_intensity": 1.0,
                "backend": "Qualcomm SD1.5 Inpainting QNN (HTP)",
            },
        )
        inspector.update_selection([img_with_mat])
        gen_labels = [child.cget("text") for child in inspector.generation_card.grid_slaves() if isinstance(child, tk.Label)]
        self.assertTrue(any("Material-Priming: 24k Gold (100%)" in line for line in gen_labels))

        # 2. Legacy image without Material Priming metadata
        legacy_img = GalleryImage(
            path=self.temp_path / "img_legacy.png",
            filename="img_legacy.png",
            extension=".png",
            width=512,
            height=512,
            file_size=1024,
            prompt="legacy cat",
            model_id="sd15",
            metadata={
                "feature": "Inpainting",
                "backend": "Qualcomm SD1.5 Inpainting QNN (HTP)",
            },
        )
        inspector.update_selection([legacy_img])
        legacy_labels = [child.cget("text") for child in inspector.generation_card.grid_slaves() if isinstance(child, tk.Label)]
        self.assertFalse(any("Material-Priming" in line for line in legacy_labels))
        inspector.destroy()


if __name__ == "__main__":
    unittest.main()
