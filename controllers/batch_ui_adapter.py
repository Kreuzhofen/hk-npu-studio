"""
SnapdragonAI Studio

Batch UI Adapter

Created by Holger Kreuzhofen
Phoenix UI
"""

class BatchUIAdapter:
    """Base interface for batch UI adapters."""

    def __init__(self, app):
        self.app = app

    def is_phoenix(self) -> bool:
        return hasattr(self.app, "phoenix_workspace")

    def enable_start_button(self):
        self.app.toolbar.enable_start_button()

    def disable_start_button(self):
        self.app.toolbar.disable_start_button()

    def enable_select_button(self):
        self.app.toolbar.enable_select_button()

    def disable_select_button(self):
        self.app.toolbar.disable_select_button()

    def enable_cancel_button(self):
        self.app.toolbar.enable_cancel_button()

    def disable_cancel_button(self):
        self.app.toolbar.disable_cancel_button()

    def enable_output_button(self):
        self.app.toolbar.enable_output_button()

    def disable_output_button(self):
        self.app.toolbar.disable_output_button()

    def set_plugin(self, name, backend, status):
        self.app.plugin_card.set_plugin(name, backend, status)

    def log(self, text):
        self.app.log_card.log(text)

    def is_job_running(self) -> bool:
        return self.app.job_card.running

    def update_runtime(self):
        self.app.job_card.update_runtime()

    def set_batch_progress(self, current, total, percent):
        self.app.job_card.set_batch_progress(current, total, percent)

    def start_job(self, plugin, backend, input_path):
        self.app.job_card.start_job(
            plugin=plugin,
            backend=backend,
            input_path=input_path,
        )

    def finish_job(self, output_path):
        self.app.job_card.finish_job(output_path)

    def fail_job(self):
        self.app.job_card.fail_job()

    def enable_file_card(self):
        self.app.file_card.enable()

    def disable_file_card(self):
        self.app.file_card.disable()

    def set_filename(self, path):
        self.app.file_card.set_filename(path)

    def add_thumbnail_image(self, path):
        self.app.thumbnail_gallery.add_image(path)

    def show_preview(self, path):
        self.app.show_preview(path)


class LegacyBatchUIAdapter(BatchUIAdapter):
    """Adapter for the existing legacy UI widgets."""

    pass


class PhoenixBatchUIAdapter(BatchUIAdapter):
    """Adapter for the Phoenix UI widgets."""

    pass


def create_batch_ui_adapter(app) -> BatchUIAdapter:
    """Creates the correct batch UI adapter for the active UI."""

    if hasattr(app, "phoenix_workspace"):
        return PhoenixBatchUIAdapter(app)

    return LegacyBatchUIAdapter(app)