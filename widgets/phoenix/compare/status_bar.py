from __future__ import annotations

import tkinter as tk

from widgets.phoenix.layout.workspace import WorkspaceStatusBar


class CompareStatusBar(WorkspaceStatusBar):
    """Status bar foundation for Compare Workspace state."""

    def __init__(self, master: tk.Misc, items: dict[str, str]) -> None:
        super().__init__(master)
        self._build(items)

    def _build(self, items: dict[str, str]) -> None:
        self.grid_columnconfigure(8, weight=1)
        self.add_item("Original", items.get("Original", "Nicht geladen"), 0)
        self.add_divider(1)
        self.add_item("Output", items.get("Output", "Nicht geladen"), 2)
        self.add_divider(3)
        self.add_item("Zoom", items.get("Zoom", "Fit"), 4)
        self.add_divider(5)
        self.add_item("Sync", items.get("Sync", "Bereit"), 6)
        self.add_divider(7)
        self.add_item("Status", items.get("Status", "Bereit"), 8, sticky="e")

    def update_values(self, items: dict[str, str]) -> None:
        for label, value in items.items():
            self.update_item(label, value)
