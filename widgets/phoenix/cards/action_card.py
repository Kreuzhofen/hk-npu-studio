from __future__ import annotations

import tkinter as tk
from typing import Callable

from widgets.phoenix.theme import PHOENIX_THEME
from widgets.phoenix.controls.button import PhoenixButton


class PhoenixActionCard(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        title: str,
        description: str,
        button_text: str,
        command: Callable[[], None],
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )

        tk.Label(
            self,
            text=title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 4))

        tk.Label(
            self,
            text=description,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            wraplength=360,
        ).pack(fill="x", padx=16, pady=(0, 12))

        PhoenixButton(
            self,
            text=button_text,
            command=command,
            button_type="primary",
        ).pack(anchor="w", padx=16, pady=(0, 14))
