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

    def refresh_queue(self):
        self.app.refresh_queue()

    def select_loaded_image(self, input_path):
        self.app.select_loaded_image(input_path)


def create_application_adapter(app) -> ApplicationAdapter:
    """Creates the application adapter."""

    return ApplicationAdapter(app)