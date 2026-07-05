from __future__ import annotations

import tkinter as tk

from widgets.phoenix.layout.workspace import WorkspaceInfoCard, WorkspacePanel
from widgets.phoenix.theme import PHOENIX_THEME


class CompareInspector(WorkspacePanel):
    """Inspector foundation for future compare metadata and processing details."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            title="Inspector",
            subtitle="Original, Output und Vergleichsstatus",
            width=286,
        )
        self.cards: dict[str, WorkspaceInfoCard] = {}
        self._build()

    def _build(self) -> None:
        for row, title in enumerate(("Original", "Output", "Bildinformationen", "Verarbeitung")):
            card = WorkspaceInfoCard(self.content, title)
            card.grid(
                row=row,
                column=0,
                sticky="ew",
                padx=PHOENIX_THEME.card_pad_x,
                pady=(0, PHOENIX_THEME.space_md),
            )
            self.cards[title] = card

    def update_sections(self, sections: dict[str, tuple[str, ...]]) -> None:
        for title, card in self.cards.items():
            card.set_lines(sections.get(title, ("-",)))
