"""
Snapdragon AI Studio

Icon Manager

Created by Holger Kreuzhofen
Phoenix UI Resources
"""

from pathlib import Path
import tkinter as tk


class Icons:
    """
    Zentraler Icon Manager.

    Diese Klasse lädt und cached Icons aus dem resources/icons Ordner.

    Aktuell ist das System vorbereitet. Wenn ein Icon noch nicht existiert,
    wird automatisch ein leeres Platzhalter-Bild erzeugt. Dadurch kann die GUI
    bereits mit Icons arbeiten, bevor echte PNG-Dateien vorhanden sind.
    """

    _cache = {}

    BASE_DIR = Path(__file__).resolve().parent
    ICON_DIR = BASE_DIR / "icons"

    DEFAULT_SIZE = (24, 24)

    ICON_FILES = {
        "images": "images.png",
        "folder": "folder.png",
        "play": "play.png",
        "stop": "stop.png",
        "output": "output.png",
        "plugin": "plugin.png",
        "settings": "settings.png",
        "phoenix": "phoenix.png",
    }

    @classmethod
    def ensure_icon_dir(cls):
        cls.ICON_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get(cls, name):
        """
        Lädt ein Icon anhand seines Namens.

        Beispiel:
            Icons.get("play")
            Icons.get("folder")
        """

        cls.ensure_icon_dir()

        if name in cls._cache:
            return cls._cache[name]

        filename = cls.ICON_FILES.get(name)

        if not filename:
            icon = cls._placeholder()
            cls._cache[name] = icon
            return icon

        path = cls.ICON_DIR / filename

        if not path.exists():
            icon = cls._placeholder()
            cls._cache[name] = icon
            return icon

        try:
            icon = tk.PhotoImage(file=str(path))
            cls._cache[name] = icon
            return icon

        except Exception:
            icon = cls._placeholder()
            cls._cache[name] = icon
            return icon

    @classmethod
    def _placeholder(cls):
        """
        Erzeugt ein transparentes Platzhalter-Icon.

        Tkinter PhotoImage unterstützt Transparenz,
        wenn keine Pixel gesetzt werden.
        """

        width, height = cls.DEFAULT_SIZE
        return tk.PhotoImage(width=width, height=height)

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()