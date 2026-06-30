from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixPropertiesPanel(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.panel_bg)
        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            text="Properties",
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            self,
            text="Select an item to inspect properties.",
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 10),
            anchor="w",
            wraplength=220,
            justify="left",
        ).pack(fill="x", padx=16)