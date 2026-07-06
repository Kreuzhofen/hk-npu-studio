from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageTk

from widgets.phoenix.gallery.thumbnail_service import ThumbnailService


class ThumbnailProvider:
    """Provides thumbnails for the Gallery UI. Prepared for future caching implementation."""

    def __init__(self, service: ThumbnailService | None = None) -> None:
        self.service = service or ThumbnailService()
        # Prepared for future cache implementations:
        # self._ram_cache = ...
        # self._disk_cache = ...

    def get_thumbnail(self, image_path: Path, size: int) -> ImageTk.PhotoImage | None:
        """
        Loads the image from the given path and creates a thumbnail.
        Prepared for cache lookup and storage.
        """
        # 1. Future: Check RAM cache
        # 2. Future: Check Disk cache
        try:
            with Image.open(image_path) as source:
                thumbnail = self.service.create_thumbnail(source, size)
                # 3. Future: Store in cache
                return thumbnail
        except Exception:
            return None
