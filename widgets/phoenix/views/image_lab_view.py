from __future__ import annotations

import tkinter as tk
from typing import Callable

from app.i18n import tr
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixImageLabView(WorkspaceFrame):
    """
    Phoenix Image Lab: Central workspace for AI image processing & restoration
    on Qualcomm Snapdragon X NPU.
    """

    def __init__(
        self,
        master: tk.Misc,
        on_navigate: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(
            master,
            title=tr("nav_phoenix_image_lab", "Phoenix Image Lab"),
            subtitle=tr(
                "image_lab_subtitle",
                "Zentraler Arbeitsbereich für lokale KI-Bildbearbeitung und Restaurierung auf der Snapdragon NPU",
            ),
            has_inspector=False,
        )
        self.on_navigate = on_navigate
        self._build_cards()

    def _navigate(self, target: str) -> None:
        if callable(self.on_navigate):
            self.on_navigate(target)

    def _build_cards(self) -> None:
        container = tk.Frame(self.content_slot, bg=PHOENIX_THEME.content_bg)
        container.pack(fill="both", expand=True, padx=PHOENIX_THEME.space_xl, pady=PHOENIX_THEME.space_lg)
        container.grid_columnconfigure((0, 1, 2), weight=1, uniform="lab_cards")
        container.grid_rowconfigure(0, weight=1)

        # Card 1: AI Photo Restore (FiDeSR Strong)
        self._create_feature_card(
            container,
            column=0,
            title=tr("nav_photo_restore", "AI Fotorestaurierung"),
            badge=tr("image_lab_restore_badge", "FiDeSR Strong • QNN/HTP"),
            badge_color=PHOENIX_THEME.success,
            desc=tr(
                "image_lab_restore_desc",
                "Lokale Rekonstruktion und Veredelung historischer oder beschädigter Fotos. Erhält native Gesichts- und Personenmerkmale in voller Auflösung.",
            ),
            action_text=tr("image_lab_open_restore", "Fotorestaurierung öffnen"),
            target="photo_restore",
            is_primary=True,
            icon_name="sparkles",
        )

        # Card 2: Generative Fill & Inpainting (SDXL)
        self._create_feature_card(
            container,
            column=1,
            title=tr("image_lab_inpainting_title", "Generatives Füllen"),
            badge=tr("image_lab_inpainting_badge", "SDXL Inpainting • QNN/HTP"),
            badge_color=PHOENIX_THEME.accent,
            desc=tr(
                "image_lab_inpainting_desc",
                "Intelligentes Entfernen störender Bildobjekte und nahtlose Neugenerierung von Bildbereichen mittels Pinselmaske.",
            ),
            action_text=tr("image_lab_open_inpainting", "Generatives Füllen öffnen"),
            target="generative_fill",
            is_primary=False,
            icon_name="image",
        )

        # Retouch shares the existing functional inpainting workspace.
        self._create_feature_card(
            container,
            column=2,
            title=tr("image_lab_retouch_title", "Retusche"),
            badge=tr("image_lab_retouch_badge", "Maskenbasierte Bildbearbeitung"),
            badge_color=PHOENIX_THEME.warning,
            desc=tr(
                "image_lab_retouch_desc",
                "Störende Bildbereiche mit einer Pinselmaske bearbeiten. Öffnet den gemeinsamen Bereich für Generatives Füllen und Retusche.",
            ),
            action_text=tr("image_lab_open_retouch", "Retusche öffnen"),
            target="generative_fill",
            is_primary=False,
            icon_name="image",
        )

    def _create_feature_card(
        self,
        parent: tk.Frame,
        column: int,
        title: str,
        badge: str,
        badge_color: str,
        desc: str,
        action_text: str,
        target: str,
        is_primary: bool,
        icon_name: str,
    ) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        card.grid(row=0, column=column, sticky="nsew", padx=PHOENIX_THEME.space_sm, pady=PHOENIX_THEME.space_xs)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        # Header area
        header_frame = tk.Frame(card, bg=PHOENIX_THEME.card_bg)
        header_frame.grid(row=0, column=0, sticky="ew", padx=PHOENIX_THEME.card_pad_x, pady=(PHOENIX_THEME.card_pad_y, 4))
        header_frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            header_frame,
            text=title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        # Badge
        badge_lbl = tk.Label(
            card,
            text=badge,
            bg=PHOENIX_THEME.card_bg,
            fg=badge_color,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        badge_lbl.grid(row=1, column=0, sticky="w", padx=PHOENIX_THEME.card_pad_x, pady=(0, 10))

        # Description
        desc_lbl = tk.Label(
            card,
            text=desc,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="nw",
            justify="left",
            wraplength=260,
        )
        desc_lbl.grid(row=2, column=0, sticky="nsew", padx=PHOENIX_THEME.card_pad_x, pady=(0, PHOENIX_THEME.card_pad_y))

        # Action Button
        btn = PhoenixButton(
            card,
            text=action_text,
            command=lambda: self._navigate(target),
            button_type="primary" if is_primary else "neutral",
            icon_name=icon_name,
            font=PHOENIX_THEME.font_button,
            height=38,
            radius=8,
        )
        btn.grid(row=3, column=0, sticky="ew", padx=PHOENIX_THEME.card_pad_x, pady=(0, PHOENIX_THEME.card_pad_y))

        return card
