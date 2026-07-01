"""
SnapdragonAI Studio

Application Adapter

Created by Holger Kreuzhofen
Phoenix UI
"""


class ApplicationAdapter:
    """Adapter for application-level operations used by controllers."""

    def __init__(self, app):
        self.app = app

    def after(self, delay_ms, callback):
        self.app.after(delay_ms, callback)

    def refresh_queue(self):
        self.app.refresh_queue()

    def select_loaded_image(self, input_path):
        self.app.select_loaded_image(input_path)

    def set_status_bar(
        self,
        engine_status,
        queue_count,
        worker_status,
        backend,
        percent,
    ):
        self.app.status_bar.set_status(
            engine_status=engine_status,
            queue_count=queue_count,
            worker_status=worker_status,
            backend=backend,
            percent=percent,
        )


def create_application_adapter(app) -> ApplicationAdapter:
    """Creates the application adapter."""

    return ApplicationAdapter(app)