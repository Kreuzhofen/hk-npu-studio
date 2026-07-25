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
            stat = path.stat()
            file_size = stat.st_size
            file_created_at = int(stat.st_ctime)
        except OSError:
            file_size = None
            file_created_at = None

        prompt: str | None = None
        model_id: str | None = None
        seed: int | None = None
        metadata: dict[str, Any] = {}

        sidecar = path.with_suffix(".json")
        if sidecar.is_file():
            try:
                import json
                with open(sidecar, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                if "metadata" in meta and isinstance(meta["metadata"], dict):
                    metadata = meta["metadata"]
                else:
                    metadata = meta
                prompt = metadata.get("prompt")
                model_id = metadata.get("model_id") or metadata.get("model")
                seed = metadata.get("seed")
            except Exception:
                pass

        return GalleryImage(
            path=path,
            filename=path.name,
            extension=path.suffix,
            width=width,
            height=height,
            file_size=file_size,
            file_created_at=file_created_at,
            prompt=prompt,
            model_id=model_id,
            seed=seed,
            metadata=metadata,
        )
