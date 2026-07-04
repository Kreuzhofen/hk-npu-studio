from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from controllers.gallery_model import GalleryImage
from widgets.phoenix.gallery.thumbnail_cache import ThumbnailCache
from widgets.phoenix.gallery.thumbnail_widget import ThumbnailWidget
from widgets.phoenix.theme import PHOENIX_THEME


class GalleryThumbnailArea(tk.Frame):
    """Scrollable responsive thumbnail grid with a professional empty state."""

    CARD_GAP = 14
    CARD_EXTRA_WIDTH = 18

    def __init__(
        self,
        master: tk.Misc,
        on_select: Callable[[GalleryImage], None],
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.on_select = on_select
        self.cache = ThumbnailCache()
        self.images: list[GalleryImage] = []
        self.selected_image: GalleryImage | None = None
        self.thumbnail_size = 124
        self.canvas: tk.Canvas
        self.grid_frame: tk.Frame
        self.empty_state: tk.Frame
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
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
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
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self._build_empty_state()

    def set_images(
        self,
        images: list[GalleryImage],
        selected_image: GalleryImage | None,
        thumbnail_size: int,
    ) -> None:
        self.images = images
        self.selected_image = selected_image
        self.thumbnail_size = thumbnail_size
        self._render_grid()

    def clear_cache(self) -> None:
        self.cache.clear()

    def _build_empty_state(self) -> None:
        self.empty_state = tk.Frame(self.grid_frame, bg=PHOENIX_THEME.card_bg)
        self.empty_state.grid_columnconfigure(0, weight=1)

        icon = tk.Label(
            self.empty_state,
            text="▧",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=(PHOENIX_THEME.font_title[0], 38, "bold"),
            anchor="center",
        )
        icon.grid(row=0, column=0, pady=(0, PHOENIX_THEME.space_lg))

        tk.Label(
            self.empty_state,
            text="Noch keine Bilder in der Galerie",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="center",
        ).grid(row=1, column=0, sticky="ew")

        tk.Label(
            self.empty_state,
            text="Wähle „Ordner öffnen“, um Bilder aus einem lokalen Ordner anzuzeigen.",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="center",
            justify="center",
            wraplength=420,
        ).grid(row=2, column=0, sticky="ew", pady=(PHOENIX_THEME.space_md, 0))

    def _render_grid(self) -> None:
        self.empty_state.grid_forget()
        for child in self.grid_frame.winfo_children():
            if child is not self.empty_state:
                child.destroy()

        if not self.images:
            self._show_empty_state()
            self._update_scroll_region(None)
            return

        self._show_thumbnails()
        self._update_scroll_region(None)

    def _show_empty_state(self) -> None:
        self.grid_frame.grid_rowconfigure(0, weight=1)
        self.grid_frame.grid_columnconfigure(0, weight=1)
        self.empty_state.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=PHOENIX_THEME.space_xl,
            pady=PHOENIX_THEME.space_xl,
        )

    def _show_thumbnails(self) -> None:
        self.grid_frame.grid_rowconfigure(0, weight=0)
        canvas_width = max(self.canvas.winfo_width(), self.thumbnail_size + 80)
        card_width = self.thumbnail_size + self.CARD_EXTRA_WIDTH
        columns = max(1, canvas_width // (card_width + self.CARD_GAP))

        for column in range(columns):
            self.grid_frame.grid_columnconfigure(column, weight=1)

        for index, image in enumerate(self.images):
            row = index // columns
            column = index % columns
            selected = self.selected_image is not None and image.path == self.selected_image.path
            thumbnail = self.cache.get(image.path, self.thumbnail_size)
            widget = ThumbnailWidget(
                self.grid_frame,
                image=image,
                thumbnail_image=thumbnail,
                size=self.thumbnail_size,
                selected=selected,
                command=self.on_select,
            )
            widget.grid(
                row=row,
                column=column,
                sticky="n",
                padx=(self.CARD_GAP // 2),
                pady=(self.CARD_GAP // 2),
            )

    def _update_scroll_region(self, _event: tk.Event | None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event: tk.Event) -> None:
        self.canvas.itemconfigure("thumbnail_grid", width=event.width)
        self.grid_frame.configure(height=event.height)
        if self.images:
            self._render_grid()
