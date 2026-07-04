"""
Snapdragon AI Studio

Central icon management for the UI.

Created by Holger Kreuzhofen
Phoenix UI Resources
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk

from engine.theme_manager import ThemeManager


@dataclass(frozen=True)
class IconAsset:
    """Resolved icon description used by widgets without knowing file names."""

    name: str
    symbol: str
    size_name: str
    size_px: int
    image: tk.PhotoImage | None = None
    path: Path | None = None

    def label(self, text: str) -> str:
        if not self.symbol:
            return text
        return f"{self.symbol}  {text}"


class IconManager:
    """
    Central logical icon registry for Snapdragon AI Studio.

    UI code should request icons by logical names such as "folder" or
    "refresh". Real Lucide files can later be added under
    resources/icons/lucide/<theme>/<name>.png without changing the views.
    Until then, consistent text-symbol fallbacks keep the interface usable.
    """

    BASE_DIR = Path(__file__).resolve().parent
    ICON_DIR = BASE_DIR / "icons"
    LUCIDE_DIR = ICON_DIR / "lucide"

    SIZE_MAP = {
        "small": 16,
        "medium": 20,
        "large": 24,
        "xlarge": 32,
        "toolbar": 18,
    }

    ICON_NAMES = (
        "folder",
        "refresh",
        "search",
        "filter",
        "sort",
        "grid",
        "image",
        "gallery",
        "settings",
        "plugins",
        "home",
        "start",
        "stop",
        "output",
        "compare",
        "batch",
        "info",
        "warning",
        "error",
    )

    FALLBACK_SYMBOLS = {
        "folder": "▣",
        "refresh": "↻",
        "search": "⌕",
        "filter": "⧉",
        "sort": "⇅",
        "grid": "▦",
        "image": "▧",
        "gallery": "▧",
        "settings": "⚙",
        "plugins": "◆",
        "home": "●",
        "start": "▶",
        "stop": "■",
        "output": "↗",
        "compare": "◫",
        "batch": "≡",
        "info": "i",
        "warning": "!",
        "error": "!",
    }

    LEGACY_FILES = {
        "folder": "folder.png",
        "image": "images.png",
        "gallery": "images.png",
        "start": "play.png",
        "stop": "stop.png",
        "output": "output.png",
        "plugins": "plugin.png",
        "settings": "settings.png",
        "phoenix": "phoenix.png",
    }

    LEGACY_ALIASES = {
        "images": "image",
        "play": "start",
        "plugin": "plugins",
    }

    _image_cache: dict[tuple[str, str, int], tk.PhotoImage] = {}
    _placeholder_cache: dict[int, tk.PhotoImage] = {}

    @classmethod
    def ensure_resource_structure(cls) -> None:
        cls.ICON_DIR.mkdir(parents=True, exist_ok=True)
        (cls.LUCIDE_DIR / "dark").mkdir(parents=True, exist_ok=True)
        (cls.LUCIDE_DIR / "light").mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_icon(cls, name: str, size: str = "medium") -> IconAsset:
        cls.ensure_resource_structure()
        logical_name = cls._normalize_name(name)
        size_px = cls.size_px(size)
        path = cls._resolve_icon_path(logical_name)
        image = cls._load_image(logical_name, path, size_px) if path else None
        symbol = cls.get_symbol(logical_name)

        return IconAsset(
            name=logical_name,
            symbol=symbol,
            size_name=size,
            size_px=size_px,
            image=image,
            path=path,
        )

    @classmethod
    def get_symbol(cls, name: str) -> str:
        logical_name = cls._normalize_name(name)
        return cls.FALLBACK_SYMBOLS.get(logical_name, cls.FALLBACK_SYMBOLS["info"])

    @classmethod
    def get_label(cls, name: str, text: str, size: str = "toolbar") -> str:
        return cls.get_icon(name, size=size).label(text)

    @classmethod
    def get_photo_image(cls, name: str, size: str = "medium") -> tk.PhotoImage:
        icon = cls.get_icon(name, size=size)
        if icon.image is not None:
            return icon.image
        return cls._placeholder(icon.size_px)

    @classmethod
    def size_px(cls, size: str) -> int:
        return cls.SIZE_MAP.get(size, cls.SIZE_MAP["medium"])

    @classmethod
    def clear_cache(cls) -> None:
        cls._image_cache.clear()
        cls._placeholder_cache.clear()

    @classmethod
    def _normalize_name(cls, name: str | None) -> str:
        if not name:
            return "info"
        normalized = str(name).strip().lower().replace("-", "_")
        normalized = cls.LEGACY_ALIASES.get(normalized, normalized)
        if normalized in cls.ICON_NAMES or normalized == "phoenix":
            return normalized
        return "info"

    @classmethod
    def _active_variant(cls) -> str:
        try:
            if ThemeManager.active_theme() == ThemeManager.PROFESSIONAL_LIGHT:
                return "light"
        except Exception:
            return "dark"
        return "dark"

    @classmethod
    def _resolve_icon_path(cls, logical_name: str) -> Path | None:
        variant = cls._active_variant()
        candidates = (
            cls.LUCIDE_DIR / variant / f"{logical_name}.png",
            cls.LUCIDE_DIR / f"{logical_name}.png",
            cls.ICON_DIR / cls.LEGACY_FILES.get(logical_name, f"{logical_name}.png"),
            cls.ICON_DIR / f"{logical_name}.png",
        )
        for path in candidates:
            if path.exists():
                return path
        return None

    @classmethod
    def _load_image(cls, logical_name: str, path: Path, size_px: int) -> tk.PhotoImage | None:
        variant = cls._active_variant()
        cache_key = (variant, logical_name, size_px)
        if cache_key in cls._image_cache:
            return cls._image_cache[cache_key]

        try:
            image = tk.PhotoImage(file=str(path))
        except Exception:
            return None

        cls._image_cache[cache_key] = image
        return image

    @classmethod
    def _placeholder(cls, size_px: int) -> tk.PhotoImage:
        if size_px not in cls._placeholder_cache:
            cls._placeholder_cache[size_px] = tk.PhotoImage(width=size_px, height=size_px)
        return cls._placeholder_cache[size_px]


class Icons:
    """Backward-compatible adapter for older widgets using resources.icons.Icons."""

    @classmethod
    def ensure_icon_dir(cls) -> None:
        IconManager.ensure_resource_structure()

    @classmethod
    def get(cls, name: str, size: str = "medium") -> tk.PhotoImage:
        return IconManager.get_photo_image(name, size=size)

    @classmethod
    def clear_cache(cls) -> None:
        IconManager.clear_cache()


