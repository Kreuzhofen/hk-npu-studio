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
        from app.i18n import tr
        self.status = tr("ready", "Bereit")
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
        self.refresh()
        return self.visible_images

    def refresh(self) -> bool:
        from app.i18n import tr
        if self.current_folder is None:
            self.status = tr("ready", "Bereit")
            return False

        self.status = tr("loading_images", "Lade Bilder")
        try:
            previous_paths = [image.path for image in self.model.images]
            loaded_images = self.image_loader.load_folder(self.current_folder)
            self.model.set_images(loaded_images)

            self.status = tr("ready", "Bereit")
            return previous_paths != [image.path for image in loaded_images]
        except Exception:
            self.model.set_images([])
            self.model.clear_selection()
            self.status = tr("status_failed", "Fehler")
            return True

    def select_image(self, image: GalleryImage, ctrl: bool = False, shift: bool = False) -> None:
        from app.i18n import tr
        self.status = tr("ready", "Bereit")
        if shift:
            self.model.select_range_to(image)
        elif ctrl:
            self.model.toggle_selection(image)
        else:
            self.model.select_single(image)

    def select_all_visible(self) -> None:
        from app.i18n import tr
        self.status = tr("ready", "Bereit")
        self.model.select_all_visible()

    def clear_selection(self) -> None:
        from app.i18n import tr
        self.status = tr("ready", "Bereit")
        self.model.clear_selection()

    def move_selection(self, offset: int) -> None:
        from app.i18n import tr
        self.status = tr("ready", "Bereit")
        self.model.move_active_selection(offset)

    def set_thumbnail_size(self, label: str) -> None:
        from app.i18n import tr
        mapping = {
            tr("size_small", "Klein"): "Klein",
            tr("size_medium", "Mittel"): "Mittel",
            tr("size_large", "Groß"): "Groß",
            tr("size_huge", "Sehr groß"): "Sehr groß",
        }
        internal_key = mapping.get(label, label)
        if internal_key in self.THUMBNAIL_SIZES:
            self.thumbnail_size_label = internal_key

    def set_search_text(self, value: str) -> None:
        from app.i18n import tr
        self.status = tr("ready", "Bereit")
        self.model.set_search_text(value)

    def set_sort_mode(self, value: str) -> None:
        from app.i18n import tr
        self.status = tr("ready", "Bereit")
        mapping = {
            tr("sort_name", "Name"): "Name",
            tr("sort_date", "Datum"): "Datum",
            tr("sort_size", "Größe"): "Größe",
            tr("sort_type", "Typ"): "Typ",
        }
        internal_key = mapping.get(value, value)
        self.model.set_sort_mode(internal_key)

    def set_filter_mode(self, value: str) -> None:
        from app.i18n import tr
        self.status = tr("ready", "Bereit")
        mapping = {
            tr("filter_all", "Alle"): "Alle",
        }
        internal_key = mapping.get(value, value)
        self.model.set_filter_mode(internal_key)

    def prepare_preview(self) -> None:
        image = self.selected_image
        if image is not None:
            from app.i18n import tr
            self.status = f"{tr('gallery_preview_prepared', 'Preview vorbereitet')}: {image.filename}"

    def prepare_compare_source(self) -> Path | None:
        """Prepares and returns the path of the selected image as a source for comparison."""
        image = self.selected_image
        if image is not None:
            from app.i18n import tr
            self.status = f"{tr('gallery_compare_source_prepared', 'Compare-Quelle vorbereitet')}: {image.filename}"
            return image.path
        return None

    def show_image(self, image_path: str | Path) -> bool:
        """Load the image folder and select the provided image if it is supported."""
        path = Path(image_path)
        if not path.exists() or not path.is_file():
            from app.i18n import tr
            self.status = tr("status_failed", "Fehler")
            return False

        self.current_folder = path.parent
        self.refresh()

        for image in self.visible_images:
            if image.path == path:
                self.model.select_single(image)
                from app.i18n import tr
                self.status = f"{tr('ready', 'Bereit')}: {image.filename}"
                return True

        from app.i18n import tr
        self.status = tr("gallery_image_not_found", "Bild nicht in der Galerie gefunden")
        return False

    def get_thumbnail_size(self) -> int:
        return self.THUMBNAIL_SIZES[self.thumbnail_size_label]

    def get_status(self) -> str:
        return self.status

    def get_image_count(self) -> int:
        return len(self.visible_images)

    def get_selection_count(self) -> int:
        return len(self.model.selected_paths)
