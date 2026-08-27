"""
HK NPU STUDIO

AI Library Page

Created by Holger Kreuzhofen
Phoenix Architecture
"""

import tkinter as tk

from engine.plugin_manager import PluginManager


BG = "#101418"
PANEL = "#171d23"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"
GREEN = "#22c55e"
WARNING = "#f59e0b"


class LibraryPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)

        self.plugin_manager = PluginManager()
        self.plugins = self.plugin_manager.scan()

        self.build()

    def card(self, parent, plugin):
        box = tk.Frame(parent, bg=PANEL)
        box.pack(fill="x", padx=24, pady=10)

        tk.Label(
            box,
            text=f"🧩 {plugin.name}",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 4))

        tk.Label(
            box,
            text=(
                f"Version: {plugin.version}\n"
                f"Backend: {plugin.backend}\n"
                f"Autor: {plugin.author}\n"
                f"Skills: {', '.join(plugin.skills) if plugin.skills else 'Keine'}"
            ),
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 10),
            justify="left",
        ).pack(anchor="w", padx=18)

        tk.Label(
            box,
            text="🟢 Plugin erkannt",
            bg=PANEL,
            fg=GREEN,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=18, pady=(8, 16))

    def build(self):
        tk.Label(
            self,
            text="AI Library",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 24, "bold"),
        ).pack(anchor="w", padx=24, pady=(24, 6))

        tk.Label(
            self,
            text="Automatisch erkannte Plugins und Fähigkeiten.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 11),
        ).pack(anchor="w", padx=24, pady=(0, 18))

        if not self.plugins:
            tk.Label(
                self,
                text="Keine Plugins gefunden.",
                bg=BG,
                fg=WARNING,
                font=("Segoe UI", 12, "bold"),
            ).pack(anchor="w", padx=24, pady=20)
            return

        for plugin in self.plugins:
            self.card(self, plugin)