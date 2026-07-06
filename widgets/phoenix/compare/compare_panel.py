from __future__ import annotations

import tkinter as tk

from widgets.phoenix.compare.compare_placeholder import ComparePlaceholder
from widgets.phoenix.theme import PHOENIX_THEME


class ComparePanel(tk.Frame):
    """Panel shell for compare sources, showing a placeholder for P-050.0."""

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        empty_title: str,
        empty_text: str,
        icon_name: str,
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.title = title
        self.empty_title = empty_title
        self.empty_text = empty_text
        self.icon_name = icon_name
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Panel Header
        tk.Label(
            self,
            text=self.title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(PHOENIX_THEME.card_pad_y, PHOENIX_THEME.space_sm),
        )

        # Placeholder Content Slot (Sprint P-050.0 only shows placeholder)
        self.placeholder = ComparePlaceholder(
            self,
            title=self.empty_title,
            subtitle=self.empty_text,
            icon_name=self.icon_name,
        )
        self.placeholder.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(0, PHOENIX_THEME.card_pad_y),
        )
