from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable

from engine.brand_manager import BrandManager
from engine.theme_manager import ThemeManager
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr
from widgets.phoenix.controls.button import PhoenixButton


class PhoenixSidebar(tk.Frame):
    BUTTON_HEIGHT = 46
    BUTTON_RADIUS = 6
    BUTTON_PADX = 14
    BUTTON_FONT = (PHOENIX_THEME.font_button[0], 11, "bold")

    ICON_COLORS = {
        "home": "#3253DC",
        "prompt": "#a78bfa",
        "models": "#34d399",
        "gallery": "#fbbf24",
        "compare": "#2dd4bf",
        "plugins": "#94a3b8",
        "settings": "#f87171",
    }
    LIGHT_ICON_COLORS = {
        "home": "#2446C0",
        "prompt": "#7C3AED",
        "models": "#15803D",
        "gallery": "#A16207",
        "compare": "#0F766E",
        "plugins": "#475569",
        "settings": "#DC2626",
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
        self.brand_label = tk.Label(
            self,
            text=BrandManager.ENGINE_NAME,
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        )
        self.brand_label.pack(
            fill="x",
            padx=PHOENIX_THEME.space_lg,
            pady=(24, 4),
        )

        self.brand_credit_label = tk.Label(
            self,
            text=BrandManager.PHOENIX_BOOST_CREDIT,
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_muted,
            font=self._brand_credit_font(),
            anchor="w",
        )
        self.brand_credit_label.pack(
            fill="x",
            padx=PHOENIX_THEME.space_lg,
            pady=(0, 16),
        )

        self._nav_button("home", tr("nav_home", "Home"))
        self._nav_button("prompt", tr("nav_ai_generate", "AI Generate"))
        self._nav_button("models", tr("nav_ai_model_manager", "AI Model Manager"))
        # self._nav_button("image", "Image")
        self._nav_button("gallery", tr("nav_gallery", "Gallery"))
        self._nav_button("compare", tr("nav_compare", "Compare"))
        self._nav_button("plugins", tr("nav_plugins", "Plugins"))
        self._nav_button("settings", tr("nav_settings", "Settings"))

    def _brand_credit_font(self) -> tuple[str, int]:
        family = PHOENIX_THEME.font_caption[0]
        title_font = tkfont.Font(root=self, font=PHOENIX_THEME.font_section)
        title_width = title_font.measure(BrandManager.ENGINE_NAME)
        max_size = PHOENIX_THEME.font_section[1] - 1

        for size in range(max_size, 0, -1):
            candidate = tkfont.Font(root=self, family=family, size=size)
            if candidate.measure(BrandManager.PHOENIX_BOOST_CREDIT) <= title_width:
                return (family, size)

        return (family, 1)

    def _nav_button(self, view_name: str, text: str) -> None:
        icon_color = self._icon_color(view_name)
        button = PhoenixButton(
            self,
            text=text,
            command=lambda: self._navigate(view_name),
            button_type="nav",
            icon_name=view_name,
            icon_color=icon_color,
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
                active_color = self._icon_color(name)
                button.configure(
                    button_type="nav_active",
                    height=self.BUTTON_HEIGHT,
                    bg=PHOENIX_THEME.panel_bg,
                    fg=active_color,
                    font=self.BUTTON_FONT,
                    icon_color=active_color,
                )
            else:
                button.configure(
                    button_type="nav",
                    height=self.BUTTON_HEIGHT,
                    bg=PHOENIX_THEME.panel_bg,
                    fg=PHOENIX_THEME.text_secondary,
                    font=self.BUTTON_FONT,
                    icon_color=self._icon_color(name),
                )

    @classmethod
    def _icon_color(cls, view_name: str) -> str:
        palette = (
            cls.LIGHT_ICON_COLORS
            if ThemeManager.active_theme() == ThemeManager.PROFESSIONAL_LIGHT
            else cls.ICON_COLORS
        )
        return palette.get(view_name, PHOENIX_THEME.accent)
