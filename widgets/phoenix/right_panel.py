from __future__ import annotations

import tkinter as tk


class PhoenixRightPanel(tk.Frame):
    def __init__(self, master: tk.Misc, controller: object | None = None) -> None:
        super().__init__(master, bg="#111827", width=280)
        self.controller = controller
        self.grid_propagate(False)
        self._build()

    def _build(self) -> None:
        title = tk.Label(
            self,
            text="Inspector",
            bg="#111827",
            fg="#F8FAFC",
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        )
        title.pack(fill="x", padx=18, pady=(18, 10))

        info = tk.Label(
            self,
            text="Noch keine Auswahl.\n\nDieser Bereich wird später für Dateiinfos, Pluginstatus und Aktionen genutzt.",
            bg="#111827",
            fg="#CBD5E1",
            font=("Segoe UI", 10),
            justify="left",
            anchor="nw",
            wraplength=230,
        )
        info.pack(fill="both", expand=True, padx=18, pady=(0, 18))