"""
Snapdragon AI Studio

Native Menu Bar Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk


class MenuBar:
    """Native Tk menu bar for Snapdragon AI Studio.

    The menu owns no application logic. It only maps menu entries to callback
    names supplied by UIBuilder.
    """

    def __init__(self, master, callbacks=None):
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

    def _callback(self, name):
        callback = self.callbacks.get(name)

        if callable(callback):
            callback()

    def _create_file_menu(self):
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label="Bilder öffnen...",
            command=lambda: self._callback("open_images"),
        )
        menu.add_command(
            label="Ordner öffnen...",
            command=lambda: self._callback("open_folder"),
        )
        menu.add_separator()
        menu.add_command(
            label="Beenden",
            command=lambda: self._callback("exit"),
        )

        self.menu.add_cascade(label="File", menu=menu)

    def _create_studio_menu(self):
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label="Start",
            command=lambda: self._callback("start"),
        )
        menu.add_command(
            label="Stop",
            command=lambda: self._callback("stop"),
        )
        menu.add_separator()
        menu.add_command(
            label="Output öffnen",
            command=lambda: self._callback("open_output"),
        )
        menu.add_separator()
        menu.add_command(
            label="Preferences...",
            command=lambda: self._callback("preferences"),
        )
        menu.add_command(
            label="Appearance...",
            command=lambda: self._callback("appearance"),
        )
        menu.add_command(
            label="Updates...",
            command=lambda: self._callback("updates"),
        )

        self.menu.add_cascade(label="Studio", menu=menu)

    def _create_view_menu(self):
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label="Queue aktualisieren",
            command=lambda: self._callback("refresh_queue"),
        )
        menu.add_separator()
        menu.add_command(
            label="Dark Theme",
            command=lambda: self._callback("dark_theme"),
        )
        menu.add_command(
            label="Light Theme",
            command=lambda: self._callback("light_theme"),
        )
        menu.add_separator()
        menu.add_command(
            label="Reset Layout",
            command=lambda: self._callback("reset_layout"),
        )

        self.menu.add_cascade(label="View", menu=menu)

    def _create_plugins_menu(self):
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label="Plugin Manager...",
            command=lambda: self._callback("plugin_manager"),
        )
        menu.add_separator()
        menu.add_command(
            label="Reload Plugins",
            command=lambda: self._callback("reload_plugins"),
        )

        self.menu.add_cascade(label="Plugins", menu=menu)

    def _create_tools_menu(self):
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label="Batch Manager",
            command=lambda: self._callback("batch_manager"),
        )
        menu.add_command(
            label="Scheduler",
            command=lambda: self._callback("scheduler"),
        )
        menu.add_command(
            label="NPU Manager",
            command=lambda: self._callback("npu_manager"),
        )
        menu.add_command(
            label="Workflow Builder",
            command=lambda: self._callback("workflow_builder"),
        )

        self.menu.add_cascade(label="Tools", menu=menu)

    def _create_help_menu(self):
        menu = tk.Menu(self.menu, tearoff=False)

        menu.add_command(
            label="Documentation",
            command=lambda: self._callback("documentation"),
        )
        menu.add_command(
            label="GitHub",
            command=lambda: self._callback("github"),
        )
        menu.add_separator()
        menu.add_command(
            label="About Snapdragon AI Studio...",
            command=lambda: self._callback("about"),
        )

        self.menu.add_cascade(label="Help", menu=menu)
