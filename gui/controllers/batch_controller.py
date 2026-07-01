"""
SnapdragonAI Studio

Batch Controller

Created by Holger Kreuzhofen
Phoenix UI
"""

import queue
import threading
import traceback
from pathlib import Path

from controllers.batch_ui_adapter import create_batch_ui_adapter


class BatchController:
    """Controls batch processing and runtime UI updates for the GUI."""

    PLUGIN_NAME = "RealESRGAN"
    BACKEND_NAME = "QNN / Snapdragon NPU"
    STATUS_BACKEND_NAME = "QNN"

    def __init__(self, app):
        self.app = app
        self.ui = create_batch_ui_adapter(app)
        self.log_queue = queue.Queue()
        self.cancel_requested = False

    def start_polling(self):
        self.app.after(100, self._poll_log_queue)
        self.app.after(500, self._update_runtime)
        self.app.after(500, self._update_status_bar)

    def start_plugin(self):
        waiting_jobs = self.app.controller.get_waiting_job_count()

        if waiting_jobs <= 0:
            self.ui.log("Keine wartenden Jobs in der Queue.")
            return

        self.cancel_requested = False
        self.app.controller.clear_last_output()
        self.ui.disable_output_button()
        self.ui.disable_start_button()
        self.ui.disable_select_button()
        self.ui.enable_cancel_button()
        self.app.file_card.disable()

        self.app.job_card.set_batch_progress(0, waiting_jobs, 0)

        self.ui.set_plugin(
            self.PLUGIN_NAME,
            self.BACKEND_NAME,
            "Batch läuft...",
        )
        self.ui.log(
            f"Starte Batch-Verarbeitung: {waiting_jobs} Job(s)"
        )

        thread = threading.Thread(
            target=self._worker_batch,
            daemon=True,
        )
        thread.start()

    def cancel_processing(self):
        self.cancel_requested = True
        self.app.controller.scheduler.request_cancel()
        self.ui.disable_cancel_button()
        self.ui.set_plugin(
            self.PLUGIN_NAME,
            self.BACKEND_NAME,
            "Abbruch angefordert",
        )
        self.ui.log(
            "Abbruch angefordert. Der aktuelle Job wird noch beendet."
        )

    def _worker_batch(self):
        try:
            results = self.app.controller.run_batch(
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

    def _update_runtime(self):
        if self.app.job_card.running:
            self.app.job_card.update_runtime()

        self.app.after(500, self._update_runtime)

    def _apply_progress(self):
        progress = self.app.controller.get_progress()

        self.app.job_card.set_batch_progress(
            progress["current"],
            progress["total"],
            progress["percent"],
        )

    def _update_status_bar(self):
        status = self.app.controller.get_engine_status()
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

        self.app.status_bar.set_status(
            engine_status=engine_status_label,
            queue_count=queue_count,
            worker_status=worker_status_label,
            backend=self.STATUS_BACKEND_NAME,
            percent=percent,
        )

        self.app.after(500, self._update_status_bar)

    def _poll_log_queue(self):
        try:
            while True:
                kind, value = self.log_queue.get_nowait()

                if kind == "job_start":
                    self._handle_job_start(value)

                elif kind == "job_done":
                    self._handle_job_done(value)

                elif kind == "job_error":
                    self._handle_job_error(value)

                elif kind == "batch_done":
                    self._handle_batch_done(value)

                elif kind == "batch_error":
                    self._handle_batch_error(value)

        except queue.Empty:
            pass

        self.app.after(100, self._poll_log_queue)

    def _handle_job_start(self, input_path):
        self.app.refresh_queue()
        self.app.select_loaded_image(input_path)
        self.app.job_card.start_job(
            plugin=self.PLUGIN_NAME,
            backend=self.BACKEND_NAME,
            input_path=input_path,
        )
        self._apply_progress()
        self.ui.set_plugin(
            self.PLUGIN_NAME,
            self.BACKEND_NAME,
            "Läuft...",
        )
        self.ui.log(
            f"Verarbeite: {Path(input_path).name}"
        )

    def _handle_job_done(self, value):
        input_path, output_path = value

        self.app.controller.set_last_output(output_path)
        self.ui.enable_output_button()
        self.app.job_card.finish_job(output_path)
        self.app.thumbnail_gallery.add_image(output_path)
        self.app.refresh_queue()
        self.app.file_card.set_filename(output_path)
        self.app.show_preview(output_path)
        self._apply_progress()
        self.ui.log(
            f"Fertig: {Path(input_path).name} -> "
            f"{Path(output_path).name}"
        )

    def _handle_job_error(self, value):
        input_path, error = value

        self.app.job_card.fail_job()
        self.app.refresh_queue()
        self._apply_progress()
        self.ui.log(
            f"Fehler bei: {Path(input_path).name}"
        )
        self.ui.log(error)

    def _handle_batch_done(self, results):
        self.app.file_card.enable()
        self.ui.enable_start_button()
        self.ui.enable_select_button()
        self.ui.disable_cancel_button()

        if self.app.controller.get_last_output():
            self.ui.enable_output_button()
        else:
            self.ui.disable_output_button()

        self._apply_progress()

        if self.cancel_requested:
            status_text = "Batch abgebrochen"
            log_text = f"Batch abgebrochen nach {len(results)} Job(s)."
        else:
            status_text = "Batch fertig"
            log_text = f"Batch abgeschlossen: {len(results)} Job(s)"

        self.ui.set_plugin(
            self.PLUGIN_NAME,
            self.BACKEND_NAME,
            status_text,
        )
        self.app.refresh_queue()
        self.ui.log(log_text)

    def _handle_batch_error(self, value):
        self.app.file_card.enable()
        self.ui.enable_start_button()
        self.ui.enable_select_button()
        self.ui.disable_cancel_button()
        self.ui.disable_output_button()
        self.ui.set_plugin(
            self.PLUGIN_NAME,
            self.BACKEND_NAME,
            "Batch Fehler",
        )
        self.app.job_card.fail_job()
        self.app.refresh_queue()
        self._apply_progress()
        self.ui.log("BATCH-FEHLER:")
        self.ui.log(value)

    def _is_phoenix(self) -> bool:
        """Returns True when the Phoenix UI is active."""
        return hasattr(self.app, "phoenix_workspace")