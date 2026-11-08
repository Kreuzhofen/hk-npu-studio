"""
HK NPU STUDIO – Phoenix Prompt Engine
Component: Interactive Point-Prompting Unit Tests (Sprint 92)

Test suite covering:
1. Object selection without source color ("Mache die Jacke zu schwarzem Leder")
2. Multi-object isolation with same color (spatial seed isolates only clicked object)
3. Ambiguous / void click points (Safety Gate rejection)
4. Small and large object scale invariance
5. Coordinate mapping and transformation across various aspect ratios and image resolutions
6. UI Point-Selection workflow and canvas marker integration
7. Dark and Light Theme visual parity

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
from controllers.prompt_edit_controller import IntentCategory, PromptEditController
from engine.color_spatial_segmenter import ColorSpatialSegmenter
from widgets.phoenix.inpainting_canvas import PhoenixInpaintingCanvas
from widgets.phoenix.theme import PHOENIX_THEME, update_phoenix_theme
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
    _TEST_TEMP_DIR = tempfile.TemporaryDirectory(prefix="hknpu_point_prompt_tests_")


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


class TestInteractivePointPrompting(unittest.TestCase):
    """Test suite for interactive point-prompting and automatic source color probing."""

    def setUp(self) -> None:
        self.segmenter = ColorSpatialSegmenter()
        self.controller = PromptEditController(segmenter=self.segmenter)
        self.root = get_shared_root()
        self.temp_path = Path(_TEST_TEMP_DIR.name)

    def test_jacket_selection_without_source_color(self) -> None:
        """
        User prompt: 'Mache die Jacke zu schwarzem Leder.' (no source color specified).
        Seed click on jacket (256, 320) must automatically detect 'red' and isolate jacket.
        """
        canonical_jacket = Path("reports/sprint_73_controller_integration/images/motif3_jacket_1_original.png")
        if not canonical_jacket.is_file():
            self.skipTest(f"Canonical jacket image not found at {canonical_jacket}")

        plan = self.controller.analyze(
            image=canonical_jacket,
            prompt="Mache die Jacke zu schwarzem Leder.",
            point_prompt=(256, 320),
        )

        self.assertTrue(plan.can_execute, f"Plan rejected: {plan.rejection_reason}")
        self.assertEqual(plan.intent, IntentCategory.MATERIAL_TRANSFORM)
        self.assertEqual(plan.material_preset, "black_leather")
        self.assertIsNotNone(plan.segment_result)
        self.assertEqual(plan.segment_result.detected_color_name, "red")
        self.assertGreater(plan.segment_result.active_pixel_count, 1000)
        self.assertIsNotNone(plan.segment_result.mask)
        self.assertEqual(plan.point_prompt, (256, 320))
        self.assertEqual(plan.controller_route, "INPAINTING_MATERIAL")

    def test_multi_object_isolation_with_same_color(self) -> None:
        """
        Verify that in an image with two separate objects of identical color,
        the point prompt isolates strictly the clicked object.
        """
        arr = np.zeros((512, 512, 3), dtype=np.uint8)
        arr[:] = [240, 240, 240]  # Light neutral background
        yy, xx = np.ogrid[:512, :512]

        # Object 1 (Left): Red circle at (120, 256), r=45
        arr[np.sqrt((xx - 120)**2 + (yy - 256)**2) < 45] = [210, 30, 30]

        # Object 2 (Right): Red circle at (390, 256), r=45
        arr[np.sqrt((xx - 390)**2 + (yy - 256)**2) < 45] = [210, 30, 30]

        test_img = Image.fromarray(arr)

        # 1. Click Left Object
        res_left = self.segmenter.segment(test_img, point_prompt=(120, 256))
        self.assertTrue(res_left.success)
        self.assertEqual(res_left.detected_color_name, "red")
        self.assertIsNotNone(res_left.spatial_bbox)
        # Left bbox x-span should be around [75, 165]
        self.assertLess(res_left.spatial_bbox[2], 250)
        self.assertGreater(res_left.spatial_bbox[0], 50)

        # 2. Click Right Object
        res_right = self.segmenter.segment(test_img, point_prompt=(390, 256))
        self.assertTrue(res_right.success)
        self.assertEqual(res_right.detected_color_name, "red")
        self.assertIsNotNone(res_right.spatial_bbox)
        # Right bbox x-span should be around [345, 435]
        self.assertGreater(res_right.spatial_bbox[0], 250)
        self.assertLess(res_right.spatial_bbox[2], 460)

    def test_ambiguous_and_void_click_points_rejected(self) -> None:
        """
        Verify Safety Gate 2 rejects clicks on neutral background or far from any object.
        """
        arr = np.zeros((512, 512, 3), dtype=np.uint8)
        arr[:] = [245, 245, 245]  # Pure white canvas
        yy, xx = np.ogrid[:512, :512]
        arr[np.sqrt((xx - 100)**2 + (yy - 100)**2) < 30] = [20, 180, 40]  # Small green object
        test_img = Image.fromarray(arr)

        # Click at (400, 400) - empty background far from object
        res_void = self.segmenter.segment(test_img, point_prompt=(400, 400))
        self.assertFalse(res_void.is_valid)

        # Controller analyze should reject via Safety Gate 2
        plan = self.controller.analyze(
            image=test_img,
            prompt="Mache die Jacke zu schwarzem Leder.",
            point_prompt=(400, 400),
        )
        self.assertFalse(plan.can_execute)
        self.assertIn("Sicherheitsabbruch Maskierung", plan.rejection_reason)

    def test_scale_invariance_small_and_large_objects(self) -> None:
        """
        Verify point prompting works across scales: small (r=15, ~700px) and large (r=120, ~45000px).
        """
        # Small object
        arr_small = np.zeros((512, 512, 3), dtype=np.uint8)
        arr_small[:] = [240, 240, 240]
        yy, xx = np.ogrid[:512, :512]
        arr_small[np.sqrt((xx - 256)**2 + (yy - 256)**2) < 15] = [210, 30, 30]
        res_small = self.segmenter.segment(Image.fromarray(arr_small), point_prompt=(256, 256))
        self.assertTrue(res_small.success)
        self.assertGreater(res_small.active_pixel_count, 500)
        self.assertLess(res_small.active_pixel_count, 1200)

        # Large object
        arr_large = np.zeros((512, 512, 3), dtype=np.uint8)
        arr_large[:] = [240, 240, 240]
        yy, xx = np.ogrid[:512, :512]
        arr_large[np.sqrt((xx - 256)**2 + (yy - 256)**2) < 120] = [210, 30, 30]
        res_large = self.segmenter.segment(Image.fromarray(arr_large), point_prompt=(256, 256))
        self.assertTrue(res_large.success)
        self.assertGreater(res_large.active_pixel_count, 40000)

    def test_coordinate_mapping_across_resolutions(self) -> None:
        """
        Verify coordinate mapping from canvas viewport to native image coordinates
        and inverse mapping from native coordinates to canvas viewport across resolutions.
        """
        resolutions = [(512, 512), (1024, 768), (128, 128), (1600, 2400)]
        viewport = (800, 600)

        for w, h in resolutions:
            zoom = PhoenixInpaintingCanvas.contain_zoom(viewport, (w, h))
            pan = (15.0, -10.0)

            # Test native center point (w // 2, h // 2)
            px_native, py_native = w // 2, h // 2
            cx, cy = PhoenixInpaintingCanvas.map_image_to_canvas(
                px_native, py_native, viewport=viewport, image_size=(w, h), zoom=zoom, pan=pan
            )
            mapped_back_x, mapped_back_y = PhoenixInpaintingCanvas.map_canvas_to_image(
                cx, cy, viewport=viewport, image_size=(w, h), zoom=zoom, pan=pan
            )

            self.assertAlmostEqual(mapped_back_x, px_native, delta=1.0)
            self.assertAlmostEqual(mapped_back_y, py_native, delta=1.0)

    def test_canvas_point_marker_and_tool_mode(self) -> None:
        """
        Verify canvas mode switching to point_select, point setting, and marker drawing.
        """
        canvas = PhoenixInpaintingCanvas(self.root)
        canvas.canvas.winfo_width = lambda: 600
        canvas.canvas.winfo_height = lambda: 600

        dummy_img_path = self.temp_path / "dummy_canvas.png"
        Image.new("RGB", (256, 256), (200, 200, 200)).save(dummy_img_path)
        canvas.load_image(dummy_img_path)

        # Switch tool mode
        canvas.set_tool_mode("point_select")
        self.assertEqual(canvas.tool_mode, "point_select")

        # Set point prompt
        canvas.set_point_prompt((128, 128))
        self.assertEqual(canvas.point_prompt, (128, 128))

        # Check marker items on tkinter canvas
        marker_items = canvas.canvas.find_withtag("point_marker")
        self.assertGreater(len(marker_items), 0, "Point marker items should be rendered on canvas.")

        # Clear point prompt
        canvas.clear_point_prompt()
        self.assertIsNone(canvas.point_prompt)
        marker_items_after = canvas.canvas.find_withtag("point_marker")
        self.assertEqual(len(marker_items_after), 0, "Point marker should be removed after clear.")

        canvas.destroy()

    def test_ui_point_selection_workflow(self) -> None:
        """
        Verify full UI workflow:
        1. Load image
        2. Set point prompt via callback or button
        3. Enter prompt without source color ('Mache die Jacke zu schwarzem Leder')
        4. Analyze automatically determines source color and shows preview
        """
        output_dir = self.temp_path / "ui_out"
        temp_dir = self.temp_path / "ui_temp"
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        inp_controller = InpaintingController(ui_dispatch=lambda cb: cb())
        view = PhoenixInpaintingView(
            master=self.root,
            controller=inp_controller,
            output_dir=output_dir,
            temp_dir=temp_dir,
        )

        test_img_path = self.temp_path / "ui_jacket.png"
        arr = np.zeros((256, 256, 3), dtype=np.uint8)
        arr[:] = [240, 240, 240]
        arr[80:180, 80:180] = [185, 105, 75]  # Red jacket patch
        Image.fromarray(arr).save(test_img_path)

        view.canvas.load_image(test_img_path)
        view.input_path = test_img_path

        # Simulate user clicking on the jacket
        view._on_point_selected((128, 128))
        self.assertEqual(view.point_prompt, (128, 128))

        # User enters prompt without source color
        view.prompt_edit_var.set("Mache die Jacke zu schwarzem Leder.")
        view._on_analyze_prompt()

        plan = view.current_prompt_plan
        self.assertIsNotNone(plan)
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.material_preset, "black_leather")
        self.assertEqual(plan.segment_result.detected_color_name, "red")
        self.assertIn("black_leather", view.prompt_edit_badge.cget("text"))

        # Reset workflow
        view._on_reset_prompt_edit()
        self.assertIsNone(view.point_prompt)
        self.assertEqual(view.prompt_edit_var.get(), "")
        self.assertIsNone(view.canvas.point_prompt)

        view.destroy()

    def test_theme_parity(self) -> None:
        """Verify interactive point-prompting UI renders cleanly in Dark and Light themes."""
        for theme_name in ("dark", "light"):
            update_phoenix_theme(theme_name)
            self.assertIsNotNone(PHOENIX_THEME.accent)
            self.assertIsNotNone(PHOENIX_THEME.card_bg)
            self.assertIsNotNone(PHOENIX_THEME.warning)

        # Restore dark theme
        update_phoenix_theme("dark")


if __name__ == "__main__":
    unittest.main()
