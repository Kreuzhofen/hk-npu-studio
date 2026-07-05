from __future__ import annotations

import tkinter as tk

from widgets.phoenix.layout.workspace import WorkspaceStatusBar


class GalleryStatusBar(WorkspaceStatusBar):
    """Status bar for Gallery runtime details."""

    def __init__(self, master: tk.Misc, status: str) -> None:
        super().__init__(master)
        self._build(status)

    def _build(self, status: str) -> None:
        self.grid_columnconfigure(6, weight=1)

        self.add_item("Bilder", "0", 0)
        self.add_divider(1)
        self.add_item("Auswahl", "0", 2)
        self.add_divider(3)
        self.add_item("Zoom", "Mittel", 4)
        self.add_divider(5)
        self.add_item("Status", status, 6, sticky="e")

    def update_values(
        self,
        image_count: int,
        selection_count: int,
        thumbnail_size: str,
        status: str,
    ) -> None:
        self.update_item("Bilder", str(image_count))
        self.update_item("Auswahl", str(selection_count))
        self.update_item("Zoom", thumbnail_size)
        self.update_item("Status", status)
