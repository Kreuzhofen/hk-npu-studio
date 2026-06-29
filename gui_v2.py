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
from gui.controllers.ui_builder import UIBuilder
from gui.controllers.import_controller import ImportController
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
        self.preview_image = None
        self.log_queue = queue.Queue()
        self.cancel_requested = False
        self.startup_overlay = None

        self._build_ui()
        self._setup_drag_and_drop()
        self._show_startup_overlay()

        self.after(100, self._poll_log_queue)
        self.after(500, self._update_runtime)
        self.after(500, self._update_status_bar)

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
        waiting_jobs = self.controller.get_waiting_job_count()

        if waiting_jobs <= 0:
            self.log_card.log("Keine wartenden Jobs in der Queue.")
            return

        self.cancel_requested = False
        self.controller.clear_last_output()
        self.toolbar.disable_output_button()
        self.toolbar.disable_start_button()
        self.toolbar.disable_select_button()
        self.toolbar.enable_cancel_button()
        self.file_card.disable()

        self.job_card.set_batch_progress(0, waiting_jobs, 0)

        self.plugin_card.set_plugin(
            "RealESRGAN",
            "QNN / Snapdragon NPU",
            "Batch läuft...",
        )
        self.log_card.log(
            f"Starte Batch-Verarbeitung: {waiting_jobs} Job(s)"
        )

        thread = threading.Thread(
            target=self._worker_batch,
            daemon=True,
        )
        thread.start()

    def cancel_processing(self):
        self.cancel_requested = True
        self.controller.scheduler.request_cancel()
        self.toolbar.disable_cancel_button()
        self.plugin_card.set_plugin(
            "RealESRGAN",
            "QNN / Snapdragon NPU",
            "Abbruch angefordert",
        )
        self.log_card.log(
            "Abbruch angefordert. Der aktuelle Job wird noch beendet."
        )

    def _worker_batch(self):
        try:
            results = self.controller.run_batch(
                on_job_start=self._on_worker_job_start,
                on_job_done=self._on_worker_job_done,
                on_job_error=self._on_worker_job_error,
            )

            self.log_queue.put(("batch_done", results))

        except Exception:
            self.log_queue.put(("batch_error", traceback.format_exc()))

    def _on_worker_job_start(self, job):
        self.log_queue.put(("job_start", job["input_path"]))

    def _on_worker_job_done(self, job, output_path):
        self.log_queue.put(
            ("job_done", (job["input_path"], output_path))
        )

    def _on_worker_job_error(self, job, error):
        self.log_queue.put(
            ("job_error", (job["input_path"], error))
        )

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

    def _update_runtime(self):
        if self.job_card.running:
            self.job_card.update_runtime()

        self.after(500, self._update_runtime)

    def _apply_progress(self):
        progress = self.controller.get_progress()

        self.job_card.set_batch_progress(
            progress["current"],
            progress["total"],
            progress["percent"],
        )

    def _update_status_bar(self):
        status = self.controller.get_engine_status()
        progress = status.get("progress", {})
        scheduler = status.get("scheduler", {})
        worker = status.get("worker", {})

        engine_status = scheduler.get("status", "idle")
        worker_status = worker.get("status", "idle")
        queue_count = status.get("waiting_jobs", 0)
        percent = progress.get("percent", 0)

        engine_status_label = {
            "idle": "Ready",
            "running": "Running",
            "paused": "Paused",
            "stopped": "Stopped",
            "cancel_requested": "Stopping",
        }.get(engine_status, engine_status)

        worker_status_label = {
            "idle": "Idle",
            "running": "Busy",
            "done": "Done",
            "error": "Error",
        }.get(worker_status, worker_status)

        self.status_bar.set_status(
            engine_status=engine_status_label,
            queue_count=queue_count,
            worker_status=worker_status_label,
            backend="QNN",
            percent=percent,
        )

        self.after(500, self._update_status_bar)

    def _poll_log_queue(self):
        try:
            while True:
                kind, value = self.log_queue.get_nowait()

                if kind == "job_start":
                    input_path = value

                    self.refresh_queue()
                    self.select_loaded_image(input_path)
                    self.job_card.start_job(
                        plugin="RealESRGAN",
                        backend="QNN / Snapdragon NPU",
                        input_path=input_path,
                    )
                    self._apply_progress()
                    self.plugin_card.set_plugin(
                        "RealESRGAN",
                        "QNN / Snapdragon NPU",
                        "Läuft...",
                    )
                    self.log_card.log(
                        f"Verarbeite: {Path(input_path).name}"
                    )

                elif kind == "job_done":
                    input_path, output_path = value

                    self.controller.set_last_output(output_path)
                    self.toolbar.enable_output_button()
                    self.job_card.finish_job(output_path)
                    self.thumbnail_gallery.add_image(output_path)
                    self.refresh_queue()
                    self.file_card.set_filename(output_path)
                    self.show_preview(output_path)
                    self._apply_progress()
                    self.log_card.log(
                        f"Fertig: {Path(input_path).name} -> "
                        f"{Path(output_path).name}"
                    )

                elif kind == "job_error":
                    input_path, error = value

                    self.job_card.fail_job()
                    self.refresh_queue()
                    self._apply_progress()
                    self.log_card.log(
                        f"Fehler bei: {Path(input_path).name}"
                    )
                    self.log_card.log(error)

                elif kind == "batch_done":
                    results = value

                    self.file_card.enable()
                    self.toolbar.enable_start_button()
                    self.toolbar.enable_select_button()
                    self.toolbar.disable_cancel_button()

                    if self.controller.get_last_output():
                        self.toolbar.enable_output_button()
                    else:
                        self.toolbar.disable_output_button()

                    self._apply_progress()

                    if self.cancel_requested:
                        status_text = "Batch abgebrochen"
                        log_text = (
                            f"Batch abgebrochen nach {len(results)} Job(s)."
                        )
                    else:
                        status_text = "Batch fertig"
                        log_text = (
                            f"Batch abgeschlossen: {len(results)} Job(s)"
                        )

                    self.plugin_card.set_plugin(
                        "RealESRGAN",
                        "QNN / Snapdragon NPU",
                        status_text,
                    )
                    self.refresh_queue()
                    self.log_card.log(log_text)

                elif kind == "batch_error":
                    self.file_card.enable()
                    self.toolbar.enable_start_button()
                    self.toolbar.enable_select_button()
                    self.toolbar.disable_cancel_button()
                    self.toolbar.disable_output_button()
                    self.plugin_card.set_plugin(
                        "RealESRGAN",
                        "QNN / Snapdragon NPU",
                        "Batch Fehler",
                    )
                    self.job_card.fail_job()
                    self.refresh_queue()
                    self._apply_progress()
                    self.log_card.log("BATCH-FEHLER:")
                    self.log_card.log(value)

        except queue.Empty:
            pass

        self.after(100, self._poll_log_queue)


if __name__ == "__main__":
    app = SnapdragonAIStudioV2()
    app.mainloop()