from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from controllers.gallery_model import GalleryImage
from widgets.phoenix.theme import PHOENIX_THEME


class ThumbnailWidget(tk.Frame):
    """Single selectable thumbnail card."""

    def __init__(
        self,
        master: tk.Misc,
        image: GalleryImage,
        thumbnail_image: tk.PhotoImage | None,
        size: int,
        selected: bool,
        command: Callable[[GalleryImage], None],
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.elevated_bg,
            highlightbackground=PHOENIX_THEME.accent if selected else PHOENIX_THEME.border,
            highlightthickness=2 if selected else 1,
        )
        self.image = image
        self.thumbnail_image = thumbnail_image
        self.command = command
        self.size = size
        self.selected = selected
        self._build()
        self._bind_clicks(self)

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        preview = tk.Frame(
            self,
            bg=PHOENIX_THEME.card_bg,
            width=self.size,
            height=self.size,
        )
        preview.grid(
            row=0,
            column=0,
            padx=PHOENIX_THEME.space_sm,
            pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.space_xs),
        )
        preview.grid_propagate(False)
        preview.grid_columnconfigure(0, weight=1)
        preview.grid_rowconfigure(0, weight=1)

        if self.thumbnail_image is None:
            image_label = tk.Label(
                preview,
                text="-",
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_section,
            )
        else:
            image_label = tk.Label(
                preview,
                image=self.thumbnail_image,
                bg=PHOENIX_THEME.card_bg,
                bd=0,
            )
        image_label.grid(row=0, column=0)
        self._bind_clicks(preview)
        self._bind_clicks(image_label)

        name_label = tk.Label(
            self,
            text=self._short_filename(self.image.filename),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary if self.selected else PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="center",
            justify="center",
            wraplength=max(96, self.size + PHOENIX_THEME.space_md),
        )
        name_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_sm,
            pady=(0, PHOENIX_THEME.space_sm),
        )
        self._bind_clicks(name_label)

    def _bind_clicks(self, widget: tk.Widget) -> None:
        widget.bind("<Button-1>", self._on_click)

    def _on_click(self, _event: tk.Event) -> None:
        self.command(self.image)

    def _short_filename(self, filename: str) -> str:
        if len(filename) <= 28:
            return filename
        stem, dot, suffix = filename.rpartition(".")
        if not dot:
            return f"{filename[:25]}..."
        return f"{stem[:20]}...{suffix}"
