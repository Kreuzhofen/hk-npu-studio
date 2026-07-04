from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from controllers.gallery_model import GalleryImage


class ImageLoader:
    """Loads supported image files from one folder without recursion."""

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp",
        ".tif",
        ".tiff",
    }

    def load_folder(self, folder: Path) -> list[GalleryImage]:
        if not folder.exists() or not folder.is_dir():
            return []

        images: list[GalleryImage] = []
        for path in sorted(folder.iterdir(), key=lambda item: item.name.lower()):
            if path.is_file() and path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                images.append(self._read_image(path))
        return images

    def _read_image(self, path: Path) -> GalleryImage:
        width: int | None = None
        height: int | None = None
        try:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source)
                width, height = image.size
        except Exception:
            width = None
            height = None

        try:
            file_size = path.stat().st_size
        except OSError:
            file_size = None

        return GalleryImage(
            path=path,
            filename=path.name,
            extension=path.suffix,
            width=width,
            height=height,
            file_size=file_size,
        )
