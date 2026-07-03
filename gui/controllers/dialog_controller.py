"""
Snapdragon AI Studio

Dialog Controller

Created by Holger Kreuzhofen
Phoenix UI
"""

from dialogs.plugin_manager import PluginManagerDialog
from dialogs.about_dialog import AboutDialog


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
        AboutDialog(self.app, self.app.brand)
