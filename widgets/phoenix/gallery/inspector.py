from __future__ import annotations

import tkinter as tk

from controllers.gallery_model import GalleryImage
from widgets.phoenix.layout.workspace import WorkspaceInfoCard, WorkspacePanel
from widgets.phoenix.theme import PHOENIX_THEME


class GalleryInspector(WorkspacePanel):
    """Inspector area for selected Gallery image metadata."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            title="Inspector",
            subtitle="Bilddetails und Auswahlstatus",
            width=286,
        )
        self.selection_card: WorkspaceInfoCard
        self.file_card: WorkspaceInfoCard
        self.generation_card: WorkspaceInfoCard
        self.path_card: WorkspaceInfoCard
        self._build()
        self.update_selection([])

    def _build(self) -> None:
        self.selection_card = self._create_section("Auswahl", 0)
        self.file_card = self._create_section("Datei", 1)
        self.generation_card = self._create_section("Generierung", 2)
        self.path_card = self._create_section("Pfad", 3)

    def update_selection(self, images: list[GalleryImage]) -> None:
        if not images:
            self._set_section(self.selection_card, ("Keine Auswahl", "Klicke ein Thumbnail an."))
            self._set_section(self.file_card, ("Name: -", "Auflösung: -", "Format: -", "Dateigröße: -", "Erstellt: -"))
            self._set_section(self.generation_card, ("Modell: -", "Prompt: -", "Seed: -"))
            self._set_section(self.path_card, ("-",))
            return

        if len(images) > 1:
            self._set_section(
                self.selection_card,
                (f"{len(images)} Bilder ausgewählt", "Ctrl/Shift-Auswahl aktiv."),
            )
            self._set_section(self.file_card, ("Mehrfachauswahl", "Einzeldetails werden nicht erzwungen."))
            self._set_section(self.generation_card, ("Mehrfachauswahl", ""))
            self._set_section(self.path_card, ("-",))
            return

        image = images[0]
        self._set_section(self.selection_card, ("1 Bild ausgewählt", image.filename))
        self._set_section(
            self.file_card,
            (
                f"Name: {image.filename}",
                f"Auflösung: {image.resolution_label}",
                f"Format: {image.format_label}",
                f"Dateigröße: {image.size_label}",
                f"Erstellt: {image.created_label}",
            ),
        )

        prompt_val = image.prompt or "-"
        model_val = image.model_id or "-"
        seed_val = str(image.seed) if image.seed is not None else "-"

        self._set_section(
            self.generation_card,
            (
                f"Modell: {model_val}",
                f"Prompt: {prompt_val}",
                f"Seed: {seed_val}",
            ),
        )
        self._set_section(self.path_card, (str(image.path),))

    def _create_section(self, title: str, row: int) -> WorkspaceInfoCard:
        card = WorkspaceInfoCard(self.content, title)
        card.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(0, PHOENIX_THEME.space_md),
        )
        return card

    def _set_section(self, card: WorkspaceInfoCard, lines: tuple[str, ...]) -> None:
        card.set_lines(lines)
