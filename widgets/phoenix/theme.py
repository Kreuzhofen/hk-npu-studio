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


PHOENIX_THEME = PhoenixTheme()