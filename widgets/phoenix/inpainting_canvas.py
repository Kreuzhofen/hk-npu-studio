from __future__ import annotations

import tkinter as tk
from pathlib import Path

from PIL import Image, ImageDraw, ImageTk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixInpaintingCanvas(tk.Frame):
    """Zoomable native-resolution image and monochrome paint mask."""

    UNDO_LIMIT = 20

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.card_bg)
        self.image: Image.Image | None = None
        self.mask: Image.Image | None = None
        self.photo: ImageTk.PhotoImage | None = None
        self.zoom = 1.0
        self.auto_fit = True
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.brush_size = 48
        self.erase = False
        self._last_native: tuple[int, int] | None = None
        self._pan_origin: tuple[int, int, float, float] | None = None
        self._undo_history: list[Image.Image] = []
        self._stroke_before: Image.Image | None = None
        self.canvas = tk.Canvas(self, bg=PHOENIX_THEME.card_bg, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self.render())
        self.canvas.bind("<Button-1>", self._paint)
        self.canvas.bind("<B1-Motion>", self._paint)
        self.canvas.bind("<ButtonRelease-1>", self._finish_stroke)
        self.canvas.bind("<MouseWheel>", self._zoom_wheel)
        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._drag_pan)

    def load_image(self, path: str | Path) -> None:
        with Image.open(path) as opened:
            self.image = opened.convert("RGB")
        self.mask = Image.new("L", self.image.size, 0)
        PhoenixInpaintingCanvas._reset_history(self)
        self.auto_fit = True
        self.pan_x = self.pan_y = 0.0
        self.render()

    def set_result(self, path: str | Path) -> None:
        with Image.open(path) as opened:
            self.image = opened.convert("RGB")
        self.mask = Image.new("L", self.image.size, 0)
        self._reset_history()
        self.auto_fit = True
        self.pan_x = self.pan_y = 0.0
        self.render()

    def set_tool(self, erase: bool) -> None:
        self.erase = erase

    def clear_mask(self) -> None:
        PhoenixInpaintingCanvas._reset_history(self)
        if self.image is not None:
            self.mask = Image.new("L", self.image.size, 0)
            self.render()

    def _reset_history(self) -> None:
        self._undo_history = []
        self._stroke_before = None
        self._last_native = None

    def remove_image(self) -> None:
        self.image = self.mask = self.photo = None
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

    def canvas_to_image(self, x: float, y: float) -> tuple[int, int] | None:
        if self.image is None:
            return None
        native = self.map_canvas_to_image(
            x, y,
            viewport=(max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())),
            image_size=self.image.size,
            zoom=self.zoom,
            pan=(self.pan_x, self.pan_y),
        )
        if not (0 <= native[0] < self.image.width and 0 <= native[1] < self.image.height):
            return None
        return round(native[0]), round(native[1])

    def paint_native(self, start: tuple[int, int], end: tuple[int, int], erase: bool | None = None) -> None:
        if self.mask is None:
            return
        self.paint_mask(
            self.mask,
            start,
            end,
            brush_size=self.brush_size,
            erase=self.erase if erase is None else erase,
        )

    @staticmethod
    def paint_mask(
        mask: Image.Image,
        start: tuple[int, int],
        end: tuple[int, int],
        *,
        brush_size: int,
        erase: bool,
    ) -> None:
        ImageDraw.Draw(mask).line(
            (start, end), fill=0 if erase else 255, width=max(1, brush_size), joint="curve"
        )

    def _paint(self, event: tk.Event) -> None:
        native = self.canvas_to_image(event.x, event.y)
        if native is None:
            return
        if self._stroke_before is None and self.mask is not None:
            self._stroke_before = self.mask.copy()
        self.paint_native(self._last_native or native, native)
        self._last_native = native
        self.render()

    def _zoom_wheel(self, event: tk.Event) -> None:
        self.auto_fit = False
        self.zoom = max(0.1, min(8.0, self.zoom * (1.1 if event.delta > 0 else 1 / 1.1)))
        self.render()

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

    def render(self) -> None:
        self.canvas.delete("all")
        if self.image is None:
            return
        viewport = (self.canvas.winfo_width(), self.canvas.winfo_height())
        if viewport[0] <= 1 or viewport[1] <= 1:
            self.after_idle(self.render)
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
