"""
Snapdragon AI Studio

Plugin Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk

from app.i18n import tr
from app.runtime_localization import localize_runtime_text
from resources.theme import Theme


class PluginCard(tk.Frame):

    def __init__(self, master):
        super().__init__(
            master,
            bd=1,
            relief="solid",
            padx=Theme.spacing("card_pad"),
            pady=Theme.spacing("card_pad"),
            bg=Theme.color("card"),
            highlightbackground=Theme.color("border"),
        )

        self._build_ui()

    def _build_ui(self):

        self.title_label = tk.Label(
            self,
            text=tr("plugin", "Plugin"),
            font=Theme.font("card_title"),
            anchor="w",
            bg=Theme.color("card"),
            fg=Theme.color("text"),
        )
        self.title_label.pack(fill="x")

        self.name_label = tk.Label(
            self,
            text=f"{tr('name', 'Name')}: -",
            anchor="w",
            font=Theme.font("body"),
            bg=Theme.color("card"),
            fg=Theme.color("text"),
        )
        self.name_label.pack(fill="x", pady=(5, 0))

        self.backend_label = tk.Label(
            self,
            text=f"{tr('backend', 'Backend')}: -",
            anchor="w",
            font=Theme.font("body"),
            bg=Theme.color("card"),
            fg=Theme.color("text"),
        )
        self.backend_label.pack(fill="x")

        self.status_label = tk.Label(
            self,
            text=f"{tr('status', 'Status')}: -",
            anchor="w",
            font=Theme.font("body"),
            bg=Theme.color("card"),
            fg=Theme.color("muted_text"),
        )
        self.status_label.pack(fill="x")

    def set_plugin(self, name, backend, status):
        localized_status = localize_runtime_text(status)
        self.name_label.configure(text=f"{tr('name', 'Name')}: {name}")
        self.backend_label.configure(text=f"{tr('backend', 'Backend')}: {backend}")
        self.status_label.configure(text=f"{tr('status', 'Status')}: {localized_status}")

        status_lower = str(status).lower()

        if "fehler" in status_lower:
            self.status_label.configure(fg=Theme.color("error"))
        elif "läuft" in status_lower or "batch" in status_lower:
            self.status_label.configure(fg=Theme.color("info"))
        elif "fertig" in status_lower:
            self.status_label.configure(fg=Theme.color("success"))
        elif "abbruch" in status_lower:
            self.status_label.configure(fg=Theme.color("warning"))
        else:
            self.status_label.configure(fg=Theme.color("muted_text"))
