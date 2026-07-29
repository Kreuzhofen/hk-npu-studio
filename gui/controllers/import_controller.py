"""
Snapdragon AI Studio

Import Controller

Created by Holger Kreuzhofen
Phoenix UI
"""

from pathlib import Path
from tkinter import filedialog

from app.i18n import tr


class ImportController:
    """
    Handles image and folder import actions for Snapdragon AI Studio.
    """

    def __init__(self, app):
        self.app = app

    def select_images(self):
        filenames = filedialog.askopenfilenames(
            title=tr("select_images_title", "Bilder auswählen"),
            filetypes=[
                (tr("image_files", "Bilddateien"), "*.png *.jpg *.jpeg *.bmp *.webp"),
                (tr("all_files", "Alle Dateien"), "*.*"),
            ],
        )

        if not filenames:
            return

        self.load_image_files(filenames)

    def select_folder(self):
        folder = filedialog.askdirectory(
            title=tr("select_image_folder_title", "Ordner mit Bildern auswählen")
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
                tr("folder_loaded_images", "Ordner geladen: {folder} ({count} Bilder)", folder=Path(folder_path).name, count=len(valid_files))
            )
        else:
            self._log(
                tr("folder_no_supported_images", "Keine unterstützten Bilder im Ordner gefunden: {folder}", folder=folder_path)
            )

    def load_image_files(self, filenames):
        result = self.app.controller.load_image_files(filenames)
        self._handle_import_result(result)

        valid_files = result["valid_files"]

        if not valid_files:
            self._log(tr("no_valid_images_loaded", "Keine gültigen Bilddateien geladen."))
            return

        if len(valid_files) == 1:
            self._log(
                tr("one_image_queued", "1 Bild geladen und zur Warteschlange hinzugefügt: {file}", file=Path(valid_files[0]).name)
            )
        else:
            self._log(
                tr("images_queued", "{count} Bilder geladen und zur Warteschlange hinzugefügt.", count=len(valid_files))
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
