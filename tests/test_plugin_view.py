import tkinter as tk
import json
from pathlib import Path
from unittest.mock import MagicMock

from engine.theme_manager import ThemeManager
from widgets.phoenix.theme import PHOENIX_THEME, update_phoenix_theme
from widgets.phoenix.views.plugin_view import PhoenixPluginView


def test_plugin_install_action_stays_outside_scrollable_content() -> None:
    root = tk.Tk()
    try:
        root.geometry("480x420")
        controller = MagicMock()
        controller.get_plugins.return_value = []
        view = PhoenixPluginView(root, controller=controller)
        view.pack(fill="both", expand=True)
        root.update_idletasks()

        assert view.install_btn.winfo_manager() == "grid"
        assert view.install_frame.master is view.content_slot
        assert view.middle_frame.master is view.content_slot
        assert view.canvas.master is view.middle_frame
        assert view.install_btn.command == view._on_install_plugin
        assert view.install_btn.normal_bg == PHOENIX_THEME.accent
        assert view.browse_btn.button_type == "neutral"
        assert view.browse_btn.icon_name == "folder"
        assert view.browse_btn.icon_color == PHOENIX_THEME.warning
        assert view.install_btn.icon_name == "plugins"
        assert view.install_btn.icon_color == PHOENIX_THEME.text_on_accent
        assert view.install_path_entry.cget("readonlybackground") == PHOENIX_THEME.elevated_bg
        assert view.install_path_entry.cget("highlightbackground") == PHOENIX_THEME.border
        assert view.middle_frame.winfo_y() + view.middle_frame.winfo_height() <= view.install_frame.winfo_y()
        assert view.install_btn.winfo_y() + view.install_btn.winfo_height() <= (
            view.install_frame.winfo_y() + view.install_frame.winfo_height()
        )
        assert view.install_frame.winfo_y() + view.install_frame.winfo_height() <= view.winfo_height()
        assert view.canvas.cget("scrollregion")

        root.geometry("1000x420")
        root.update()
        assert view._install_actions_stacked is False

        root.geometry("360x520")
        root.update()
        assert view._install_actions_stacked is True
        assert view.install_btn.winfo_manager() == "grid"
        assert view.canvas.cget("scrollregion")
        assert view.browse_btn.winfo_y() + view.browse_btn.winfo_height() <= view.install_frame.winfo_height()
        assert view.install_btn.winfo_y() + view.install_btn.winfo_height() <= view.install_frame.winfo_height()
    finally:
        root.destroy()


def test_plugin_install_labels_are_complete_in_all_locales() -> None:
    expected = {
        "de_DE": ("Plugin installieren:", "Ordner wählen...", "Installieren"),
        "en_US": ("Install Plugin:", "Select folder...", "Install"),
        "es_ES": ("Instalar complemento:", "Seleccionar carpeta...", "Instalar"),
    }
    root = Path(__file__).resolve().parents[1]
    for locale, labels in expected.items():
        data = json.loads((root / "locales" / f"{locale}.json").read_text(encoding="utf-8"))
        assert (
            data["plugins_install_title"],
            data["plugins_choose_folder_btn"],
            data["plugins_install_btn"],
        ) == labels


def test_plugin_install_theme_tokens_rebuild_for_light_and_dark() -> None:
    root = tk.Tk()
    original_theme = ThemeManager.active_theme()
    try:
        for theme_name in ("dark", "light"):
            update_phoenix_theme(theme_name)
            controller = MagicMock()
            controller.get_plugins.return_value = []
            view = PhoenixPluginView(root, controller=controller)
            assert view.install_path_entry.cget("readonlybackground") == PHOENIX_THEME.elevated_bg
            assert view.install_path_entry.cget("highlightbackground") == PHOENIX_THEME.border
            assert view.browse_btn.icon_color == PHOENIX_THEME.warning
            assert view.install_btn.icon_color == PHOENIX_THEME.text_on_accent
            view.destroy()
    finally:
        update_phoenix_theme(original_theme)
        root.destroy()
