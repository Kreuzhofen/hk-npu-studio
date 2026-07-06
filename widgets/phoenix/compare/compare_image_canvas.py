from __future__ import annotations

import tkinter as tk
from PIL import Image, ImageTk

from widgets.phoenix.theme import PHOENIX_THEME


class CompareImageCanvas(tk.Frame):
    """
    A canvas component that displays a PIL Image using an internal viewport architecture.
    Prepared for future zoom and panning features.
    """

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.card_bg)
        self.image: Image.Image | None = None
        self.photo_image: ImageTk.PhotoImage | None = None

        # Viewport State (Zoom & Pan parameters)
        self.zoom_scale: float = 1.0
        self.pan_offset_x: int = 0
        self.pan_offset_y: int = 0
        self.auto_fit: bool = True

        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._on_resize)

    def set_image(self, image: Image.Image | None) -> None:
        """Sets the active PIL image and resets viewport state to auto-fit."""
        self.image = image
        self.auto_fit = True
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.render()

    def render(self) -> None:
        """Renders the image on the canvas based on current viewport coordinates."""
        self.canvas.delete("all")
        self.photo_image = None

        if self.image is None:
            return

        # 1. Determine viewport size
        viewport_width = max(self.canvas.winfo_width(), 1)
        viewport_height = max(self.canvas.winfo_height(), 1)

        img_width, img_height = self.image.size
        if img_width <= 0 or img_height <= 0:
            return

        # 2. Viewport scaling calculation
        if self.auto_fit:
            # Scale proportionally to fit completely within the viewport
            self.zoom_scale = min(viewport_width / img_width, viewport_height / img_height)

        render_width = max(1, int(img_width * self.zoom_scale))
        render_height = max(1, int(img_height * self.zoom_scale))

        # 3. Perform image scaling
        resized = self.image.resize((render_width, render_height), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(resized)

        # 4. Compute layout center applying viewport pan offsets
        center_x = (viewport_width // 2) + self.pan_offset_x
        center_y = (viewport_height // 2) + self.pan_offset_y

        self.canvas.create_image(
            center_x,
            center_y,
            image=self.photo_image,
            anchor="center",
        )

    def _on_resize(self, _event: tk.Event) -> None:
        """Redraws the viewport when the canvas dimensions change."""
        if self.image is not None:
            self.render()
