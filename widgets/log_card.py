"""
SnapdragonAI Studio

Log Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

from tkinter import ttk
import tkinter as tk


class LogCard(ttk.LabelFrame):
    """
    Widget zur Anzeige des Protokolls.
    """

    def __init__(self, master):
        super().__init__(master, text="Protokoll")

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