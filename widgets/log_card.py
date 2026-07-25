"""
Snapdragon AI Studio

Log Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk
from tkinter import ttk

from widgets.base_card import BaseCard


class LogCard(BaseCard):
    """
    Widget zur Anzeige des Protokolls.
    """

    def __init__(self, master):
        super().__init__(master, "Protokoll")

        self.log_text = tk.Text(
            self,
            height=8,
            wrap="word",
            font=("Consolas", 9),
        )

        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.log_text.yview,
            style="Phoenix.Vertical.TScrollbar"
        )

        self.log_text.configure(
            yscrollcommand=scrollbar.set
        )

        self.log_text.pack(
            side="left",
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        scrollbar.pack(
            side="right",
            fill="y",
            pady=10,
        )

    def log(self, text: str):
        """
        Fügt eine Log-Zeile hinzu.
        """

        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def clear(self):
        """
        Löscht das Protokoll.
        """

        self.log_text.delete("1.0", "end")

    def get_text(self):
        """
        Liefert den kompletten Log-Inhalt zurück.
        """

        return self.log_text.get("1.0", "end")

    def set_enabled(self, enabled: bool):
        """
        Aktiviert oder deaktiviert die Log-Ausgabe.
        """

        state = "normal" if enabled else "disabled"
        self.log_text.configure(state=state)