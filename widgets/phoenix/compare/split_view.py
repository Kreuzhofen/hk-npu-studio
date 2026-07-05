from __future__ import annotations

import tkinter as tk

from resources.icons import IconManager
from widgets.phoenix.theme import PHOENIX_THEME


class CompareSplitView(tk.Frame):
    """Responsive split preview foundation for original and output images."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.grid_columnconfigure(0, weight=1, uniform="compare_preview")
        self.grid_columnconfigure(1, weight=1, uniform="compare_preview")
        self.grid_rowconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        self._create_preview_panel(
            column=0,
            title="Original",
            empty_title="Originalbild laden",
            empty_text="Öffne links ein Ausgangsbild für den späteren Qualitätsvergleich.",
            icon_name="image",
        )
        self._create_preview_panel(
            column=1,
            title="Ergebnis",
            empty_title="Ausgabe erscheint nach Verarbeitung",
            empty_text="Hier wird künftig das AI- oder Batch-Ergebnis synchron angezeigt.",
            icon_name="output",
        )

    def _create_preview_panel(
        self,
        column: int,
        title: str,
        empty_title: str,
        empty_text: str,
        icon_name: str,
    ) -> None:
        outer_pad = (0, PHOENIX_THEME.space_sm) if column == 0 else (PHOENIX_THEME.space_sm, 0)
        panel = tk.Frame(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        panel.grid(row=0, column=column, sticky="nsew", padx=outer_pad, pady=0)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        tk.Label(
            panel,
            text=title,
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

        empty = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        empty.grid(row=1, column=0, sticky="nsew", padx=PHOENIX_THEME.card_pad_x, pady=(0, PHOENIX_THEME.card_pad_y))
        empty.grid_columnconfigure(0, weight=1)
        empty.grid_rowconfigure(0, weight=1)
        empty.grid_rowconfigure(4, weight=1)

        tk.Label(
            empty,
            text=IconManager.get_symbol(icon_name),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=(PHOENIX_THEME.font_title[0], 42, "bold"),
            anchor="center",
        ).grid(row=1, column=0, sticky="ew", pady=(0, PHOENIX_THEME.space_lg))

        tk.Label(
            empty,
            text=empty_title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="center",
        ).grid(row=2, column=0, sticky="ew")

        tk.Label(
            empty,
            text=empty_text,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="center",
            justify="center",
            wraplength=360,
        ).grid(row=3, column=0, sticky="ew", pady=(PHOENIX_THEME.space_md, 0))
