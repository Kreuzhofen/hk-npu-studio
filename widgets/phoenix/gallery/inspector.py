from __future__ import annotations

import tkinter as tk

from controllers.gallery_model import GalleryImage
from widgets.phoenix.theme import PHOENIX_THEME


class GalleryInspector(tk.Frame):
    """Inspector area for selected Gallery image metadata."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            width=286,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.grid_propagate(False)
        self.selection_card: tk.Frame
        self.file_card: tk.Frame
        self.path_card: tk.Frame
        self._build()
        self.update_selection([])

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

        self.selection_card = self._create_section("Auswahl", 2)
        self.file_card = self._create_section("Datei", 3)
        self.path_card = self._create_section("Pfad", 4)

    def update_selection(self, images: list[GalleryImage]) -> None:
        if not images:
            self._set_section(self.selection_card, ("Keine Auswahl", "Klicke ein Thumbnail an."))
            self._set_section(self.file_card, ("Name: -", "Auflösung: -", "Format: -", "Dateigröße: -"))
            self._set_section(self.path_card, ("-",))
            return

        if len(images) > 1:
            self._set_section(
                self.selection_card,
                (f"{len(images)} Bilder ausgewählt", "Ctrl/Shift-Auswahl aktiv."),
            )
            self._set_section(self.file_card, ("Mehrfachauswahl", "Einzeldetails werden nicht erzwungen."))
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
            ),
        )
        self._set_section(self.path_card, (str(image.path),))

    def _create_section(self, title: str, row: int) -> tk.Frame:
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
        return card

    def _set_section(self, card: tk.Frame, lines: tuple[str, ...]) -> None:
        for child in card.grid_slaves():
            info = child.grid_info()
            if int(info.get("row", 0)) > 0:
                child.destroy()

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
