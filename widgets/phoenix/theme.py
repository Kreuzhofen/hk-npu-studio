from __future__ import annotations

from dataclasses import dataclass

from engine.theme_manager import ThemeManager


@dataclass(frozen=True)
class PhoenixTheme:
    app_bg: str
    panel_bg: str
    content_bg: str
    header_bg: str
    card_bg: str
    elevated_bg: str
    border: str

    text_primary: str
    text_secondary: str
    text_muted: str
    text_disabled: str
    text_on_accent: str

    accent: str
    accent_dark: str
    accent_soft: str
    success: str

    background: str
    surface: str
    card: str
    elevated: str
    button: str
    button_hover: str
    button_active: str
    sidebar: str
    header: str
    workspace: str

    font_title: tuple[str, int, str] = ("Segoe UI", 22, "bold")
    font_section: tuple[str, int, str] = ("Segoe UI", 15, "bold")
    font_card_title: tuple[str, int, str] = ("Segoe UI", 9, "bold")
    font_value: tuple[str, int, str] = ("Segoe UI", 16, "bold")
    font_body: tuple[str, int] = ("Segoe UI", 10)
    font_small: tuple[str, int] = ("Segoe UI", 9)
    font_caption: tuple[str, int] = ("Segoe UI", 8)
    font_button: tuple[str, int, str] = ("Segoe UI", 10, "bold")

    space_xs: int = 4
    space_sm: int = 8
    space_md: int = 12
    space_lg: int = 18
    space_xl: int = 28
    card_pad_x: int = 20
    card_pad_y: int = 18
    button_pad_x: int = 14
    button_pad_y: int = 8


def _create_phoenix_theme() -> PhoenixTheme:
    palette = ThemeManager.palette()

    return PhoenixTheme(
        app_bg=palette.background,
        panel_bg=palette.sidebar,
        content_bg=palette.workspace,
        header_bg=palette.header,
        card_bg=palette.card,
        elevated_bg=palette.elevated,
        border=palette.border,
        text_primary=palette.text,
        text_secondary=palette.text,
        text_muted=palette.text_secondary,
        text_disabled=palette.text_disabled,
        text_on_accent=palette.text_on_accent,
        accent=palette.accent,
        accent_dark=palette.button_active,
        accent_soft=palette.surface,
        success=palette.success,
        background=palette.background,
        surface=palette.surface,
        card=palette.card,
        elevated=palette.elevated,
        button=palette.button,
        button_hover=palette.button_hover,
        button_active=palette.button_active,
        sidebar=palette.sidebar,
        header=palette.header,
        workspace=palette.workspace,
    )


PHOENIX_THEME = _create_phoenix_theme()
