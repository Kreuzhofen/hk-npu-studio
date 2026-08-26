from __future__ import annotations

import json
import re
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

import pytest

from app.i18n import set_language
from widgets.phoenix.theme import update_phoenix_theme
from widgets.phoenix.sidebar import PhoenixSidebar
from widgets.phoenix.workspace import PhoenixWorkspace
from widgets.phoenix.views.model_manager_view import PhoenixModelManagerView
from widgets.menu_bar import MenuBar


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GERMAN_UI = re.compile(
    r"\b(?:Modell|Generierung|Installiert|Beschreibung|Verfügbar|Nicht)\b",
    re.IGNORECASE,
)


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


def test_sidebar_visual_contract_in_all_languages(tk_root):
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

    try:
        for theme_name in ("dark", "light"):
            update_phoenix_theme(theme_name)
            for scaling in (1.0, 1.25, 1.5, 1.75):
                tk_root.tk.call("tk", "scaling", scaling)
                for locale, labels in expected_labels.items():
                    set_language(locale)
                    sidebar = PhoenixSidebar(tk_root)
                    tk_root.update_idletasks()

                    assert PhoenixSidebar.BUTTON_HEIGHT == 46
                    assert PhoenixSidebar.BUTTON_FONT[1] == 11
                    assert PhoenixSidebar.ICON_COLORS == expected_colors
                    assert tuple(
                        sidebar._buttons[name].text
                        for name in ("home", "prompt", "models")
                    ) == labels
                    assert sidebar.brand_label.cget("text") == "HK NPU STUDIO"
                    assert (
                        sidebar.brand_credit_label.cget("text")
                        == "Featuring Phoenix Boost"
                    )

                    title_font = tkfont.Font(
                        root=tk_root,
                        font=sidebar.brand_label.cget("font"),
                    )
                    credit_font = tkfont.Font(
                        root=tk_root,
                        font=sidebar.brand_credit_label.cget("font"),
                    )
                    assert credit_font.measure("Featuring Phoenix Boost") <= (
                        title_font.measure("HK NPU STUDIO")
                    )
                    assert sidebar.brand_label.cget("anchor") == "w"
                    assert sidebar.brand_credit_label.cget("anchor") == "w"
                    assert sidebar.brand_label.pack_info()["padx"] == (
                        sidebar.brand_credit_label.pack_info()["padx"]
                    )

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


def _visible_widget_texts(widget: tk.Misc) -> list[str]:
    texts: list[str] = []
    try:
        value = widget.cget("text")
        if isinstance(value, str) and value.strip():
            texts.append(value.strip())
    except (AttributeError, tk.TclError):
        value = getattr(widget, "text", "")
        if isinstance(value, str) and value.strip():
            texts.append(value.strip())
    for child in widget.winfo_children():
        texts.extend(_visible_widget_texts(child))
    return texts


def test_all_phoenix_pages_are_language_pure_at_runtime(tk_root):
    foreign_markers = {
        "de_DE": re.compile(
            r"\b(?:Settings|Generate|Available|Installed|Download Ready|No recent|Properties)\b",
            re.IGNORECASE,
        ),
        "en_US": re.compile(
            r"\b(?:Einstellungen|Generierung|Verfügbar|Installiert|Beschreibung|Löschen|Abbrechen)\b",
            re.IGNORECASE,
        ),
        "es_ES": re.compile(
            r"\b(?:Einstellungen|Generierung|Verfügbar|Installiert|Beschreibung|"
            r"Settings|Generate|Available|Installed|Download Ready|No recent|Properties)\b",
            re.IGNORECASE,
        ),
    }

    try:
        for locale, marker in foreign_markers.items():
            set_language(locale)
            workspace = PhoenixWorkspace(tk_root)
            workspace.pack(fill="both", expand=True)
            for view_name in workspace._view_factories:
                workspace.show_view(view_name)
                tk_root.update_idletasks()
                view = workspace._views[view_name]
                assert "could not be loaded" not in " ".join(_visible_widget_texts(view))

            visible_texts = _visible_widget_texts(workspace)
            mixed = [
                text
                for text in visible_texts
                if marker.search(re.sub(r"https?://\S+|huggingface\.co/\S+", "", text))
            ]
            assert mixed == []
            workspace.destroy()
    finally:
        set_language("de_DE")


def _menu_labels(menu: tk.Menu) -> list[str]:
    labels: list[str] = []
    end = menu.index("end")
    if end is None:
        return labels
    for index in range(end + 1):
        if menu.type(index) in {"separator", "tearoff"}:
            continue
        label = menu.entrycget(index, "label")
        if label:
            labels.append(label)
        submenu_name = (
            menu.entrycget(index, "menu")
            if menu.type(index) == "cascade"
            else ""
        )
        if submenu_name:
            labels.extend(_menu_labels(menu.nametowidget(submenu_name)))
    return labels


def test_main_menu_and_installer_cover_all_supported_languages(tk_root):
    try:
        expected_file_menu = {
            "de_DE": "Datei",
            "en_US": "File",
            "es_ES": "Archivo",
        }
        for locale, expected in expected_file_menu.items():
            set_language(locale)
            menu_bar = MenuBar(tk_root)
            labels = _menu_labels(menu_bar.menu)
            assert labels[0] == expected
            assert len(labels) >= 15
            menu_bar.menu.destroy()
    finally:
        set_language("de_DE")

    installer = (
        PROJECT_ROOT / "installer" / "snapdragon_ai_studio.iss"
    ).read_text(encoding="utf-8")
    for language in ("english", "german", "spanish"):
        assert f'Name: "{language}"' in installer
