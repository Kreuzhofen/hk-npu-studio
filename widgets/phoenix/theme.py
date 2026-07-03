from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhoenixTheme:
    app_bg: str = "#111315"
    panel_bg: str = "#181B1F"
    content_bg: str = "#111315"
    header_bg: str = "#181B1F"
    card_bg: str = "#20242A"
    elevated_bg: str = "#272C33"
    border: str = "#343A43"

    text_primary: str = "#F2F4F8"
    text_secondary: str = "#D7DCE4"
    text_muted: str = "#AAB2C0"
    text_disabled: str = "#6B7280"
    text_on_accent: str = "#F2F4F8"

    accent: str = "#2F80ED"
    accent_dark: str = "#1E5FBF"
    accent_soft: str = "#D8E8FF"

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


PHOENIX_THEME = PhoenixTheme()
