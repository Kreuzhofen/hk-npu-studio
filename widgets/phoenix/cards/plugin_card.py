from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixPluginCard(tk.Frame):
    def __init__(self, master: tk.Misc, name: str, status: str, description: str = "") -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )

        tk.Label(
            self,
            text=name,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(12, 2))

        tk.Label(
            self,
            text=status,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(fill="x", padx=14)

        if description:
            tk.Label(
                self,
                text=description,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_secondary,
                font=("Segoe UI", 9),
                anchor="w",
                justify="left",
                wraplength=220,
            ).pack(fill="x", padx=14, pady=(6, 12))