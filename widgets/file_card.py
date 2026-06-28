"""
SnapdragonAI Studio

File Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk

from resources.theme import Theme


class FileCard(tk.Frame):

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
            text="Aktuelles Bild",
            font=Theme.font("card_title"),
            anchor="w",
            bg=Theme.color("card"),
            fg=Theme.color("text"),
        )
        self.title_label.pack(fill="x")

        self.filename_entry = tk.Entry(
            self,
            font=Theme.font("body"),
            bg="#FFFFFF",
            fg=Theme.color("text"),
            relief="solid",
            bd=1,
        )
        self.filename_entry.pack(fill="x", pady=(8, 0))

    def set_filename(self, filename):
        self.filename_entry.configure(state="normal")
        self.filename_entry.delete(0, tk.END)
        self.filename_entry.insert(0, filename)

    def get_filename(self):
        return self.filename_entry.get().strip()

    def disable(self):
        self.filename_entry.configure(state="disabled")

    def enable(self):
        self.filename_entry.configure(state="normal")