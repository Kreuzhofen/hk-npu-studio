from __future__ import annotations


class GalleryController:
    """Prepared controller boundary for the Phoenix Gallery Workspace."""

    def __init__(self) -> None:
        self.status = "Bereit"

    def get_status(self) -> str:
        return self.status
