from __future__ import annotations

from pathlib import Path

from controllers.gallery_image_loader import ImageLoader
from controllers.gallery_model import GalleryImage, GalleryModel


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
        self.model = GalleryModel()
        from config import OUTPUT_DIR
        self.current_folder: Path | None = OUTPUT_DIR
        self.thumbnail_size_label = "Mittel"
        self.status = "Bereit"
        self.refresh()

    @property
    def images(self) -> list[GalleryImage]:
        return self.model.images

    @property
    def selected_image(self) -> GalleryImage | None:
        selected = self.model.selected_images()
        return selected[0] if len(selected) == 1 else None

    @property
    def selected_images(self) -> list[GalleryImage]:
        return self.model.selected_images()

    @property
    def visible_images(self) -> list[GalleryImage]:
        return self.model.visible_images()

    @property
    def selected_paths(self) -> set[Path]:
        return set(self.model.selected_paths)

    def open_folder(self, folder: str | Path) -> list[GalleryImage]:
        self.current_folder = Path(folder)
        return self.refresh()

    def refresh(self) -> list[GalleryImage]:
        if self.current_folder is None:
            self.status = "Bereit"
            return self.visible_images

        self.status = "Lade Bilder"
        try:
            self.model.set_images(self.image_loader.load_folder(self.current_folder))
            self.status = "Bereit"
        except Exception:
            self.model.set_images([])
            self.model.clear_selection()
            self.status = "Fehler"
        return self.visible_images

    def select_image(self, image: GalleryImage, ctrl: bool = False, shift: bool = False) -> None:
        self.status = "Bereit"
        if shift:
            self.model.select_range_to(image)
        elif ctrl:
            self.model.toggle_selection(image)
        else:
            self.model.select_single(image)

    def select_all_visible(self) -> None:
        self.status = "Bereit"
        self.model.select_all_visible()

    def clear_selection(self) -> None:
        self.status = "Bereit"
        self.model.clear_selection()

    def move_selection(self, offset: int) -> None:
        self.status = "Bereit"
        self.model.move_active_selection(offset)

    def set_thumbnail_size(self, label: str) -> None:
        if label in self.THUMBNAIL_SIZES:
            self.thumbnail_size_label = label

    def set_search_text(self, value: str) -> None:
        self.status = "Bereit"
        self.model.set_search_text(value)

    def set_sort_mode(self, value: str) -> None:
        self.status = "Bereit"
        self.model.set_sort_mode(value)

    def set_filter_mode(self, value: str) -> None:
        self.status = "Bereit"
        self.model.set_filter_mode(value)

    def prepare_preview(self) -> None:
        image = self.selected_image
        if image is not None:
            self.status = f"Preview vorbereitet: {image.filename}"

    def prepare_compare_source(self) -> Path | None:
        """Prepares and returns the path of the selected image as a source for comparison."""
        image = self.selected_image
        if image is not None:
            self.status = f"Compare-Quelle vorbereitet: {image.filename}"
            return image.path
        return None

    def show_image(self, image_path: str | Path) -> bool:
        """Load the image folder and select the provided image if it is supported."""
        path = Path(image_path)
        if not path.exists() or not path.is_file():
            self.status = "Fehler"
            return False

        self.current_folder = path.parent
        self.refresh()

        for image in self.visible_images:
            if image.path == path:
                self.model.select_single(image)
                self.status = f"Bereit: {image.filename}"
                return True

        self.status = "Bild nicht in der Galerie gefunden"
        return False

    def get_thumbnail_size(self) -> int:
        return self.THUMBNAIL_SIZES[self.thumbnail_size_label]

    def get_status(self) -> str:
        return self.status

    def get_image_count(self) -> int:
        return len(self.visible_images)

    def get_selection_count(self) -> int:
        return len(self.model.selected_paths)
