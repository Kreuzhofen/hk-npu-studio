from __future__ import annotations

import tkinter as tk

from controllers.gallery_controller import GalleryController
from controllers.gallery_model import GalleryImage
from widgets.phoenix.gallery.status_bar import GalleryStatusBar
from widgets.phoenix.gallery.thumbnail_area import GalleryThumbnailArea
from widgets.phoenix.gallery.toolbar import GalleryToolbar
from widgets.phoenix.layout.workspace import WorkspaceFrame


class PhoenixGalleryView(WorkspaceFrame):
    """Phoenix Gallery Workspace with a responsive placeholder Thumbnail-Grid."""

    # Klassenkonstanten zur Vermeidung von Magic Numbers
    DEFAULT_THUMBNAIL_SIZE = 124

    def __init__(self, master: tk.Misc, controller: object | None = None) -> None:
        super().__init__(
            master,
            title="Gallery Workspace",
            subtitle="Bildkatalog durchsuchen und verwalten",
            has_inspector=False,
        )
        self.controller = controller or GalleryController()

        self.thumbnail_area: GalleryThumbnailArea
        self.toolbar: GalleryToolbar
        self.status_bar: GalleryStatusBar

        self._build_shell()
        self._refresh_ui()

    def _build_shell(self) -> None:
        # 1. Build Toolbar and place in self.header.toolbar_slot
        self.toolbar = GalleryToolbar(
            self.header.toolbar_slot,
            on_open_folder=self._on_open_folder,
            on_refresh=self._on_refresh,
            on_thumbnail_size_change=self._on_thumbnail_size_change,
            on_search_change=self._on_search_change,
            on_sort_change=self._on_sort_change,
            on_filter_change=self._on_filter_change,
        )
        self.toolbar.grid(row=0, column=0, sticky="ew")

        # 2. Build Thumbnail Area and place in self.content_slot
        self.content_slot.grid_rowconfigure(0, weight=1)
        self.content_slot.grid_columnconfigure(0, weight=1)

        self.thumbnail_area = GalleryThumbnailArea(
            self.content_slot,
            on_select=self._select_image,
            on_clear_selection=self._clear_selection,
            on_double_click=self._on_double_click,
        )
        self.thumbnail_area.grid(row=0, column=0, sticky="nsew")

        # 3. Build Status Bar and place in self.status_slot
        self.status_bar = GalleryStatusBar(self.status_slot, self.controller.get_status())
        self.status_bar.grid(row=0, column=0, sticky="ew")

    def _on_open_folder(self) -> None:
        from tkinter import filedialog
        folder = filedialog.askdirectory(
            title="Bilderordner auswählen",
            initialdir=self.controller.current_folder or ""
        )
        if folder:
            self.controller.open_folder(folder)
            self._refresh_ui()

    def _on_refresh(self) -> None:
        self.controller.refresh()
        self._refresh_ui()

    def _on_thumbnail_size_change(self, size_label: str) -> None:
        self.controller.set_thumbnail_size(size_label)
        self._refresh_ui()

    def _on_search_change(self, value: str) -> None:
        self.controller.set_search_text(value)
        self._refresh_ui()

    def _on_sort_change(self, value: str) -> None:
        self.controller.set_sort_mode(value)
        self._refresh_ui()

    def _on_filter_change(self, value: str) -> None:
        self.controller.set_filter_mode(value)
        self._refresh_ui()

    def _select_image(self, image: GalleryImage, event: tk.Event) -> None:
        """Behandelt das Anklicken einer Karte zur visuellen Markierung."""
        # Einzelbildauswahl (Mehrfachauswahl laut Sprintumfang nicht implementiert)
        self.controller.select_image(image, ctrl=False, shift=False)
        self._refresh_ui()

    def _clear_selection(self) -> None:
        """Löscht die visuelle Selektionsmarkierung."""
        self.controller.clear_selection()
        self._refresh_ui()

    def _on_double_click(self, image: GalleryImage) -> None:
        # First ensure the image is selected in the controller
        self.controller.select_image(image, ctrl=False, shift=False)
        path = self.controller.prepare_compare_source()
        self._refresh_ui()

        if path:
            app = self.winfo_toplevel()
            if hasattr(app, "application_controller") and app.application_controller is not None:
                app.application_controller.open_compare_with_image(path)

    def refresh(self) -> None:
        """Aktualisiert die Galerie beim Wechseln/Periodisch."""
        self._refresh_ui()

    def show_generated_image(self, image_path: str) -> None:
        """Load the generated image into the Asset Library and select it."""
        self.controller.show_image(image_path)
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        """Aktualisiert die Galerie-Ansicht."""
        self.thumbnail_area.set_images(
            images=self.controller.visible_images,
            selected_paths=self.controller.selected_paths,
            thumbnail_size=self.controller.get_thumbnail_size(),
        )
        self.status_bar.update_values(
            image_count=self.controller.get_image_count(),
            selection_count=self.controller.get_selection_count(),
            thumbnail_size=self.controller.thumbnail_size_label,
            status=self.controller.get_status(),
        )

