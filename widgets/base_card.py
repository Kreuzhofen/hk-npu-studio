"""
HK NPU STUDIO

Base Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

from tkinter import ttk


class BaseCard(ttk.LabelFrame):
    """
    Gemeinsame Basisklasse für alle Karten-Widgets
    im HK NPU STUDIO.
    """

    def __init__(self, master, title: str):
        super().__init__(master, text=title)

    def set_title(self, title: str):
        """
        Ändert den Titel der Karte.
        """

        self.configure(text=title)