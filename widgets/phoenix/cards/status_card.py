from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixStatusCard(tk.Frame):
    def __init__(self, master: tk.Misc, title: str, value: str, detail: str = "") -> None:
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
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 4))

        tk.Label(
            self,
            text=value,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16)

        if detail:
            tk.Label(
                self,
                text=detail,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_secondary,
                font=("Segoe UI", 9),
                anchor="w",
                wraplength=360,
            ).pack(fill="x", padx=16, pady=(6, 14))
        else:
            tk.Frame(self, bg=PHOENIX_THEME.card_bg, height=14).pack(fill="x")