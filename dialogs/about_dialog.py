"""
HK NPU STUDIO

About Dialog

Created by Holger Kreuzhofen
Phoenix UI
"""

from __future__ import annotations

import tkinter as tk

from app.i18n import tr
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from widgets.phoenix.theme import PHOENIX_THEME


class AboutDialog(StudioDialog):
    def __init__(self, master: tk.Misc, brand: BrandManager):
        super().__init__(
            master,
            title=f"{tr('about', 'Über')} {brand.app_name()}",
            brand=brand,
            size=(460, 760),
            min_size=(420, 700),
            resizable=False,
        )

        self._build_ui()
        self.center(master)

    def _build_ui(self) -> None:
        logo_image = self.load_logo_image(128)
        if logo_image is not None:
            tk.Label(
                self.body,
                image=logo_image,
                bg=PHOENIX_THEME.card_bg,
                bd=0,
            ).pack(anchor="center", pady=(0, PHOENIX_THEME.space_md))

        tk.Label(
            self.body,
            text=self.brand.header_brand_name(),
            font=PHOENIX_THEME.font_title,
            fg=PHOENIX_THEME.text_primary,
            bg=PHOENIX_THEME.card_bg,
        ).pack(anchor="center")

        tk.Label(
            self.body,
            text=self.brand.version_string(),
            font=PHOENIX_THEME.font_small,
            fg=PHOENIX_THEME.text_muted,
            bg=PHOENIX_THEME.card_bg,
        ).pack(anchor="center", pady=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_md))

        tk.Label(
            self.body,
            text=self.brand.platform_description(),
            font=PHOENIX_THEME.font_small,
            fg=PHOENIX_THEME.text_muted,
            bg=PHOENIX_THEME.card_bg,
        ).pack(anchor="center")

        tk.Label(
            self.body,
            text=self.brand.slogan(),
            font=PHOENIX_THEME.font_small,
            fg=PHOENIX_THEME.text_muted,
            bg=PHOENIX_THEME.card_bg,
            justify="center",
        ).pack(anchor="center", pady=(PHOENIX_THEME.space_xs, 0))

        tk.Label(
            self.body,
            text=self.brand.phoenix_boost_credit(),
            font=PHOENIX_THEME.font_small,
            fg=PHOENIX_THEME.text_muted,
            bg=PHOENIX_THEME.card_bg,
        ).pack(
            anchor="center",
            pady=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_lg),
        )

        self.add_separator()

        tk.Label(
            self.body,
            text=tr("created_by", "Erstellt von"),
            font=PHOENIX_THEME.font_small,
            fg=PHOENIX_THEME.text_muted,
            bg=PHOENIX_THEME.card_bg,
        ).pack(anchor="center")

        tk.Label(
            self.body,
            text=self.brand.author(),
            font=PHOENIX_THEME.font_button,
            fg=PHOENIX_THEME.text_primary,
            bg=PHOENIX_THEME.card_bg,
        ).pack(anchor="center", pady=(PHOENIX_THEME.space_xs, 0))

        tk.Label(
            self.body,
            text=tr(
                "creator_roles",
                "Gründer • Product Owner • Release Manager",
            ),
            font=PHOENIX_THEME.font_small,
            fg=PHOENIX_THEME.text_muted,
            bg=PHOENIX_THEME.card_bg,
        ).pack(anchor="center", pady=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_sm))

        tk.Label(
            self.body,
            text=self.brand.copyright(),
            font=PHOENIX_THEME.font_small,
            fg=PHOENIX_THEME.text_muted,
            bg=PHOENIX_THEME.card_bg,
        ).pack(anchor="center", pady=(0, PHOENIX_THEME.space_md))

        tk.Label(
            self.body,
            text=self.brand.ai_assistance(),
            font=PHOENIX_THEME.font_small,
            fg=PHOENIX_THEME.text_muted,
            bg=PHOENIX_THEME.card_bg,
        ).pack(anchor="center", pady=(0, PHOENIX_THEME.space_md))

        tk.Label(
            self.body,
            text=self.brand.trademark_notice(),
            font=PHOENIX_THEME.font_small,
            fg=PHOENIX_THEME.text_muted,
            bg=PHOENIX_THEME.card_bg,
            justify="center",
            wraplength=340,
        ).pack(anchor="center", pady=(0, PHOENIX_THEME.space_xl))

        self.add_footer_button(tr("ok", "OK"), self.close)
