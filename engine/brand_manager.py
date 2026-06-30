from pathlib import Path

class BrandManager:
    """Central paths for Snapdragon AI Studio Brand Pack 1.0."""

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
    ABOUT = BRAND_ROOT / "about" / "phoenix_about.png"

    @classmethod
    def png(cls, size: int) -> Path:
        return cls.BRAND_ROOT / "png" / f"phoenix_{size}.png"
