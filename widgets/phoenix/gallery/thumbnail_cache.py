from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, ImageTk


class ThumbnailCache:
    """Creates and stores Tk thumbnail images for the Gallery UI."""

    def __init__(self) -> None:
        self._cache: dict[tuple[Path, int], ImageTk.PhotoImage] = {}

    def get(self, image_path: Path, size: int) -> ImageTk.PhotoImage | None:
        key = (image_path, size)
        if key not in self._cache:
            thumbnail = self._create_thumbnail(image_path, size)
            if thumbnail is None:
                return None
            self._cache[key] = ImageTk.PhotoImage(thumbnail)
        return self._cache[key]

    def clear(self) -> None:
        self._cache.clear()

    def _create_thumbnail(self, image_path: Path, size: int) -> Image.Image | None:
        try:
            with Image.open(image_path) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                image.thumbnail((size, size), Image.Resampling.LANCZOS)
                return image
        except Exception:
            return None
