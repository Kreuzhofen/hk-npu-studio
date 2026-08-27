"""
HK NPU STUDIO

Native Menu Bar Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from app.i18n import tr

class MenuBar:
    """Native Tk menu bar for HK NPU STUDIO.

    The menu maps menu entries to callback names supplied by UIBuilder
    and binds hotkeys for accessibility.
    """

    def __init__(self, master: tk.Misc, callbacks: dict[str, Callable[[], None]] | None = None) -> None:
        self.master = master
        self.callbacks = callbacks or {}

        self.menu = tk.Menu(master)
        master.config(menu=self.menu)

        self._create_file_menu()
        self._create_studio_menu()
        self._create_view_menu()
        self._create_plugins_menu()
        self._create_tools_menu()
        self._create_help_menu()

        # Bind hotkeys to master window
        self.master.bind("<F11>", self._on_f11)
        self.master.bind("<Alt-F4>", self._on_alt_f4)
        self.master.bind("<F1>", self._on_f1)

    def _callback(self, name: str) -> None:
        callback = self.callbacks.get(name)
        if callable(callback):
            callback()

    def _on_f11(self, event: tk.Event | None = None) -> str:
        self._callback("toggle_fullscreen")
        return "break"

    def _on_alt_f4(self, event: tk.Event | None = None) -> str:
        self._callback("exit")
        return "break"

    def _create_file_menu(self) -> None:
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label=tr("menu_open_output", "Output-Ordner öffnen"),
            command=lambda: self._callback("open_output_dir"),
        )
        menu.add_command(
            label=tr("menu_open_models", "Modell-Ordner öffnen"),
            command=lambda: self._callback("open_models_dir"),
        )
        menu.add_separator()
        menu.add_command(
            label=tr("menu_exit", "Beenden"),
            accelerator="Alt+F4",
            command=lambda: self._callback("exit"),
        )

        self.menu.add_cascade(label=tr("menu_file", "Datei"), menu=menu)

    def _create_studio_menu(self) -> None:
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label=tr("menu_clear_cache", "VRAM-/NPU-Cache leeren"),
            command=lambda: self._callback("clear_cache"),
        )
        menu.add_command(
            label=tr("menu_hardware_info", "Hardware-Info"),
            command=lambda: self._callback("hardware_info"),
        )

        self.menu.add_cascade(label=tr("studio", "Studio"), menu=menu)

    def _create_view_menu(self) -> None:
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label=tr("menu_toggle_fullscreen", "Vollbild umschalten"),
            accelerator="F11",
            command=lambda: self._callback("toggle_fullscreen"),
        )
        menu.add_command(
            label=tr("menu_toggle_sidebar", "Seitenleiste umschalten"),
            command=lambda: self._callback("toggle_sidebar"),
        )

        self.menu.add_cascade(label=tr("menu_view", "Ansicht"), menu=menu)

    def _create_plugins_menu(self) -> None:
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label=tr("menu_manage_plugins", "Plugins verwalten"),
            command=lambda: self._callback("manage_plugins"),
        )
        menu.add_command(
            label=tr("menu_open_plugins", "Plugin-Ordner öffnen"),
            command=lambda: self._callback("open_plugins_dir"),
        )

        self.menu.add_cascade(label=tr("nav_plugins", "Plugins"), menu=menu)

    def _create_tools_menu(self) -> None:
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label=tr("menu_show_log", "Log-Datei anzeigen"),
            command=lambda: self._callback("show_log"),
        )

        self.menu.add_cascade(label=tr("tools", "Werkzeuge"), menu=menu)

    def _on_f1(self, event: tk.Event | None = None) -> str:
        self._show_help()
        return "break"

    def _show_help(self) -> None:
        from dialogs.help_dialog import HelpDialog
        brand = getattr(self.master, "brand", None)
        HelpDialog(self.master, brand)

    def _create_help_menu(self) -> None:
        from app.i18n import get_current_language
        menu = tk.Menu(self.menu, tearoff=False)

        lang = get_current_language()
        if lang == "de_DE":
            manual_label = tr("menu_manual_key" + "", "Handbuch")
        elif lang == "es_ES":
            manual_label = tr("menu_manual_key" + "", "Manual de usuario")
        else:
            manual_label = tr("menu_manual_key" + "", "User Manual")

        menu.add_command(
            label=manual_label,
            accelerator="F1",
            command=self._show_help,
        )

        menu.add_command(
            label=tr("menu_about", "Über HK NPU STUDIO"),
            command=lambda: self._callback("about"),
        )

        self.menu.add_cascade(label=tr("menu_help", "Hilfe"), menu=menu)
