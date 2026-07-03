from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhoenixTheme:
    app_bg: str = "#0B1020"
    panel_bg: str = "#111827"
    content_bg: str = "#0F172A"
    header_bg: str = "#020617"
    card_bg: str = "#111827"
    border: str = "#1E293B"

    text_primary: str = "#F8FAFC"
    text_secondary: str = "#CBD5E1"
    text_muted: str = "#94A3B8"

    accent: str = "#2563EB"
    accent_dark: str = "#172554"
    accent_soft: str = "#DBEAFE"

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
