from __future__ import annotations

import tkinter as tk
from typing import Callable

from app.i18n import tr
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.theme import PHOENIX_THEME


class ModelReadyDialog(StudioDialog):
    """Shared non-technical completion for guided model setup."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_open_generate: Callable[[], None],
        brand: BrandManager | None = None,
    ) -> None:
        self._on_open_generate = on_open_generate
        super().__init__(
            master,
            title=tr("setup_complete_title", "Setup complete"),
            brand=brand,
            size=(540, 300),
            min_size=(480, 270),
            resizable=False,
        )
        self._build_ui()
        self.center(master)
        self.wait_window(self)

    def _build_ui(self) -> None:
        card = self.add_card()
        content = tk.Frame(card, bg=PHOENIX_THEME.elevated_bg)
        content.pack(fill="x", padx=PHOENIX_THEME.card_pad_x, pady=PHOENIX_THEME.card_pad_y)
        tk.Label(
            content,
            text=tr("home_studio_ready", "✓ Snapdragon AI Studio is ready"),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.success,
            font=PHOENIX_THEME.font_section,
            anchor="center",
            justify="center",
            wraplength=420,
        ).pack(fill="x")
        self.create_button = PhoenixButton(
            self.footer,
            text=tr("home_create_first_image", "Create first image"),
            command=self._open_generate,
            button_type="primary",
            width=260,
        )
        self.create_button.pack(anchor="center")

    def _open_generate(self) -> None:
        self._on_open_generate()
        self.close()
