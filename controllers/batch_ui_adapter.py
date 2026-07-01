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