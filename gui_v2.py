"""
Snapdragon AI Studio

GUI Version 2

Created by Holger Kreuzhofen
Phoenix UI
"""

import os
import subprocess
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
        self.clear_gallery_selection()
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

    def set_gallery_selection(self, filename):
        success, value = self.controller.select_image(filename)

        if not success:
            self._log(f"{value}: {filename}")
            return

        self.selected_gallery_image = value

    def get_selected_gallery_image(self):
        return getattr(self, "selected_gallery_image", None)

    def clear_gallery_selection(self):
        self.selected_gallery_image = None

    def refresh_queue(self):
        jobs = self.controller.get_queue()

        if hasattr(self, "queue_card"):
            self.queue_card.set_jobs(jobs)

        if hasattr(self, "phoenix_workspace"):
            image_paths = [job["input_path"] for job in jobs if job.get("input_path")]
            self.phoenix_workspace.set_gallery_images(image_paths)

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
        self.batch_controller.start_plugin()

    def cancel_processing(self):
        self.batch_controller.cancel_processing()

    def open_output(self):
        last_output = self.controller.get_last_output()

        if not last_output:
            self._log("Noch kein Output vorhanden.")
            return

        if hasattr(self, "phoenix_workspace"):
            self._open_output_directory()
            return

        last_batch_count = self.controller.get_last_batch_count()

        if last_batch_count > 1:
            self._open_output_directory()
            return

        self._open_output_file(last_output)

    def _open_output_file(self, output_file):
        output_path = Path(output_file)

        if not output_path.exists():
            self._log(f"Output nicht gefunden: {output_path}")
            self._disable_output_button()
            return

        try:
            os.startfile(output_path)
            self._log(f"Output geöffnet: {output_path.name}")

        except Exception as error:
            self._log(f"Output konnte nicht geöffnet werden: {error}")

    def _open_output_directory(self):
        output_directory = self.controller.get_last_output_directory()

        if not output_directory:
            self._log("Kein Output-Ordner vorhanden.")
            return

        output_path = Path(output_directory)

        if not output_path.exists():
            self._log(f"Output-Ordner nicht gefunden: {output_path}")
            self._disable_output_button()
            return

        try:
            os.startfile(output_path)
            self._log(f"Output-Ordner geöffnet: {output_path}")

        except Exception:
            try:
                subprocess.Popen(["explorer", str(output_path)])
                self._log(f"Output-Ordner geöffnet: {output_path}")

            except Exception as error:
                self._log(f"Output-Ordner konnte nicht geöffnet werden: {error}")

    def _disable_output_button(self):
        if hasattr(self, "toolbar"):
            self.toolbar.disable_output_button()

        if hasattr(self, "phoenix_workspace"):
            actions = getattr(self.phoenix_workspace, "actions", None)

            if actions is not None and hasattr(actions, "disable_output_button"):
                actions.disable_output_button()


if __name__ == "__main__":
    app = SnapdragonAIStudioV2()
    app.mainloop()
