from __future__ import annotations

import tkinter as tk
from tkinter import filedialog

from controllers.gallery_controller import GalleryController
from controllers.gallery_model import GalleryImage
from widgets.phoenix.gallery.inspector import GalleryInspector
from widgets.phoenix.gallery.status_bar import GalleryStatusBar
from widgets.phoenix.gallery.thumbnail_area import GalleryThumbnailArea
from widgets.phoenix.gallery.toolbar import GalleryToolbar
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixGalleryView(tk.Frame):
    """Professional interactive Gallery Workspace."""

    CTRL_MASK = 0x0004
    SHIFT_MASK = 0x0001

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
        self._bind_keyboard()
        self._refresh_ui()

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
            text="Öffne einen lokalen Ordner, um Bilder als responsive Galerie zu durchsuchen.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(PHOENIX_THEME.space_xs, 0))

        self.gallery_toolbar = GalleryToolbar(
            self.header,
            on_open_folder=self._open_folder,
            on_refresh=self._refresh_folder,
            on_thumbnail_size_change=self._set_thumbnail_size,
            on_search_change=self._set_search_text,
            on_sort_change=self._set_sort_mode,
            on_filter_change=self._set_filter_mode,
        )
        self.gallery_toolbar.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(PHOENIX_THEME.space_md, 0),
        )

    def _build_main_area(self) -> None:
        self.thumbnail_area = GalleryThumbnailArea(
            self,
            on_select=self._select_image,
            on_clear_selection=self._clear_selection,
            on_double_click=self._prepare_preview,
        )
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

    def _bind_keyboard(self) -> None:
        self._bind_gallery_key("<Control-a>", self._select_all)
        self._bind_gallery_key("<Control-A>", self._select_all)
        self._bind_gallery_key("<Escape>", self._clear_selection_event)
        self._bind_gallery_key("<Return>", self._prepare_preview_event)
        self._bind_gallery_key("<Left>", lambda event: self._move_selection(-1))
        self._bind_gallery_key("<Right>", lambda event: self._move_selection(1))
        self._bind_gallery_key(
            "<Up>",
            lambda event: self._move_selection(-self.thumbnail_area.get_column_count()),
        )
        self._bind_gallery_key(
            "<Down>",
            lambda event: self._move_selection(self.thumbnail_area.get_column_count()),
        )

    def _bind_gallery_key(self, sequence: str, callback) -> None:
        self.thumbnail_area.bind(sequence, callback)
        self.thumbnail_area.canvas.bind(sequence, callback)

    def _open_folder(self) -> None:
        folder = filedialog.askdirectory(title="Bildordner öffnen")
        if not folder:
            return

        self.controller.status = "Lade Bilder"
        self._refresh_status()
        self.update_idletasks()
        self.controller.open_folder(folder)
        self.thumbnail_area.clear_cache()
        self._refresh_ui()
        self.thumbnail_area.focus_gallery()

    def _refresh_folder(self) -> None:
        if self.controller.current_folder is None:
            self._refresh_ui()
            return

        self.controller.status = "Lade Bilder"
        self._refresh_status()
        self.update_idletasks()
        self.controller.refresh()
        self.thumbnail_area.clear_cache()
        self._refresh_ui()

    def _set_thumbnail_size(self, label: str) -> None:
        self.controller.set_thumbnail_size(label)
        self._refresh_ui()

    def _set_search_text(self, value: str) -> None:
        self.controller.set_search_text(value)
        self._refresh_ui()

    def _set_sort_mode(self, value: str) -> None:
        self.controller.set_sort_mode(value)
        self._refresh_ui()

    def _set_filter_mode(self, value: str) -> None:
        self.controller.set_filter_mode(value)
        self._refresh_ui()

    def _select_image(self, image: GalleryImage, event: tk.Event) -> None:
        ctrl = bool(event.state & self.CTRL_MASK)
        shift = bool(event.state & self.SHIFT_MASK)
        self.controller.select_image(image, ctrl=ctrl, shift=shift)
        self._refresh_ui()

    def _clear_selection(self) -> None:
        self.controller.clear_selection()
        self._refresh_ui()

    def _prepare_preview(self, image: GalleryImage) -> None:
        self.controller.select_image(image)
        self.controller.prepare_preview()
        self._refresh_ui()

    def _select_all(self, event: tk.Event) -> str | None:
        if self._event_from_search(event):
            return None
        self.controller.select_all_visible()
        self._refresh_ui()
        return "break"

    def _clear_selection_event(self, event: tk.Event) -> str | None:
        if self._event_from_search(event):
            return None
        self._clear_selection()
        return "break"

    def _prepare_preview_event(self, event: tk.Event) -> str | None:
        if self._event_from_search(event):
            return None
        self.controller.prepare_preview()
        self._refresh_ui()
        return "break"

    def _move_selection(self, offset: int) -> str | None:
        if self.focus_get() == self.gallery_toolbar.search_entry:
            return None
        self.controller.move_selection(offset)
        self._refresh_ui()
        return "break"

    def _event_from_search(self, event: tk.Event) -> bool:
        return event.widget == self.gallery_toolbar.search_entry

    def _refresh_ui(self) -> None:
        self.thumbnail_area.set_images(
            self.controller.visible_images,
            self.controller.selected_paths,
            self.controller.get_thumbnail_size(),
        )
        self.inspector.update_selection(self.controller.selected_images)
        self._refresh_status()

    def _refresh_status(self) -> None:
        self.status_bar.update_values(
            image_count=self.controller.get_image_count(),
            selection_count=self.controller.get_selection_count(),
            thumbnail_size=self.controller.thumbnail_size_label,
            status=self.controller.get_status(),
        )
