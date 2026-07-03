"""
Snapdragon AI Studio

Batch Runtime Adapter

Created by Holger Kreuzhofen
Phoenix UI
"""


class BatchRuntimeAdapter:
    """Adapter for batch runtime operations."""

    def __init__(self, app):
        self.app = app

    def get_waiting_job_count(self):
        return self.app.controller.get_waiting_job_count()

    def clear_last_output(self):
        self.app.controller.clear_last_output()

    def get_last_output(self):
        return self.app.controller.get_last_output()

    def get_last_output_directory(self):
        return self.app.controller.get_last_output_directory()

    def get_last_batch_count(self):
        return self.app.controller.get_last_batch_count()

    def set_last_output(self, output_path):
        self.app.controller.set_last_output(output_path)

    def get_progress(self):
        return self.app.controller.get_progress()

    def get_engine_status(self):
        return self.app.controller.get_engine_status()

    def set_queue_status(self, input_path, status, output_path=None):
        self.app.controller.set_queue_status(input_path, status, output_path)

    def request_cancel(self):
        self.app.controller.scheduler.request_cancel()

    def run_batch(
        self,
        on_job_start,
        on_job_done,
        on_job_error,
    ):
        return self.app.controller.run_batch(
            on_job_start=on_job_start,
            on_job_done=on_job_done,
            on_job_error=on_job_error,
        )


def create_batch_runtime_adapter(app) -> BatchRuntimeAdapter:
    """Creates the batch runtime adapter."""

    return BatchRuntimeAdapter(app)
