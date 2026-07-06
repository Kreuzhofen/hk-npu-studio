from __future__ import annotations

from PIL import Image, ImageOps


class ThumbnailService:
    """Core service for creating image thumbnails preserving aspect ratio and EXIF orientation."""

    @staticmethod
    def prepare_thumbnail_image(image: Image.Image, size: int) -> Image.Image:
        """
        Resizes a PIL Image to fit within size x size, preserving aspect ratio.
        Transposes orientation based on EXIF metadata if present.
        Returns a PIL Image (safe to call in background threads).
        """
        processed = ImageOps.exif_transpose(image).convert("RGB")
        processed.thumbnail((size, size), Image.Resampling.LANCZOS)
        return processed
