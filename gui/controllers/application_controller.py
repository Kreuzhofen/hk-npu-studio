"""
Snapdragon AI Studio

Application Controller

Created by Holger Kreuzhofen
Phoenix UI
"""

from engine.brand_manager import BrandManager
from engine.gui_controller import GuiController
from resources.theme import Theme
from gui.ui_mode import UIMode
from gui.controllers.batch_controller import BatchController
from gui.controllers.dialog_controller import DialogController
from gui.controllers.import_controller import ImportController
from gui.controllers.ui_builder import UIBuilder
from widgets.startup_overlay import StartupOverlay


class ApplicationController:
    """
    Coordinates application startup and high-level controller wiring.
    """

    def __init__(self, app, dnd_available=False, dnd_files=None):
        self.app = app
        self.dnd_available = dnd_available
        self.dnd_files = dnd_files
        self.ui_mode = UIMode.PHOENIX

    def initialize(self):
        self._initialize_branding()
        self._configure_main_window()
        self._create_controllers()
        self._initialize_runtime_state()
        self._build_ui()
        self._setup_drag_and_drop()
        self._show_startup_overlay()
        self.app.deiconify()
        self._start_runtime_polling()

    def _initialize_branding(self):
        self.app.brand = BrandManager()
        self.app.brand.initialize()

    def _configure_main_window(self):
        self.app.title(self.app.brand.window_title())
        if BrandManager.APP_ICON.exists():
            try:
                self.app.iconbitmap(str(BrandManager.APP_ICON))
            except Exception:
                pass
        self.app.geometry("1400x900")
        self.app.configure(bg=Theme.color("background"))

    def _create_controllers(self):
        self.app.controller = GuiController()
        self.app.import_controller = ImportController(self.app)
        self.app.batch_controller = BatchController(self.app)
        self.app.dialog_controller = DialogController(self.app)

    def _initialize_runtime_state(self):
        self.app.preview_image = None
        self.app.startup_overlay = None

    def _build_ui(self):
        builder = UIBuilder(
            self.app,
            dnd_available=self.dnd_available,
            ui_mode=self.ui_mode,
        )
        builder.build()

    def _show_startup_overlay(self):
        self.app.startup_overlay = StartupOverlay(self.app, self.app.brand)
        self.app.startup_overlay.show()
        self.app.after(1600, self.app.startup_overlay.fade_out)

    def _setup_drag_and_drop(self):
        if not self.dnd_available:
            return

        if self.ui_mode is not UIMode.LEGACY:
            return

        drop_targets = [
            self.app,
            self.app.file_card,
            self.app.preview_card,
            self.app.thumbnail_gallery,
            self.app.queue_card,
        ]

        for target in drop_targets:
            target.drop_target_register(self.dnd_files)
            target.dnd_bind("<<Drop>>", self.app.on_drop_file)

    def _start_runtime_polling(self):
        self.app.batch_controller.start_polling()
