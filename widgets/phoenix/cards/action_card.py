from __future__ import annotations

import tkinter as tk
from typing import Callable

from widgets.phoenix.theme import PHOENIX_THEME


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

        tk.Button(
            self,
            text=button_text,
            command=command,
            bg=PHOENIX_THEME.accent,
            fg="#FFFFFF",
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
            cursor="hand2",
        ).pack(anchor="w", padx=16, pady=(0, 14))