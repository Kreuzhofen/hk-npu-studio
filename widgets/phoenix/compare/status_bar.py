from __future__ import annotations

import tkinter as tk

from widgets.phoenix.layout.workspace import WorkspaceStatusBar
from app.i18n import tr
from app.runtime_localization import localize_runtime_text


class CompareStatusBar(WorkspaceStatusBar):
    """Status bar foundation for Compare Workspace state."""

    def __init__(self, master: tk.Misc, items: dict[str, str]) -> None:
        super().__init__(master)
        self._build(items)

    def _build(self, items: dict[str, str]) -> None:
        self.grid_columnconfigure(8, weight=1)
        self.add_item(tr("compare_left_title", "Original"), items.get("Original", tr("not_loaded", "Nicht geladen")), 0)
        self.add_divider(1)
        self.add_item(tr("output_title", "Ausgabe"), items.get("Output", tr("not_loaded", "Nicht geladen")), 2)
        self.add_divider(3)
        self.add_item(tr("zoom", "Zoom"), items.get("Zoom", tr("fit", "Einpassen")), 4)
        self.add_divider(5)
        self.add_item(tr("compare_sync_short", "Sync"), localize_runtime_text(items.get("Sync", "ready")), 6)
        self.add_divider(7)
        self.add_item(tr("status", "Status"), localize_runtime_text(items.get("Status", "ready")), 8, sticky="e")

    def update_values(self, items: dict[str, str]) -> None:
        label_mapping = {
            "Original": tr("compare_left_title", "Original"),
            "Output": tr("output_title", "Ausgabe"),
            "Zoom": tr("zoom", "Zoom"),
            "Sync": tr("compare_sync_short", "Sync"),
            "Status": tr("status", "Status"),
        }
        for label, value in items.items():
            display_value = (
                localize_runtime_text(value)
                if label in {"Sync", "Status"}
                else value
            )
            self.update_item(label_mapping.get(label, label), display_value)
