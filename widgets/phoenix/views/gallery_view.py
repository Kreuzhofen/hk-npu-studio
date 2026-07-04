from __future__ import annotations

import tkinter as tk

from controllers.gallery_controller import GalleryController
from widgets.phoenix.gallery.inspector import GalleryInspector
from widgets.phoenix.gallery.status_bar import GalleryStatusBar
from widgets.phoenix.gallery.thumbnail_area import GalleryThumbnailArea
from widgets.phoenix.gallery.toolbar import GalleryToolbar
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixGalleryView(tk.Frame):
    """Professional Gallery Workspace foundation."""

    def __init__(
        self,
        master: tk.Misc,
        controller: GalleryController | None = None,
    ) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.controller = controller or GalleryController()

        self.header: tk.Frame
        self.gallery_toolbar: GalleryToolbar
        self.thumbnail_area: GalleryThumbnailArea
        self.inspector: GalleryInspector
        self.status_bar: GalleryStatusBar

        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self._build_header()
        self._build_main_area()
        self._build_status_bar()

    def _build_header(self) -> None:
        self.header = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        self.header.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.space_lg,
            pady=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_md),
        )
        self.header.grid_columnconfigure(0, weight=1)

        title_group = tk.Frame(self.header, bg=PHOENIX_THEME.content_bg)
        title_group.grid(row=0, column=0, sticky="ew")
        title_group.grid_columnconfigure(0, weight=1)

        tk.Label(
            title_group,
            text="Gallery Workspace",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            title_group,
            text="Professionelle Bildübersicht für spätere Thumbnail-, Filter- und Auswahl-Workflows.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(PHOENIX_THEME.space_xs, 0))

        self.gallery_toolbar = GalleryToolbar(self.header)
        self.gallery_toolbar.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(PHOENIX_THEME.space_md, 0),
        )

    def _build_main_area(self) -> None:
        self.thumbnail_area = GalleryThumbnailArea(self)
        self.thumbnail_area.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_md),
            pady=(0, PHOENIX_THEME.space_md),
        )

        self.inspector = GalleryInspector(self)
        self.inspector.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=(0, PHOENIX_THEME.space_lg),
            pady=(0, PHOENIX_THEME.space_md),
        )

    def _build_status_bar(self) -> None:
        self.status_bar = GalleryStatusBar(self, self.controller.get_status())
        self.status_bar.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.space_lg,
            pady=(0, PHOENIX_THEME.space_lg),
        )
