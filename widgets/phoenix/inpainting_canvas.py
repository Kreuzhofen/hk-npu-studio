from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import tkinter as tk

import numpy as np
from PIL import Image, ImageDraw, ImageTk

from widgets.phoenix.theme import PHOENIX_THEME


@lru_cache(maxsize=128)
def _generate_brush_stamp(radius: float, hardness: float) -> np.ndarray:
    """
    Generate a 2D radial stamp kernel for the specified radius and hardness.
    Values: uint8 in [0, 255].
    - hardness = 1.0: hard circular stamp (100% core).
    - hardness = 0.5: 50% core radius, smooth cosine falloff to outer edge.
    - hardness = 0.0: point core, smooth cosine falloff across full radius.
    """
    r_int = max(1, int(np.ceil(radius)))
    size = 2 * r_int + 1
    y, x = np.ogrid[-r_int:r_int + 1, -r_int:r_int + 1]
    dist = np.sqrt(x * x + y * y)

    stamp = np.zeros((size, size), dtype=np.float32)
    h = float(np.clip(hardness, 0.0, 1.0))
    r_core = radius * h

    if h >= 0.999 or r_core >= radius:
        stamp[dist <= radius] = 255.0
    else:
        stamp[dist <= r_core] = 255.0
        transition = (dist > r_core) & (dist <= radius)
        t = (dist[transition] - r_core) / (radius - r_core)
        stamp[transition] = 255.0 * 0.5 * (1.0 + np.cos(np.pi * t))

    return np.round(stamp).astype(np.uint8)


