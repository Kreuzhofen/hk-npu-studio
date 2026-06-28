"""
SnapdragonAI Studio

Theme Foundation

Created by Holger Kreuzhofen
Phoenix UI Theme
"""


class Theme:

    APP_NAME = "SnapdragonAI Studio"
    ENGINE_NAME = "Phoenix Engine 1.0"

    COLORS = {
        "background": "#F5F6F8",
        "card": "#FFFFFF",
        "border": "#D0D4DA",
        "text": "#202124",
        "muted_text": "#5F6368",
        "accent": "#C62828",
        "success": "#2E7D32",
        "warning": "#F9A825",
        "error": "#C62828",
        "info": "#1565C0",
    }

    FONTS = {
        "title": ("Segoe UI", 14, "bold"),
        "card_title": ("Segoe UI", 11, "bold"),
        "body": ("Segoe UI", 10),
        "small": ("Segoe UI", 9),
        "button": ("Segoe UI", 10),
    }

    SPACING = {
        "window_pad": 10,
        "card_pad": 10,
        "small": 4,
        "medium": 8,
        "large": 12,
    }

    @classmethod
    def color(cls, name):
        return cls.COLORS.get(name, "#000000")

    @classmethod
    def font(cls, name):
        return cls.FONTS.get(name, cls.FONTS["body"])

    @classmethod
    def spacing(cls, name):
        return cls.SPACING.get(name, 0)