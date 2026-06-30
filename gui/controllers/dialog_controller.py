"""
SnapdragonAI Studio

Dialog Controller

Created by Holger Kreuzhofen
Phoenix UI
"""

from dialogs.plugin_manager import PluginManagerDialog

try:
    from dialogs.about_dialog import AboutDialog
    ABOUT_DIALOG_AVAILABLE = True
except ImportError:
    AboutDialog = None
    ABOUT_DIALOG_AVAILABLE = False


class DialogController:
    """
    Central controller for all secondary GUI dialogs.

    The main window delegates dialog creation to this controller so gui_v2.py
    remains focused on application startup, controller wiring and event routing.
    """

    def __init__(self, app):
        self.app = app

    def open_plugin_manager(self):
        PluginManagerDialog(self.app)

    def open_about_dialog(self):
        if ABOUT_DIALOG_AVAILABLE:
            AboutDialog(self.app)
            return

        if hasattr(self.app, "log_card"):
            self.app.log_card.log("About-Dialog ist noch nicht verfügbar.")
