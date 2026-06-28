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

from engine.phoenix_adapter import PhoenixAdapter
from widgets.file_card import FileCard
from widgets.preview_card import PreviewCard
from widgets.log_card import LogCard
from widgets.plugin_card import PluginCard
from widgets.job_card import JobCard
from widgets.thumbnail_gallery import ThumbnailGallery


BaseWindow = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk


class SnapdragonAIStudioV2(BaseWindow):

    def __init__(self):
        super().__init__()

        self.title("SnapdragonAI Studio V2")
        self.geometry("1200x850")

        self.adapter = PhoenixAdapter()
        self.preview_image = None
        self.log_queue = queue.Queue()
        self.last_output = None

        self._build_ui()
        self._setup_drag_and_drop()

        self.after(100, self._poll_log_queue)
        self.after(500, self._update_runtime)

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

        self.plugin_card.set_plugin(
            "RealESRGAN",
            "QNN / Snapdragon NPU",
            "Bereit",
        )

        self.file_card.select_button.configure(
            command=self.select_image
        )

        self.file_card.start_button.configure(
            command=self.start_plugin
        )

        self.output_button = tk.Button(
            top,
            text="Output öffnen",
            command=self.open_output,
            state="disabled",
        )
        self.output_button.pack(
            side="left",
            fill="y",
            padx=5,
        )

        self.job_card = JobCard(main)
        self.job_card.pack(
            fill="x",
            pady=(10, 0),
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

        self.thumbnail_gallery = ThumbnailGallery(
            main,
            on_select=self.load_image_file,
            max_items=10,
        )
        self.thumbnail_gallery.pack(
            fill="x",
            pady=(0, 10),
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

    def _setup_drag_and_drop(self):
        """
        Aktiviert Drag & Drop für Bilddateien, falls tkinterdnd2 vorhanden ist.
        """

        if not DND_AVAILABLE:
            return

        drop_targets = [
            self,
            self.file_card,
            self.preview_card,
            self.thumbnail_gallery,
        ]

        for target in drop_targets:
            target.drop_target_register(DND_FILES)
            target.dnd_bind("<<Drop>>", self._on_drop_file)

    def _on_drop_file(self, event):
        """
        Verarbeitet eine per Drag & Drop abgelegte Datei.
        """

        dropped_files = self.tk.splitlist(event.data)

        if not dropped_files:
            self.log_card.log("Drag & Drop: keine Datei erkannt.")
            return

        filename = dropped_files[0]
        self.load_image_file(filename)

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

        self.load_image_file(filename)

    def load_image_file(self, filename):
        """
        Lädt eine Bilddatei in die GUI.
        """

        path = Path(filename)

        if not path.exists():
            self.log_card.log(f"Datei nicht gefunden: {filename}")
            return

        if not self._is_supported_image(path):
            self.log_card.log(f"Nicht unterstützte Bilddatei: {path.name}")
            return

        self.file_card.set_filename(str(path))
        self.thumbnail_gallery.add_image(str(path))
        self.log_card.log(f"Bild geladen: {path.name}")
        self.show_preview(str(path))

    def _is_supported_image(self, path):
        """
        Prüft, ob die Datei ein unterstütztes Bildformat hat.
        """

        supported_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".webp",
        }

        return path.suffix.lower() in supported_extensions

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

    def start_plugin(self):
        """
        Startet das Upscaling über die Phoenix Engine.
        """

        filename = self.file_card.get_filename()

        if not filename:
            self.log_card.log("Kein Bild ausgewählt.")
            return

        if not Path(filename).exists():
            self.log_card.log(f"Datei nicht gefunden: {filename}")
            return

        self.last_output = None
        self.output_button.configure(state="disabled")

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
        self.log_card.log("Starte Phoenix Engine...")

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
            result = self.adapter.run(
                "image.upscale",
                input_path=filename,
            )

            output_path = result["output_path"]

            self.log_queue.put(("done", output_path))

        except Exception:
            self.log_queue.put(("error", traceback.format_exc()))

    def open_output(self):
        """
        Öffnet die zuletzt erzeugte Output-Datei.
        """

        if not self.last_output:
            self.log_card.log("Noch kein Output vorhanden.")
            return

        output_path = Path(self.last_output)

        if not output_path.exists():
            self.log_card.log(f"Output nicht gefunden: {output_path}")
            self.output_button.configure(state="disabled")
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
                    self.last_output = value

                    self.file_card.enable()
                    self.output_button.configure(state="normal")
                    self.plugin_card.set_plugin(
                        "RealESRGAN",
                        "QNN / Snapdragon NPU",
                        "Fertig",
                    )
                    self.job_card.finish_job(value)
                    self.thumbnail_gallery.add_image(value)
                    self.log_card.log(f"Fertig: {value}")
                    self.show_preview(value)

                elif kind == "error":
                    self.file_card.enable()
                    self.output_button.configure(state="disabled")
                    self.plugin_card.set_plugin(
                        "RealESRGAN",
                        "QNN / Snapdragon NPU",
                        "Fehler",
                    )
                    self.job_card.fail_job()
                    self.log_card.log("FEHLER:")
                    self.log_card.log(value)

        except queue.Empty:
            pass

        self.after(100, self._poll_log_queue)


if __name__ == "__main__":
    app = SnapdragonAIStudioV2()
    app.mainloop()