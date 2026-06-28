"""
SnapdragonAI Studio

Plugin Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk


class PluginCard(tk.Frame):

    def __init__(self, master):
        super().__init__(master, bd=1, relief="groove", padx=10, pady=10)

        self._build_ui()

    def _build_ui(self):

        self.title_label = tk.Label(
            self,
            text="Plugin",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        self.title_label.pack(fill="x")

        self.name_label = tk.Label(
            self,
            text="Name: -",
            anchor="w",
        )
        self.name_label.pack(fill="x", pady=(5, 0))

        self.backend_label = tk.Label(
            self,
            text="Backend: -",
            anchor="w",
        )
        self.backend_label.pack(fill="x")

        self.status_label = tk.Label(
            self,
            text="Status: -",
            anchor="w",
        )
        self.status_label.pack(fill="x")

    def set_plugin(self, name, backend, status):
        self.name_label.configure(text=f"Name: {name}")
        self.backend_label.configure(text=f"Backend: {backend}")
        self.status_label.configure(text=f"Status: {status}")