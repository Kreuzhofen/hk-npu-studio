"""
SnapdragonAI Studio

GUI Version 2

Created by Holger Kreuzhofen
Phoenix UI
"""

import queue
import threading
import traceback
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from PIL import Image, ImageTk

from engine.phoenix_adapter import PhoenixAdapter
from widgets.file_card import FileCard
from widgets.preview_card import PreviewCard
from widgets.log_card import LogCard
from widgets.plugin_card import PluginCard


class SnapdragonAIStudioV2(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("SnapdragonAI Studio V2")
        self.geometry("1200x800")

        self.adapter = PhoenixAdapter()
        self.preview_image = None
        self.log_queue = queue.Queue()

        self._build_ui()
        self.after(100, self._poll_log_queue)

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
        self.log_card.log(f"Bild ausgewählt: {Path(filename).name}")
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

    def _poll_log_queue(self):
        """
        Verarbeitet Rückmeldungen aus dem Hintergrundthread.
        """

        try:
            while True:
                kind, value = self.log_queue.get_nowait()

                if kind == "done":
                    self.file_card.enable()
                    self.plugin_card.set_plugin(
                        "RealESRGAN",
                        "QNN / Snapdragon NPU",
                        "Fertig",
                    )
                    self.log_card.log(f"Fertig: {value}")
                    self.show_preview(value)

                elif kind == "error":
                    self.file_card.enable()
                    self.plugin_card.set_plugin(
                        "RealESRGAN",
                        "QNN / Snapdragon NPU",
                        "Fehler",
                    )
                    self.log_card.log("FEHLER:")
                    self.log_card.log(value)

        except queue.Empty:
            pass

        self.after(100, self._poll_log_queue)


if __name__ == "__main__":
    app = SnapdragonAIStudioV2()
    app.mainloop()