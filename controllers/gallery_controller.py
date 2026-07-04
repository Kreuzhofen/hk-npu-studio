from __future__ import annotations

from pathlib import Path

from controllers.gallery_image_loader import ImageLoader
from controllers.gallery_model import GalleryImage


class GalleryController:
    """Controller boundary for the Phoenix Gallery Workspace."""

    THUMBNAIL_SIZES = {
        "Klein": 88,
        "Mittel": 124,
        "Groß": 164,
        "Sehr groß": 212,
    }

    def __init__(self, image_loader: ImageLoader | None = None) -> None:
        self.image_loader = image_loader or ImageLoader()
        self.current_folder: Path | None = None
        self.images: list[GalleryImage] = []
        self.selected_image: GalleryImage | None = None
        self.thumbnail_size_label = "Mittel"
        self.status = "Bereit"

    def open_folder(self, folder: str | Path) -> list[GalleryImage]:
        self.current_folder = Path(folder)
        return self.refresh()

    def refresh(self) -> list[GalleryImage]:
        if self.current_folder is None:
            self.status = "Bereit"
            return self.images

        self.status = "Lade Bilder"
        try:
            self.images = self.image_loader.load_folder(self.current_folder)
            self._restore_selection_after_reload()
            self.status = "Bereit"
        except Exception:
            self.images = []
            self.selected_image = None
            self.status = "Fehler"
        return self.images

    def select_image(self, image: GalleryImage | None) -> None:
        self.selected_image = image

    def set_thumbnail_size(self, label: str) -> None:
        if label in self.THUMBNAIL_SIZES:
            self.thumbnail_size_label = label

    def get_thumbnail_size(self) -> int:
        return self.THUMBNAIL_SIZES[self.thumbnail_size_label]

    def get_status(self) -> str:
        return self.status

    def get_image_count(self) -> int:
        return len(self.images)

    def get_selection_count(self) -> int:
        return 1 if self.selected_image is not None else 0

    def _restore_selection_after_reload(self) -> None:
        if self.selected_image is None:
            return

        selected_path = self.selected_image.path
        self.selected_image = next(
            (image for image in self.images if image.path == selected_path),
            None,
        )
