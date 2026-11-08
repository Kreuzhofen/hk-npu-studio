from __future__ import annotations

import inspect
import tempfile
import unittest
import tkinter as tk
from types import SimpleNamespace
from pathlib import Path

from PIL import Image

from controllers.inpainting_controller import InpaintingController
from engine.backends.sd15_qnn_inpainting_adapter import (
    SD15QnnInpaintingAdapter,
    SD15QnnInpaintingResult,
    EulerScheduler,
)
from widgets.phoenix.inpainting_canvas import PhoenixInpaintingCanvas
from widgets.phoenix.views.inpainting_view import PhoenixInpaintingView
from widgets.phoenix.views.image_lab_view import PhoenixImageLabView
from widgets.phoenix.workspace import PhoenixWorkspace
from widgets.phoenix.theme import PHOENIX_THEME, update_phoenix_theme

# Compatibility alias for legacy tests
RORemDlcResult = SD15QnnInpaintingResult

_SHARED_ROOT: tk.Tk | None = None
_TEST_TEMP_DIR: tempfile.TemporaryDirectory | None = None
_ORIGINAL_OUTPUT_DIR: Path | None = None


def get_shared_root() -> tk.Tk:
    global _SHARED_ROOT
    if _SHARED_ROOT is None:
        _SHARED_ROOT = tk.Tk()
    return _SHARED_ROOT


def setUpModule() -> None:
    global _TEST_TEMP_DIR, _ORIGINAL_OUTPUT_DIR
    _TEST_TEMP_DIR = tempfile.TemporaryDirectory(prefix="hknpu_ui_tests_out_")
    import widgets.phoenix.views.inpainting_view as iv
    _ORIGINAL_OUTPUT_DIR = iv.OUTPUT_DIR
    iv.OUTPUT_DIR = Path(_TEST_TEMP_DIR.name)


def tearDownModule() -> None:
    global _SHARED_ROOT, _TEST_TEMP_DIR, _ORIGINAL_OUTPUT_DIR
    if _ORIGINAL_OUTPUT_DIR is not None:
        import widgets.phoenix.views.inpainting_view as iv
        iv.OUTPUT_DIR = _ORIGINAL_OUTPUT_DIR
        _ORIGINAL_OUTPUT_DIR = None
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
            callback("denoise", 0.75, "Schritt 15/20")
        if self.result is not None:
            return self.result
        out_path = args[3] if len(args) > 3 else kwargs.get("output_path", "output.png")
        if out_path:
            p = Path(out_path)
            # Guard: Strictly prevent test artifacts from polluting production output folder
            from config import OUTPUT_DIR as PROD_OUTPUT_DIR
            if p.parent.resolve() == PROD_OUTPUT_DIR.resolve() or not p.is_absolute():
                target_dir = self.artifact_dir or (Path(_TEST_TEMP_DIR.name) if _TEST_TEMP_DIR else p.parent)
                p = target_dir / p.name
                out_path = str(p)
            p.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (512, 512), (120, 120, 120)).save(p)
        return SD15QnnInpaintingResult(success=True, output_path=out_path)

    def cancel(self) -> None:
        self.cancelled = True

    def close(self) -> None:
        pass


