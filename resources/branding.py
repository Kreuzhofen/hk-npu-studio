"""
SnapdragonAI Studio

Branding

Created by Holger Kreuzhofen
"""


class Branding:
    """
    Zentrale Branding-Informationen.

    Diese Datei enthält sämtliche Informationen, die später
    in GUI, Splash Screen, About-Dialog, Installer und Logs
    verwendet werden.
    """

    # --------------------------------------------------
    # Produkt
    # --------------------------------------------------

    APP_NAME = "SnapdragonAI Studio"

    APP_VERSION = "2.0"

    ENGINE_NAME = "Phoenix Engine"

    ENGINE_VERSION = "1.0"

    # --------------------------------------------------
    # Autor
    # --------------------------------------------------

    AUTHOR = "Holger Kreuzhofen"

    COPYRIGHT = "© 2026 Holger Kreuzhofen"

    # --------------------------------------------------
    # Projekt
    # --------------------------------------------------

    COMPANY = ""

    WEBSITE = ""

    GITHUB = ""

    # --------------------------------------------------
    # Fenster
    # --------------------------------------------------

    WINDOW_TITLE = (
        f"{APP_NAME}"
    )

    WINDOW_TITLE_WITH_VERSION = (
        f"{APP_NAME} {APP_VERSION}"
    )

    # --------------------------------------------------
    # About
    # --------------------------------------------------

    ABOUT = (
        f"{APP_NAME}\n"
        f"{ENGINE_NAME} {ENGINE_VERSION}\n\n"
        f"Created by {AUTHOR}"
    )

    # --------------------------------------------------
    # Splash
    # --------------------------------------------------

    SPLASH_TITLE = APP_NAME

    SPLASH_SUBTITLE = ENGINE_NAME

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    READY = "Ready"

    LOADING = "Loading..."

    RUNNING = "Running..."

    STOPPED = "Stopped"