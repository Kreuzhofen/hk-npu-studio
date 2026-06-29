"""
SnapdragonAI Studio

UI Builder for GUI Version 2

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk

from resources.theme import Theme
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
    """Builds the main SnapdragonAI Studio V2 user interface.

    This class contains only widget construction and layout wiring.
    Application behavior stays in SnapdragonAIStudioV2.
    """

    def __init__(self, app, dnd_available=False):
        self.app = app
        self.dnd_available = dnd_available


    def _build_menu(self):
        menubar = tk.Menu(self.app)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Bilder öffnen...", command=self.app.select_images)
        file_menu.add_command(label="Ordner öffnen...", command=self.app.select_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.app.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        studio_menu = tk.Menu(menubar, tearoff=False)
        studio_menu.add_command(label="Start", command=self.app.start_plugin)
        studio_menu.add_command(label="Stop", command=self.app.cancel_processing)
        studio_menu.add_separator()
        studio_menu.add_command(label="Output öffnen", command=self.app.open_output)
        menubar.add_cascade(label="Studio", menu=studio_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="Queue aktualisieren", command=self.app.refresh_queue)
        menubar.add_cascade(label="View", menu=view_menu)

        plugins_menu = tk.Menu(menubar, tearoff=False)
        plugins_menu.add_command(label="Plugin Manager", command=self.app.open_plugin_manager)
        menubar.add_cascade(label="Plugins", menu=plugins_menu)

        tools_menu = tk.Menu(menubar, tearoff=False)
        tools_menu.add_command(label="Output öffnen", command=self.app.open_output)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Info", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.app.config(menu=menubar)

    def _show_about(self):
        about = tk.Toplevel(self.app)
        about.title("About SnapdragonAI Studio")
        about.configure(bg=Theme.color("background"))
        about.resizable(False, False)
        about.transient(self.app)
        about.grab_set()

        label = tk.Label(
            about,
            text=(
                "SnapdragonAI Studio 2.0\n"
                "Phoenix Engine\n"
                "Created by Holger Kreuzhofen\n"
                "© 2026 Holger Kreuzhofen"
            ),
            bg=Theme.color("background"),
            fg=Theme.color("text"),
            padx=24,
            pady=18,
            justify="center",
        )
        label.pack(fill="both", expand=True)

        button = tk.Button(about, text="OK", command=about.destroy, width=12)
        button.pack(pady=(0, 16))

        about.update_idletasks()
        x = self.app.winfo_rootx() + (self.app.winfo_width() // 2) - (about.winfo_width() // 2)
        y = self.app.winfo_rooty() + (self.app.winfo_height() // 2) - (about.winfo_height() // 2)
        about.geometry(f"+{x}+{y}")

    def build(self):
        self._build_menu()

        main = tk.Frame(
            self.app,
            bg=Theme.color("background"),
        )
        main.pack(fill="both", expand=True, padx=10, pady=10)

        self.app.toolbar = Toolbar(
            main,
            on_select_images=self.app.select_images,
            on_select_folder=self.app.select_folder,
            on_start=self.app.start_plugin,
            on_cancel=self.app.cancel_processing,
            on_open_output=self.app.open_output,
            on_open_plugin_manager=self.app.open_plugin_manager,
        )
        self.app.toolbar.pack(fill="x")

        top = tk.Frame(
            main,
            bg=Theme.color("background"),
        )
        top.pack(fill="x", pady=(10, 0))

        self.app.file_card = FileCard(top)
        self.app.file_card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5,
        )

        self.app.plugin_card = PluginCard(top)
        self.app.plugin_card.pack(
            side="left",
            fill="both",
            padx=5,
        )

        self.app.plugin_card.set_plugin(
            "RealESRGAN",
            "QNN / Snapdragon NPU",
            "Bereit",
        )

        self.app.job_card = JobCard(main)
        self.app.job_card.pack(
            fill="x",
            pady=(10, 0),
        )

        content = tk.Frame(
            main,
            bg=Theme.color("background"),
        )
        content.pack(
            fill="both",
            expand=True,
            pady=10,
        )

        preview_area = tk.Frame(
            content,
            bg=Theme.color("background"),
        )
        preview_area.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 8),
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
            pady=(0, 8),
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
        self.app.log_card.pack(fill="x", pady=(0, 8))

        self.app.status_bar = StatusBar(main)
        self.app.status_bar.pack(fill="x")

        if self.dnd_available:
            self.app.log_card.log("Drag & Drop ist verfügbar.")
        else:
            self.app.log_card.log(
                "Drag & Drop nicht verfügbar. "
                "Installiere optional: pip install tkinterdnd2"
            )
