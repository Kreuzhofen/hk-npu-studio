from __future__ import annotations

import tkinter as tk

from widgets.phoenix.cards.status_card import PhoenixStatusCard
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixDashboard(tk.Frame):
    def __init__(self, master: tk.Misc, controller: object | None = None) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.controller = controller
        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            text="Dashboard",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 22, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(24, 8))

        tk.Label(
            self,
            text="Phoenix Workspace läuft parallel zur bestehenden GUI.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 11),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 16))

        PhoenixStatusCard(
            self,
            title="Workspace Status",
            value="Aktiv",
            detail="Legacy-GUI bleibt unverändert.",
        ).pack(fill="x", padx=24, pady=8)

        PhoenixStatusCard(
            self,
            title="Sprint",
            value="P-024.3",
            detail="Phoenix Workspace Integration.",
        ).pack(fill="x", padx=24, pady=8)

        PhoenixStatusCard(
            self,
            title="Views",
            value="Home · Plugins · Settings · Image",
            detail="Sidebar-Navigation ist vorbereitet.",
        ).pack(fill="x", padx=24, pady=8)