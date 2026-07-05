from __future__ import annotations

import tkinter as tk
from pathlib import Path

from controllers.gallery_model import GalleryImage
from widgets.phoenix.gallery.thumbnail_area import GalleryThumbnailArea
from widgets.phoenix.layout.workspace import WorkspaceFrame


class PhoenixGalleryView(WorkspaceFrame):
    """Phoenix Gallery Workspace with a responsive placeholder Thumbnail-Grid."""

    # Klassenkonstanten zur Vermeidung von Magic Numbers
    DEFAULT_THUMBNAIL_SIZE = 124
    MOCK_IMAGE_COUNT = 12

    def __init__(self, master: tk.Misc, controller: object | None = None) -> None:
        super().__init__(
            master,
            title="Gallery Workspace",
            subtitle="Bildkatalog durchsuchen und verwalten",
            has_inspector=False,
        )
        self.controller = controller

        # Lokale Zustände für die Auswahldemo (ohne Model/Controller)
        self.selected_paths: set[Path] = set()
        self.mock_images: list[GalleryImage] = []

        self.thumbnail_area: GalleryThumbnailArea

        self._generate_mock_data()
        self._build_shell()
        self._refresh_ui()

    def _generate_mock_data(self) -> None:
        """
        Erzeugt 12 temporäre Platzhalter-Bilder für das Layout-Grid (Sprint P-049.0B).
        Diese Daten werden in einem zukünftigen Sprint durch den echten Image Loader ersetzt.
        """
        formats = [".png", ".jpg", ".webp", ".tiff"]
        resolutions = [
            (1920, 1080),
            (1280, 720),
            (2048, 2048),
            (1024, 768),
        ]
        
        for i in range(1, self.MOCK_IMAGE_COUNT + 1):
            fmt = formats[(i - 1) % len(formats)]
            res = resolutions[(i - 1) % len(resolutions)]
            filename = f"placeholder_{i:03d}{fmt}"
            
            self.mock_images.append(
                GalleryImage(
                    path=Path(f"mock_dir/{filename}"),
                    filename=filename,
                    extension=fmt,
                    width=res[0],
                    height=res[1],
                    file_size=1024 * 1024 * i,  # Mock Dateigröße
                )
            )

    def _build_shell(self) -> None:
        # Konfigurieren der Grid-Spalten im Inhaltsbereich
        self.content_slot.grid_rowconfigure(0, weight=1)
        self.content_slot.grid_columnconfigure(0, weight=1)

        # Verwende die modulare Grid-Komponente für die Platzhalter
        self.thumbnail_area = GalleryThumbnailArea(
            self.content_slot,
            on_select=self._select_image,
            on_clear_selection=self._clear_selection,
            on_double_click=self._on_double_click_placeholder,
        )
        self.thumbnail_area.grid(row=0, column=0, sticky="nsew")

    def _select_image(self, image: GalleryImage, event: tk.Event) -> None:
        """Behandelt das Anklicken einer Karte zur visuellen Markierung."""
        # Nur Einzelbildauswahl (Mehrfachauswahl NICHT implementiert)
        if image.path in self.selected_paths:
            self.selected_paths.remove(image.path)
        else:
            self.selected_paths.clear()
            self.selected_paths.add(image.path)
        self._refresh_ui()

    def _clear_selection(self) -> None:
        """Löscht die visuelle Selektionsmarkierung."""
        self.selected_paths.clear()
        self._refresh_ui()

    def _on_double_click_placeholder(self, image: GalleryImage) -> None:
        """Doppelklick-Platzhalter-Callback."""
        pass

    def _refresh_ui(self) -> None:
        """Aktualisiert die Galerie-Ansicht."""
        self.thumbnail_area.set_images(
            images=self.mock_images,
            selected_paths=self.selected_paths,
            thumbnail_size=self.DEFAULT_THUMBNAIL_SIZE,
        )
