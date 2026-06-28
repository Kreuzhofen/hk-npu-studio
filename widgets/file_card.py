"""
SnapdragonAI Studio

File Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk
from tkinter import ttk

from widgets.base_card import BaseCard


class FileCard(BaseCard):
    """
    Widget zur Auswahl eines Eingabebildes.
    """

    def __init__(self, master):
        super().__init__(master, "Bild auswählen")

        self.selected_file = tk.StringVar()

        self.entry = ttk.Entry(
            self,
            textvariable=self.selected_file,
        )

        self.entry.pack(
            fill="x",
            padx=10,
            pady=(10, 6),
        )

        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(
            fill="x",
            padx=10,
            pady=(0, 10),
        )

        self.select_button = ttk.Button(
            self.button_frame,
            text="Auswählen",
        )

        self.start_button = ttk.Button(
            self.button_frame,
            text="Plugin starten",
        )

        self.manager_button = ttk.Button(
            self.button_frame,
            text="Plugin Manager",
        )

        self.select_button.pack(side="left")

        self.start_button.pack(
            side="left",
            padx=6,
        )

        self.manager_button.pack(side="left")

    def set_filename(self, filename: str):
        """
        Setzt den Dateinamen.
        """
        self.selected_file.set(filename)

    def get_filename(self):
        """
        Liefert den Dateinamen.
        """
        return self.selected_file.get()

    def enable(self):
        """
        Aktiviert alle Buttons.
        """
        self.select_button.configure(state="normal")
        self.start_button.configure(state="normal")
        self.manager_button.configure(state="normal")

    def disable(self):
        """
        Deaktiviert alle Buttons.
        """
        self.select_button.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self.manager_button.configure(state="disabled")

    def clear(self):
        """
        Löscht den Dateinamen.
        """
        self.selected_file.set("")