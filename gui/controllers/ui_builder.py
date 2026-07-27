"""
Snapdragon AI Studio

UI Builder for GUI Version 2

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk

from gui.ui_mode import UIMode
from resources.theme import Theme
from widgets.header import Header
from widgets.menu_bar import MenuBar
from widgets.toolbar import Toolbar
from widgets.file_card import FileCard
from widgets.preview_card import PreviewCard
from widgets.log_card import LogCard
from widgets.plugin_card import PluginCard
from widgets.job_card import JobCard
from widgets.thumbnail_gallery import ThumbnailGallery
from widgets.queue_card import QueueCard
from widgets.status_bar import StatusBar


class UIBuilder:
    """Builds the active Snapdragon AI Studio V2 user interface."""

    def __init__(self, app, dnd_available=False, ui_mode=UIMode.LEGACY):
        self.app = app
        self.dnd_available = dnd_available
        self.ui_mode = ui_mode

    def build(self):
        self._build_menu_bar()

        if self.ui_mode is UIMode.PHOENIX:
            self._build_phoenix_ui()
            return

        self._build_main_layout()
        self._log_runtime_capabilities()

    def _build_legacy_ui(self):
        self._build_menu_bar()
        self._build_main_layout()
        self._log_runtime_capabilities()

    def _build_phoenix_ui(self):
        from widgets.phoenix.workspace import PhoenixWorkspace
        from controllers.workflow_controller import WorkflowController

        self.app.phoenix_workspace = PhoenixWorkspace(
            self.app,
            controller=getattr(self.app, "batch_controller", None),
        )
        self.app.phoenix_workspace.pack(fill="both", expand=True)

        self.app.workflow_controller = WorkflowController(
            app=self.app,
            workspace=self.app.phoenix_workspace
        )

    def _build_menu_bar(self):
        self.app.menu_bar = MenuBar(
            self.app,
            callbacks={
                "open_output_dir": self.app.open_output_dir,
                "open_models_dir": self.app.open_models_dir,
                "exit": self.app.exit_app,
                "clear_cache": self.app.clear_cache,
                "hardware_info": self.app.hardware_info,
                "toggle_fullscreen": self.app.toggle_fullscreen,
                "toggle_sidebar": self.app.toggle_sidebar,
                "manage_plugins": self.app.manage_plugins,
                "open_plugins_dir": self.app.open_plugins_dir,
                "show_log": self.app.show_log,
                "about": self.app.open_about_dialog,
            },
        )

    def _build_main_layout(self):
        main = tk.Frame(
            self.app,
            bg=Theme.color("background"),
        )
        main.pack(
            fill="both",
            expand=True,
            padx=Theme.spacing("window_pad"),
            pady=Theme.spacing("window_pad"),
        )

        self.app.header = Header(main, self.app.brand)
        self.app.header.pack(fill="x")

        self.app.toolbar = Toolbar(
            main,
            on_select_images=self.app.select_images,
            on_select_folder=self.app.select_folder,
            on_start=self.app.start_plugin,
            on_cancel=self.app.cancel_processing,
            on_open_output=self.app.open_output,
            on_open_plugin_manager=self.app.open_plugin_manager,
        )
        self.app.toolbar.pack(fill="x", pady=(Theme.spacing("medium"), 0))

        top = tk.Frame(
            main,
            bg=Theme.color("background"),
        )
        top.pack(fill="x", pady=(Theme.spacing("large"), 0))

        self.app.file_card = FileCard(top)
        self.app.file_card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, Theme.spacing("medium")),
        )

        self.app.plugin_card = PluginCard(top)
        self.app.plugin_card.pack(
            side="left",
            fill="both",
        )

        self.app.plugin_card.set_plugin(
            "RealESRGAN",
            "QNN / Snapdragon NPU",
            "Bereit",
        )

        self.app.job_card = JobCard(main)
        self.app.job_card.pack(
            fill="x",
            pady=(Theme.spacing("large"), 0),
        )

        content = tk.Frame(
            main,
            bg=Theme.color("background"),
        )
        content.pack(
            fill="both",
            expand=True,
            pady=Theme.spacing("large"),
        )

        preview_area = tk.Frame(
            content,
            bg=Theme.color("background"),
        )
        preview_area.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, Theme.spacing("medium")),
        )

        self.app.preview_card = PreviewCard(preview_area)
        self.app.preview_card.pack(
            fill="both",
            expand=True,
        )

        side_area = tk.Frame(
            content,
            width=330,
            bg=Theme.color("background"),
        )
        side_area.pack(
            side="right",
            fill="y",
        )
        side_area.pack_propagate(False)

        self.app.thumbnail_gallery = ThumbnailGallery(
            side_area,
            on_select=self.app.select_loaded_image,
            max_items=50,
        )
        self.app.thumbnail_gallery.pack(
            fill="both",
            expand=True,
            pady=(0, Theme.spacing("medium")),
        )

        self.app.queue_card = QueueCard(
            side_area,
            on_select=self.app.select_loaded_image,
        )
        self.app.queue_card.pack(
            fill="both",
            expand=True,
        )

        self.app.log_card = LogCard(main)
        self.app.log_card.pack(fill="x", pady=(0, Theme.spacing("medium")))

        self.app.status_bar = StatusBar(main)
        self.app.status_bar.pack(fill="x")

    def _log_runtime_capabilities(self):
        if self.dnd_available:
            self.app.log_card.log("Drag & Drop ist verfügbar.")
        else:
            self.app.log_card.log(
                "Drag & Drop nicht verfügbar. "
                "Installiere optional: pip install tkinterdnd2"
            )

    def _log_not_available(self):
        if hasattr(self.app, "log_card"):
            self.app.log_card.log("Diese Funktion ist noch nicht verfügbar.")
