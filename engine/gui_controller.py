"""
SnapdragonAI Studio

GUI Controller

Created by Holger Kreuzhofen
Phoenix Controller Layer
"""

from pathlib import Path

from engine.import_service import ImportService
from engine.phoenix_adapter import PhoenixAdapter
from engine.phoenix_queue import PhoenixQueue
from engine.phoenix_scheduler import PhoenixScheduler
from engine.phoenix_worker import PhoenixWorker


class GuiController:

    def __init__(self):
        self.adapter = PhoenixAdapter()
        self.import_service = ImportService()

        self.scheduler = PhoenixScheduler()
        self.phoenix_queue = PhoenixQueue()
        self.worker = PhoenixWorker()

        self.loaded_images = []
        self.current_image = None
        self.last_output = None

    def is_supported_image(self, path):
        return self.import_service.is_supported_image(path)

    def load_image_files(self, filenames):
        result = self.import_service.import_files(filenames)
        return self._register_import_result(result)

    def load_image_folder(self, folder_path):
        result = self.import_service.import_folder(folder_path, recursive=True)
        return self._register_import_result(result)

    def _register_import_result(self, result):
        valid_files = result["valid_files"]

        for full_path in valid_files:
            if full_path not in self.loaded_images:
                self.loaded_images.append(full_path)

            self.add_to_queue(full_path)

        if valid_files:
            self.current_image = valid_files[0]

        return result

    def select_image(self, filename):
        path = Path(filename)

        if not path.exists():
            return False, "Datei nicht gefunden"

        if not self.is_supported_image(path):
            return False, "Nicht unterstütztes Bildformat"

        self.current_image = str(path.resolve())
        return True, self.current_image

    def get_current_image(self):
        return self.current_image

    def clear_last_output(self):
        self.last_output = None

    def set_last_output(self, output_path):
        self.last_output = output_path

    def get_last_output(self):
        return self.last_output

    def add_to_queue(self, input_path):
        full_path = str(Path(input_path).resolve())

        for job in self.phoenix_queue.get_jobs():
            if job["input_path"] == full_path:
                return

        self.phoenix_queue.enqueue(
            {
                "input_path": full_path,
                "output_path": None,
                "status": "wartet",
            }
        )

    def get_queue(self):
        return self.phoenix_queue.get_jobs()

    def get_waiting_job_count(self):
        count = 0

        for job in self.phoenix_queue.get_jobs():
            if job.get("status") == "wartet":
                count += 1

        return count

    def set_queue_status(self, input_path, status, output_path=None):
        full_path = str(Path(input_path).resolve())

        for job in self.phoenix_queue.get_jobs():
            if job["input_path"] == full_path:
                job["status"] = status

                if output_path:
                    job["output_path"] = output_path

                return

    def get_queue_job(self, input_path):
        full_path = str(Path(input_path).resolve())

        for job in self.phoenix_queue.get_jobs():
            if job["input_path"] == full_path:
                return job

        return None

    def run_batch(
        self,
        on_job_start=None,
        on_job_done=None,
        on_job_error=None,
    ):
        results = self.scheduler.process_all_jobs(
            phoenix_queue=self.phoenix_queue,
            worker=self.worker,
            task=self._run_upscale_job,
            on_job_start=on_job_start,
            on_job_done=self._wrap_job_done(on_job_done),
            on_job_error=on_job_error,
        )

        return results

    def _wrap_job_done(self, callback):
        def wrapped(job, output_path):
            self.last_output = output_path

            if callback:
                callback(job, output_path)

        return wrapped

    def _run_upscale_job(self, job):
        result = self.adapter.run(
            "image.upscale",
            input_path=job["input_path"],
        )

        return result["output_path"]

    def get_progress(self):
        return self.scheduler.get_progress()

    def get_engine_status(self):
        return {
            "scheduler": self.scheduler.get_status(),
            "worker": self.worker.get_status(),
            "queue_size": self.phoenix_queue.size(),
            "waiting_jobs": self.get_waiting_job_count(),
            "queue": self.phoenix_queue.get_jobs(),
            "progress": self.get_progress(),
        }