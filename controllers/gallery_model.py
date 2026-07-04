from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class GalleryImage:
    """Image metadata used by the Gallery Workspace."""

    path: Path
    filename: str
    extension: str
    width: int | None
    height: int | None
    file_size: int | None

    @property
    def resolution_label(self) -> str:
        if self.width is None or self.height is None:
            return "-"
        return f"{self.width} × {self.height}"

    @property
    def format_label(self) -> str:
        return self.extension.upper().lstrip(".") or "-"

    @property
    def size_label(self) -> str:
        if self.file_size is None:
            return "-"

        size = float(self.file_size)
        units = ("B", "KB", "MB", "GB")
        for unit in units:
            if size < 1024 or unit == units[-1]:
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024


@dataclass
class GalleryModel:
    """State model for Gallery filtering, sorting and selection."""

    images: list[GalleryImage] = field(default_factory=list)
    search_text: str = ""
    sort_mode: str = "Name"
    filter_mode: str = "Alle"
    selected_paths: set[Path] = field(default_factory=set)
    active_path: Path | None = None
    anchor_path: Path | None = None

    def set_images(self, images: list[GalleryImage]) -> None:
        self.images = images
        valid_paths = {image.path for image in images}
        self.selected_paths = {path for path in self.selected_paths if path in valid_paths}
        if self.active_path not in valid_paths:
            self.active_path = next(iter(self.selected_paths), None)
        if self.anchor_path not in valid_paths:
            self.anchor_path = self.active_path

    def set_search_text(self, value: str) -> None:
        self.search_text = value.strip().lower()
        self._drop_hidden_selection()

    def set_sort_mode(self, value: str) -> None:
        self.sort_mode = value

    def set_filter_mode(self, value: str) -> None:
        self.filter_mode = value
        self._drop_hidden_selection()

    def visible_images(self) -> list[GalleryImage]:
        images = [image for image in self.images if self._matches_search(image)]
        images = [image for image in images if self._matches_filter(image)]
        return sorted(images, key=self._sort_key)

    def selected_images(self) -> list[GalleryImage]:
        selected = [image for image in self.visible_images() if image.path in self.selected_paths]
        return selected

    def select_single(self, image: GalleryImage) -> None:
        self.selected_paths = {image.path}
        self.active_path = image.path
        self.anchor_path = image.path

    def toggle_selection(self, image: GalleryImage) -> None:
        if image.path in self.selected_paths:
            self.selected_paths.remove(image.path)
        else:
            self.selected_paths.add(image.path)
        self.active_path = image.path
        self.anchor_path = image.path

    def select_range_to(self, image: GalleryImage) -> None:
        visible = self.visible_images()
        if not visible:
            return

        anchor = self.anchor_path or self.active_path or image.path
        index_by_path = {item.path: index for index, item in enumerate(visible)}
        if anchor not in index_by_path:
            anchor = image.path

        start = index_by_path[anchor]
        end = index_by_path[image.path]
        low, high = sorted((start, end))
        self.selected_paths = {item.path for item in visible[low : high + 1]}
        self.active_path = image.path
        self.anchor_path = anchor

    def select_all_visible(self) -> None:
        visible = self.visible_images()
        self.selected_paths = {image.path for image in visible}
        self.active_path = visible[0].path if visible else None
        self.anchor_path = self.active_path

    def clear_selection(self) -> None:
        self.selected_paths.clear()
        self.active_path = None
        self.anchor_path = None

    def move_active_selection(self, offset: int) -> None:
        visible = self.visible_images()
        if not visible:
            self.clear_selection()
            return

        index_by_path = {image.path: index for index, image in enumerate(visible)}
        current_index = index_by_path.get(self.active_path, 0)
        next_index = min(max(current_index + offset, 0), len(visible) - 1)
        self.select_single(visible[next_index])

    def _drop_hidden_selection(self) -> None:
        visible_paths = {image.path for image in self.visible_images()}
        self.selected_paths = {path for path in self.selected_paths if path in visible_paths}
        if self.active_path not in visible_paths:
            self.active_path = next(iter(self.selected_paths), None)
        if self.anchor_path not in visible_paths:
            self.anchor_path = self.active_path

    def _matches_search(self, image: GalleryImage) -> bool:
        if not self.search_text:
            return True
        return self.search_text in image.filename.lower()

    def _matches_filter(self, image: GalleryImage) -> bool:
        extension = image.extension.lower().lstrip(".")
        if self.filter_mode == "Alle":
            return True
        if self.filter_mode == "JPG/JPEG":
            return extension in {"jpg", "jpeg"}
        if self.filter_mode == "TIFF":
            return extension in {"tif", "tiff"}
        return extension == self.filter_mode.lower()

    def _sort_key(self, image: GalleryImage) -> tuple:
        if self.sort_mode == "Datum":
            try:
                return (image.path.stat().st_mtime, image.filename.lower())
            except OSError:
                return (0, image.filename.lower())
        if self.sort_mode == "Größe":
            return (image.file_size or 0, image.filename.lower())
        if self.sort_mode == "Typ":
            return (image.extension.lower(), image.filename.lower())
        return (image.filename.lower(),)
