"""
Snapdragon AI Studio

Branding

Created by Holger Kreuzhofen
"""


class Branding:
    """
    Zentrale Branding-Informationen.
    """

    APP_NAME = "Snapdragon AI Studio"
    APP_VERSION = "2.0.0-dev68"

    ENGINE_NAME = "Phoenix Engine"
    ENGINE_VERSION = "1.0"

    AUTHOR = "Holger Kreuzhofen"
    COPYRIGHT = "© 2026 Holger Kreuzhofen"

    COMPANY = ""
    WEBSITE = ""
    GITHUB = ""

    WINDOW_TITLE = APP_NAME
    WINDOW_TITLE_WITH_VERSION = f"{APP_NAME} {APP_VERSION}"

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