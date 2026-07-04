from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class GalleryStatusBar(tk.Frame):
    """Status bar for Gallery runtime details."""

    def __init__(self, master: tk.Misc, status: str) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.surface,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.values: dict[str, tk.Label] = {}
        self._build(status)

    def _build(self, status: str) -> None:
        self.grid_columnconfigure(6, weight=1)

        self._item("Bilder", "0", 0)
        self._divider(1)
        self._item("Auswahl", "0", 2)
        self._divider(3)
        self._item("Zoom", "Mittel", 4)
        self._divider(5)
        self._item("Status", status, 6, sticky="e")

    def update_values(
        self,
        image_count: int,
        selection_count: int,
        thumbnail_size: str,
        status: str,
    ) -> None:
        self.values["Bilder"].configure(text=str(image_count))
        self.values["Auswahl"].configure(text=str(selection_count))
        self.values["Zoom"].configure(text=thumbnail_size)
        self.values["Status"].configure(text=status)

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

        value_label = tk.Label(
            host,
            text=value,
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        value_label.pack(side="left", padx=(PHOENIX_THEME.space_xs, 0))
        self.values[label] = value_label

    def _divider(self, column: int) -> None:
        tk.Frame(self, bg=PHOENIX_THEME.border, width=1).grid(
            row=0,
            column=column,
            sticky="ns",
            pady=PHOENIX_THEME.space_sm,
        )
