from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("i18n")

_current_language = "de_DE"
_translations: dict[str, dict[str, str]] = {}
LOCALES_DIR = Path(__file__).parent.parent / "locales"

# Try loading language from preferences on module load (skip under test environment)
try:
    import sys
    if "unittest" not in sys.modules:
        _pref_path = Path(r"C:\SnapdragonAI\data\preferences.json")
        if _pref_path.exists():
            with open(_pref_path, "r", encoding="utf-8") as _f:
                _data = json.load(_f)
                _lang_val = _data.get("language", "Deutsch")
                _current_language = "en_US" if _lang_val == "English" else "de_DE"
except Exception:
    pass


def load_translations(lang_code: str) -> dict[str, str]:
    locale_file = LOCALES_DIR / f"{lang_code}.json"
    if not locale_file.is_file():
        logger.warning(f"Locale file for '{lang_code}' not found under {locale_file}")
        return {}
    try:
        with open(locale_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
    except Exception as e:
        logger.error(f"Failed to load translations for '{lang_code}': {e}")
    return {}


def set_language(lang_code: str) -> None:
    global _current_language
    _current_language = lang_code
    if lang_code not in _translations:
        _translations[lang_code] = load_translations(lang_code)


def get_current_language() -> str:
    return _current_language


def tr(key: str, default: str | None = None, **kwargs: Any) -> str:
    if _current_language not in _translations:
        set_language(_current_language)
    
    lang_translations = _translations.get(_current_language, {})
    val = lang_translations.get(key, default)
    if val is None:
        val = key
        
    if kwargs:
        try:
            val = val.format(**kwargs)
        except Exception as e:
            logger.error(f"i18n format error for key '{key}': {e}")
            
    return val


def get_available_languages() -> list[str]:
    if not LOCALES_DIR.is_dir():
        return ["de_DE", "en_US"]
    langs = []
    for p in LOCALES_DIR.glob("*.json"):
        langs.append(p.stem)
    return sorted(langs) if langs else ["de_DE", "en_US"]
