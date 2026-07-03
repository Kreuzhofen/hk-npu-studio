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
        "background": BrandManager.COLORS["COLOR_BACKGROUND"],
        "surface": BrandManager.COLORS["COLOR_SURFACE"],
        "card": BrandManager.COLORS["COLOR_CARD"],
        "elevated": BrandManager.COLORS["COLOR_ELEVATED"],
        "border": BrandManager.COLORS["COLOR_BORDER"],
        "text": BrandManager.COLORS["COLOR_TEXT"],
        "muted_text": BrandManager.COLORS["COLOR_TEXT_SECONDARY"],
        "accent": BrandManager.COLORS["COLOR_PRIMARY"],
        "success": BrandManager.COLORS["COLOR_PRIMARY"],
        "warning": BrandManager.COLORS["COLOR_TEXT_SECONDARY"],
        "error": BrandManager.COLORS["COLOR_TEXT_SECONDARY"],
        "info": BrandManager.COLORS["COLOR_PRIMARY"],
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
        return cls.COLORS.get(name, cls.COLORS["text"])

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
