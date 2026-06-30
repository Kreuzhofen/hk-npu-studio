from __future__ import annotations

import tkinter as tk

from widgets.phoenix.cards.status_card import PhoenixStatusCard
from widgets.phoenix.controls.command_bar import PhoenixCommandBar
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixHomeView(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self._build()

    def _build(self) -> None:
        command_bar = PhoenixCommandBar(self)
        command_bar.pack(fill="x", padx=24, pady=(20, 12))

        tk.Label(
            self,
            text="Home",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 22, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(4, 12))

        PhoenixStatusCard(
            self,
            title="Workspace",
            value="Phoenix Workspace aktiv",
            detail="Die neue Oberfläche läuft parallel zur Legacy-GUI.",
        ).pack(fill="x", padx=24, pady=8)