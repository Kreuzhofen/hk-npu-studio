from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from pathlib import Path

from controllers.gallery_model import GalleryImage
from resources.icons import IconManager
from widgets.phoenix.gallery.thumbnail_provider import ThumbnailProvider
from widgets.phoenix.gallery.thumbnail_widget import ThumbnailWidget
from widgets.phoenix.theme import PHOENIX_THEME


class GalleryThumbnailArea(tk.Frame):
    """Scrollable responsive thumbnail grid with a professional empty state."""

    CARD_GAP = 14
    CARD_EXTRA_WIDTH = 18

    def __init__(
        self,
        master: tk.Misc,
        on_select: Callable[[GalleryImage, tk.Event], None],
        on_clear_selection: Callable[[], None],
        on_double_click: Callable[[GalleryImage], None],
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            takefocus=True,
        )
        self.on_select = on_select
        self.on_clear_selection = on_clear_selection
        self.on_double_click = on_double_click
        self.provider = ThumbnailProvider(self)
        self.render_generation = 0
        self.images: list[GalleryImage] = []
        self.selected_paths: set[Path] = set()
        self.thumbnail_size = 124
        self.current_columns = 1
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
        self.canvas.bind("<Button-1>", self._on_free_space_click)
        self.grid_frame.bind("<Button-1>", self._on_free_space_click)
        self._build_empty_state()

    def set_images(
        self,
        images: list[GalleryImage],
        selected_paths: set[Path],
        thumbnail_size: int,
    ) -> None:
        self.images = images
        self.selected_paths = selected_paths
        self.thumbnail_size = thumbnail_size
        self._render_grid()


    def get_column_count(self) -> int:
        return self.current_columns

    def focus_gallery(self) -> None:
        self.focus_set()
        self.canvas.focus_set()

    def _build_empty_state(self) -> None:
        self.empty_state = tk.Frame(self.grid_frame, bg=PHOENIX_THEME.card_bg)
        self.empty_state.grid_columnconfigure(0, weight=1)

        icon = tk.Label(
            self.empty_state,
            text=IconManager.get_symbol("gallery"),
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
        self.render_generation += 1
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
        self.current_columns = max(1, canvas_width // (card_width + self.CARD_GAP))

        for column in range(self.current_columns):
            self.grid_frame.grid_columnconfigure(column, weight=1)

        for index, image in enumerate(self.images):
            row = index // self.current_columns
            column = index % self.current_columns
            selected = image.path in self.selected_paths

            widget = ThumbnailWidget(
                self.grid_frame,
                image=image,
                thumbnail_image=None,
                size=self.thumbnail_size,
                selected=selected,
                command=self._select_image,
                double_command=self.on_double_click,
            )
            widget.grid(
                row=row,
                column=column,
                sticky="n",
                padx=(self.CARD_GAP // 2),
                pady=(self.CARD_GAP // 2),
            )

            # Request thumbnail asynchronously with safety checks (generation, widget lifetime, path alignment)
            thumbnail = self.provider.get_thumbnail(
                image.path,
                self.thumbnail_size,
                callback=lambda img, w=widget, path=image.path, gen=self.render_generation: self._update_widget_safe(w, img, path, gen),
            )
            if thumbnail is not None:
                widget.set_thumbnail(thumbnail)

    def _update_widget_safe(self, widget: ThumbnailWidget, photo_image: ImageTk.PhotoImage, path: Path, gen: int) -> None:
        try:
            if (
                gen == self.render_generation
                and widget.winfo_exists()
                and getattr(widget, "image", None) is not None
                and widget.image.path == path
            ):
                widget.set_thumbnail(photo_image)
        except Exception:
            pass

    def _select_image(self, image: GalleryImage, event: tk.Event) -> None:
        self.focus_gallery()
        self.on_select(image, event)

    def _on_free_space_click(self, event: tk.Event) -> None:
        if event.widget in {self.canvas, self.grid_frame}:
            self.focus_gallery()
            self.on_clear_selection()

    def _update_scroll_region(self, _event: tk.Event | None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event: tk.Event) -> None:
        self.canvas.itemconfigure("thumbnail_grid", width=event.width)
        self.grid_frame.configure(height=event.height)
        if self.images:
            self._render_grid()

    def cleanup(self) -> None:
        """Clears all loaded images and explicitly destroys widgets to release memory."""
        self.images = []
        self.selected_paths = set()
        for child in self.grid_frame.winfo_children():
            if child is not self.empty_state:
                child.destroy()

