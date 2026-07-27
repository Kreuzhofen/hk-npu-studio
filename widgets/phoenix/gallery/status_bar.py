from __future__ import annotations

import tkinter as tk

from widgets.phoenix.layout.workspace import WorkspaceStatusBar
from app.i18n import tr


class GalleryStatusBar(WorkspaceStatusBar):
    """Status bar for Gallery runtime details."""

    def __init__(self, master: tk.Misc, status: str) -> None:
        super().__init__(master)
        self._build(status)

    def _build(self, status: str) -> None:
        self.grid_columnconfigure(6, weight=1)

        self.add_item(tr("images", "Bilder"), "0", 0)
        self.add_divider(1)
        self.add_item(tr("selection", "Auswahl"), "0", 2)
        self.add_divider(3)
        self.add_item(tr("zoom", "Zoom"), tr("size_medium", "Mittel"), 4)
        self.add_divider(5)
        
        display_status = tr("ready", "Bereit") if status == "Bereit" else status
        self.add_item(tr("status", "Status"), display_status, 6, sticky="e")

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

    def update_item(self, label: str, value: str) -> None:
        mapping = {
            "Bilder": tr("images", "Bilder"),
            "Auswahl": tr("selection", "Auswahl"),
            "Zoom": tr("zoom", "Zoom"),
            "Status": tr("status", "Status"),
        }
        display_label = mapping.get(label, label)
        display_value = tr("ready", "Bereit") if value == "Bereit" else value
        super().update_item(display_label, display_value)
