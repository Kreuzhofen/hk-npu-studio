"""
Snapdragon AI Studio

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


class LegacyBatchUIAdapter(BatchUIAdapter):
    """Adapter for the existing legacy UI widgets."""

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

    def show_image_pair(self, input_path, output_path):
        self.show_preview(output_path)


class PhoenixBatchUIAdapter(BatchUIAdapter):
    """Adapter for the Phoenix UI widgets."""

    def _actions(self):
        workspace = getattr(self.app, "phoenix_workspace", None)

        if workspace is None:
            return None

        return getattr(workspace, "actions", None)

    def _call_action(self, method_name):
        actions = self._actions()

        if actions is None:
            return

        method = getattr(actions, method_name, None)

        if callable(method):
            method()

    def _log_to_app(self, text):
        logger = getattr(self.app, "_log", None)

        if callable(logger):
            logger(text)
            return

        print(text)

    def enable_start_button(self):
        self._call_action("enable_start_button")

    def disable_start_button(self):
        self._call_action("disable_start_button")

    def enable_select_button(self):
        pass

    def disable_select_button(self):
        pass

    def enable_cancel_button(self):
        self._call_action("enable_cancel_button")

    def disable_cancel_button(self):
        self._call_action("disable_cancel_button")

    def enable_output_button(self):
        self._call_action("enable_output_button")

    def disable_output_button(self):
        self._call_action("disable_output_button")

    def set_plugin(self, name, backend, status):
        self._log_to_app(f"{name} | {backend} | {status}")

    def log(self, text):
        self._log_to_app(text)

    def is_job_running(self) -> bool:
        return False

    def update_runtime(self):
        pass

    def set_batch_progress(self, current, total, percent):
        pass

    def start_job(self, plugin, backend, input_path):
        self._log_to_app(f"Job gestartet: {input_path}")

    def finish_job(self, output_path):
        self._log_to_app(f"Job fertig: {output_path}")

    def fail_job(self):
        self._log_to_app("Job fehlgeschlagen.")

    def enable_file_card(self):
        pass

    def disable_file_card(self):
        pass

    def set_filename(self, path):
        pass

    def add_thumbnail_image(self, path):
        pass

    def show_preview(self, path):
        workspace = getattr(self.app, "phoenix_workspace", None)

        if workspace is None:
            return

        view = workspace._get_or_create_view("image")

        if hasattr(view, "show_output_image"):
            view.show_output_image(path)
        elif hasattr(view, "show_image"):
            view.show_image(path)

    def show_image_pair(self, input_path, output_path):
        workspace = getattr(self.app, "phoenix_workspace", None)

        if workspace is None:
            return

        if hasattr(workspace, "show_image_pair"):
            workspace.show_image_pair(input_path, output_path)
            return

        view = workspace._get_or_create_view("image")

        if hasattr(view, "show_image_pair"):
            view.show_image_pair(input_path, output_path)
        elif hasattr(view, "show_output_image"):
            view.show_output_image(output_path)


class DynamicBatchUIAdapter(BatchUIAdapter):
    """Delegates batch UI calls to the currently active UI."""

    def _target(self):
        if hasattr(self.app, "phoenix_workspace"):
            return PhoenixBatchUIAdapter(self.app)

        return LegacyBatchUIAdapter(self.app)

    def enable_start_button(self):
        self._target().enable_start_button()

    def disable_start_button(self):
        self._target().disable_start_button()

    def enable_select_button(self):
        self._target().enable_select_button()

    def disable_select_button(self):
        self._target().disable_select_button()

    def enable_cancel_button(self):
        self._target().enable_cancel_button()

    def disable_cancel_button(self):
        self._target().disable_cancel_button()

    def enable_output_button(self):
        self._target().enable_output_button()

    def disable_output_button(self):
        self._target().disable_output_button()

    def set_plugin(self, name, backend, status):
        self._target().set_plugin(name, backend, status)

    def log(self, text):
        self._target().log(text)

    def is_job_running(self) -> bool:
        return self._target().is_job_running()

    def update_runtime(self):
        self._target().update_runtime()

    def set_batch_progress(self, current, total, percent):
        self._target().set_batch_progress(current, total, percent)

    def start_job(self, plugin, backend, input_path):
        self._target().start_job(plugin, backend, input_path)

    def finish_job(self, output_path):
        self._target().finish_job(output_path)

    def fail_job(self):
        self._target().fail_job()

    def enable_file_card(self):
        self._target().enable_file_card()

    def disable_file_card(self):
        self._target().disable_file_card()

    def set_filename(self, path):
        self._target().set_filename(path)

    def add_thumbnail_image(self, path):
        self._target().add_thumbnail_image(path)

    def show_preview(self, path):
        self._target().show_preview(path)

    def show_image_pair(self, input_path, output_path):
        self._target().show_image_pair(input_path, output_path)


def create_batch_ui_adapter(app) -> BatchUIAdapter:
    """Creates the dynamic batch UI adapter."""

    return DynamicBatchUIAdapter(app)
