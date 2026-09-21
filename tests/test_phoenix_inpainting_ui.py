from __future__ import annotations

import inspect
import tempfile
import unittest
import tkinter as tk
from types import SimpleNamespace
from pathlib import Path

from PIL import Image

from controllers.inpainting_controller import InpaintingController
from engine.backends.rorem_dlc_inpainting_adapter import RORemDlcInpaintingAdapter, RORemDlcResult, RORemDlcRuntime
from widgets.phoenix.inpainting_canvas import PhoenixInpaintingCanvas
from widgets.phoenix.views.inpainting_view import PhoenixInpaintingView
from widgets.phoenix.workspace import PhoenixWorkspace


class FakeAdapter:
    def __init__(self, result=None) -> None:
        self.result = result or RORemDlcResult(success=True, output_path="output.png")
        self.calls = []
        self.cancelled = False

    def run(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        callback = kwargs.get("progress_callback")
        if callback:
            callback("denoising", 0.75, "Schritt 3/8")
        return self.result

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
        root = tk.Tk()
        root.withdraw()
        try:
            canvas = PhoenixInpaintingCanvas(root)
            # Avoid rendering into a deliberately withdrawn test widget.
            canvas.render = lambda: None
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
            root.destroy()

    def test_responsive_buttons_dark_light_all_dpi(self) -> None:
        from widgets.phoenix.theme import update_phoenix_theme
        try:
            for theme in ("dark", "light"):
                update_phoenix_theme(theme)
                for dpi in (1.0, 1.25, 1.5, 1.75):
                    root = tk.Tk()
                    try:
                        root.tk.call("tk", "scaling", (96 / 72) * dpi)
                        view = PhoenixInpaintingView(root)
                        view.pack(fill="both", expand=True)
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
                        root.destroy()
        finally:
            update_phoenix_theme("dark")

    def test_compact_reflow_uses_content_width_breakpoints(self) -> None:
        from widgets.phoenix.theme import PHOENIX_THEME
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


class InpaintingControllerTests(unittest.TestCase):
    def test_four_requested_steps_are_not_truncated_by_default_strength(self) -> None:
        self.assertEqual(RORemDlcRuntime._resolve_init_timestep(4, 0.9999), 4)

    def test_start_forwards_parameters_progress_and_success(self) -> None:
        adapter = FakeAdapter()
        controller = InpaintingController(adapter=adapter)
        progress = []
        completed = []
        controller.start(
            input_image_path="input.png", mask_image_path="mask.png", prompt="fill",
            output_path="output.png", steps=4, seed=7,
            on_progress=lambda *values: progress.append(values), on_complete=completed.append,
            asynchronous=False,
        )
        args, kwargs = adapter.calls[0]
        self.assertEqual(args[:4], ("input.png", "mask.png", "fill", "output.png"))
        self.assertEqual(kwargs["steps"], 4)
        self.assertEqual(kwargs["seed"], 7)
        self.assertEqual(progress, [("denoising", 0.75, "Schritt 3/8")])
        self.assertTrue(completed[0].success)

    def test_cancel_is_cooperative(self) -> None:
        adapter = FakeAdapter()
        controller = InpaintingController(adapter=adapter)
        controller.cancel()
        self.assertTrue(adapter.cancelled)

    def test_error_result_reaches_view_callback_without_exception(self) -> None:
        adapter = FakeAdapter(RORemDlcResult(
            success=False, error_code="ERR_QNN_INIT_FAILED", error_message="QNN unavailable"
        ))
        completed = []
        InpaintingController(adapter=adapter).start(
            input_image_path="input", mask_image_path="mask", prompt="fill", output_path="output",
            on_complete=completed.append, asynchronous=False,
        )
        self.assertEqual(completed[0].error_code, "ERR_QNN_INIT_FAILED")


class InpaintingUiRegistrationTests(unittest.TestCase):
    def test_view_and_controller_are_importable(self) -> None:
        self.assertTrue(inspect.isclass(PhoenixInpaintingView))
        self.assertTrue(inspect.isclass(InpaintingController))

    def test_controller_defaults_to_rorem_htp_without_cpu_ai_fallback(self) -> None:
        controller = InpaintingController()
        self.assertIsInstance(controller.adapter, RORemDlcInpaintingAdapter)
        self.assertFalse(controller.adapter.runtime.CPU_AI_FALLBACK)

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


if __name__ == "__main__":
    unittest.main()
