from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixHeader(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.header_bg, height=64)
        self.grid_propagate(False)
        self.pack_propagate(False)

        self.title_label: tk.Label
        self.view_label: tk.Label

        self._build()

    def _build(self) -> None:
        left = tk.Frame(self, bg=PHOENIX_THEME.header_bg)
        left.pack(side="left", fill="y", padx=18)

        self.title_label = tk.Label(
            left,
            text="Snapdragon AI Studio",
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 15, "bold"),
            anchor="w",
        )
        self.title_label.pack(side="top", anchor="w", pady=(10, 0))

        self.view_label = tk.Label(
            left,
            text="Home",
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.view_label.pack(side="top", anchor="w", pady=(0, 8))

        badge = tk.Label(
            self,
            text="Local AI Workspace",
            bg=PHOENIX_THEME.accent_dark,
            fg=PHOENIX_THEME.accent_soft,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
        )
        badge.pack(side="right", padx=18)

    def set_view(self, title: str) -> None:
        self.view_label.configure(text=title)
