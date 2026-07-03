"""
Snapdragon AI Studio

Theme Foundation

Created by Holger Kreuzhofen
Phoenix UI Theme
"""

from engine.brand_manager import BrandManager


class Theme:

    APP_NAME = BrandManager.APP_NAME
    ENGINE_NAME = BrandManager().engine()

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

    ICON_SIZES = {
        "small": 16,
        "medium": 24,
        "large": 32,
        "toolbar": 20,
    }

    BORDER_RADIUS = {
        "small": 4,
        "medium": 8,
        "large": 12,
    }

    ANIMATION = {
        "fast": 120,
        "normal": 200,
        "slow": 350,
    }

    DPI = {
        "icon_scale": 1.0,
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

    @classmethod
    def icon_size(cls, name):
        return cls.ICON_SIZES.get(name, cls.ICON_SIZES["medium"])

    @classmethod
    def radius(cls, name):
        return cls.BORDER_RADIUS.get(name, 0)

    @classmethod
    def animation(cls, name):
        return cls.ANIMATION.get(name, cls.ANIMATION["normal"])

    @classmethod
    def dpi(cls, name):
        return cls.DPI.get(name, 1.0)
