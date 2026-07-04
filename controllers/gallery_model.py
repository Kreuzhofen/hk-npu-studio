from __future__ import annotations

from dataclasses import dataclass
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
