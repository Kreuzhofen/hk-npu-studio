"""
Snapdragon AI Studio

Branding

Created by Holger Kreuzhofen
"""

from engine.release_config import RELEASE


class Branding:
    """
    Zentrale Branding-Informationen.
    """

    APP_NAME = RELEASE.app_name
    APP_VERSION = RELEASE.display_version

    ENGINE_NAME = "Phoenix Engine"
    ENGINE_VERSION = "1.0"

    AUTHOR = "Holger Kreuzhofen"
    COPYRIGHT = "© 2026 Holger Kreuzhofen\nAll rights reserved."

    COLOR_BACKGROUND = "#111315"
    COLOR_SURFACE = "#181B1F"
    COLOR_CARD = "#20242A"
    COLOR_ELEVATED = "#272C33"
    COLOR_BORDER = "#343A43"
    COLOR_ACCENT = "#2F80ED"
    COLOR_TEXT = "#F2F4F8"
    COLOR_MUTED_TEXT = "#AAB2C0"

    COMPANY = ""
    WEBSITE = ""
    GITHUB = ""

    WINDOW_TITLE = APP_NAME
    WINDOW_TITLE_WITH_VERSION = APP_NAME

    ABOUT = (
        f"{APP_NAME}\n"
        f"{ENGINE_NAME} {ENGINE_VERSION}\n\n"
        f"Created by {AUTHOR}"
    )

    SPLASH_TITLE = APP_NAME
    SPLASH_SUBTITLE = ENGINE_NAME

    READY = "Ready"
    LOADING = "Loading..."
    RUNNING = "Running..."
    STOPPED = "Stopped"
