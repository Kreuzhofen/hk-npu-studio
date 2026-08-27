"""
HK NPU STUDIO

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
        BrandManager.apply_window_icon(self.app)
        
        # Load theme & language from preferences and initialize PHOENIX_THEME and locales
        from app.settings_manager import SettingsManager
        from widgets.phoenix.theme import update_phoenix_theme, PHOENIX_THEME
        from app.i18n import set_language
        
        prefs = SettingsManager.load_settings()
        
        # Theme
        theme_val = prefs.get("theme", "Dunkel")
        dark_theme_values = {"Dunkel", "Dark", "dark", "professional_dark"}
        update_phoenix_theme("dark" if theme_val in dark_theme_values else "light")
        
        # Language
        lang_val = prefs.get("language", "Deutsch")
        from app.i18n import LANGUAGE_CODES
        set_language(LANGUAGE_CODES.get(str(lang_val), "de_DE"))
        
        self.app.geometry("1400x900")
        self.app.configure(bg=PHOENIX_THEME.app_bg)

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

    def register_generated_asset(self, path) -> None:
        """Register a generated image in the existing AI Asset Library view."""
        if not hasattr(self.app, "phoenix_workspace"):
            return

        workspace = self.app.phoenix_workspace
        gallery_view = workspace._get_or_create_view("gallery")
        show_generated = getattr(gallery_view, "show_generated_image", None)
        if callable(show_generated):
            show_generated(str(path))

    def open_gallery_with_image(self, path) -> None:
        """Switch to the AI Asset Library and select the generated image."""
        if not hasattr(self.app, "phoenix_workspace"):
            return

        self.register_generated_asset(path)
        self.app.phoenix_workspace.show_view("gallery")

    def open_compare_with_image(self, path) -> None:
        """Switches to the Compare Workspace and loads the given path as the original image, clearing the output."""
        if not hasattr(self.app, "phoenix_workspace"):
            return

        workspace = self.app.phoenix_workspace
        compare_view = workspace._get_or_create_view("compare")

        if hasattr(compare_view, "controller") and compare_view.controller is not None:
            compare_view.controller.load_original(path)
            compare_view.controller.clear_output()

        workspace.show_view("compare")

    def open_compare_with_output(self, path) -> None:
        """Switch to the Compare Workspace and load a generated image as output."""
        if not hasattr(self.app, "phoenix_workspace"):
            return

        workspace = self.app.phoenix_workspace
        compare_view = workspace._get_or_create_view("compare")

        if hasattr(compare_view, "controller") and compare_view.controller is not None:
            compare_view.controller.load_output(path)

        workspace.show_view("compare")
