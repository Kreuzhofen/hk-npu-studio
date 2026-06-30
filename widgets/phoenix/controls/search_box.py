from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixSearchBox(tk.Frame):
    def __init__(self, master: tk.Misc, placeholder: str = "Search") -> None:
        super().__init__(master, bg=PHOENIX_THEME.panel_bg)
        self.placeholder = placeholder
        self.value = tk.StringVar()

        self.entry = tk.Entry(
            self,
            textvariable=self.value,
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
        )
        self.entry.pack(fill="x", padx=10, pady=8)
        self.entry.insert(0, placeholder)