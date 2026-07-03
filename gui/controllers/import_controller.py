"""
Snapdragon AI Studio

Import Controller

Created by Holger Kreuzhofen
Phoenix UI
"""

from pathlib import Path
from tkinter import filedialog


class ImportController:
    """
    Handles image and folder import actions for Snapdragon AI Studio.
    """

    def __init__(self, app):
        self.app = app

    def select_images(self):
        filenames = filedialog.askopenfilenames(
            title="Bilder auswählen",
            filetypes=[
                ("Bilddateien", "*.png *.jpg *.jpeg *.bmp *.webp"),
                ("Alle Dateien", "*.*"),
            ],
        )

        if not filenames:
            return

        self.load_image_files(filenames)

    def select_folder(self):
        folder = filedialog.askdirectory(
            title="Ordner mit Bildern auswählen"
        )

        if not folder:
            return

        self.load_image_folder(folder)

    def load_image_folder(self, folder_path):
        result = self.app.controller.load_image_folder(folder_path)
        self._handle_import_result(result)

        valid_files = result["valid_files"]

        if valid_files:
            self._log(
                f"Ordner geladen: {Path(folder_path).name} "
                f"({len(valid_files)} Bilder)"
            )
        else:
            self._log(
                f"Keine unterstützten Bilder im Ordner gefunden: "
                f"{folder_path}"
            )

    def load_image_files(self, filenames):
        result = self.app.controller.load_image_files(filenames)
        self._handle_import_result(result)

        valid_files = result["valid_files"]

        if not valid_files:
            self._log("Keine gültigen Bilddateien geladen.")
            return

        if len(valid_files) == 1:
            self._log(
                f"1 Bild geladen und zur Queue hinzugefügt: "
                f"{Path(valid_files[0]).name}"
            )
        else:
            self._log(
                f"{len(valid_files)} Bilder geladen und zur Queue hinzugefügt."
            )

    def _handle_import_result(self, result):
        valid_files = result["valid_files"]
        rejected_files = result["rejected_files"]

        for filename, reason in rejected_files:
            self._log(f"{reason}: {filename}")

        if hasattr(self.app, "thumbnail_gallery"):
            for filename in valid_files:
                self.app.thumbnail_gallery.add_image(filename)

        self.app.refresh_queue()

        if valid_files:
            self.app.select_loaded_image(valid_files[0])

    def _log(self, message):
        if hasattr(self.app, "_log"):
            self.app._log(message)
            return

        if hasattr(self.app, "log_card"):
            self.app.log_card.log(message)
            return

        print(message)