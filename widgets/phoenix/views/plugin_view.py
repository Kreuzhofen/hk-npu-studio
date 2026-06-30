from __future__ import annotations

import tkinter as tk

from widgets.phoenix.cards.plugin_card import PhoenixPluginCard
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixPluginView(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            text="Plugins",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 22, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(24, 12))

        PhoenixPluginCard(
            self,
            name="Plugin System",
            status="Ready",
            description="Plugin cards are prepared for later engine integration.",
        ).pack(fill="x", padx=24, pady=8)