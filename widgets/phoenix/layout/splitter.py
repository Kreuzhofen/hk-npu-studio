from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixSplitter(tk.Frame):
    def __init__(self, master: tk.Misc, orientation: str = "vertical") -> None:
        width = 1 if orientation == "vertical" else 0
        height = 1 if orientation == "horizontal" else 0

        super().__init__(
            master,
            bg=PHOENIX_THEME.border,
            width=width,
            height=height,
        )