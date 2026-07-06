from __future__ import annotations

from PIL import Image, ImageOps, ImageTk


class ThumbnailService:
    """Core service for creating image thumbnails preserving aspect ratio and EXIF orientation."""

    @staticmethod
    def create_thumbnail(image: Image.Image, size: int) -> ImageTk.PhotoImage:
        """
        Resizes a PIL Image to fit within size x size, preserving aspect ratio.
        Transposes orientation based on EXIF metadata if present.
        """
        # Ensure correct EXIF orientation and RGB mode
        processed = ImageOps.exif_transpose(image).convert("RGB")
        processed.thumbnail((size, size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(processed)
