from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class GalleryStatusBar(tk.Frame):
    """Static status bar foundation for future Gallery runtime details."""

    def __init__(self, master: tk.Misc, status: str) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.surface,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.status = status
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(6, weight=1)

        self._item("Bilder", "0", 0)
        self._divider(1)
        self._item("Auswahl", "0", 2)
        self._divider(3)
        self._item("Zoom", "Mittel", 4)
        self._divider(5)
        self._item("Status", self.status, 6, sticky="e")

    def _item(self, label: str, value: str, column: int, sticky: str = "w") -> None:
        host = tk.Frame(self, bg=PHOENIX_THEME.surface)
        host.grid(
            row=0,
            column=column,
            sticky=sticky,
            padx=PHOENIX_THEME.space_md,
            pady=PHOENIX_THEME.space_sm,
        )

        tk.Label(
            host,
            text=label,
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        ).pack(side="left")

        tk.Label(
            host,
            text=value,
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).pack(side="left", padx=(PHOENIX_THEME.space_xs, 0))

    def _divider(self, column: int) -> None:
        tk.Frame(self, bg=PHOENIX_THEME.border, width=1).grid(
            row=0,
            column=column,
            sticky="ns",
            pady=PHOENIX_THEME.space_sm,
        )
