"""
HK NPU STUDIO – Phoenix Prompt Engine
Component: Prompt Edit UI Unit Tests
Sprint 74: Test Suite for Prompt-driven Image Editing UI & Workflow

Created by Senior Software Engineer (Antigravity / Gemini)
Chief Software Architect: ChatGPT
Product Owner: Holger Kreuzhofen
"""

from __future__ import annotations

import tempfile
import unittest
import tkinter as tk
from pathlib import Path

import numpy as np
from PIL import Image

from controllers.inpainting_controller import InpaintingController
from controllers.prompt_edit_controller import IntentCategory, PromptEditController, PromptEditResult
from engine.backends.sd15_qnn_inpainting_adapter import SD15QnnInpaintingResult
from widgets.phoenix.inpainting_canvas import PhoenixInpaintingCanvas
from widgets.phoenix.views.inpainting_view import PhoenixInpaintingView
from widgets.phoenix.theme import PHOENIX_THEME, update_phoenix_theme

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
    _TEST_TEMP_DIR = tempfile.TemporaryDirectory(prefix="hknpu_prompt_ui_tests_")


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


class FakeAdapter:
    def __init__(self, result=None, artifact_dir: Path | str | None = None) -> None:
        self.result = result
        self.artifact_dir = Path(artifact_dir) if artifact_dir is not None else None
        self.calls = []
        self.cancelled = False
        self.runtime = type("Runtime", (), {"CPU_AI_FALLBACK": False})()

    def run(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        callback = kwargs.get("progress_callback")
        if callback:
            callback("denoise", 0.8, "Schritt 16/20")
        if self.result is not None:
            return self.result
        out_path = args[3] if len(args) > 3 else kwargs.get("output_path", "output.png")
        if out_path:
            p = Path(out_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            # Create a dummy image
            Image.new("RGB", (64, 64), (200, 180, 50)).save(p)
        return SD15QnnInpaintingResult(success=True, output_path=out_path)

    def cancel(self) -> None:
        self.cancelled = True

    def close(self) -> None:
        pass


class TestPromptEditUI(unittest.TestCase):
    """Test suite verifying Prompt-Edit Bar, safety gates, canvas preview, and workflow."""

    def setUp(self) -> None:
        self.root = get_shared_root()
        self.temp_path = Path(_TEST_TEMP_DIR.name)
        self.output_dir = self.temp_path / "outputs"
        self.temp_dir = self.temp_path / "temp"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.fake_adapter = FakeAdapter(artifact_dir=self.output_dir)
        self.controller = InpaintingController(
            adapter=self.fake_adapter,
            ui_dispatch=lambda cb: cb(),
        )

        self.view = PhoenixInpaintingView(
            master=self.root,
            controller=self.controller,
            output_dir=self.output_dir,
            temp_dir=self.temp_dir,
        )

        # Create a test synthetic RGB image (e.g. red apple in center)
        self.test_img_path = self.temp_path / "test_apple.png"
        arr = np.zeros((128, 128, 3), dtype=np.uint8)
        arr[:] = [240, 240, 240]  # Light gray background
        # Red circle in center
        yy, xx = np.ogrid[:128, :128]
        dist = np.sqrt((xx - 64) ** 2 + (yy - 64) ** 2)
        arr[dist < 32] = [210, 30, 30]  # Red apple
        Image.fromarray(arr).save(self.test_img_path)

    def tearDown(self) -> None:
        try:
            self.view.destroy()
        except Exception:
            pass

    def test_prompt_edit_bar_widgets_exist(self) -> None:
        """Verify all Prompt-Edit widgets are instantiated and correctly positioned."""
        self.assertTrue(hasattr(self.view, "prompt_edit_bar"))
        self.assertTrue(hasattr(self.view, "prompt_edit_entry"))
        self.assertTrue(hasattr(self.view, "prompt_edit_point_btn"))
        self.assertTrue(hasattr(self.view, "prompt_edit_analyze_btn"))
        self.assertTrue(hasattr(self.view, "prompt_edit_preview_btn"))
        self.assertTrue(hasattr(self.view, "prompt_edit_compare_btn"))
        self.assertTrue(hasattr(self.view, "prompt_edit_exec_btn"))
        self.assertTrue(hasattr(self.view, "prompt_edit_reset_btn"))
        self.assertTrue(hasattr(self.view, "prompt_edit_badge"))
        self.assertTrue(hasattr(self.view, "prompt_edit_mode_label"))

    def test_analyze_without_image_shows_warning(self) -> None:
        """Verify analyzing without loading an image shows appropriate feedback."""
        self.view.prompt_edit_var.set("Verwandle den Apfel in 24k Gold")
        self.view._on_analyze_prompt()
        self.assertIn("Bitte zuerst ein Bild laden", self.view.prompt_edit_badge.cget("text"))

    def test_analyze_empty_prompt_shows_warning(self) -> None:
        """Verify empty prompt shows guidance without crashing."""
        self.view.canvas.load_image(self.test_img_path)
        self.view.prompt_edit_var.set("   ")
        self.view._on_analyze_prompt()
        self.assertIn("Bitte einen Bearbeitungsauftrag eingeben", self.view.prompt_edit_badge.cget("text"))

    def test_safety_gate_rejection_for_unknown_intent(self) -> None:
        """Verify Safety Gate 1 rejects non-editing or ambiguous prompts."""
        self.view.canvas.load_image(self.test_img_path)
        self.view.prompt_edit_var.set("Wer bist du und was kannst du tun?")
        self.view._on_analyze_prompt()

        self.assertIsNotNone(self.view.current_prompt_plan)
        self.assertFalse(self.view.current_prompt_plan.can_execute)
        self.assertEqual(self.view.current_prompt_plan.intent, IntentCategory.UNKNOWN)
        self.assertIn("Zurückgewiesen", self.view.prompt_edit_badge.cget("text"))
        self.assertEqual(self.view.prompt_edit_badge.cget("fg"), PHOENIX_THEME.danger)

    def test_analyze_valid_material_prompt(self) -> None:
        """Verify analyzing a valid material transform prompt updates plan, canvas, and inspector."""
        self.view.canvas.load_image(self.test_img_path)
        self.view.input_path = self.test_img_path
        self.view.prompt_edit_var.set("Verwandle den Apfel in 24k Gold")
        self.view._on_analyze_prompt()

        plan = self.view.current_prompt_plan
        self.assertIsNotNone(plan)
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.MATERIAL_TRANSFORM)
        self.assertEqual(plan.material_preset, "24k_gold")
        self.assertEqual(plan.controller_route, "INPAINTING_MATERIAL")

        # Verify badge feedback
        badge_text = self.view.prompt_edit_badge.cget("text")
        self.assertIn("MATERIAL_TRANSFORM", badge_text)
        self.assertIn("24k_gold", badge_text)
        self.assertEqual(self.view.prompt_edit_badge.cget("fg"), PHOENIX_THEME.accent)

        # Verify mask overlay on canvas
        self.assertTrue(self.view.canvas.has_mask())

        # Verify preview image was prepared
        self.assertIsNotNone(self.view.canvas.preview_image)
        self.assertTrue(self.view.canvas.is_showing_preview)

        # Verify inspector fields synchronization
        self.assertIn("Gold", self.view.prompt.get("1.0", "end"))
        self.assertEqual(self.view.material_preset_var.get(), "24k_gold")
        self.assertAlmostEqual(float(self.view.strength_var.get()), 0.75, places=2)

    def test_canvas_toggle_preview_and_compare(self) -> None:
        """Verify toggling preview / compare flips between original and preview."""
        self.view.canvas.load_image(self.test_img_path)
        self.view.input_path = self.test_img_path
        self.view.prompt_edit_var.set("Verwandle den Apfel in 24k Gold")
        self.view._on_analyze_prompt()

        self.assertTrue(self.view.canvas.is_showing_preview)
        self.assertIn("Vorschau", self.view.prompt_edit_mode_label.cget("text"))

        # Toggle to original
        self.view._on_toggle_compare()
        self.assertFalse(self.view.canvas.is_showing_preview)
        self.assertIn("Original", self.view.prompt_edit_mode_label.cget("text"))

        # Toggle back to preview
        self.view._on_toggle_compare()
        self.assertTrue(self.view.canvas.is_showing_preview)
        self.assertIn("Vorschau", self.view.prompt_edit_mode_label.cget("text"))

    def test_reset_prompt_edit(self) -> None:
        """Verify reset clears mask, plan, entry, and restores original image."""
        self.view.canvas.load_image(self.test_img_path)
        self.view.input_path = self.test_img_path
        self.view.prompt_edit_var.set("Verwandle den Apfel in 24k Gold")
        self.view._on_analyze_prompt()

        self.assertTrue(self.view.canvas.has_mask())
        self.assertIsNotNone(self.view.current_prompt_plan)

        # Perform reset
        self.view._on_reset_prompt_edit()
        self.assertEqual(self.view.prompt_edit_var.get(), "")
        self.assertIsNone(self.view.current_prompt_plan)
        self.assertFalse(self.view.canvas.has_mask())
        self.assertFalse(self.view.canvas.is_showing_preview)
        self.assertIn("Canvas: Original", self.view.prompt_edit_mode_label.cget("text"))

    def test_execute_prompt_edit_workflow(self) -> None:
        """Verify full execution pipeline dispatches to PromptEditController and updates UI."""
        self.view.canvas.load_image(self.test_img_path)
        self.view.input_path = self.test_img_path
        self.view.prompt_edit_var.set("Verwandle den Apfel in 24k Gold")
        self.view._on_analyze_prompt()

        # Execute synchronously in test
        self.view._on_execute_prompt_edit(asynchronous=False)

        # Process Tkinter event queue including after() callbacks
        self.root.update()

        # Verify controller received execution
        self.assertGreaterEqual(len(self.fake_adapter.calls), 1)
        self.assertIsNotNone(self.view.result_path)
        self.assertTrue(self.view.result_path.is_file())
        self.assertIn("Erfolgreich generiert", self.view.prompt_edit_badge.cget("text"))
        self.assertIn("Canvas: HTP-Ergebnis", self.view.prompt_edit_mode_label.cget("text"))

    def test_non_destructive_output_path(self) -> None:
        """Verify the original input file is strictly preserved and never overwritten."""
        self.view.canvas.load_image(self.test_img_path)
        self.view.input_path = self.test_img_path
        self.view.prompt_edit_var.set("Verwandle den Apfel in 24k Gold")
        self.view._on_analyze_prompt()
        self.view._on_execute_prompt_edit(asynchronous=False)

        self.root.update()
        self.assertIsNotNone(self.view.result_path)
        self.assertNotEqual(self.view.result_path.resolve(), self.test_img_path.resolve())
        self.assertTrue(self.test_img_path.is_file())

    def test_theme_parity(self) -> None:
        """Verify Prompt-Edit UI renders without errors in both Dark and Light themes."""
        try:
            for mode in ("dark", "light"):
                update_phoenix_theme(mode)
                test_view = PhoenixInpaintingView(
                    master=self.root,
                    controller=self.controller,
                    output_dir=self.output_dir,
                    temp_dir=self.temp_dir,
                )
                test_view.canvas.load_image(self.test_img_path)
                test_view.prompt_edit_var.set("Verwandle den Apfel in 24k Gold")
                test_view._on_analyze_prompt()
                self.root.update_idletasks()
                self.assertEqual(test_view.prompt_edit_bar.cget("bg"), PHOENIX_THEME.card_bg)
                self.assertEqual(test_view.prompt_edit_entry.cget("bg"), PHOENIX_THEME.elevated_bg)
                test_view.destroy()
        finally:
            update_phoenix_theme("dark")


if __name__ == "__main__":
    unittest.main()
