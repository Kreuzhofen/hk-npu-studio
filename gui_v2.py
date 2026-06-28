"""
SnapdragonAI Studio

GUI Version 2

Created by Holger Kreuzhofen
Phoenix UI
"""

import os
import queue
import threading
import time
import traceback
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
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
        self.last_output = None
        self.job_start_time = None
        self.job_running = False

        self._build_ui()
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

        self.progress_frame = tk.Frame(main)
        self.progress_frame.pack(fill="x", pady=(10, 0))

        self.progress_label = tk.Label(
            self.progress_frame,
            text="Status: Bereit",
            anchor="w",
        )
        self.progress_label.pack(fill="x")

        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode="determinate",
            maximum=100,
            value=0,
        )
        self.progress_bar.pack(fill="x", pady=5)

        self.runtime_label = tk.Label(
            self.progress_frame,
            text="Laufzeit: 00:00",
            anchor="w",
        )
        self.runtime_label.pack(fill="x")

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

        self.last_output = None
        self.output_button.configure(state="disabled")

        self.job_start_time = time.time()
        self.job_running = True
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start(10)
        self.progress_label.configure(
            text="Status: Bild wird verarbeitet..."
        )
        self.runtime_label.configure(text="Laufzeit: 00:00")

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

    def _finish_progress(self, status_text, progress_value):
        """
        Beendet die Fortschrittsanzeige.
        """

        self.job_running = False
        self.progress_bar.stop()
        self.progress_bar.configure(
            mode="determinate",
            value=progress_value,
        )
        self.progress_label.configure(text=status_text)

    def _update_runtime(self):
        """
        Aktualisiert die Laufzeit während ein Job läuft.
        """

        if self.job_running and self.job_start_time:
            elapsed = int(time.time() - self.job_start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60

            self.runtime_label.configure(
                text=f"Laufzeit: {minutes:02d}:{seconds:02d}"
            )

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
                    self._finish_progress(
                        "Status: Fertig",
                        100,
                    )
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
                    self._finish_progress(
                        "Status: Fehler",
                        0,
                    )
                    self.log_card.log("FEHLER:")
                    self.log_card.log(value)

        except queue.Empty:
            pass

        self.after(100, self._poll_log_queue)


if __name__ == "__main__":
    app = SnapdragonAIStudioV2()
    app.mainloop()