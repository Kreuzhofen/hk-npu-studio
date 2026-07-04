from __future__ import annotations

import tkinter as tk

from controllers.gallery_controller import GalleryController
from widgets.phoenix.theme import PHOENIX_THEME


class GalleryThumbnailView(tk.Frame):
    """Scrollable foundation for the future thumbnail grid."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.canvas: tk.Canvas
        self.grid_frame: tk.Frame
        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightthickness=0,
            bd=0,
        )
        scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.grid_frame = tk.Frame(self.canvas, bg=PHOENIX_THEME.card_bg)
        self.canvas.create_window(
            (0, 0),
            window=self.grid_frame,
            anchor="nw",
            tags="thumbnail_grid",
        )

        self.grid_frame.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_grid)

        tk.Label(
            self.grid_frame,
            text="Noch keine Bilder geladen",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="center",
        ).grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=PHOENIX_THEME.card_pad_y,
        )
        self.grid_frame.grid_columnconfigure(0, weight=1)

    def _update_scroll_region(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_grid(self, event: tk.Event) -> None:
        self.canvas.itemconfigure("thumbnail_grid", width=event.width)


class GalleryInspector(tk.Frame):
    """Prepared inspector area for future image metadata."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            width=260,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.grid_propagate(False)
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        tk.Label(
            self,
            text="Inspector",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(PHOENIX_THEME.card_pad_y, PHOENIX_THEME.space_sm),
        )

        tk.Label(
            self,
            text="Bildinformationen werden hier vorbereitet.",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="nw",
            justify="left",
            wraplength=210,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(0, PHOENIX_THEME.card_pad_y),
        )


class PhoenixGalleryView(tk.Frame):
    """Foundation for the future Phoenix Gallery Workspace."""

    def __init__(
        self,
        master: tk.Misc,
        controller: GalleryController | None = None,
    ) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.controller = controller or GalleryController()

        self.toolbar: tk.Frame
        self.thumbnail_view: GalleryThumbnailView
        self.inspector: GalleryInspector
        self.status_bar: tk.Frame

        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self._build_toolbar()
        self._build_thumbnail_area()
        self._build_inspector()
        self._build_status_bar()

    def _build_toolbar(self) -> None:
        self.toolbar = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        self.toolbar.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.space_lg,
            pady=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_md),
        )
        self.toolbar.grid_columnconfigure(0, weight=1)

        tk.Label(
            self.toolbar,
            text="Gallery Workspace",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            self.toolbar,
            text="Vorbereitet für Thumbnail Grid, Filter und Auswahl.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(PHOENIX_THEME.space_xs, 0))

    def _build_thumbnail_area(self) -> None:
        self.thumbnail_view = GalleryThumbnailView(self)
        self.thumbnail_view.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_md),
            pady=(0, PHOENIX_THEME.space_md),
        )

    def _build_inspector(self) -> None:
        self.inspector = GalleryInspector(self)
        self.inspector.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=(0, PHOENIX_THEME.space_lg),
            pady=(0, PHOENIX_THEME.space_md),
        )

    def _build_status_bar(self) -> None:
        self.status_bar = tk.Frame(
            self,
            bg=PHOENIX_THEME.surface,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.status_bar.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.space_lg,
            pady=(0, PHOENIX_THEME.space_lg),
        )

        tk.Label(
            self.status_bar,
            text=f"Status: {self.controller.get_status()}",
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).pack(
            fill="x",
            padx=PHOENIX_THEME.space_md,
            pady=PHOENIX_THEME.space_sm,
        )