class PhoenixInpaintingCanvas(tk.Frame):
    """Zoomable native-resolution image and monochrome paint mask with soft brush support."""

    UNDO_LIMIT = 20

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.card_bg)
        self.image: Image.Image | None = None
        self.original_image: Image.Image | None = None
        self.preview_image: Image.Image | None = None
        self.is_showing_preview: bool = False
        self.mask: Image.Image | None = None
        self.photo: ImageTk.PhotoImage | None = None
        self.zoom = 1.0
        self.auto_fit = True
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.brush_size = 48
        self.brush_hardness = 1.0
        self.erase = False
        self.tool_mode: str = "brush"  # "brush", "eraser", "point_select"
        self.point_prompt: tuple[int, int] | None = None
        self.negative_points: list[tuple[int, int]] = []
        self.on_point_selected = None
        self.on_negative_point_selected = None
        self._last_native: tuple[int, int] | None = None
        self._last_mouse_pos: tuple[float, float] | None = None
        self._pan_origin: tuple[int, int, float, float] | None = None
        self._undo_history: list[Image.Image] = []
        self._stroke_before: Image.Image | None = None
        self.canvas = tk.Canvas(self, bg=PHOENIX_THEME.card_bg, bd=0, highlightthickness=0, cursor="cross")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self.render())
        self.canvas.bind("<Button-1>", self._paint)
        self.canvas.bind("<Button-3>", self._on_right_click_point)
        self.canvas.bind("<Alt-Button-1>", self._on_right_click_point)
        self.canvas.bind("<Control-Button-1>", self._on_ctrl_click_point)
        self.canvas.bind("<Shift-Button-1>", self._on_ctrl_click_point)
        self.canvas.bind("<B1-Motion>", self._paint)
        self.canvas.bind("<ButtonRelease-1>", self._finish_stroke)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Enter>", self._on_mouse_enter)
        self.canvas.bind("<Leave>", self._on_mouse_leave)
        self.canvas.bind("<MouseWheel>", self._zoom_wheel)
        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._drag_pan)

    @property
    def brush_radius(self) -> int:
        return max(1, round(self.brush_size / 2.0))

    @brush_radius.setter
    def brush_radius(self, val: int) -> None:
        self.brush_size = max(2, int(val) * 2)
        self._refresh_brush_preview()

    def set_brush_size(self, size: int) -> None:
        self.brush_size = max(1, int(size))
        self._refresh_brush_preview()

    def set_brush_radius(self, radius: int) -> None:
        self.brush_radius = radius

    def set_brush_hardness(self, hardness: float) -> None:
        val = float(hardness)
        if val > 1.0:
            val = val / 100.0
        self.brush_hardness = max(0.0, min(1.0, val))
        self._refresh_brush_preview()

    def load_image(self, path: str | Path) -> None:
        with Image.open(path) as opened:
            self.image = opened.convert("RGB")
        self.original_image = self.image.copy()
        self.preview_image = None
        self.is_showing_preview = False
        self.point_prompt = None
        self.mask = Image.new("L", self.image.size, 0)
        PhoenixInpaintingCanvas._reset_history(self)
        self.auto_fit = True
        self.pan_x = self.pan_y = 0.0
        self.render()

    def set_result(self, path: str | Path) -> None:
        with Image.open(path) as opened:
            self.image = opened.convert("RGB")
        self.preview_image = self.image.copy()
        self.is_showing_preview = True
        self.point_prompt = None
        self.negative_points.clear()
        self.mask = Image.new("L", self.image.size, 0)
        self._reset_history()
        self.auto_fit = True
        self.pan_x = self.pan_y = 0.0
        self.render()

    def set_tool(self, erase: bool) -> None:
        self.erase = erase
        self.tool_mode = "eraser" if erase else "brush"
        if hasattr(self, "canvas") and self.canvas is not None:
            self.canvas.configure(cursor="cross")

    def set_tool_mode(self, mode: str) -> None:
        """Set tool mode: 'brush', 'eraser', or 'point_select'."""
        self.tool_mode = mode
        if hasattr(self, "canvas") and self.canvas is not None:
            if mode == "eraser":
                self.erase = True
                self.canvas.configure(cursor="cross")
            elif mode == "point_select":
                self.erase = False
                self.canvas.configure(cursor="crosshair")
            else:
                self.erase = False
                self.canvas.configure(cursor="cross")

    def set_point_prompt(self, point: tuple[int, int] | None) -> None:
        """Set active point-prompt seed coordinates in native image pixels."""
        self.point_prompt = point
        self.render()

    def add_negative_point(self, point: tuple[int, int]) -> None:
        """Add negative exclusion point in native image coordinates."""
        if point not in self.negative_points:
            self.negative_points.append(point)
            self.render()

    def clear_point_prompt(self) -> None:
        """Clear active point-prompt seed coordinates and negative points."""
        self.point_prompt = None
        self.negative_points.clear()
        self.render()

    def clear_mask(self) -> None:
        PhoenixInpaintingCanvas._reset_history(self)
        if self.image is not None:
            self.mask = Image.new("L", self.image.size, 0)
            self.render()

    def set_mask(self, mask: Image.Image) -> None:
        """Set inpainting mask from an external Image (e.g. segmenter output)."""
        if self.image is None:
            return
        if mask.size != self.image.size:
            mask = mask.resize(self.image.size, Image.Resampling.NEAREST)
        self.mask = mask.convert("L")
        self._reset_history()
        self.render()

    def has_mask(self) -> bool:
        """Return True if a mask exists and has at least one painted pixel."""
        if self.mask is None:
            return False
        extrema = self.mask.getextrema()
        return extrema is not None and extrema[1] > 0

    def set_preview_image(self, image: Image.Image) -> None:
        """Set a preview image (e.g. material priming preview) without altering original."""
        if self.image is None:
            return
        if image.size != self.image.size:
            image = image.resize(self.image.size, Image.Resampling.LANCZOS)
        self.preview_image = image.convert("RGB")
        self.image = self.preview_image.copy()
        self.is_showing_preview = True
        self.render()

    def restore_original_image(self) -> None:
        """Restore the canvas to original unmodified image."""
        if self.original_image is not None:
            self.image = self.original_image.copy()
            self.is_showing_preview = False
            self.render()

    def toggle_compare(self) -> bool:
        """
        Toggle between original image and preview/result image.
        Returns True if preview is currently shown, False if original is shown.
        """
        if self.original_image is None or self.preview_image is None:
            return False
        if self.is_showing_preview:
            self.image = self.original_image.copy()
            self.is_showing_preview = False
        else:
            self.image = self.preview_image.copy()
            self.is_showing_preview = True
        self.render()
        return self.is_showing_preview

    def _reset_history(self) -> None:
        self._undo_history = []
        self._stroke_before = None
        self._last_native = None

    def remove_image(self) -> None:
        self.image = self.mask = self.photo = None
        self.original_image = self.preview_image = None
        self.is_showing_preview = False
        self.point_prompt = None
        self._reset_history()
        self.pan_x = self.pan_y = 0.0
        self._pan_origin = None
        self.auto_fit = True
        self.render()

    def _finish_stroke(self, _event=None) -> None:
        if self._stroke_before is not None:
            self._undo_history.append(self._stroke_before)
            del self._undo_history[:-self.UNDO_LIMIT]
        self._stroke_before = None
        self._last_native = None

    def undo(self) -> None:
        self._finish_stroke()
        if self._undo_history:
            self.mask = self._undo_history.pop()
            self.render()

    def save_mask(self, path: str | Path) -> Path:
        if self.mask is None:
            raise ValueError("No inpainting mask available")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.mask.save(target, format="PNG")
        return target

    @staticmethod
    def contain_zoom(viewport: tuple[int, int], image_size: tuple[int, int]) -> float:
        return min(viewport[0] / image_size[0], viewport[1] / image_size[1])

    @staticmethod
    def map_canvas_to_image(
        x: float, y: float, *, viewport: tuple[int, int], image_size: tuple[int, int], zoom: float, pan: tuple[float, float]
    ) -> tuple[float, float]:
        rendered = (image_size[0] * zoom, image_size[1] * zoom)
        left = viewport[0] / 2 + pan[0] - rendered[0] / 2
        top = viewport[1] / 2 + pan[1] - rendered[1] / 2
        return (x - left) / zoom, (y - top) / zoom

    @staticmethod
    def map_image_to_canvas(
        px: float, py: float, *, viewport: tuple[int, int], image_size: tuple[int, int], zoom: float, pan: tuple[float, float]
    ) -> tuple[float, float]:
        rendered = (image_size[0] * zoom, image_size[1] * zoom)
        left = viewport[0] / 2 + pan[0] - rendered[0] / 2
        top = viewport[1] / 2 + pan[1] - rendered[1] / 2
        return left + px * zoom, top + py * zoom

    def canvas_to_image(self, x: float, y: float, margin: float = 0.0) -> tuple[int, int] | None:
        if self.image is None:
            return None
        native = self.map_canvas_to_image(
            x, y,
            viewport=(max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())),
            image_size=self.image.size,
            zoom=self.zoom,
            pan=(self.pan_x, self.pan_y),
        )
        if not (-margin <= native[0] < self.image.width + margin and -margin <= native[1] < self.image.height + margin):
            return None
        return round(native[0]), round(native[1])

    def image_to_canvas(self, px: float, py: float) -> tuple[float, float] | None:
        if self.image is None:
            return None
        return self.map_image_to_canvas(
            px, py,
            viewport=(max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())),
            image_size=self.image.size,
            zoom=self.zoom,
            pan=(self.pan_x, self.pan_y),
        )

    def paint_native(self, start: tuple[int, int], end: tuple[int, int], erase: bool | None = None) -> None:
        if self.mask is None:
            return
        brush_size = getattr(self, "brush_size", 48)
        hardness = getattr(self, "brush_hardness", 1.0)
        tool_erase = getattr(self, "erase", False)
        self.paint_mask(
            self.mask,
            start,
            end,
            brush_size=brush_size,
            hardness=hardness,
            erase=tool_erase if erase is None else erase,
        )

    @staticmethod
    def paint_mask(
        mask: Image.Image,
        start: tuple[int, int],
        end: tuple[int, int],
        *,
        brush_size: int,
        hardness: float = 1.0,
        erase: bool = False,
    ) -> None:
        """
        Paint or erase on mask with smooth continuous stroke interpolation
        and radial hardness control (0-100%). Modifies mask in-place.
        """
        radius = max(1.0, float(brush_size) / 2.0)
        h_clamped = float(np.clip(hardness, 0.0, 1.0))
        stamp = _generate_brush_stamp(round(radius, 1), round(h_clamped, 3))
        r_int = int(np.ceil(radius))

        x0, y0 = start
        x1, y1 = end
        dx = x1 - x0
        dy = y1 - y0
        dist = float(np.hypot(dx, dy))
        step = max(1.0, radius * 0.08)
        num_steps = max(1, int(np.ceil(dist / step))) if dist > 0 else 1

        mask_arr = np.array(mask, dtype=np.uint8)
        mh, mw = mask_arr.shape

        for i in range(num_steps + 1):
            t = i / num_steps if num_steps > 0 else 0.0
            cx = int(round(x0 + t * dx))
            cy = int(round(y0 + t * dy))

            x_min = max(0, cx - r_int)
            x_max = min(mw, cx + r_int + 1)
            y_min = max(0, cy - r_int)
            y_max = min(mh, cy + r_int + 1)

            if x_max <= x_min or y_max <= y_min:
                continue

            sx_min = x_min - (cx - r_int)
            sx_max = sx_min + (x_max - x_min)
            sy_min = y_min - (cy - r_int)
            sy_max = sy_min + (y_max - y_min)

            sub_stamp = stamp[sy_min:sy_max, sx_min:sx_max]
            if erase:
                mask_arr[y_min:y_max, x_min:x_max] = np.minimum(
                    mask_arr[y_min:y_max, x_min:x_max],
                    255 - sub_stamp,
                )
            else:
                mask_arr[y_min:y_max, x_min:x_max] = np.maximum(
                    mask_arr[y_min:y_max, x_min:x_max],
                    sub_stamp,
                )

        # Update PIL mask in-place
        mask.paste(Image.fromarray(mask_arr, mode="L"))

    def _on_ctrl_click_point(self, event: tk.Event) -> str:
        """Handle explicit Ctrl+Click or Shift+Click to set point prompt at any time."""
        native = self.canvas_to_image(event.x, event.y)
        if native is not None:
            self.set_point_prompt(native)
            if callable(self.on_point_selected):
                self.on_point_selected(native)
        return "break"

    def _on_right_click_point(self, event: tk.Event) -> str:
        """Handle Right-Click or Alt+Click to set negative exclusion point."""
        native = self.canvas_to_image(event.x, event.y)
        if native is not None:
            self.add_negative_point(native)
            if callable(self.on_negative_point_selected):
                self.on_negative_point_selected(native)
        return "break"

    def _paint(self, event: tk.Event) -> None:
        if getattr(self, "tool_mode", "brush") == "point_select":
            native = self.canvas_to_image(event.x, event.y)
            if native is not None:
                self.set_point_prompt(native)
                if callable(self.on_point_selected):
                    self.on_point_selected(native)
            return

        brush_size = getattr(self, "brush_size", 48)
        radius = max(1.0, float(brush_size) / 2.0)
        try:
            native = self.canvas_to_image(event.x, event.y, margin=radius)
        except TypeError:
            native = self.canvas_to_image(event.x, event.y)
        if native is None:
            self._last_native = None
            return
        if self._stroke_before is None and self.mask is not None:
            self._stroke_before = self.mask.copy()
        self.paint_native(self._last_native or native, native)
        self._last_native = native
        self.render()
        self._last_mouse_pos = (event.x, event.y)
        if hasattr(self, "canvas") and self.canvas is not None:
            self._draw_brush_preview(event.x, event.y)

    def _on_mouse_move(self, event: tk.Event) -> None:
        self._last_mouse_pos = (event.x, event.y)
        self._draw_brush_preview(event.x, event.y)

    def _on_mouse_enter(self, event: tk.Event) -> None:
        self._last_mouse_pos = (event.x, event.y)
        self._draw_brush_preview(event.x, event.y)

    def _on_mouse_leave(self, _event: tk.Event = None) -> None:
        self._last_mouse_pos = None
        if hasattr(self, "canvas") and self.canvas is not None:
            self.canvas.delete("brush_preview")

    def _refresh_brush_preview(self) -> None:
        if self._last_mouse_pos is not None:
            self._draw_brush_preview(*self._last_mouse_pos)

    def _draw_brush_preview(self, x: float, y: float) -> None:
        if not hasattr(self, "canvas") or self.canvas is None:
            return
        self.canvas.delete("brush_preview")
        if self.image is None:
            return
        brush_size = getattr(self, "brush_size", 48)
        hardness = getattr(self, "brush_hardness", 1.0)
        zoom = getattr(self, "zoom", 1.0)
        screen_r = max(1.5, min(4000.0, (brush_size / 2.0) * zoom))

        # Outer circle indicating full brush radius
        self.canvas.create_oval(
            x - screen_r, y - screen_r, x + screen_r, y + screen_r,
            outline=PHOENIX_THEME.accent,
            width=1.5,
            tags="brush_preview",
        )

        # Inner circle indicating core boundary for hardness < 1.0
        h = max(0.0, min(1.0, hardness))
        if h < 0.98:
            inner_r = screen_r * h
            if inner_r >= 1:
                self.canvas.create_oval(
                    x - inner_r, y - inner_r, x + inner_r, y + inner_r,
                    outline=PHOENIX_THEME.text_secondary,
                    dash=(3, 3),
                    width=1.0,
                    tags="brush_preview",
                )

    def _zoom_wheel(self, event: tk.Event) -> None:
        self._last_mouse_pos = (event.x, event.y)
        self.auto_fit = False
        self.zoom = max(0.1, min(8.0, self.zoom * (1.1 if event.delta > 0 else 1 / 1.1)))
        self.render()
        self._refresh_brush_preview()

    def _start_pan(self, event: tk.Event) -> None:
        self.auto_fit = False
        self._pan_origin = (event.x, event.y, self.pan_x, self.pan_y)

    def _drag_pan(self, event: tk.Event) -> None:
        if self._pan_origin is None:
            return
        start_x, start_y, pan_x, pan_y = self._pan_origin
        self.pan_x = pan_x + event.x - start_x
        self.pan_y = pan_y + event.y - start_y
        self.render()
        self._refresh_brush_preview()

    def render(self) -> None:
        self.canvas.delete("all")
        if self.image is None:
            return
        viewport = (self.canvas.winfo_width(), self.canvas.winfo_height())
        if viewport[0] <= 1 or viewport[1] <= 1:
            return
        if self.auto_fit:
            self.zoom = self.contain_zoom(viewport, self.image.size)
        size = (max(1, round(self.image.width * self.zoom)), max(1, round(self.image.height * self.zoom)))
        composite = self.image.convert("RGBA")
        if self.mask is not None:
            accent = PHOENIX_THEME.accent.lstrip("#")
            color = tuple(int(accent[index:index + 2], 16) for index in (0, 2, 4))
            alpha = self.mask.point(lambda value: round(value * 0.42))
            overlay = Image.new("RGBA", self.image.size, (*color, 0))
            overlay.putalpha(alpha)
            composite = Image.alpha_composite(composite, overlay)
        rendered = composite.resize(size, Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(rendered)
        self.canvas.create_image(viewport[0] / 2 + self.pan_x, viewport[1] / 2 + self.pan_y, image=self.photo)
        self._draw_point_marker()
        self._refresh_brush_preview()

    def _draw_point_marker(self) -> None:
        """Draw high-polish Phoenix crosshair target marker at active point_prompt and negative points."""
        self.canvas.delete("point_marker")
        if self.image is None:
            return

        # 1. Negative points (Red crosshair with 'X')
        for nx, ny in getattr(self, "negative_points", []):
            c_pos = self.image_to_canvas(nx, ny)
            if c_pos is not None:
                ncx, ncy = c_pos
                r_neg = 10.0
                self.canvas.create_oval(
                    ncx - r_neg, ncy - r_neg, ncx + r_neg, ncy + r_neg,
                    outline=PHOENIX_THEME.error,
                    width=2,
                    tags="point_marker",
                )
                self.canvas.create_line(
                    ncx - r_neg + 3, ncy - r_neg + 3, ncx + r_neg - 3, ncy + r_neg - 3,
                    fill=PHOENIX_THEME.error,
                    width=2,
                    tags="point_marker",
                )
                self.canvas.create_line(
                    ncx - r_neg + 3, ncy + r_neg - 3, ncx + r_neg - 3, ncy - r_neg + 3,
                    fill=PHOENIX_THEME.error,
                    width=2,
                    tags="point_marker",
                )

        # 2. Positive point (Accent target)
        if self.point_prompt is None:
            return
        c_pos = self.image_to_canvas(self.point_prompt[0], self.point_prompt[1])
        if c_pos is None:
            return
        cx, cy = c_pos

        r_outer = 12.0
        r_inner = 3.5

        # Outer ring
        self.canvas.create_oval(
            cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer,
            outline=PHOENIX_THEME.accent,
            width=2,
            tags="point_marker",
        )
        # Inner center dot
        self.canvas.create_oval(
            cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner,
            fill=PHOENIX_THEME.warning,
            outline="#FFFFFF",
            width=1.5,
            tags="point_marker",
        )
        # Crosshair reticles
        self.canvas.create_line(cx - 18, cy, cx - 6, cy, fill=PHOENIX_THEME.accent, width=2, tags="point_marker")
        self.canvas.create_line(cx + 6, cy, cx + 18, cy, fill=PHOENIX_THEME.accent, width=2, tags="point_marker")
        self.canvas.create_line(cx, cy - 18, cx, cy - 6, fill=PHOENIX_THEME.accent, width=2, tags="point_marker")
        self.canvas.create_line(cx, cy + 6, cx, cy + 18, fill=PHOENIX_THEME.accent, width=2, tags="point_marker")

        # Label coordinates
        px, py = self.point_prompt
        self.canvas.create_text(
            cx + 14, cy - 14,
            text=f"({px}, {py})",
            fill=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            tags="point_marker",
        )
