from dataclasses import dataclass
from pathlib import Path


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

    APP_NAME = "Snapdragon AI Studio"
    APP_VERSION = "2.0 Preview"

    ENGINE_NAME = "Phoenix Engine"
    ENGINE_VERSION = "1.0"

    AUTHOR = "Holger Kreuzhofen"
    COPYRIGHT = "© Holger Kreuzhofen"

    SLOGAN = "Phoenix Engine"
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
        "COLOR_BACKGROUND": "#0F1117",
        "COLOR_SURFACE": "#171B24",
        "COLOR_PRIMARY": "#2F80ED",
        "COLOR_TEXT": "#F2F4F8",
        "COLOR_TEXT_SECONDARY": "#AAB2C0",
    }

    FONTS = {
        "FONT_TITLE": "Segoe UI",
        "FONT_BODY": "Segoe UI",
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

    def color(self, name: str) -> str:
        return self.COLORS.get(name, "#FFFFFF")

    def font(self, name: str) -> str:
        return self.FONTS.get(name, "Segoe UI")

    @classmethod
    def png(cls, size: int) -> Path:
        return cls.BRAND_ROOT / "png" / f"phoenix_{size}.png"
