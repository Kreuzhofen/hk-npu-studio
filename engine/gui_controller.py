"""
Snapdragon AI Studio

GUI Controller

Created by Holger Kreuzhofen
Phoenix Controller Layer
"""

from pathlib import Path
from engine.file_utils import get_unique_filename

from PIL import Image, ImageOps

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
        self.last_output_directory = None
        self.last_batch_count = 0

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
        self.last_output_directory = None
        self.last_batch_count = 0

    def set_last_output(self, output_path):
        self.last_output = output_path

        if output_path:
            self.last_output_directory = str(Path(output_path).resolve().parent)

    def get_last_output(self):
        return self.last_output

    def get_last_output_directory(self):
        return self.last_output_directory

    def get_last_batch_count(self):
        return self.last_batch_count

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
        self.last_batch_count = 0

        results = self.scheduler.process_all_jobs(
            phoenix_queue=self.phoenix_queue,
            worker=self.worker,
            task=self._run_upscale_job,
            on_job_start=on_job_start,
            on_job_done=self._wrap_job_done(on_job_done),
            on_job_error=on_job_error,
        )

        self.last_batch_count = len(results)
        return results

    def _wrap_job_done(self, callback):
        def wrapped(job, output_path):
            self.set_last_output(output_path)

            if callback:
                callback(job, output_path)

        return wrapped

    def _run_upscale_job(self, job):
        result = self.adapter.run(
            "image.upscale",
            input_path=job["input_path"],
        )

        return self._make_unique_output_path(
            input_path=job["input_path"],
            output_path=result["output_path"],
        )

    def _make_unique_output_path(self, input_path, output_path):
        source_path = Path(output_path)

        if not source_path.exists():
            raise FileNotFoundError(source_path)

        self._match_output_orientation_to_original(input_path, source_path)

        target_path = self._build_unique_output_path(
            input_path=input_path,
            output_dir=source_path.parent,
        )

        if source_path.resolve() == target_path.resolve():
            return str(source_path)

        source_path.replace(target_path)
        return str(target_path)

    def _match_output_orientation_to_original(self, input_path, output_path):
        orientation = self._get_original_orientation(input_path)

        if orientation in (None, 1):
            return

        if self._output_matches_visible_orientation(input_path, output_path):
            return

        transpose_operation = {
            2: Image.Transpose.FLIP_LEFT_RIGHT,
            3: Image.Transpose.ROTATE_180,
            4: Image.Transpose.FLIP_TOP_BOTTOM,
            5: Image.Transpose.TRANSPOSE,
            6: Image.Transpose.ROTATE_270,
            7: Image.Transpose.TRANSVERSE,
            8: Image.Transpose.ROTATE_90,
        }.get(orientation)

        if transpose_operation is None:
            return

        with Image.open(output_path) as output_image:
            corrected_image = output_image.transpose(transpose_operation)
            corrected_image.save(output_path)

    def _output_matches_visible_orientation(self, input_path, output_path):
        try:
            with Image.open(input_path) as input_image:
                visible_input = ImageOps.exif_transpose(input_image)
                input_ratio = visible_input.width / visible_input.height

            with Image.open(output_path) as output_image:
                output_ratio = output_image.width / output_image.height

            return abs(input_ratio - output_ratio) < 0.01
        except Exception:
            return False

    def _get_original_orientation(self, input_path):
        try:
            with Image.open(input_path) as input_image:
                exif = input_image.getexif()
                return exif.get(274)
        except Exception:
            return None

    def _build_unique_output_path(self, input_path, output_dir):
        input_stem = Path(input_path).stem
        base_name = f"{input_stem}_upscaled.png"
        return get_unique_filename(output_dir, base_name)

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
