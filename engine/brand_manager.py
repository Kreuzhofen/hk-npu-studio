from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from engine.theme_manager import ThemeManager
from engine.release_config import RELEASE


@dataclass(frozen=True)
class BrandState:
    """Runtime branding state."""

    app_name: str
    app_version: str
    engine_name: str
    engine_version: str
    window_title: str


class BrandManager:
    """Central branding and asset manager for Snapdragon AI Studio."""

    APP_NAME = RELEASE.app_name
    APP_VERSION = RELEASE.display_version

    ENGINE_NAME = "Phoenix Engine"
    ENGINE_VERSION = "1.0"

    AUTHOR = RELEASE.publisher
    COPYRIGHT = "© 2026 Holger Kreuzhofen\nAll rights reserved."

    SLOGAN = "Phoenix Engine"
    AI_ASSISTANCE = "Developed with AI assistance using OpenAI"
    ABOUT_DESCRIPTION = (
        "Professional local AI platform for image enhancement,\n"
        "AI workflows and Snapdragon NPU acceleration."
    )
    WINDOW_TITLE_WITH_VERSION = APP_NAME

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    BRAND_ROOT = PROJECT_ROOT / "assets" / "brand"

    MASTER_LOGO = BRAND_ROOT / "master" / "phoenix_master.svg"

    SVG_BLACK = BRAND_ROOT / "svg" / "phoenix_black.svg"
    SVG_WHITE = BRAND_ROOT / "svg" / "phoenix_white.svg"
    SVG_BLUE = BRAND_ROOT / "svg" / "phoenix_blue.svg"

    APP_ICON = BRAND_ROOT / "icons" / "app.ico"
    PHOENIX_ICON = BRAND_ROOT / "icons" / "phoenix.ico"

    HEADER_DARK = BRAND_ROOT / "header" / "phoenix_header_dark.png"
    HEADER_LIGHT = BRAND_ROOT / "header" / "phoenix_header_light.png"

    SPLASH = BRAND_ROOT / "splash" / "phoenix_splash.png"
    ABOUT_IMAGE = BRAND_ROOT / "about" / "phoenix_about.png"

    COLORS = {
        "COLOR_BACKGROUND": "#111315",
        "COLOR_SURFACE": "#181B1F",
        "COLOR_CARD": "#20242A",
        "COLOR_ELEVATED": "#272C33",
        "COLOR_BORDER": "#343A43",
        "COLOR_PRIMARY": "#2F80ED",
        "COLOR_TEXT": "#F2F4F8",
        "COLOR_TEXT_ON_ACCENT": "#F2F4F8",
        "COLOR_TEXT_SECONDARY": "#AAB2C0",
        "COLOR_DISABLED_TEXT": "#6B7280",
    }

    FONTS = {
        "FONT_TITLE": "Segoe UI",
        "FONT_BODY": "Segoe UI",
        "FONT_SMALL": "Segoe UI",
    }

    COLOR_ROLES = {
        "COLOR_BACKGROUND": "background",
        "COLOR_SURFACE": "surface",
        "COLOR_CARD": "card",
        "COLOR_ELEVATED": "elevated",
        "COLOR_BORDER": "border",
        "COLOR_PRIMARY": "accent",
        "COLOR_TEXT": "text",
        "COLOR_TEXT_ON_ACCENT": "text_on_accent",
        "COLOR_TEXT_SECONDARY": "text_secondary",
        "COLOR_DISABLED_TEXT": "text_disabled",
    }

    def __init__(self):
        self.state = BrandState(
            app_name=self.APP_NAME,
            app_version=self.APP_VERSION,
            engine_name=self.ENGINE_NAME,
            engine_version=self.ENGINE_VERSION,
            window_title=self.window_title(),
        )

    def initialize(self):
        return self

    def app_name(self) -> str:
        return self.APP_NAME

    def version(self) -> str:
        return self.APP_VERSION

    def app_version(self) -> str:
        return self.APP_VERSION

    def version_string(self) -> str:
        return f"Version {self.APP_VERSION}"

    def slogan(self) -> str:
        return self.SLOGAN

    def engine(self) -> str:
        return f"{self.ENGINE_NAME} {self.ENGINE_VERSION}"

    def engine_name(self) -> str:
        return self.ENGINE_NAME

    def engine_version(self) -> str:
        return self.ENGINE_VERSION

    def window_title(self) -> str:
        return self.APP_NAME

    def author(self) -> str:
        return self.AUTHOR

    def copyright(self) -> str:
        return self.COPYRIGHT

    def ai_assistance(self) -> str:
        return self.AI_ASSISTANCE

    def about_description(self) -> str:
        return self.ABOUT_DESCRIPTION

    def color(self, name: str) -> str:
        role = self.COLOR_ROLES.get(name)
        if role is not None:
            return ThemeManager.color(role)

        return self.COLORS.get(name, self.COLORS["COLOR_TEXT"])

    def font(self, name: str) -> str:
        return self.FONTS.get(name, "Segoe UI")

    def logo_image(self, size: int) -> Image.Image:
        image = Image.open(self.png(size)).convert("RGBA")

        if ThemeManager.active_theme() == ThemeManager.PROFESSIONAL_LIGHT:
            return self._create_light_logo_image(image)

        return image

    def _create_light_logo_image(self, image: Image.Image) -> Image.Image:
        silhouette_color = self._light_logo_color()
        detail_color = self._light_logo_detail_color()
        output = Image.new("RGBA", image.size, (0, 0, 0, 0))
        source_pixels = image.load()
        output_pixels = output.load()

        for y in range(image.height):
            for x in range(image.width):
                red, green, blue, alpha = source_pixels[x, y]
                if alpha == 0:
                    continue

                luminance = (red * 299 + green * 587 + blue * 114) / 1000
                color = detail_color if alpha > 32 and luminance < 96 else silhouette_color
                output_pixels[x, y] = (*color, alpha)

        return output

    def _light_logo_color(self) -> tuple[int, int, int]:
        return self._hex_to_rgb(ThemeManager.color("text"))

    def _light_logo_detail_color(self) -> tuple[int, int, int]:
        return self._hex_to_rgb(ThemeManager.color("header"))

    def _hex_to_rgb(self, value: str) -> tuple[int, int, int]:
        color = value.lstrip("#")
        return tuple(
            int(color[index : index + 2], 16)
            for index in (0, 2, 4)
        )

    @classmethod
    def png(cls, size: int) -> Path:
        return cls.BRAND_ROOT / "png" / f"phoenix_{size}.png"
