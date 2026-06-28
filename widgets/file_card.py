"""
SnapdragonAI Studio

File Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk


class FileCard(tk.Frame):

    def __init__(self, master):
        super().__init__(master, bd=1, relief="groove", padx=10, pady=10)

        self._build_ui()

    def _build_ui(self):

        self.title_label = tk.Label(
            self,
            text="Bild auswählen",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.title_label.pack(fill="x")

        self.filename_entry = tk.Entry(self)
        self.filename_entry.pack(fill="x", pady=(8, 8))

        button_frame = tk.Frame(self)
        button_frame.pack(fill="x")

        self.select_button = tk.Button(
            button_frame,
            text="Auswählen",
        )
        self.select_button.pack(side="left", padx=(0, 6))

        self.start_button = tk.Button(
            button_frame,
            text="Plugin starten",
        )
        self.start_button.pack(side="left")

    def set_filename(self, filename):
        self.filename_entry.delete(0, tk.END)
        self.filename_entry.insert(0, filename)

    def get_filename(self):
        return self.filename_entry.get().strip()

    def disable(self):
        self.select_button.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self.filename_entry.configure(state="disabled")

    def enable(self):
        self.select_button.configure(state="normal")
        self.start_button.configure(state="normal")
        self.filename_entry.configure(state="normal")