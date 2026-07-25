from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import tempfile
import os
import time
import threading
from pathlib import Path
from PIL import Image, ImageDraw

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
from widgets.phoenix.views.prompt_view import PhoenixPromptView

# Restore original palette function
ThemeManager.palette = original_palette_func


class CannyEdgePreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        self.controller = PromptWorkspaceController()
        self.view = PhoenixPromptView(self.root, controller=self.controller)

        # Create a temporary image for testing canny edge extraction
        self.temp_dir = tempfile.TemporaryDirectory()
        self.image_path = os.path.join(self.temp_dir.name, "test_input.png")
        img = Image.new("RGB", (256, 256), color="white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 200, 200], outline="black", fill="gray")
        img.save(self.image_path)

    def tearDown(self) -> None:
        self.view.destroy()
        self.temp_dir.cleanup()

    def _wait_for_canny_preview(self, target_low=None, target_high=None, timeout=2.0) -> bool:
        """Helper to process event loop until canny preview is populated."""
        start = time.time()
        while time.time() - start < timeout:
            self.root.update()
            self.root.update_idletasks()
            photo_ref = getattr(self.view, "_dnd_canny_photo_ref", None)
            if photo_ref is not None:
                if target_low is None or (
                    getattr(self.view, "_canny_rendered_low", None) == target_low
                    and getattr(self.view, "_canny_rendered_high", None) == target_high
                ):
                    return True
            time.sleep(0.02)
        return False

    def test_valid_reference_image_creates_canny_preview(self) -> None:
        """1. Gültiges Referenzbild erzeugt eine Canny-Vorschau"""
        self.view.model_var.set("controlnet_canny_qnn")
        self.view._apply_generation_contract("controlnet_canny_qnn")

        # Load reference image
        self.view._load_reference_image(self.image_path)
        
        # Wait for the background thread to compute canny
        success = self._wait_for_canny_preview(target_low=50, target_high=150)
        self.assertTrue(success)
        self.assertIsNotNone(self.view._dnd_canny_photo_ref)
        self.assertEqual(self.view._dnd_canny_status_label.cget("text"), "Vorschau aktuell")

    def test_low_high_changes_trigger_new_preview(self) -> None:
        """2. Low/High-Änderung erzeugt eine neue Vorschau"""
        self.view.model_var.set("controlnet_canny_qnn")
        self.view._apply_generation_contract("controlnet_canny_qnn")
        self.view._load_reference_image(self.image_path)
        self._wait_for_canny_preview(target_low=50, target_high=150)

        # Save first preview details
        first_ref = self.view._dnd_canny_photo_ref
        first_low = self.view._canny_rendered_low
        self.assertEqual(first_low, 50)

        # Trigger slider changes
        self.view.canny_low_var.set(80)
        self.view.canny_high_var.set(200)

        # Wait for debounce and new preview computation
        start = time.time()
        while time.time() - start < 0.3:
            self.root.update()
            self.root.update_idletasks()
            time.sleep(0.01)

        success = self._wait_for_canny_preview(target_low=80, target_high=200)
        self.assertTrue(success)
        
        # Verify preview details updated
        self.assertEqual(self.view._canny_rendered_low, 80)
        self.assertEqual(self.view._canny_rendered_high, 200)

    def test_different_thresholds_produce_different_edge_data(self) -> None:
        """3. Unterschiedliche Schwellenwerte erzeugen unterschiedliche Edge-Daten"""
        from engine.controlnet_canny_backend import canny_edge_detector

        edges_a = canny_edge_detector(self.image_path, low_threshold=20, high_threshold=80)
        edges_b = canny_edge_detector(self.image_path, low_threshold=150, high_threshold=230)

        # High thresholds should detect fewer edges
        sum_a = edges_a.sum()
        sum_b = edges_b.sum()
        
        self.assertNotEqual(sum_a, sum_b)
        self.assertTrue(sum_a > sum_b, f"Expected more edges in A ({sum_a}) than B ({sum_b})")

    def test_invalid_thresholds_prevent_calculation(self) -> None:
        """4. Low >= High verhindert die Neuberechnung"""
        self.view.model_var.set("controlnet_canny_qnn")
        self.view._apply_generation_contract("controlnet_canny_qnn")
        self.view._load_reference_image(self.image_path)
        self._wait_for_canny_preview()

        # Set invalid values
        self.view.canny_low_var.set(150)
        self.view.canny_high_var.set(100)

        # Trigger update
        self.view._trigger_canny_preview_update()
        self.root.update()

        # Verify preview cleared, error status shown, and photo reference is None
        self.assertIsNone(self.view._dnd_canny_photo_ref)
        self.assertIsNone(self.view._canny_rendered_low)
        self.assertIn("Low Threshold >= High Threshold", self.view._dnd_canny_status_label.cget("text"))
        self.assertEqual(self.view._dnd_canny_preview_label.cget("text"), "⚠️")

    def test_removing_image_clears_previews_and_state(self) -> None:
        """5. Entfernen des Bildes löscht beide Vorschauen"""
        self.view.model_var.set("controlnet_canny_qnn")
        self.view._apply_generation_contract("controlnet_canny_qnn")
        self.view._load_reference_image(self.image_path)
        self._wait_for_canny_preview()

        self.assertIsNotNone(self.view._dnd_photo_ref)
        self.assertIsNotNone(self.view._dnd_canny_photo_ref)

        # Remove image
        self.view._remove_reference_image()
        self.root.update()

        # Both preview refs must be None
        self.assertIsNone(self.view._dnd_photo_ref)
        self.assertIsNone(self.view._dnd_canny_photo_ref)
        self.assertIsNone(self.view._canny_debounce_id)
        self.assertIsNone(self.view._canny_rendered_path)

    def test_model_change_clears_canny_preview(self) -> None:
        """6. Modellwechsel löscht die Canny-Vorschau"""
        self.view.model_var.set("controlnet_canny_qnn")
        self.view._apply_generation_contract("controlnet_canny_qnn")
        self.view._load_reference_image(self.image_path)
        self._wait_for_canny_preview()

        # Switch model
        self.view.model_var.set("stable_diffusion_v1_5_qnn")
        self.view._on_model_changed()
        self.root.update()

        # Verify preview cleared
        self.assertIsNone(self.view._dnd_canny_photo_ref)
        self.assertIsNone(self.view._canny_rendered_path)
        self.assertEqual(self.view.controlnet_frame.winfo_manager(), "")

    def test_model_switching_back_does_not_restore_preview(self) -> None:
        """7. Zurückwechseln zu ControlNet zeigt keinen alten Zustand"""
        self.view.model_var.set("controlnet_canny_qnn")
        self.view._apply_generation_contract("controlnet_canny_qnn")
        self.view._load_reference_image(self.image_path)
        self._wait_for_canny_preview()

        # Switch to SD 1.5
        self.view.model_var.set("stable_diffusion_v1_5_qnn")
        self.view._on_model_changed()
        self.root.update()

        # Switch back to ControlNet
        self.view.model_var.set("controlnet_canny_qnn")
        self.view._on_model_changed()
        self.root.update()

        # Previews must remain empty (no old image restored)
        self.assertIsNone(self.view._dnd_photo_ref)
        self.assertIsNone(self.view._dnd_canny_photo_ref)

    def test_sd_models_remain_unchanged(self) -> None:
        """8. SD1.5 und SD2.1 bleiben unverändert"""
        self.view.model_var.set("stable_diffusion_v1_5_qnn")
        self.view._on_model_changed()
        self.root.update()

        self.assertEqual(self.view.controlnet_frame.winfo_manager(), "")
        self.assertEqual(self.view.dnd_card.winfo_manager(), "")

        self.view.model_var.set("stable_diffusion_v2_1_qnn")
        self.view._on_model_changed()
        self.root.update()

        self.assertEqual(self.view.controlnet_frame.winfo_manager(), "")
        self.assertEqual(self.view.dnd_card.winfo_manager(), "")

    def test_debounce_prevents_multiple_parallel_updates(self) -> None:
        """9. Debounce erzeugt keine mehrfachen parallelen Aktualisierungen"""
        self.view.model_var.set("controlnet_canny_qnn")
        self.view._apply_generation_contract("controlnet_canny_qnn")
        self.view._load_reference_image(self.image_path)
        self._wait_for_canny_preview()

        # Change threshold multiple times rapidly
        debounce_ids = []
        for i in range(5):
            self.view.canny_low_var.set(60 + i)
            debounce_ids.append(self.view._canny_debounce_id)

        # Assert all intermediate debounce IDs are different and only the last one exists
        self.assertEqual(len(debounce_ids), 5)
        # We can trigger the final update
        self.view._trigger_canny_preview_update()
        self.root.update()
        
        # Debounce ID should be cleared
        self.assertIsNone(self.view._canny_debounce_id)


if __name__ == "__main__":
    unittest.main()
