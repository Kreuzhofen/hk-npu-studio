from __future__ import annotations

import tkinter as tk

from widgets.phoenix.controls.search_box import PhoenixSearchBox
from widgets.phoenix.controls.toolbar import PhoenixToolbar
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixCommandBar(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self._build()

    def _build(self) -> None:
        toolbar = PhoenixToolbar(self)
        toolbar.pack(side="left", padx=0)

        search = PhoenixSearchBox(self, placeholder="Search workspace")
        search.pack(side="right", fill="x", expand=False)