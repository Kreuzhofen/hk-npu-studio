"""
SnapdragonAI Studio

GUI Version 2

Created by Holger Kreuzhofen
Phoenix UI
"""

import os
import queue
import threading
import traceback
import tkinter as tk
from tkinter import filedialog
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
from engine.gui_controller import GuiController
from widgets.toolbar import Toolbar
from widgets.file_card import FileCard
from widgets.preview_card import PreviewCard
from widgets.log_card import LogCard
from widgets.plugin_card import PluginCard
from widgets.job_card import JobCard
from widgets.thumbnail_gallery import ThumbnailGallery
from widgets.queue_card import QueueCard


BaseWindow = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk


class SnapdragonAIStudioV2(BaseWindow):

    def __init__(self):
        super().__init__()

        self.title("SnapdragonAI Studio V2")
        self.geometry("1400x900")

        self.controller = GuiController()
        self.preview_image = None
        self.log_queue = queue.Queue()

        self._build_ui()
        self._setup_drag_and_drop()

        self.after(100, self._poll_log_queue)
        self.after(500, self._update_runtime)

    def _build_ui(self):

        main = tk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        self.toolbar = Toolbar(
            main,
            on_select_images=self.select_images,
            on_select_folder=self.select_folder,
            on_start=self.start_plugin,
            on_open_output=self.open_output,
            on_open_plugin_manager=self.open_plugin_manager,
        )
        self.toolbar.pack(fill="x")

        top = tk.Frame(main)
        top.pack(fill="x", pady=(10, 0))

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

        self.plugin_card.set_plugin(
            "RealESRGAN",
            "QNN / Snapdragon NPU",
            "Bereit",
        )

        self.job_card = JobCard(main)
        self.job_card.pack(
            fill="x",
            pady=(10, 0),
        )

        content = tk.Frame(main)
        content.pack(
            fill="both",
            expand=True,
            pady=10,
        )

        preview_area = tk.Frame(content)
        preview_area.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 8),
        )

        self.preview_card = PreviewCard(preview_area)
        self.preview_card.pack(
            fill="both",
            expand=True,
        )

        side_area = tk.Frame(content, width=330)
        side_area.pack(
            side="right",
            fill="y",
        )
        side_area.pack_propagate(False)

        self.thumbnail_gallery = ThumbnailGallery(
            side_area,
            on_select=self.select_loaded_image,
            max_items=50,
        )
        self.thumbnail_gallery.pack(
            fill="both",
            expand=True,
            pady=(0, 8),
        )

        self.queue_card = QueueCard(
            side_area,
            on_select=self.select_loaded_image,
        )
        self.queue_card.pack(
            fill="both",
            expand=True,
        )

        self.log_card = LogCard(main)
        self.log_card.pack(fill="x")

        if DND_AVAILABLE:
            self.log_card.log("Drag & Drop ist verfügbar.")
        else:
            self.log_card.log(
                "Drag & Drop nicht verfügbar. "
                "Installiere optional: pip install tkinterdnd2"
            )

    def open_plugin_manager(self):
        """
        Öffnet den Plugin Manager Dialog.
        """

        PluginManagerDialog(self)

    def _setup_drag_and_drop(self):
        """
        Aktiviert Drag & Drop für Bilddateien und Ordner.
        """

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
        """
        Verarbeitet per Drag & Drop abgelegte Dateien oder Ordner.
        """

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
        """
        Öffnet einen Dateidialog und lädt ein oder mehrere Bilder.
        """

        filenames = filedialog.askopenfilenames(
            title="Bilder auswählen",
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

        if not filenames:
            return

        self.load_image_files(filenames)

    def select_folder(self):
        """
        Öffnet einen Ordnerdialog und lädt alle unterstützten Bilder.
        """

        folder = filedialog.askdirectory(
            title="Ordner mit Bildern auswählen"
        )

        if not folder:
            return

        self.load_image_folder(folder)

    def load_image_folder(self, folder_path):
        """
        Lädt alle unterstützten Bilder aus einem Ordner.
        """

        result = self.controller.load_image_folder(folder_path)
        self._handle_import_result(result)

        valid_files = result["valid_files"]

        if valid_files:
            self.log_card.log(
                f"Ordner geladen: {Path(folder_path).name} "
                f"({len(valid_files)} Bilder)"
            )
        else:
            self.log_card.log(
                f"Keine unterstützten Bilder im Ordner gefunden: "
                f"{folder_path}"
            )

    def load_image_files(self, filenames):
        """
        Lädt mehrere Bilddateien über den Controller in die GUI.
        """

        result = self.controller.load_image_files(filenames)
        self._handle_import_result(result)

        valid_files = result["valid_files"]

        if not valid_files:
            self.log_card.log("Keine gültigen Bilddateien geladen.")
            return

        if len(valid_files) == 1:
            self.log_card.log(
                f"1 Bild geladen und zur Queue hinzugefügt: "
                f"{Path(valid_files[0]).name}"
            )
        else:
            self.log_card.log(
                f"{len(valid_files)} Bilder geladen und zur Queue hinzugefügt."
            )

    def _handle_import_result(self, result):
        """
        Übernimmt importierte Bilder in Galerie, Vorschau und Queue.
        """

        valid_files = result["valid_files"]
        rejected_files = result["rejected_files"]

        for filename, reason in rejected_files:
            self.log_card.log(f"{reason}: {filename}")

        for filename in valid_files:
            self.thumbnail_gallery.add_image(filename)

        self.refresh_queue()

        if valid_files:
            self.select_loaded_image(valid_files[0])

    def select_loaded_image(self, filename):
        """
        Wählt ein geladenes Bild als aktuelles Bild aus.
        """

        success, value = self.controller.select_image(filename)

        if not success:
            self.log_card.log(f"{value}: {filename}")
            return

        self.file_card.set_filename(value)
        self.thumbnail_gallery.select_image(value)
        self.queue_card.select_job(value)
        self.show_preview(value)

    def refresh_queue(self):
        """
        Aktualisiert die sichtbare Batch Queue.
        """

        self.queue_card.set_jobs(
            self.controller.get_queue()
        )

    def show_preview(self, filename):
        """
        Lädt ein Bild und zeigt es in der PreviewCard an.
        """

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
        """
        Startet das Upscaling für das aktuell ausgewählte Bild.
        """

        filename = self.controller.get_current_image()

        if not filename:
            filename = self.file_card.get_filename()

        if not filename:
            self.log_card.log("Kein Bild ausgewählt.")
            return

        if not Path(filename).exists():
            self.log_card.log(f"Datei nicht gefunden: {filename}")
            return

        self.controller.clear_last_output()
        self.toolbar.disable_output_button()
        self.toolbar.disable_start_button()
        self.controller.set_queue_status(filename, "läuft")
        self.refresh_queue()

        self.job_card.start_job(
            plugin="RealESRGAN",
            backend="QNN / Snapdragon NPU",
            input_path=filename,
        )

        self.file_card.disable()
        self.plugin_card.set_plugin(
            "RealESRGAN",
            "QNN / Snapdragon NPU",
            "Läuft...",
        )
        self.log_card.log(
            f"Starte Phoenix Engine für: {Path(filename).name}"
        )

        thread = threading.Thread(
            target=self._worker,
            args=(filename,),
            daemon=True,
        )
        thread.start()

    def _worker(self, filename):
        """
        Führt das Plugin im Hintergrund aus.
        """

        try:
            output_path = self.controller.run_upscale(filename)
            self.log_queue.put(("done", (filename, output_path)))

        except Exception:
            self.controller.set_queue_status(filename, "Fehler")
            self.log_queue.put(("error", traceback.format_exc()))

    def open_output(self):
        """
        Öffnet die zuletzt erzeugte Output-Datei.
        """

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

    def _update_runtime(self):
        """
        Aktualisiert die Laufzeit der JobCard.
        """

        if self.job_card.running:
            self.job_card.update_runtime()

        self.after(500, self._update_runtime)

    def _poll_log_queue(self):
        """
        Verarbeitet Rückmeldungen aus dem Hintergrundthread.
        """

        try:
            while True:
                kind, value = self.log_queue.get_nowait()

                if kind == "done":
                    input_path, output_path = value
                    self.controller.set_last_output(output_path)
                    self.controller.set_queue_status(
                        input_path,
                        "fertig",
                        output_path=output_path,
                    )

                    self.file_card.enable()
                    self.toolbar.enable_start_button()
                    self.toolbar.enable_output_button()
                    self.plugin_card.set_plugin(
                        "RealESRGAN",
                        "QNN / Snapdragon NPU",
                        "Fertig",
                    )
                    self.job_card.finish_job(output_path)
                    self.thumbnail_gallery.add_image(output_path)
                    self.refresh_queue()
                    self.log_card.log(f"Fertig: {output_path}")
                    self.select_loaded_image(output_path)

                elif kind == "error":
                    self.file_card.enable()
                    self.toolbar.enable_start_button()
                    self.toolbar.disable_output_button()
                    self.plugin_card.set_plugin(
                        "RealESRGAN",
                        "QNN / Snapdragon NPU",
                        "Fehler",
                    )
                    self.job_card.fail_job()
                    self.refresh_queue()
                    self.log_card.log("FEHLER:")
                    self.log_card.log(value)

        except queue.Empty:
            pass

        self.after(100, self._poll_log_queue)


if __name__ == "__main__":
    app = SnapdragonAIStudioV2()
    app.mainloop()