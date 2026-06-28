"""
SnapdragonAI Studio

Plugin Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

from tkinter import ttk


class PluginCard(ttk.LabelFrame):
    """
    Zeigt Informationen über das aktuell aktive Plugin.
    """

    def __init__(self, master):
        super().__init__(master, text="Aktives Plugin")

        self.name_var = ttk.Label(self, text="Plugin: -")
        self.backend_var = ttk.Label(self, text="Backend: -")
        self.status_var = ttk.Label(self, text="Status: -")

        self.name_var.pack(anchor="w", padx=10, pady=(10, 4))
        self.backend_var.pack(anchor="w", padx=10, pady=4)
        self.status_var.pack(anchor="w", padx=10, pady=(4, 10))

    def set_plugin(self, name: str, backend: str, status: str):
        """
        Aktualisiert die Plugin-Anzeige.
        """

        self.name_var.configure(text=f"Plugin: {name}")
        self.backend_var.configure(text=f"Backend: {backend}")
        self.status_var.configure(text=f"Status: {status}")

    def clear(self):
        """
        Setzt die Anzeige zurück.
        """

        self.set_plugin("-", "-", "-")