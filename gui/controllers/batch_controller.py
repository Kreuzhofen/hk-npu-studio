"""
Snapdragon AI Studio

Batch Controller

Created by Holger Kreuzhofen
Phoenix UI
"""

import queue
import threading
import traceback
from pathlib import Path

from controllers.application_adapter import create_application_adapter
from controllers.batch_runtime_adapter import create_batch_runtime_adapter
from controllers.batch_ui_adapter import create_batch_ui_adapter
from engine.batch_state_machine import BatchStateMachine


class BatchController:
    """Controls batch processing and runtime UI updates for the GUI."""

    PLUGIN_NAME = "Nicht verbunden"
    BACKEND_NAME = "Noch keine Engine aktiv"
    STATUS_BACKEND_NAME = "Stub"

    def __init__(self, app):
        self.application = create_application_adapter(app)
        self.runtime = create_batch_runtime_adapter(app)
        self.ui = create_batch_ui_adapter(app)
        self.log_queue = queue.Queue()
        self.state_machine = BatchStateMachine()
        self.cancel_requested = False
        self.current_job_path = None
        self.activity_log = []
        self.deferred_gallery_jobs = []

    def start_polling(self):
        self.application.after(100, self._poll_log_queue)
        self.application.after(500, self._update_runtime)
        self.application.after(500, self._update_status_bar)

    def get_batch_state(self):
        return self.state_machine.get_state()

    def get_batch_last_error(self):
        return self.state_machine.get_last_error()

    def can_start_batch(self):
        return self.state_machine.can_start()

    def can_stop_batch(self):
        return self.state_machine.can_stop()

    def is_batch_busy(self):
        return self.state_machine.is_busy()

    def _append_activity(self, message):
        self.activity_log.append(message)
        self.activity_log = self.activity_log[-20:]

    def get_dashboard_snapshot(self):
        """Return a read-only snapshot for the Phoenix dashboard."""
        status = self.runtime.get_engine_status()
        progress = status.get("progress", {})
        scheduler = status.get("scheduler", {})
        worker = status.get("worker", {})

        batch_state = self.state_machine.get_state()
        waiting_jobs = status.get("waiting_jobs", 0)

        current = progress.get("current", 0)
        total = progress.get("total", 0)
        percent = progress.get("percent", 0)

        scheduler_status = scheduler.get("status", "idle")
        worker_status = worker.get("status", "idle")
        last_output = self.runtime.get_last_output()

        batch_label = {
            "idle": "Bereit",
            "ready": "Bereit",
            "running": "Läuft",
            "stopping": "Stoppt",
            "finished": "Abgeschlossen",
            "error": "Fehler",
        }.get(batch_state, str(batch_state))

        lifecycle_label = {
            "idle": "Idle",
            "running": "Running",
            "paused": "Paused",
            "stopped": "Stopped",
            "cancel_requested": "Stopping",
        }.get(scheduler_status, str(scheduler_status))

        worker_label = {
            "idle": "Worker idle",
            "running": "Worker aktiv",
            "done": "Worker fertig",
            "error": "Worker Fehler",
        }.get(worker_status, str(worker_status))

        output_label = "Kein Output ausgewählt"
        if last_output:
            output_label = Path(last_output).name

        if self.current_job_path:
            current_job = Path(self.current_job_path).name
        else:
            current_job = "Kein aktiver Job"

        if waiting_jobs:
            queue_label = f"Queue: {waiting_jobs} wartend"
        else:
            queue_label = "Queue leer"

        detail = (
            f"{queue_label} · "
            f"Fortschritt: {current}/{total} ({percent}%) · "
            f"{worker_label}"
        )

        return {
            "workspace_status": "Aktiv",
            "batch_status": batch_label,
            "lifecycle_status": lifecycle_label,
            "output_status": output_label,
            "detail": detail,
            "current": current,
            "total": total,
            "percent": percent,
            "worker_status": worker_label,
            "waiting_jobs": waiting_jobs,
            "current_job": current_job,
            "last_output": output_label,
            "plugin": self.PLUGIN_NAME,
            "backend": self.BACKEND_NAME,
            "activity": list(self.activity_log),
        }

    def start_plugin(self):
        if not self.state_machine.can_start():
            self.ui.log(
                f"Batch kann im aktuellen Zustand nicht gestartet werden: "
                f"{self.state_machine.get_state()}"
            )
            return

        self._prepare_gallery_selection_batch()
        waiting_jobs = self.runtime.get_waiting_job_count()

        if waiting_jobs <= 0:
            self.state_machine.reset()
            self.ui.log("Keine wartenden Jobs in der Queue.")
            return

        self.state_machine.set_ready()
        self.state_machine.start()

        self.cancel_requested = False
        self.current_job_path = None
        self.runtime.clear_last_output()
        self.ui.disable_output_button()
        self.ui.disable_start_button()
        self.ui.disable_select_button()
        self.ui.enable_cancel_button()
        self.ui.disable_file_card()

        self.ui.set_batch_progress(0, waiting_jobs, 0)

        self.ui.set_plugin(
            self.PLUGIN_NAME,
            self.BACKEND_NAME,
            "Batch läuft...",
        )
        self._append_activity("Batch gestartet")
        self.ui.log(f"Starte Batch-Verarbeitung: {waiting_jobs} Job(s)")

        thread = threading.Thread(
            target=self._worker_batch,
            daemon=True,
        )
        thread.start()

    def cancel_processing(self):
        if not self.state_machine.can_stop():
            self.ui.log(
                f"Abbruch ist im aktuellen Zustand nicht möglich: "
                f"{self.state_machine.get_state()}"
            )
            return

        self.cancel_requested = True
        self.state_machine.request_stop()
        self.runtime.request_cancel()
        self.ui.disable_cancel_button()
        self.ui.set_plugin(
            self.PLUGIN_NAME,
            self.BACKEND_NAME,
            "Abbruch angefordert",
        )
        self.ui.log("Abbruch angefordert. Der aktuelle Job wird noch beendet.")

    def _prepare_gallery_selection_batch(self):
        self.deferred_gallery_jobs = []
        selected_image = self.application.get_selected_gallery_image()

        if not selected_image:
            return

        selected_path = str(Path(selected_image).resolve())
        status = self.runtime.get_engine_status()
        queue = status.get("queue", [])
        selected_found = False

        for job in queue:
            input_path = job.get("input_path")

            if not input_path:
                continue

            resolved_input = str(Path(input_path).resolve())

            if resolved_input == selected_path:
                selected_found = True
                if job.get("status") != "wartet":
                    self.runtime.set_queue_status(input_path, "wartet")
                continue

            if job.get("status") == "wartet":
                self.runtime.set_queue_status(input_path, "zurückgestellt")
                self.deferred_gallery_jobs.append(input_path)

        if selected_found:
            self.ui.log(f"Gallery-Auswahl aktiv: {Path(selected_path).name}")

    def _restore_deferred_gallery_jobs(self):
        for input_path in self.deferred_gallery_jobs:
            self.runtime.set_queue_status(input_path, "wartet")

        self.deferred_gallery_jobs = []
        self.application.clear_gallery_selection()

    def _worker_batch(self):
        try:
            results = self.runtime.run_batch(
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
        self.log_queue.put(("job_done", (job["input_path"], output_path)))

    def _on_worker_job_error(self, job, error):
        self.log_queue.put(("job_error", (job["input_path"], error)))

    def _update_runtime(self):
        if self.state_machine.is_busy() or self.ui.is_job_running():
            self.ui.update_runtime()

        self.application.after(500, self._update_runtime)

    def _apply_progress(self):
        progress = self.runtime.get_progress()
        self.ui.set_batch_progress(
            progress["current"],
            progress["total"],
            progress["percent"],
        )

    def _update_status_bar(self):
        status = self.runtime.get_engine_status()
        progress = status.get("progress", {})
        scheduler = status.get("scheduler", {})
        worker = status.get("worker", {})

        engine_status = scheduler.get("status", "idle")
        worker_status = worker.get("status", "idle")
        queue_count = status.get("waiting_jobs", 0)
        percent = progress.get("percent", 0)
        batch_state = self.state_machine.get_state()

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

        if batch_state == "running":
            engine_status_label = "Running"
        elif batch_state == "stopping":
            engine_status_label = "Stopping"
        elif batch_state == "finished":
            engine_status_label = "Finished"
        elif batch_state == "error":
            engine_status_label = "Error"

        self.application.set_status_bar(
            engine_status=engine_status_label,
            queue_count=queue_count,
            worker_status=worker_status_label,
            backend=self.STATUS_BACKEND_NAME,
            percent=percent,
        )

        self.application.after(500, self._update_status_bar)

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

        self.application.after(100, self._poll_log_queue)

    def _handle_job_start(self, input_path):
        self.current_job_path = input_path
        self._append_activity(f"Job gestartet: {Path(input_path).name}")
        self.application.refresh_queue()
        if not self.ui.is_phoenix():
            self.application.select_loaded_image(input_path)
        self.ui.start_job(
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
        self.ui.log(f"Verarbeite: {Path(input_path).name}")

    def _handle_job_done(self, value):
        input_path, output_path = value

        self.runtime.set_last_output(output_path)
        self._append_activity(f"Job fertig: {Path(input_path).name}")
        self.ui.enable_output_button()
        self.ui.finish_job(output_path)
        self.ui.add_thumbnail_image(output_path)
        self.application.refresh_queue()
        self.ui.set_filename(output_path)
        self.ui.show_image_pair(input_path, output_path)
        self._apply_progress()
        self.ui.log(
            f"Fertig: {Path(input_path).name} -> "
            f"{Path(output_path).name}"
        )

    def _handle_job_error(self, value):
        input_path, error = value

        self.ui.fail_job()
        self.application.refresh_queue()
        self._apply_progress()
        self.ui.log(f"Fehler bei: {Path(input_path).name}")
        self.ui.log(error)

    def _handle_batch_done(self, results):
        self.state_machine.finish()
        self.current_job_path = None
        self._restore_deferred_gallery_jobs()

        self.ui.enable_file_card()
        self.ui.enable_start_button()
        self.ui.enable_select_button()
        self.ui.disable_cancel_button()

        if self.runtime.get_last_output():
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
        self._append_activity("Batch abgeschlossen")
        self.application.refresh_queue()
        self.ui.log(log_text)

    def _handle_batch_error(self, value):
        self.state_machine.fail(value)
        self.current_job_path = None
        self._restore_deferred_gallery_jobs()
        self._append_activity("Batch Fehler")

        self.ui.enable_file_card()
        self.ui.enable_start_button()
        self.ui.enable_select_button()
        self.ui.disable_cancel_button()
        self.ui.disable_output_button()
        self.ui.set_plugin(
            self.PLUGIN_NAME,
            self.BACKEND_NAME,
            "Batch Fehler",
        )
        self.ui.fail_job()
        self.application.refresh_queue()
        self._apply_progress()
        self.ui.log("BATCH-FEHLER:")
        self.ui.log(value)
