"""
SnapdragonAI Studio

GUI Version 2

Created by Holger Kreuzhofen
Phoenix UI
"""

import os
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_FILES = None
    TkinterDnD = None
    DND_AVAILABLE = False

from gui.controllers.application_controller import ApplicationController


BaseWindow = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk


class SnapdragonAIStudioV2(BaseWindow):

    def __init__(self):
        super().__init__()

        self.application_controller = ApplicationController(
            self,
            dnd_available=DND_AVAILABLE,
            dnd_files=DND_FILES,
        )
        self.application_controller.initialize()

    def open_plugin_manager(self):
        self.dialog_controller.open_plugin_manager()

    def open_about_dialog(self):
        self.dialog_controller.open_about_dialog()

    def _log(self, message):
        if hasattr(self, "log_card"):
            self.log_card.log(message)
            return

        print(message)

    def on_drop_file(self, event):
        dropped_paths = self.tk.splitlist(event.data)

        if not dropped_paths:
            self._log("Drag & Drop: keine Datei erkannt.")
            return

        files = []
        folders = []

        for dropped_path in dropped_paths:
            path = Path(dropped_path)

            if path.is_dir():
                folders.append(path)
            else:
                files.append(path)

        if files:
            self.load_image_files(files)

        for folder in folders:
            self.load_image_folder(folder)

    def select_images(self):
        self.import_controller.select_images()

    def select_folder(self):
        self.import_controller.select_folder()

    def load_image_folder(self, folder_path):
        self.import_controller.load_image_folder(folder_path)

    def load_image_files(self, filenames):
        self.import_controller.load_image_files(filenames)

    def select_loaded_image(self, filename):
        success, value = self.controller.select_image(filename)

        if not success:
            self._log(f"{value}: {filename}")
            return

        if hasattr(self, "phoenix_workspace"):
            self.phoenix_workspace.show_image(value)
            return

        self.file_card.set_filename(value)
        self.thumbnail_gallery.select_image(value)
        self.queue_card.select_job(value)
        self.show_preview(value)

    def refresh_queue(self):
        jobs = self.controller.get_queue()

        if hasattr(self, "queue_card"):
            self.queue_card.set_jobs(jobs)

    def show_preview(self, filename):
        if hasattr(self, "phoenix_workspace"):
            self.phoenix_workspace.show_image(filename)
            return

        try:
            image = Image.open(filename).convert("RGB")
            image.thumbnail((850, 520))

            self.preview_image = ImageTk.PhotoImage(image)
            self.preview_card.set_image(self.preview_image)

            self._log(f"Vorschau aktualisiert: {Path(filename).name}")

        except Exception as error:
            self.preview_card.set_text(
                f"Vorschaufehler:\n{error}"
            )
            self._log(f"Vorschaufehler: {error}")

    def start_plugin(self):
        if hasattr(self, "phoenix_workspace") and not hasattr(self, "toolbar"):
            self._log("Plugin-Start in Phoenix ist noch nicht vollständig verbunden.")
            return

        self.batch_controller.start_plugin()

    def cancel_processing(self):
        if hasattr(self, "phoenix_workspace") and not hasattr(self, "toolbar"):
            self._log("Stop in Phoenix ist noch nicht vollständig verbunden.")
            return

        self.batch_controller.cancel_processing()

    def open_output(self):
        last_output = self.controller.get_last_output()

        if not last_output:
            self._log("Noch kein Output vorhanden.")
            return

        output_path = Path(last_output)

        if not output_path.exists():
            self._log(f"Output nicht gefunden: {output_path}")

            if hasattr(self, "toolbar"):
                self.toolbar.disable_output_button()

            return

        try:
            os.startfile(output_path)
            self._log(f"Output geöffnet: {output_path.name}")

        except Exception as error:
            self._log(f"Output konnte nicht geöffnet werden: {error}")


if __name__ == "__main__":
    app = SnapdragonAIStudioV2()
    app.mainloop()