"""
SnapdragonAI Studio

Thumbnail Gallery Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk
from pathlib import Path


class ThumbnailGallery(tk.Frame):

    def __init__(self, master, on_select=None, max_items=50):
        super().__init__(master, bd=1, relief="groove", padx=8, pady=8)

        self.on_select = on_select
        self.max_items = max_items
        self.items = []

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

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            height=18,
            exportselection=False,
        )
        self.listbox.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.scrollbar = tk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.listbox.yview,
        )
        self.scrollbar.pack(
            side="right",
            fill="y",
        )

        self.listbox.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.listbox.bind(
            "<<ListboxSelect>>",
            self._on_select,
        )

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
        self.select_image(full_path)

    def _refresh(self):

        self.listbox.delete(0, tk.END)

        if not self.items:
            self.info_label.configure(text="Noch keine Bilder geladen.")
            return

        self.info_label.configure(
            text=f"Bilder geladen: {len(self.items)}"
        )

        for index, filename in enumerate(self.items, start=1):
            path = Path(filename)
            self.listbox.insert(
                tk.END,
                f"{index}. {path.name}",
            )

    def select_image(self, filename):
        full_path = str(Path(filename).resolve())

        if full_path not in self.items:
            return

        index = self.items.index(full_path)

        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.listbox.see(index)

    def _on_select(self, event):
        selection = self.listbox.curselection()

        if not selection:
            return

        index = selection[0]
        filename = self.items[index]

        if self.on_select:
            self.on_select(filename)