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

from dialogs.plugin_manager import PluginManagerDialog
from engine.brand_manager import BrandManager
from engine.gui_controller import GuiController
from resources.branding import Branding
from resources.theme import Theme
from gui.controllers.batch_controller import BatchController
from gui.controllers.import_controller import ImportController
from gui.controllers.ui_builder import UIBuilder
from widgets.startup_overlay import StartupOverlay


BaseWindow = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk


class SnapdragonAIStudioV2(BaseWindow):

    def __init__(self):
        super().__init__()

        self.brand = BrandManager()
        self.brand.initialize()

        self.title(Branding.WINDOW_TITLE_WITH_VERSION)
        self.geometry("1400x900")
        self.configure(bg=Theme.color("background"))

        self.controller = GuiController()
        self.import_controller = ImportController(self)
        self.batch_controller = BatchController(self)
        self.preview_image = None
        self.startup_overlay = None

        self._build_ui()
        self._setup_drag_and_drop()
        self._show_startup_overlay()
        self.batch_controller.start_polling()

    def _show_startup_overlay(self):
        self.startup_overlay = StartupOverlay(self, self.brand)
        self.startup_overlay.show()
        self.after(1600, self.startup_overlay.fade_out)

    def _build_ui(self):
        UIBuilder(self, dnd_available=DND_AVAILABLE).build()

    def open_plugin_manager(self):
        PluginManagerDialog(self)

    def _setup_drag_and_drop(self):
        if not DND_AVAILABLE:
            return

        drop_targets = [
            self,
            self.file_card,
            self.preview_card,
            self.thumbnail_gallery,
            self.queue_card,
        ]

        for target in drop_targets:
            target.drop_target_register(DND_FILES)
            target.dnd_bind("<<Drop>>", self._on_drop_file)

    def _on_drop_file(self, event):
        dropped_paths = self.tk.splitlist(event.data)

        if not dropped_paths:
            self.log_card.log("Drag & Drop: keine Datei erkannt.")
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
            self.log_card.log(f"{value}: {filename}")
            return

        self.file_card.set_filename(value)
        self.thumbnail_gallery.select_image(value)
        self.queue_card.select_job(value)
        self.show_preview(value)

    def refresh_queue(self):
        self.queue_card.set_jobs(
            self.controller.get_queue()
        )

    def show_preview(self, filename):
        try:
            image = Image.open(filename).convert("RGB")
            image.thumbnail((850, 520))

            self.preview_image = ImageTk.PhotoImage(image)
            self.preview_card.set_image(self.preview_image)

            self.log_card.log(f"Vorschau aktualisiert: {Path(filename).name}")

        except Exception as error:
            self.preview_card.set_text(
                f"Vorschaufehler:\n{error}"
            )
            self.log_card.log(
                f"Vorschaufehler: {error}"
            )

    def start_plugin(self):
        self.batch_controller.start_plugin()

    def cancel_processing(self):
        self.batch_controller.cancel_processing()

    def open_output(self):
        last_output = self.controller.get_last_output()

        if not last_output:
            self.log_card.log("Noch kein Output vorhanden.")
            return

        output_path = Path(last_output)

        if not output_path.exists():
            self.log_card.log(f"Output nicht gefunden: {output_path}")
            self.toolbar.disable_output_button()
            return

        try:
            os.startfile(output_path)
            self.log_card.log(f"Output geöffnet: {output_path.name}")

        except Exception as error:
            self.log_card.log(f"Output konnte nicht geöffnet werden: {error}")


if __name__ == "__main__":
    app = SnapdragonAIStudioV2()
    app.mainloop()
