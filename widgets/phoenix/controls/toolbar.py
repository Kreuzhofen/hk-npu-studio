from __future__ import annotations

import tkinter as tk
from typing import Callable

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixToolbar(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self._build()

    def _build(self) -> None:
        self.add_button("New", self._noop)
        self.add_button("Open", self._noop)
        self.add_button("Run", self._noop)

    def add_button(self, text: str, command: Callable[[], None]) -> None:
        tk.Button(
            self,
            text=text,
            command=command,
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_secondary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))

    def _noop(self) -> None:
        return None