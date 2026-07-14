"""
Snapdragon AI Studio

Theme Manager

Created by Holger Kreuzhofen
Phoenix UI
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ThemePalette:
    background: str
    surface: str
    card: str
    elevated: str
    border: str
    accent: str
    success: str
    warning: str
    error: str
    text: str
    text_secondary: str
    text_disabled: str
    text_on_accent: str
    button: str
    button_hover: str
    button_active: str
    sidebar: str
    header: str
    workspace: str


class ThemeManager:
    PROFESSIONAL_DARK = "professional_dark"
    PROFESSIONAL_LIGHT = "professional_light"

    # Evaluate environment variable and map 'dark' / 'light' to internal theme names
    _env_val = os.environ.get("SNAPDRAGON_AI_THEME", "").strip().lower()
    if _env_val in ("light", PROFESSIONAL_LIGHT):
        _active_theme = PROFESSIONAL_LIGHT
    elif _env_val in ("dark", PROFESSIONAL_DARK):
        _active_theme = PROFESSIONAL_DARK
    else:
        _active_theme = PROFESSIONAL_DARK


    _palettes = {
        PROFESSIONAL_DARK: ThemePalette(
            background="#111315",
            surface="#181B1F",
            card="#20242A",
            elevated="#272C33",
            border="#343A43",
            accent="#2F80ED",
            success="#22C55E",
            warning="#AAB2C0",
            error="#AAB2C0",
            text="#F2F4F8",
            text_secondary="#AAB2C0",
            text_disabled="#6B7280",
            text_on_accent="#F2F4F8",
            button="#2F80ED",
            button_hover="#1E5FBF",
            button_active="#1E5FBF",
            sidebar="#181B1F",
            header="#181B1F",
            workspace="#111315",
        ),
        PROFESSIONAL_LIGHT: ThemePalette(
            background="#F1F2F3",
            surface="#E5E7EA",
            card="#F7F8F8",
            elevated="#F7F8F8",
            border="#D1D4D8",
            accent="#2F80ED",
            success="#15803D",
            warning="#6E7A89",
            error="#6E7A89",
            text="#18212C",
            text_secondary="#586575",
            text_disabled="#9BA5B1",
            text_on_accent="#FFFFFF",
            button="#2F80ED",
            button_hover="#2468C9",
            button_active="#1E5FBF",
            sidebar="#E5E7EA",
            header="#F7F8F8",
            workspace="#F1F2F3",
        ),
    }

    @classmethod
    def set_active_theme(cls, theme_name: str) -> None:
        normalized = theme_name.strip().lower()
        if normalized in ("light", cls.PROFESSIONAL_LIGHT):
            normalized = cls.PROFESSIONAL_LIGHT
        elif normalized in ("dark", cls.PROFESSIONAL_DARK):
            normalized = cls.PROFESSIONAL_DARK
        else:
            normalized = cls.PROFESSIONAL_DARK

        cls._active_theme = normalized


    @classmethod
    def active_theme(cls) -> str:
        if cls._active_theme not in cls._palettes:
            return cls.PROFESSIONAL_DARK

        return cls._active_theme

    @classmethod
    def palette(cls) -> ThemePalette:
        return cls._palettes[cls.active_theme()]

    @classmethod
    def color(cls, role: str) -> str:
        palette = cls.palette()
        return getattr(palette, role, palette.text)