class InpaintingCanvasTests(unittest.TestCase):
    def test_load_image_keeps_native_aspect_ratio_and_mask_size(self) -> None:
        class CanvasState:
            image = None
            mask = None
            auto_fit = False
            pan_x = 1.0
            pan_y = 1.0
            render = staticmethod(lambda: None)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "landscape.png"
            Image.new("RGB", (1600, 900)).save(path)
            state = CanvasState()
            PhoenixInpaintingCanvas.load_image(state, path)

        self.assertEqual(state.image.size, (1600, 900))
        self.assertEqual(state.mask.size, (1600, 900))

    def test_stroke_undo_brush_eraser_multiple_and_limit(self) -> None:
        class Canvas(PhoenixInpaintingCanvas):
            def __init__(self):
                self.image = Image.new("RGB", (64, 64))
                self.mask = Image.new("L", (64, 64), 0)
                self.brush_size = 8
                self.erase = False
                self._reset_history()
            def render(self):
                pass
            def canvas_to_image(self, x, y):
                return (x, y)

        canvas = Canvas()
        canvas.undo()
        event = SimpleNamespace(x=20, y=20)
        canvas._paint(event)
        canvas._paint(SimpleNamespace(x=30, y=20))
        canvas._finish_stroke()
        self.assertEqual(len(canvas._undo_history), 1)
        canvas.erase = True
        canvas._paint(event)
        canvas._finish_stroke()
        self.assertEqual(canvas.mask.getpixel((20, 20)), 0)
        canvas.undo()
        self.assertEqual(canvas.mask.getpixel((20, 20)), 255)
        canvas.undo()
        self.assertEqual(canvas.mask.getextrema(), (0, 0))
        for _ in range(25):
            canvas._paint(event)
            canvas._finish_stroke()
        self.assertEqual(len(canvas._undo_history), canvas.UNDO_LIMIT)
        canvas.clear_mask()
        self.assertFalse(canvas._undo_history)

    def test_remove_image_is_session_only_and_clears_history(self) -> None:
        root = get_shared_root()
        canvas = PhoenixInpaintingCanvas(root)
        canvas.render = lambda: None
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "input.png"
                Image.new("RGB", (80, 40)).save(path)
                canvas.load_image(path)
                canvas._undo_history.append(canvas.mask.copy())
                canvas.remove_image()
                self.assertTrue(path.is_file())
                self.assertIsNone(canvas.image)
                self.assertIsNone(canvas.mask)
                self.assertFalse(canvas._undo_history)
                canvas.load_image(path)
                self.assertFalse(canvas._undo_history)
        finally:
            canvas.destroy()

    def test_responsive_buttons_dark_light_all_dpi(self) -> None:
        root = get_shared_root()
        try:
            for theme in ("dark", "light"):
                update_phoenix_theme(theme)
                for dpi in (1.0, 1.25, 1.5, 1.75):
                    root.tk.call("tk", "scaling", (96 / 72) * dpi)
                    view = PhoenixInpaintingView(root)
                    view.pack(fill="both", expand=True)
                    try:
                        self.assertEqual(view.brush_button.icon_name, "sparkles")
                        self.assertEqual(view.eraser_button.icon_name, "remove_image")
                        self.assertIsNone(view.brush_button.icon_color)
                        self.assertIsNone(view.eraser_button.icon_color)
                        rows = []
                        for width in (650, 1500, 650):
                            root.geometry(f"{width}x1000")
                            root.update()
                            rows.append(max(int(item.grid_info()["row"]) for item in view._toolbar_items))
                            if width == 1500:
                                self.assertEqual(rows[-1], 0)
                                self.assertTrue(all(int(button.grid_info()["row"]) == 0 for button in view.action_buttons))
                            for item in view._toolbar_items:
                                self.assertEqual(item.winfo_width(), item.winfo_reqwidth())
                            for item in (*view._toolbar_items, view.start_button, view.cancel_button, view.save_button):
                                self.assertTrue(item.winfo_ismapped())
                                self.assertLessEqual(item.winfo_x() + item.winfo_width(), item.master.winfo_width())
                        self.assertGreater(rows[0], rows[1])
                        self.assertEqual(rows[0], rows[2])
                    finally:
                        view.destroy()
        finally:
            update_phoenix_theme("dark")

    def test_compact_reflow_uses_content_width_breakpoints(self) -> None:
        class Item:
            def winfo_reqwidth(self):
                return 100
            def grid(self, **kwargs):
                self.position = kwargs
        class Host:
            def grid_columnconfigure(self, column, weight):
                assert weight == 0
        items = [Item() for _ in range(6)]
        cell = 100 + 2 * PHOENIX_THEME.space_xs
        for columns in (6, 4, 2, 1):
            PhoenixInpaintingView._reflow(Host(), items, columns * cell)
            self.assertEqual([item.position["row"] for item in items], [index // columns for index in range(6)])
            self.assertTrue(all(item.position["sticky"] == "w" for item in items))
        for columns in (3, 2, 1):
            PhoenixInpaintingView._reflow(Host(), items[:3], columns * cell)
            self.assertEqual([item.position["row"] for item in items[:3]], [index // columns for index in range(3)])

    def test_contain_fit_preserves_landscape_aspect_ratio(self) -> None:
        zoom = PhoenixInpaintingCanvas.contain_zoom((800, 600), (1600, 900))
        self.assertEqual((1600 * zoom, 900 * zoom), (800.0, 450.0))

    def test_contain_fit_preserves_portrait_aspect_ratio(self) -> None:
        zoom = PhoenixInpaintingCanvas.contain_zoom((800, 600), (900, 1600))
        self.assertEqual((900 * zoom, 1600 * zoom), (337.5, 600.0))

    def test_contain_fit_preserves_square_aspect_ratio(self) -> None:
        zoom = PhoenixInpaintingCanvas.contain_zoom((800, 600), (1024, 1024))
        self.assertEqual((1024 * zoom, 1024 * zoom), (600.0, 600.0))

    def test_contain_fit_recalculates_after_resize(self) -> None:
        first = PhoenixInpaintingCanvas.contain_zoom((800, 600), (1600, 900))
        second = PhoenixInpaintingCanvas.contain_zoom((1200, 600), (1600, 900))
        self.assertEqual(first, 0.5)
        self.assertAlmostEqual(second, 2 / 3)

    def test_letterbox_offsets_are_included_in_coordinate_mapping(self) -> None:
        zoom = PhoenixInpaintingCanvas.contain_zoom((800, 600), (1600, 900))
        center = PhoenixInpaintingCanvas.map_canvas_to_image(
            400, 300, viewport=(800, 600), image_size=(1600, 900), zoom=zoom, pan=(0, 0)
        )
        top_left = PhoenixInpaintingCanvas.map_canvas_to_image(
            0, 75, viewport=(800, 600), image_size=(1600, 900), zoom=zoom, pan=(0, 0)
        )
        self.assertEqual(center, (800.0, 450.0))
        self.assertEqual(top_left, (0.0, 0.0))

    def test_mask_contract_and_brush(self) -> None:
        mask = Image.new("L", (1024, 1024), 0)
        PhoenixInpaintingCanvas.paint_mask(mask, (100, 100), (140, 100), brush_size=24, erase=False)
        self.assertEqual(mask.getpixel((120, 100)), 255)
        self.assertEqual(mask.getpixel((10, 10)), 0)

    def test_eraser_clears_mask_pixels(self) -> None:
        mask = Image.new("L", (1024, 1024), 255)
        PhoenixInpaintingCanvas.paint_mask(mask, (100, 100), (140, 100), brush_size=24, erase=True)
        self.assertEqual(mask.getpixel((120, 100)), 0)

    def test_zoom_pan_coordinate_transform(self) -> None:
        point = PhoenixInpaintingCanvas.map_canvas_to_image(
            600, 450, viewport=(800, 600), image_size=(1024, 1024), zoom=0.5, pan=(20, -10)
        )
        self.assertEqual(point, (872.0, 832.0))

    def test_resize_and_dpi_mapping_use_actual_viewport(self) -> None:
        first = PhoenixInpaintingCanvas.map_canvas_to_image(
            400, 300, viewport=(800, 600), image_size=(1024, 1024), zoom=0.5, pan=(0, 0)
        )
        second = PhoenixInpaintingCanvas.map_canvas_to_image(
            800, 600, viewport=(1600, 1200), image_size=(1024, 1024), zoom=1.0, pan=(0, 0)
        )
        self.assertEqual(first, second)
        self.assertEqual(first, (512.0, 512.0))

    def test_clear_mask_contract(self) -> None:
        class CanvasState:
            image = Image.new("RGB", (1024, 1024))
            mask = Image.new("L", (1024, 1024), 255)
            render = staticmethod(lambda: None)

        state = CanvasState()
        PhoenixInpaintingCanvas.clear_mask(state)
        self.assertEqual(state.mask.getextrema(), (0, 0))

    def test_soft_brush_hardness_100_percent(self) -> None:
        mask = Image.new("L", (100, 100), 0)
        PhoenixInpaintingCanvas.paint_mask(mask, (50, 50), (50, 50), brush_size=40, hardness=1.0, erase=False)
        self.assertEqual(mask.getpixel((50, 50)), 255)
        self.assertEqual(mask.getpixel((50, 65)), 255)
        self.assertEqual(mask.getpixel((50, 75)), 0)

    def test_soft_brush_hardness_50_percent(self) -> None:
        mask = Image.new("L", (100, 100), 0)
        PhoenixInpaintingCanvas.paint_mask(mask, (50, 50), (50, 50), brush_size=40, hardness=0.5, erase=False)
        self.assertEqual(mask.getpixel((50, 50)), 255)
        self.assertEqual(mask.getpixel((50, 60)), 255)
        mid_val = mask.getpixel((50, 65))
        self.assertTrue(110 <= mid_val <= 145, f"Expected mid transition near 128, got {mid_val}")
        self.assertEqual(mask.getpixel((50, 70)), 0)
        self.assertEqual(mask.getpixel((50, 75)), 0)

    def test_soft_brush_hardness_0_percent(self) -> None:
        mask = Image.new("L", (100, 100), 0)
        PhoenixInpaintingCanvas.paint_mask(mask, (50, 50), (50, 50), brush_size=40, hardness=0.0, erase=False)
        self.assertEqual(mask.getpixel((50, 50)), 255)
        mid_val = mask.getpixel((50, 60))
        self.assertTrue(110 <= mid_val <= 145, f"Expected mid transition near 128, got {mid_val}")
        self.assertEqual(mask.getpixel((50, 70)), 0)
        self.assertEqual(mask.getpixel((50, 75)), 0)

    def test_soft_brush_eraser_with_hardness(self) -> None:
        mask = Image.new("L", (100, 100), 255)
        PhoenixInpaintingCanvas.paint_mask(mask, (50, 50), (50, 50), brush_size=40, hardness=0.5, erase=True)
        self.assertEqual(mask.getpixel((50, 50)), 0)
        self.assertEqual(mask.getpixel((50, 60)), 0)
        mid_val = mask.getpixel((50, 65))
        self.assertTrue(110 <= mid_val <= 145, f"Expected mid transition near 128, got {mid_val}")
        self.assertEqual(mask.getpixel((50, 70)), 255)
        self.assertEqual(mask.getpixel((50, 75)), 255)

    def test_single_click_creates_circular_stamp(self) -> None:
        mask = Image.new("L", (60, 60), 0)
        PhoenixInpaintingCanvas.paint_mask(mask, (30, 30), (30, 30), brush_size=20, hardness=1.0, erase=False)
        self.assertEqual(mask.getpixel((30, 30)), 255)
        self.assertEqual(mask.getpixel((30, 35)), 255)
        self.assertEqual(mask.getpixel((30, 25)), 255)
        self.assertEqual(mask.getpixel((35, 30)), 255)
        self.assertEqual(mask.getpixel((25, 30)), 255)
        self.assertEqual(mask.getpixel((30, 45)), 0)

    def test_canvas_brush_size_and_hardness_properties(self) -> None:
        root = get_shared_root()
        canvas = PhoenixInpaintingCanvas(root)
        try:
            self.assertEqual(canvas.brush_size, 48)
            self.assertEqual(canvas.brush_radius, 24)
            self.assertEqual(canvas.brush_hardness, 1.0)

            canvas.set_brush_size(64)
            self.assertEqual(canvas.brush_size, 64)
            self.assertEqual(canvas.brush_radius, 32)

            canvas.brush_radius = 20
            self.assertEqual(canvas.brush_size, 40)
            self.assertEqual(canvas.brush_radius, 20)

            canvas.set_brush_hardness(0.5)
            self.assertEqual(canvas.brush_hardness, 0.5)

            canvas.set_brush_hardness(75)
            self.assertEqual(canvas.brush_hardness, 0.75)

            canvas.set_brush_hardness(-0.5)
            self.assertEqual(canvas.brush_hardness, 0.0)
            canvas.set_brush_hardness(150)
            self.assertEqual(canvas.brush_hardness, 1.0)
        finally:
            canvas.destroy()

    def test_border_and_corner_masking_quality(self) -> None:
        mask = Image.new("L", (100, 100), 0)
        for pt in [(0, 0), (99, 0), (0, 99), (99, 99)]:
            PhoenixInpaintingCanvas.paint_mask(mask, pt, pt, brush_size=20, hardness=1.0, erase=False)
            self.assertEqual(mask.getpixel(pt), 255)

        PhoenixInpaintingCanvas.paint_mask(mask, (20, 0), (80, 0), brush_size=20, hardness=0.5, erase=False)
        self.assertEqual(mask.getpixel((50, 0)), 255)

        PhoenixInpaintingCanvas.paint_mask(mask, (0, 20), (0, 80), brush_size=20, hardness=0.5, erase=False)
        self.assertEqual(mask.getpixel((0, 50)), 255)

    def test_rapid_motion_outside_and_reentry_prevents_spurious_lines(self) -> None:
        root = get_shared_root()
        canvas = PhoenixInpaintingCanvas(root)
        canvas.render = lambda: None
        canvas.image = Image.new("RGB", (100, 100))
        canvas.mask = Image.new("L", (100, 100), 0)
        try:
            canvas._paint(SimpleNamespace(x=20, y=20))
            self.assertIsNotNone(canvas._last_native)

            canvas._paint(SimpleNamespace(x=500, y=500))
            self.assertIsNone(canvas._last_native)

            canvas._paint(SimpleNamespace(x=80, y=80))
            self.assertEqual(canvas.mask.getpixel((50, 50)), 0)
        finally:
            canvas.destroy()

    def test_brush_size_range_8_to_160(self) -> None:
        mask = Image.new("L", (200, 200), 0)
        PhoenixInpaintingCanvas.paint_mask(mask, (30, 30), (30, 30), brush_size=8, hardness=1.0)
        self.assertEqual(mask.getpixel((30, 30)), 255)
        self.assertEqual(mask.getpixel((30, 33)), 255)
        self.assertEqual(mask.getpixel((30, 36)), 0)

        PhoenixInpaintingCanvas.paint_mask(mask, (100, 100), (100, 100), brush_size=160, hardness=1.0)
        self.assertEqual(mask.getpixel((100, 100)), 255)
        self.assertEqual(mask.getpixel((100, 175)), 255)


class InpaintingControllerTests(unittest.TestCase):
    def test_euler_scheduler_timesteps(self) -> None:
        scheduler = EulerScheduler()
        scheduler.set_timesteps(20)
        self.assertEqual(len(scheduler.timesteps), 20)
        self.assertEqual(len(scheduler.sigmas), 21)

    def test_start_forwards_parameters_progress_and_success(self) -> None:
        adapter = FakeAdapter()
        controller = InpaintingController(adapter=adapter)
        progress = []
        completed = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "input.png"
            mask_path = tmp / "mask.png"
            output_path = tmp / "output.png"
            Image.new("RGB", (512, 512), (100, 100, 100)).save(input_path)
            mask_img = Image.new("L", (512, 512), 255)
            mask_img.save(mask_path)

            controller.start(
                input_image_path=input_path,
                mask_image_path=mask_path,
                prompt="fill",
                output_path=output_path,
                steps=20,
                seed=7,
                on_progress=lambda *values: progress.append(values),
                on_complete=completed.append,
                asynchronous=False,
            )
            self.assertEqual(len(adapter.calls), 1)
            args, kwargs = adapter.calls[0]
            self.assertEqual(args[:4], (input_path, mask_path, "fill", output_path))
            self.assertEqual(kwargs["steps"], 20)
            self.assertEqual(kwargs["seed"], 7)
            self.assertEqual(progress, [("denoise", 0.75, "Schritt 15/20")])
            self.assertTrue(completed[0].success)

    def test_start_small_mask_uses_focused_crop(self) -> None:
        adapter = FakeAdapter()
        controller = InpaintingController(adapter=adapter)
        completed = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "input.png"
            mask_path = tmp / "mask.png"
            output_path = tmp / "output.png"
            Image.new("RGB", (512, 512), (100, 100, 100)).save(input_path)
            mask_img = Image.new("L", (512, 512), 0)
            mask_img.paste(255, (100, 100, 200, 200))
            mask_img.save(mask_path)

            controller.start(
                input_image_path=input_path,
                mask_image_path=mask_path,
                prompt="fill",
                output_path=output_path,
                steps=20,
                seed=7,
                on_complete=completed.append,
                asynchronous=False,
            )
            self.assertEqual(len(adapter.calls), 1)
            args, kwargs = adapter.calls[0]
            self.assertTrue(args[0].name.startswith("source_512"))
            self.assertTrue(args[1].name.startswith("mask_512"))
            self.assertEqual(args[2], "fill")
            self.assertTrue(completed[0].success)
            self.assertTrue(output_path.is_file())

    def test_cancel_is_cooperative(self) -> None:
        adapter = FakeAdapter()
        controller = InpaintingController(adapter=adapter)
        controller.cancel()
        self.assertTrue(adapter.cancelled)

    def test_error_result_reaches_view_callback_without_exception(self) -> None:
        adapter = FakeAdapter(SD15QnnInpaintingResult(
            success=False, error_code="ERR_NPU_INFERENCE_FAILED", error_message="QNN unavailable"
        ))
        completed = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "input.png"
            mask_path = tmp / "mask.png"
            output_path = tmp / "output.png"
            Image.new("RGB", (512, 512), (100, 100, 100)).save(input_path)
            mask_img = Image.new("L", (512, 512), 0)
            mask_img.paste(255, (100, 100, 200, 200))
            mask_img.save(mask_path)

            InpaintingController(adapter=adapter).start(
                input_image_path=input_path,
                mask_image_path=mask_path,
                prompt="fill",
                output_path=output_path,
                on_complete=completed.append,
                asynchronous=False,
            )
            self.assertEqual(completed[0].error_code, "ERR_NPU_INFERENCE_FAILED")
            self.assertEqual(completed[0].error_message, "QNN unavailable")


    def test_controller_clamps_edge_parameters(self) -> None:
        adapter = FakeAdapter()
        controller = InpaintingController(adapter=adapter)
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "input.png"
            mask_path = tmp / "mask.png"
            output_path = tmp / "output.png"
            Image.new("RGB", (512, 512), (100, 100, 100)).save(input_path)
            mask_img = Image.new("L", (512, 512), 0)
            mask_img.paste(255, (100, 100, 200, 200))
            mask_img.save(mask_path)

            # Test excessive values clamped: feather 99 -> 15, dilate 50 -> 8, cfg 99.0 -> 15.0
            controller.start(
                input_image_path=input_path,
                mask_image_path=mask_path,
                prompt="fill",
                output_path=output_path,
                feather_radius=99,
                dilate_pixels=50,
                cfg_scale=99.0,
                asynchronous=False,
            )
            _, kwargs = adapter.calls[-1]
            self.assertEqual(kwargs["feather_radius"], 15)
            self.assertEqual(kwargs["dilate_pixels"], 8)
            self.assertEqual(kwargs["cfg_scale"], 15.0)

            # Test under-bound values clamped: feather -10 -> 0, dilate -5 -> 0, cfg -2.0 -> 1.0
            controller.start(
                input_image_path=input_path,
                mask_image_path=mask_path,
                prompt="fill",
                output_path=output_path,
                feather_radius=-10,
                dilate_pixels=-5,
                cfg_scale=-2.0,
                asynchronous=False,
            )
            _, kwargs = adapter.calls[-1]
            self.assertEqual(kwargs["feather_radius"], 0)
            self.assertEqual(kwargs["dilate_pixels"], 0)
            self.assertEqual(kwargs["cfg_scale"], 1.0)


class InpaintingUiRegistrationTests(unittest.TestCase):
    def test_view_and_controller_are_importable(self) -> None:
        self.assertTrue(inspect.isclass(PhoenixInpaintingView))
        self.assertTrue(inspect.isclass(InpaintingController))

    def test_controller_defaults_to_sd15_qnn_htp(self) -> None:
        controller = InpaintingController()
        self.assertIsInstance(controller.adapter, SD15QnnInpaintingAdapter)
        self.assertTrue(callable(controller.adapter.run))

    def test_workspace_and_sidebar_registration_exists(self) -> None:
        self.assertIn("inpainting", PhoenixWorkspace.VIEW_TITLE_KEYS)
        workspace_source = inspect.getsource(PhoenixWorkspace._register_views)
        self.assertIn('"generative_fill": PhoenixInpaintingView', workspace_source)
        from widgets.phoenix.sidebar import PhoenixSidebar
        self.assertIn('"inpainting"', inspect.getsource(PhoenixSidebar._build))

    def test_success_handler_displays_result(self) -> None:
        source = inspect.getsource(PhoenixInpaintingView._on_complete)
        self.assertIn("self.canvas.set_result", source)

    def test_tool_buttons_use_existing_phoenix_selected_states(self) -> None:
        source = inspect.getsource(PhoenixInpaintingView)
        self.assertIn('button_type="nav_active"', source)
        self.assertIn('button_type="neutral"', source)

    def test_overview_toolbar_button_contract(self) -> None:
        root = get_shared_root()
        view = PhoenixInpaintingView(root)
        try:
            self.assertTrue(hasattr(view, "overview_button"))
            self.assertEqual(view.overview_button.cget("text"), "Übersicht")
            self.assertEqual(view.overview_button.button_type, "neutral")
            self.assertEqual(view.overview_button.icon_name, "back")
            self.assertEqual(view.overview_button.radius, 6)
            self.assertEqual(view.overview_button._height, 32)
            self.assertIs(view._toolbar_items[0], view.overview_button)
        finally:
            view.destroy()

    def test_view_steps_range_and_default(self) -> None:
        root = get_shared_root()
        view = PhoenixInpaintingView(root)
        try:
            self.assertEqual(view.steps.get(), 20)
            self.assertEqual(int(view.steps_scale.cget("from")), 10)
            self.assertEqual(int(view.steps_scale.cget("to")), 50)
            self.assertEqual(int(view.steps_spin.cget("from")), 10)
            self.assertEqual(int(view.steps_spin.cget("to")), 50)
            view.steps.set(35)
            self.assertEqual(view.steps_scale.get(), 35)
            self.assertEqual(int(view.steps_spin.get()), 35)
        finally:
            view.destroy()

    def test_view_labels_and_model_badge(self) -> None:
        root = get_shared_root()
        view = PhoenixInpaintingView(root)
        try:
            self.assertEqual(view.model_badge.cget("text"), "SD 1.5 NPU")
            texts = []
            for child in view.header.winfo_children():
                for sub in child.winfo_children():
                    try:
                        texts.append(sub.cget("text"))
                    except Exception:
                        pass
            self.assertTrue(
                any("Stable Diffusion 1.5 auf Qualcomm Hexagon NPU" in t for t in texts),
                f"Subtitle not found in header texts: {texts}",
            )
        finally:
            view.destroy()

    def test_brush_controls_ui_and_synchronization(self) -> None:
        root = get_shared_root()
        view = PhoenixInpaintingView(root)
        try:
            self.assertEqual(view.brush_size.get(), 48)
            self.assertEqual(view.brush_hardness.get(), 100)
            self.assertEqual(view.hardness_display_var.get(), "100%")

            view._on_brush_size_change("64")
            self.assertEqual(view.canvas.brush_size, 64)

            view._on_brush_hardness_change("45")
            self.assertEqual(view.canvas.brush_hardness, 0.45)
            self.assertEqual(view.hardness_display_var.get(), "45%")
        finally:
            view.destroy()

    def test_theme_parity_dark_and_light(self) -> None:
        root = get_shared_root()
        for theme in ("dark", "light"):
            update_phoenix_theme(theme)
            view = PhoenixInpaintingView(root)
            try:
                self.assertEqual(view.cget("bg"), PHOENIX_THEME.app_bg)
                self.assertEqual(view.model_badge.cget("bg"), PHOENIX_THEME.card_bg)
                self.assertEqual(view.model_badge.cget("fg"), PHOENIX_THEME.accent)
                self.assertEqual(view.steps_scale.cget("bg"), PHOENIX_THEME.card_bg)
                self.assertEqual(view.steps_scale.cget("troughcolor"), PHOENIX_THEME.elevated_bg)
                self.assertEqual(view.feather_scale.cget("bg"), PHOENIX_THEME.card_bg)
                self.assertEqual(view.feather_scale.cget("troughcolor"), PHOENIX_THEME.elevated_bg)
                self.assertEqual(view.dilate_scale.cget("bg"), PHOENIX_THEME.card_bg)
                self.assertEqual(view.dilate_scale.cget("troughcolor"), PHOENIX_THEME.elevated_bg)
                self.assertEqual(view.cfg_scale.cget("bg"), PHOENIX_THEME.card_bg)
                self.assertEqual(view.cfg_scale.cget("troughcolor"), PHOENIX_THEME.elevated_bg)
                self.assertEqual(view.negative_prompt.cget("bg"), PHOENIX_THEME.elevated_bg)
                self.assertEqual(view.negative_prompt.cget("fg"), PHOENIX_THEME.text_primary)
            finally:
                view.destroy()
        update_phoenix_theme("dark")

    def test_image_lab_view_sd15_badge(self) -> None:
        root = get_shared_root()
        lab = PhoenixImageLabView(root)
        try:
            found_badge = False
            for child in lab.content_slot.winfo_children():
                for card in child.winfo_children():
                    for widget in card.winfo_children():
                        try:
                            text = widget.cget("text")
                            if "SD 1.5 Inpainting" in text:
                                found_badge = True
                        except Exception:
                            pass
            self.assertTrue(found_badge, "Badge 'SD 1.5 Inpainting • QNN/HTP' not found in Image Lab cards")
        finally:
            lab.destroy()


    def test_edge_settings_defaults_and_ranges(self) -> None:
        root = get_shared_root()
        view = PhoenixInpaintingView(root)
        try:
            self.assertEqual(view.feather_radius.get(), 5)
            self.assertEqual(int(view.feather_scale.cget("from")), 0)
            self.assertEqual(int(view.feather_scale.cget("to")), 15)
            self.assertEqual(int(view.feather_spin.cget("from")), 0)
            self.assertEqual(int(view.feather_spin.cget("to")), 15)

            self.assertEqual(view.dilate_pixels.get(), 0)
            self.assertEqual(int(view.dilate_scale.cget("from")), 0)
            self.assertEqual(int(view.dilate_scale.cget("to")), 8)
            self.assertEqual(int(view.dilate_spin.cget("from")), 0)
            self.assertEqual(int(view.dilate_spin.cget("to")), 8)

            self.assertEqual(view.cfg_scale.get(), 7.5)
            self.assertEqual(float(view.cfg_scale.cget("from")), 1.0)
            self.assertEqual(float(view.cfg_scale.cget("to")), 15.0)
            self.assertEqual(float(view.cfg_scale.cget("resolution")), 0.5)
            self.assertEqual(float(view.cfg_spin.cget("from")), 1.0)
            self.assertEqual(float(view.cfg_spin.cget("to")), 15.0)
            self.assertEqual(float(view.cfg_spin.cget("increment")), 0.5)

            self.assertEqual(view.negative_prompt.get("1.0", "end-1c"), "")
        finally:
            view.destroy()

    def test_preset_selection_and_button_states(self) -> None:
        root = get_shared_root()
        view = PhoenixInpaintingView(root)
        try:
            # Default state: "add" preset is active (5, 0, 7.5)
            self.assertEqual(view.active_preset, "add")
            self.assertEqual(view.feather_radius.get(), 5)
            self.assertEqual(view.dilate_pixels.get(), 0)
            self.assertEqual(view.cfg_scale.get(), 7.5)
            self.assertEqual(view.preset_add_button.button_type, "nav_active")
            self.assertEqual(view.preset_replace_button.button_type, "neutral")
            self.assertEqual(view.preset_remove_button.button_type, "neutral")

            # Apply "replace" preset -> (6, 2, 8.5)
            view._apply_preset("replace")
            self.assertEqual(view.feather_radius.get(), 6)
            self.assertEqual(view.dilate_pixels.get(), 2)
            self.assertEqual(view.cfg_scale.get(), 8.5)
            self.assertEqual(view.active_preset, "replace")
            self.assertEqual(view.preset_replace_button.button_type, "nav_active")
            self.assertEqual(view.preset_add_button.button_type, "neutral")
            self.assertEqual(view.preset_remove_button.button_type, "neutral")

            # Apply "remove" preset -> (8, 3, 5.0)
            view._apply_preset("remove")
            self.assertEqual(view.feather_radius.get(), 8)
            self.assertEqual(view.dilate_pixels.get(), 3)
            self.assertEqual(view.cfg_scale.get(), 5.0)
            self.assertEqual(view.active_preset, "remove")
            self.assertEqual(view.preset_remove_button.button_type, "nav_active")
            self.assertEqual(view.preset_add_button.button_type, "neutral")
            self.assertEqual(view.preset_replace_button.button_type, "neutral")

            # Apply "add" preset again -> (5, 0, 7.5)
            view._apply_preset("add")
            self.assertEqual(view.feather_radius.get(), 5)
            self.assertEqual(view.dilate_pixels.get(), 0)
            self.assertEqual(view.cfg_scale.get(), 7.5)
            self.assertEqual(view.active_preset, "add")
            self.assertEqual(view.preset_add_button.button_type, "nav_active")
            self.assertEqual(view.preset_replace_button.button_type, "neutral")
            self.assertEqual(view.preset_remove_button.button_type, "neutral")
        finally:
            view.destroy()

    def test_manual_slider_change_clears_preset_selection(self) -> None:
        root = get_shared_root()
        view = PhoenixInpaintingView(root)
        try:
            # Manually change feather/dilate to custom values (11, 4)
            view.feather_radius.set(11)
            view.dilate_pixels.set(4)
            view._on_slider_manual_change()
            self.assertIsNone(view.active_preset)
            self.assertEqual(view.preset_add_button.button_type, "neutral")
            self.assertEqual(view.preset_replace_button.button_type, "neutral")
            self.assertEqual(view.preset_remove_button.button_type, "neutral")

            # Manually change CFG scale to custom value (9.0)
            view._apply_preset("add")
            self.assertEqual(view.active_preset, "add")
            view.cfg_var.set(9.0)
            view._on_slider_manual_change()
            self.assertIsNone(view.active_preset)
            self.assertEqual(view.preset_add_button.button_type, "neutral")

            # Manually change back to preset "replace" coordinates (6, 2, 8.5)
            view.feather_radius.set(6)
            view.dilate_pixels.set(2)
            view.cfg_var.set(8.5)
            view._on_slider_manual_change()
            self.assertEqual(view.active_preset, "replace")
            self.assertEqual(view.preset_replace_button.button_type, "nav_active")
        finally:
            view.destroy()

    def test_view_start_passes_edge_and_cfg_parameters_to_controller(self) -> None:
        root = get_shared_root()
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            adapter = FakeAdapter(artifact_dir=tmp)
            controller = InpaintingController(adapter=adapter)
            view = PhoenixInpaintingView(root, controller=controller, output_dir=tmp, temp_dir=tmp)
            try:
                input_path = tmp / "input.png"
                Image.new("RGB", (512, 512), (100, 100, 100)).save(input_path)
                view.input_path = input_path
                view.prompt.insert("1.0", "a beautiful fantasy palace")
                view.negative_prompt.insert("1.0", "blurry, low quality, artifacts")
                view.cfg_var.set(8.5)
                view.feather_radius.set(12)
                view.dilate_pixels.set(4)
                view.canvas.save_mask = lambda p: Image.new("L", (512, 512), 255).save(p)

                real_start = controller.start
                controller.start = lambda **kwargs: real_start(**{**kwargs, "asynchronous": False})

                view._start()

                self.assertEqual(len(adapter.calls), 1)
                _, kwargs = adapter.calls[0]
                self.assertEqual(kwargs["negative_prompt"], "blurry, low quality, artifacts")
                self.assertEqual(kwargs["cfg_scale"], 8.5)
                self.assertEqual(kwargs["feather_radius"], 12)
                self.assertEqual(kwargs["dilate_pixels"], 4)
            finally:
                view.destroy()

    def test_view_start_with_empty_negative_prompt(self) -> None:
        root = get_shared_root()
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            adapter = FakeAdapter(artifact_dir=tmp)
            controller = InpaintingController(adapter=adapter)
            view = PhoenixInpaintingView(root, controller=controller, output_dir=tmp, temp_dir=tmp)
            try:
                input_path = tmp / "input.png"
                Image.new("RGB", (512, 512), (100, 100, 100)).save(input_path)
                view.input_path = input_path
                view.prompt.insert("1.0", "a pristine cybernetic city")
                # Leave negative prompt empty
                view.canvas.save_mask = lambda p: Image.new("L", (512, 512), 255).save(p)

                real_start = controller.start
                controller.start = lambda **kwargs: real_start(**{**kwargs, "asynchronous": False})

                view._start()

                self.assertEqual(len(adapter.calls), 1)
                _, kwargs = adapter.calls[0]
                self.assertEqual(kwargs["negative_prompt"], "")
                self.assertEqual(kwargs["cfg_scale"], 7.5)
                self.assertEqual(kwargs["feather_radius"], 5)
                self.assertEqual(kwargs["dilate_pixels"], 0)
            finally:
                view.destroy()

    def test_denoising_strength_slider_and_spinbox_defaults_and_range(self) -> None:
        root = get_shared_root()
        view = PhoenixInpaintingView(root)
        try:
            self.assertTrue(hasattr(view, "strength_var"))
            self.assertAlmostEqual(view.strength_var.get(), 1.0, places=2)
            self.assertAlmostEqual(float(view.strength_spin.cget("from")), 0.1, places=2)
            self.assertAlmostEqual(float(view.strength_spin.cget("to")), 1.0, places=2)
            self.assertAlmostEqual(float(view.strength_spin.cget("increment")), 0.05, places=2)
            self.assertAlmostEqual(float(view.strength_scale.cget("from")), 0.1, places=2)
            self.assertAlmostEqual(float(view.strength_scale.cget("to")), 1.0, places=2)
            self.assertAlmostEqual(float(view.strength_scale.cget("resolution")), 0.05, places=2)
        finally:
            view.destroy()

    def test_view_start_passes_denoising_strength_to_controller_and_adapter(self) -> None:
        root = get_shared_root()
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            adapter = FakeAdapter(artifact_dir=tmp)
            controller = InpaintingController(adapter=adapter)
            view = PhoenixInpaintingView(root, controller=controller, output_dir=tmp, temp_dir=tmp)
            try:
                input_path = tmp / "input.png"
                Image.new("RGB", (512, 512), (100, 100, 100)).save(input_path)
                view.input_path = input_path
                view.prompt.insert("1.0", "modify car color")
                view.strength_var.set(0.65)
                view.canvas.save_mask = lambda p: Image.new("L", (512, 512), 255).save(p)

                real_start = controller.start
                controller.start = lambda **kwargs: real_start(**{**kwargs, "asynchronous": False})

                view._start()

                self.assertEqual(len(adapter.calls), 1)
                _, kwargs = adapter.calls[0]
                self.assertEqual(kwargs["denoising_strength"], 0.65)
            finally:
                view.destroy()

    def test_ui_tests_never_pollute_production_output_dir(self) -> None:
        from config import OUTPUT_DIR as PROD_OUTPUT_DIR
        root = get_shared_root()
        prod_files_before = set(PROD_OUTPUT_DIR.iterdir()) if PROD_OUTPUT_DIR.exists() else set()

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            adapter = FakeAdapter(artifact_dir=tmp)
            controller = InpaintingController(adapter=adapter)
            view = PhoenixInpaintingView(root, controller=controller, output_dir=tmp, temp_dir=tmp)
            try:
                input_path = tmp / "input.png"
                Image.new("RGB", (512, 512), (100, 100, 100)).save(input_path)
                view.input_path = input_path
                view.prompt.insert("1.0", "isolation verification test")
                view.canvas.save_mask = lambda p: Image.new("L", (512, 512), 255).save(p)

                real_start = controller.start
                controller.start = lambda **kwargs: real_start(**{**kwargs, "asynchronous": False})
                view._start()

                # Verify test artifact was written to tmp
                created_in_tmp = list(tmp.glob("generative_fill_*.png"))
                self.assertEqual(len(created_in_tmp), 1)

                # Verify production output directory is 100% untouched
                prod_files_after = set(PROD_OUTPUT_DIR.iterdir()) if PROD_OUTPUT_DIR.exists() else set()
                new_files_in_prod = prod_files_after - prod_files_before
                self.assertEqual(len(new_files_in_prod), 0, f"Production output polluted with: {new_files_in_prod}")
            finally:
                view.destroy()

    def test_slider_manual_change_with_strength_deselects_preset(self) -> None:
        root = get_shared_root()
        view = PhoenixInpaintingView(root)
        try:
            view._apply_preset("add")
            self.assertEqual(view.active_preset, "add")
            self.assertEqual(view.strength_var.get(), 1.0)

            # Modifying strength deselects preset
            view.strength_var.set(0.70)
            view._on_slider_manual_change()
            self.assertIsNone(view.active_preset)
            self.assertEqual(view.preset_add_button.button_type, "neutral")

            # Setting strength back to 1.0 restores preset match
            view.strength_var.set(1.0)
            view._on_slider_manual_change()
            self.assertEqual(view.active_preset, "add")
            self.assertEqual(view.preset_add_button.button_type, "nav_active")

            # Re-applying a preset restores strength to 1.0
            view.strength_var.set(0.50)
            view._apply_preset("replace")
            self.assertEqual(view.active_preset, "replace")
            self.assertEqual(view.strength_var.get(), 1.0)
        finally:
            view.destroy()

    def test_controller_clamps_denoising_strength(self) -> None:
        adapter = FakeAdapter()
        controller = InpaintingController(adapter=adapter)
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            in_p = tmp / "in.png"
            mask_p = tmp / "mask.png"
            out_p = tmp / "out.png"
            Image.new("RGB", (512, 512)).save(in_p)
            Image.new("L", (512, 512), 255).save(mask_p)

            # Test lower clamp (< 0.1 -> 0.1)
            controller.start(
                input_image_path=in_p,
                mask_image_path=mask_p,
                prompt="test low",
                output_path=out_p,
                denoising_strength=0.02,
                asynchronous=False,
            )
            self.assertEqual(adapter.calls[-1][1]["denoising_strength"], 0.1)

            # Test upper clamp (> 1.0 -> 1.0)
            controller.start(
                input_image_path=in_p,
                mask_image_path=mask_p,
                prompt="test high",
                output_path=out_p,
                denoising_strength=1.85,
                asynchronous=False,
            )
            self.assertEqual(adapter.calls[-1][1]["denoising_strength"], 1.0)


if __name__ == "__main__":
    unittest.main()
