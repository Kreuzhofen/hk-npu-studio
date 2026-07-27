from __future__ import annotations

import tkinter as tk
from typing import Callable

from engine.brand_manager import BrandManager
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr
from widgets.phoenix.controls.button import PhoenixButton


class PhoenixSidebar(tk.Frame):
    BUTTON_HEIGHT = 42
    BUTTON_RADIUS = 6
    BUTTON_PADX = 14
    BUTTON_FONT = (PHOENIX_THEME.font_button[0], 10, "bold")

    ICON_COLORS = {
        "home": "#60a5fa",
        "prompt": "#a78bfa",
        "models": "#34d399",
        "gallery": "#fbbf24",
        "compare": "#2dd4bf",
        "plugins": "#fb7185",
        "settings": "#cbd5e1",
    }

    def __init__(
        self,
        master: tk.Misc,
        controller: object | None = None,
        on_navigate: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(master, bg=PHOENIX_THEME.panel_bg, width=220)
        self.controller = controller
        self.on_navigate = on_navigate
        self.grid_propagate(False)
        self.pack_propagate(False)

        self._buttons: dict[str, tk.Button] = {}

        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            text=BrandManager.ENGINE_NAME,
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.space_lg, pady=(24, 4))

        tk.Label(
            self,
            text=tr("nav_workspace_version", "Workspace 1.0"),
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.space_lg, pady=(0, 16))

        self._nav_button("home", tr("nav_home", "Home"))
        self._nav_button("prompt", tr("nav_ai_generate", "AI Generate"))
        self._nav_button("models", tr("nav_ai_model_manager", "AI Model Manager"))
        # self._nav_button("image", "Image")
        self._nav_button("gallery", tr("nav_gallery", "Gallery"))
        self._nav_button("compare", tr("nav_compare", "Compare"))
        self._nav_button("plugins", tr("nav_plugins", "Plugins"))
        self._nav_button("settings", tr("nav_settings", "Settings"))

    def _nav_button(self, view_name: str, text: str) -> None:
        button = PhoenixButton(
            self,
            text=text,
            command=lambda: self._navigate(view_name),
            button_type="nav",
            icon_name=view_name,
            icon_color=self.ICON_COLORS.get(view_name, PHOENIX_THEME.accent),
            height=self.BUTTON_HEIGHT,
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=self.BUTTON_FONT,
            radius=self.BUTTON_RADIUS,
        )
        button.pack(fill="x", padx=self.BUTTON_PADX, pady=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_xs))
        self._buttons[view_name] = button

    def _navigate(self, view_name: str) -> None:
        if self.on_navigate is not None:
            self.on_navigate(view_name)

    def set_active(self, view_name: str) -> None:
        for name, button in self._buttons.items():
            if name == view_name:
                button.configure(
                    button_type="nav_active",
                    height=self.BUTTON_HEIGHT,
                    bg=PHOENIX_THEME.panel_bg,
                    fg=PHOENIX_THEME.text_primary,
                    font=self.BUTTON_FONT,
                    icon_color=self.ICON_COLORS.get(name, PHOENIX_THEME.accent),
                )
            else:
                button.configure(
                    button_type="nav",
                    height=self.BUTTON_HEIGHT,
                    bg=PHOENIX_THEME.panel_bg,
                    fg=PHOENIX_THEME.text_secondary,
                    font=self.BUTTON_FONT,
                    icon_color=self.ICON_COLORS.get(name, PHOENIX_THEME.accent),
                )
