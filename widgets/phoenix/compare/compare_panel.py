from __future__ import annotations

import tkinter as tk
from PIL import Image

from widgets.phoenix.compare.compare_image_canvas import CompareImageCanvas
from widgets.phoenix.compare.compare_placeholder import ComparePlaceholder
from widgets.phoenix.theme import PHOENIX_THEME


class ComparePanel(tk.Frame):
    """Panel shell for compare sources, managing placeholder and image canvas slots."""

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        empty_title: str,
        empty_text: str,
        icon_name: str,
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.title = title
        self.empty_title = empty_title
        self.empty_text = empty_text
        self.icon_name = icon_name
        self.active_image: Image.Image | None = None
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Panel Header
        tk.Label(
            self,
            text=self.title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(PHOENIX_THEME.card_pad_y, PHOENIX_THEME.space_sm),
        )

        # Create content slot frame
        self.content_frame = tk.Frame(self, bg=PHOENIX_THEME.card_bg)
        self.content_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(0, PHOENIX_THEME.card_pad_y),
        )
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # 1. Placeholder
        self.placeholder = ComparePlaceholder(
            self.content_frame,
            title=self.empty_title,
            subtitle=self.empty_text,
            icon_name=self.icon_name,
        )
        self.placeholder.grid(row=0, column=0, sticky="nsew")

        # 2. Image Canvas
        self.image_canvas = CompareImageCanvas(self.content_frame)
        # Initially not gridded, shown dynamically

    def set_image(self, image: Image.Image | None) -> None:
        """Sets the panel image, switching between placeholder and image canvas views."""
        self.active_image = image

        if image is None:
            self.image_canvas.grid_forget()
            self.placeholder.grid(row=0, column=0, sticky="nsew")
            self.image_canvas.set_image(None)
        else:
            self.placeholder.grid_forget()
            self.image_canvas.grid(row=0, column=0, sticky="nsew")
            self.image_canvas.set_image(image)

    def set_zoom(self, zoom_scale: float | None) -> None:
        """Sets the zoom scale on the image canvas component."""
        self.image_canvas.set_zoom(zoom_scale)

    def update_panel(self, image: Image.Image | None, zoom_scale: float | None) -> None:
        """Updates the panel content slot with image and zoom scale."""
        self.active_image = image

        if image is None:
            self.image_canvas.grid_forget()
            self.placeholder.grid(row=0, column=0, sticky="nsew")
            self.image_canvas.update_viewport(None, zoom_scale)
        else:
            self.placeholder.grid_forget()
            self.image_canvas.grid(row=0, column=0, sticky="nsew")
            self.image_canvas.update_viewport(image, zoom_scale)
