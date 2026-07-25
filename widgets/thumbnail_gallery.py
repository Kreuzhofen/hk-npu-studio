"""
Snapdragon AI Studio

Thumbnail Gallery Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk


class ThumbnailGallery(tk.Frame):

    def __init__(self, master, on_select=None, max_items=50):
        super().__init__(master, bd=1, relief="groove", padx=8, pady=8)

        self.on_select = on_select
        self.max_items = max_items
        self.items = []
        self.view_mode = "list"
        self.thumbnail_images = []
        self.thumbnail_buttons = []

        self._build_ui()

    def _build_ui(self):

        header = tk.Frame(self)
        header.pack(fill="x")

        self.title_label = tk.Label(
            header,
            text="Galerie",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.title_label.pack(side="left", fill="x", expand=True)

        self.toggle_button = tk.Button(
            header,
            text="Miniaturen anzeigen",
            command=self.toggle_view_mode,
        )
        self.toggle_button.pack(side="right")

        self.info_label = tk.Label(
            self,
            text="Noch keine Bilder geladen.",
            anchor="w",
        )
        self.info_label.pack(fill="x", pady=(4, 6))

        self.content_frame = tk.Frame(self)
        self.content_frame.pack(fill="both", expand=True)

        self._build_list_view()

    def toggle_view_mode(self):

        if self.view_mode == "list":
            self.view_mode = "thumbnails"
            self.toggle_button.configure(text="Liste anzeigen")
        else:
            self.view_mode = "list"
            self.toggle_button.configure(text="Miniaturen anzeigen")

        self._refresh()

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

    def _clear_content(self):

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.thumbnail_images = []
        self.thumbnail_buttons = []

    def _refresh(self):

        if not self.items:
            self.info_label.configure(text="Noch keine Bilder geladen.")
        else:
            self.info_label.configure(
                text=f"Bilder geladen: {len(self.items)}"
            )

        if self.view_mode == "list":
            self._build_list_view()
        else:
            self._build_thumbnail_view()

    def _build_list_view(self):

        self._clear_content()

        list_frame = tk.Frame(self.content_frame)
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

        from tkinter import ttk
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.listbox.yview,
            style="Phoenix.Vertical.TScrollbar",
        )
        scrollbar.pack(
            side="right",
            fill="y",
        )

        self.listbox.configure(
            yscrollcommand=scrollbar.set
        )

        self.listbox.bind(
            "<<ListboxSelect>>",
            self._on_list_select,
        )

        for index, filename in enumerate(self.items, start=1):
            path = Path(filename)
            self.listbox.insert(
                tk.END,
                f"{index}. {path.name}",
            )

    def _build_thumbnail_view(self):

        self._clear_content()

        canvas = tk.Canvas(self.content_frame, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        from tkinter import ttk
        scrollbar = ttk.Scrollbar(
            self.content_frame,
            orient="vertical",
            command=canvas.yview,
            style="Phoenix.Vertical.TScrollbar",
        )
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        thumb_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=thumb_frame, anchor="nw")

        thumb_frame.bind(
            "<Configure>",
            lambda event: canvas.configure(
                scrollregion=canvas.bbox("all")
            ),
        )

        columns = 2

        for index, filename in enumerate(self.items):
            path = Path(filename)
            thumbnail = self._create_thumbnail(path)
            self.thumbnail_images.append(thumbnail)

            button = tk.Button(
                thumb_frame,
                image=thumbnail,
                text=path.name,
                compound="top",
                wraplength=115,
                width=130,
                height=125,
                command=lambda value=filename: self._select(value),
            )

            row = index // columns
            column = index % columns

            button.grid(
                row=row,
                column=column,
                padx=4,
                pady=4,
                sticky="n",
            )

            self.thumbnail_buttons.append(button)

    def _create_thumbnail(self, path):

        try:
            image = Image.open(path).convert("RGB")
            image.thumbnail((110, 82))
            return ImageTk.PhotoImage(image)

        except Exception:
            image = Image.new("RGB", (110, 82), "gray")
            return ImageTk.PhotoImage(image)

    def select_image(self, filename):
        full_path = str(Path(filename).resolve())

        if full_path not in self.items:
            return

        index = self.items.index(full_path)

        if self.view_mode == "list" and hasattr(self, "listbox"):
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
            self.listbox.activate(index)
            self.listbox.see(index)

    def _on_list_select(self, event):

        selection = self.listbox.curselection()

        if not selection:
            return

        index = selection[0]
        filename = self.items[index]

        self._select(filename)

    def _select(self, filename):

        if self.on_select:
            self.on_select(filename)