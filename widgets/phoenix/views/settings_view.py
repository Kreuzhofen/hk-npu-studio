from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixSettingsView(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            text="Settings",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 22, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(24, 8))

        tk.Label(
            self,
            text="Phoenix settings will be added here.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 11),
            anchor="w",
        ).pack(fill="x", padx=24)