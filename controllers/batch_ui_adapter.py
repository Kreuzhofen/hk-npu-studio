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