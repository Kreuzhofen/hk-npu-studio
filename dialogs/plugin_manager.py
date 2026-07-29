"""
Snapdragon AI Studio

Plugin Manager Dialog

Created by Holger Kreuzhofen
Phoenix UI
"""

from __future__ import annotations

import tkinter as tk

from app.i18n import tr
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from widgets.phoenix.theme import PHOENIX_THEME


class PluginManagerDialog(StudioDialog):
    def __init__(self, master: tk.Misc):
        super().__init__(
            master,
            title=tr("plugin_manager", "Plugin-Manager"),
            brand=getattr(master, "brand", BrandManager()),
            size=(560, 420),
            min_size=(480, 360),
            resizable=False,
        )

        self._build_ui()
        self.center(master)

    def _build_ui(self) -> None:
        self.add_title(
            tr("plugin_manager", "Plugin-Manager"),
            tr(
                "plugin_manager_subtitle",
                "Verfügbare Studio-Plugins und ihre Laufzeitumgebung.",
            ),
        )

        plugin_card = self.add_card()

        content = tk.Frame(plugin_card, bg=PHOENIX_THEME.elevated_bg)
        content.pack(
            fill="x",
            padx=PHOENIX_THEME.card_pad_x,
            pady=PHOENIX_THEME.card_pad_y,
        )

        tk.Label(
            content,
            text=tr("plugin", "Plugin"),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            content,
            text="RealESRGAN",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_value,
            anchor="w",
        ).pack(fill="x", pady=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_md))

        self._info_row(content, tr("type", "Typ"), tr("image_upscale", "Bildskalierung"))
        self._info_row(content, tr("backend", "Backend"), "QNN / Snapdragon NPU")
        self._info_row(content, tr("status", "Status"), tr("ready", "Bereit"))

        tk.Label(
            self.body,
            text=tr(
                "more_plugins_later",
                "Weitere Plugins folgen in späteren Versionen.",
            ),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).pack(fill="x", pady=(PHOENIX_THEME.space_xs, 0))

        self.add_footer_button(tr("ok", "OK"), self.close)

    def _info_row(self, master: tk.Misc, label: str, value: str) -> None:
        row = tk.Frame(master, bg=PHOENIX_THEME.elevated_bg)
        row.pack(fill="x", pady=(0, PHOENIX_THEME.space_sm))
        row.grid_columnconfigure(0, weight=0)
        row.grid_columnconfigure(1, weight=1)

        tk.Label(
            row,
            text=label,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            width=10,
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            row,
            text=value,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=0, column=1, sticky="w")
