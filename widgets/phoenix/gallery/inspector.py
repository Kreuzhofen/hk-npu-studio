from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class GalleryInspector(tk.Frame):
    """Prepared inspector area for future Gallery metadata."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            width=286,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.grid_propagate(False)
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        tk.Label(
            self,
            text="Inspector",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(PHOENIX_THEME.card_pad_y, PHOENIX_THEME.space_xs),
        )

        tk.Label(
            self,
            text="Bilddetails und Auswahlstatus",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(0, PHOENIX_THEME.space_lg),
        )

        self._section("Auswahl", ("Keine Auswahl", "Bereit für Einzel- und Mehrfachauswahl."), 2)
        self._section("Datei", ("Name: -", "Typ: -", "Auflösung: -"), 3)
        self._section("Verarbeitung", ("Original / Output: vorbereitet", "Compare: vorbereitet"), 4)

    def _section(self, title: str, lines: tuple[str, ...], row: int) -> None:
        card = tk.Frame(
            self,
            bg=PHOENIX_THEME.elevated_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        card.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(0, PHOENIX_THEME.space_md),
        )
        card.grid_columnconfigure(0, weight=1)

        tk.Label(
            card,
            text=title,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_sm),
        )

        for index, line in enumerate(lines, start=1):
            tk.Label(
                card,
                text=line,
                bg=PHOENIX_THEME.elevated_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_small,
                anchor="w",
                justify="left",
                wraplength=220,
            ).grid(
                row=index,
                column=0,
                sticky="ew",
                padx=PHOENIX_THEME.space_md,
                pady=(0, PHOENIX_THEME.space_xs),
            )

        tk.Frame(card, bg=PHOENIX_THEME.elevated_bg, height=PHOENIX_THEME.space_sm).grid(
            row=len(lines) + 1,
            column=0,
            sticky="ew",
        )
