from __future__ import annotations

import tkinter as tk
from PIL import Image, ImageTk

from widgets.phoenix.theme import PHOENIX_THEME


class CompareImageCanvas(tk.Frame):
    """A canvas component that displays a PIL Image scaled proportionally without distortion."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.card_bg)
        self.image: Image.Image | None = None
        self.photo_image: ImageTk.PhotoImage | None = None
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
        """Sets the active PIL image and triggers a render."""
        self.image = image
        self.render()

    def render(self) -> None:
        """Renders the image on the canvas, scaled proportionally to fit the canvas dimensions."""
        self.canvas.delete("all")
        self.photo_image = None

        if self.image is None:
            return

        canvas_width = max(self.canvas.winfo_width(), 1)
        canvas_height = max(self.canvas.winfo_height(), 1)

        img_width, img_height = self.image.size
        if img_width <= 0 or img_height <= 0:
            return

        # Calculate proportional scale (Fit)
        scale = min(canvas_width / img_width, canvas_height / img_height)
        render_width = max(1, int(img_width * scale))
        render_height = max(1, int(img_height * scale))

        # Perform high-quality scaling
        resized = self.image.resize((render_width, render_height), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(resized)

        # Center the image on the canvas
        self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.photo_image,
            anchor="center",
        )

    def _on_resize(self, _event: tk.Event) -> None:
        """Handle canvas resizing and redraw the image."""
        if self.image is not None:
            self.render()
