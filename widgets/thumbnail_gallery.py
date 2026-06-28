"""
SnapdragonAI Studio

Thumbnail Gallery Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk
from pathlib import Path


class ThumbnailGallery(tk.Frame):

    def __init__(self, master, on_select=None, max_items=10):
        super().__init__(master, bd=1, relief="groove", padx=10, pady=8)

        self.on_select = on_select
        self.max_items = max_items
        self.items = []
        self.buttons = []

        self._build_ui()

    def _build_ui(self):

        self.title_label = tk.Label(
            self,
            text="Galerie",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.title_label.pack(fill="x")

        self.info_label = tk.Label(
            self,
            text="Noch keine Bilder geladen.",
            anchor="w",
        )
        self.info_label.pack(fill="x", pady=(4, 6))

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(fill="x")

    def add_image(self, filename):
        path = Path(filename)

        if not path.exists():
            return

        full_path = str(path.resolve())

        if full_path in self.items:
            self.items.remove(full_path)

        self.items.insert(0, full_path)
        self.items = self.items[:self.max_items]

        self._refresh()

    def _refresh(self):

        for button in self.buttons:
            button.destroy()

        self.buttons = []

        if not self.items:
            self.info_label.configure(text="Noch keine Bilder geladen.")
            return

        self.info_label.configure(
            text=f"Zuletzt geladene Bilder: {len(self.items)}"
        )

        for index, filename in enumerate(self.items, start=1):
            path = Path(filename)

            button = tk.Button(
                self.button_frame,
                text=f"{index}. {path.name}",
                command=lambda value=filename: self._select(value),
                width=22,
                anchor="w",
            )
            button.pack(side="left", padx=3, pady=3)

            self.buttons.append(button)

    def _select(self, filename):
        if self.on_select:
            self.on_select(filename)