"""
SnapdragonAI Studio

GUI Version 2

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from PIL import Image, ImageTk

from widgets.file_card import FileCard
from widgets.preview_card import PreviewCard
from widgets.log_card import LogCard
from widgets.plugin_card import PluginCard


class SnapdragonAIStudioV2(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("SnapdragonAI Studio V2")
        self.geometry("1200x800")

        self.preview_image = None

        self._build_ui()

    def _build_ui(self):

        main = tk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(main)
        top.pack(fill="x")

        self.file_card = FileCard(top)
        self.file_card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5,
        )

        self.plugin_card = PluginCard(top)
        self.plugin_card.pack(
            side="left",
            fill="both",
            padx=5,
        )

        self.file_card.select_button.configure(
            command=self.select_image
        )

        middle = tk.Frame(main)
        middle.pack(
            fill="both",
            expand=True,
            pady=10,
        )

        self.preview_card = PreviewCard(middle)
        self.preview_card.pack(
            fill="both",
            expand=True,
        )

        self.log_card = LogCard(main)
        self.log_card.pack(fill="x")

    def select_image(self):
        """
        Öffnet einen Dateidialog und zeigt das Bild in der Vorschau.
        """

        filename = filedialog.askopenfilename(
            title="Bild auswählen",
            filetypes=[
                (
                    "Bilddateien",
                    "*.png *.jpg *.jpeg *.bmp *.webp",
                ),
                (
                    "Alle Dateien",
                    "*.*",
                ),
            ],
        )

        if not filename:
            return

        self.file_card.set_filename(filename)

        self.log_card.log(
            f"Bild ausgewählt: {Path(filename).name}"
        )

        self.show_preview(filename)

    def show_preview(self, filename):
        """
        Lädt ein Bild und zeigt es in der PreviewCard an.
        """

        try:
            image = Image.open(filename).convert("RGB")
            image.thumbnail((850, 420))

            self.preview_image = ImageTk.PhotoImage(image)
            self.preview_card.set_image(self.preview_image)

            self.log_card.log("Vorschau aktualisiert.")

        except Exception as error:
            self.preview_card.set_text(
                f"Vorschaufehler:\n{error}"
            )
            self.log_card.log(
                f"Vorschaufehler: {error}"
            )


if __name__ == "__main__":
    app = SnapdragonAIStudioV2()
    app.mainloop()