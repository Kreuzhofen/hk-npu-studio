from __future__ import annotations

import json
import re
import tkinter as tk
from pathlib import Path

from app.i18n import set_language
from widgets.phoenix.theme import update_phoenix_theme
from widgets.phoenix.sidebar import PhoenixSidebar
from widgets.phoenix.views.model_manager_view import PhoenixModelManagerView


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GERMAN_UI = re.compile(
    r"\b(?:Modell|Generierung|Installiert|Beschreibung|Verfügbar|Nicht)\b",
    re.IGNORECASE,
)


def test_sidebar_visual_contract_in_all_languages():
    expected_labels = {
        "de_DE": ("Startseite", "KI-Generierung", "Modell-Manager"),
        "en_US": ("Home", "AI Generate", "AI Model Manager"),
        "es_ES": ("Inicio", "Generación con IA", "Gestor de modelos"),
    }
    expected_colors = {
        "home": "#3253DC",
        "prompt": "#a78bfa",
        "models": "#34d399",
        "gallery": "#fbbf24",
        "compare": "#2dd4bf",
        "plugins": "#94a3b8",
        "settings": "#f87171",
    }

    root = tk.Tk()
    root.withdraw()
    try:
        for theme_name in ("dark", "light"):
            update_phoenix_theme(theme_name)
            for locale, labels in expected_labels.items():
                set_language(locale)
                sidebar = PhoenixSidebar(root)
                root.update_idletasks()

                assert PhoenixSidebar.BUTTON_HEIGHT == 46
                assert PhoenixSidebar.BUTTON_FONT[1] == 11
                assert PhoenixSidebar.ICON_COLORS == expected_colors
                assert tuple(
                    sidebar._buttons[name].text for name in ("home", "prompt", "models")
                ) == labels

                expected_theme_colors = (
                    PhoenixSidebar.LIGHT_ICON_COLORS
                    if theme_name == "light"
                    else expected_colors
                )
                for name, button in sidebar._buttons.items():
                    sidebar.set_active(name)
                    assert button.button_type == "nav_active"
                    assert button.icon_color == expected_theme_colors[name]
                    assert button.normal_fg == expected_theme_colors[name]
                sidebar.destroy()
    finally:
        root.destroy()
        set_language("de_DE")
        update_phoenix_theme("dark")


def test_model_descriptions_are_localized_for_every_catalog_model():
    definitions = []
    for path in sorted((PROJECT_ROOT / "resources" / "models").glob("*.json")):
        definitions.append(json.loads(path.read_text(encoding="utf-8")))

    localized: dict[str, dict[str, str]] = {}
    try:
        for locale in ("de_DE", "en_US", "es_ES"):
            set_language(locale)
            localized[locale] = {
                model["id"]: PhoenixModelManagerView._localized_description(model)
                for model in definitions
            }
    finally:
        set_language("de_DE")

    assert set(localized["de_DE"]) == set(localized["en_US"]) == set(localized["es_ES"])
    for model_id in localized["de_DE"]:
        assert localized["de_DE"][model_id]
        assert localized["en_US"][model_id]
        assert localized["es_ES"][model_id]
        assert not GERMAN_UI.search(localized["en_US"][model_id])
        assert not GERMAN_UI.search(localized["es_ES"][model_id])
