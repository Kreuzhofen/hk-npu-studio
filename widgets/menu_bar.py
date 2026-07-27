"""
Snapdragon AI Studio

Native Menu Bar Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable


class MenuBar:
    """Native Tk menu bar for Snapdragon AI Studio.

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
            label="Output-Ordner öffnen",
            command=lambda: self._callback("open_output_dir"),
        )
        menu.add_command(
            label="Modell-Ordner öffnen",
            command=lambda: self._callback("open_models_dir"),
        )
        menu.add_separator()
        menu.add_command(
            label="Beenden",
            accelerator="Alt+F4",
            command=lambda: self._callback("exit"),
        )

        self.menu.add_cascade(label="File", menu=menu)

    def _create_studio_menu(self) -> None:
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label="VRAM / NPU Cache leeren",
            command=lambda: self._callback("clear_cache"),
        )
        menu.add_command(
            label="Hardware-Info",
            command=lambda: self._callback("hardware_info"),
        )

        self.menu.add_cascade(label="Studio", menu=menu)

    def _create_view_menu(self) -> None:
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label="Vollbild umschalten",
            accelerator="F11",
            command=lambda: self._callback("toggle_fullscreen"),
        )
        menu.add_command(
            label="Seitenleiste umschalten",
            command=lambda: self._callback("toggle_sidebar"),
        )

        self.menu.add_cascade(label="View", menu=menu)

    def _create_plugins_menu(self) -> None:
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label="Plugins verwalten",
            command=lambda: self._callback("manage_plugins"),
        )
        menu.add_command(
            label="Plugin-Ordner öffnen",
            command=lambda: self._callback("open_plugins_dir"),
        )

        self.menu.add_cascade(label="Plugins", menu=menu)

    def _create_tools_menu(self) -> None:
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label="Log-Datei anzeigen",
            command=lambda: self._callback("show_log"),
        )

        self.menu.add_cascade(label="Tools", menu=menu)

    def _create_help_menu(self) -> None:
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label="Über Snapdragon AI Studio",
            command=lambda: self._callback("about"),
        )

        self.menu.add_cascade(label="Help", menu=menu)
