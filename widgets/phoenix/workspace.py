from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from widgets.phoenix.dashboard import PhoenixDashboard
from widgets.phoenix.header import PhoenixHeader
from widgets.phoenix.sidebar import PhoenixSidebar
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr


class PhoenixWorkspace(tk.Frame):
    """Phoenix Workspace v1.0."""

    VIEW_TITLE_KEYS: dict[str, tuple[str, str]] = {
        "home": ("nav_home", "Startseite"),
        "dashboard": ("dashboard_title", "Dashboard"),
        "plugins": ("nav_plugins", "Erweiterungen"),
        "settings": ("nav_settings", "Einstellungen"),
        "image": ("image_workspace", "Bild-Workspace"),
        "gallery": ("nav_gallery", "Galerie"),
        "compare": ("nav_compare", "Vergleich"),
        "prompt": ("nav_ai_generate", "KI-Generierung"),
        "models": ("nav_ai_model_manager", "Modell-Manager"),
    }

    def __init__(self, master: tk.Misc, controller: object | None = None) -> None:
        super().__init__(master, bg=PHOENIX_THEME.app_bg)
        self.controller = controller

        from widgets.phoenix.theme import configure_phoenix_styles
        configure_phoenix_styles(self)

        self.header: PhoenixHeader
        self.sidebar: PhoenixSidebar
        self.content_host: tk.Frame
        self.right_panel: tk.Frame | None = None

        self._views: dict[str, tk.Frame] = {}
        self._view_factories: dict[str, Callable[[tk.Misc], tk.Frame]] = {}
        self.current_view: str | None = None

        self._configure_grid()
        self._register_views()
        self._build_layout()
        self.show_view("home")
        self._refresh_views()

    @property
    def actions(self):
        return self.right_panel

    def _configure_grid(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

    def _register_views(self) -> None:
        from widgets.phoenix.views.compare_view import PhoenixCompareView
        from widgets.phoenix.views.gallery_view import PhoenixGalleryView
        from widgets.phoenix.views.home_view import PhoenixHomeView
        from widgets.phoenix.views.image_view import PhoenixImageView
        from widgets.phoenix.views.plugin_view import PhoenixPluginView
        from widgets.phoenix.views.settings_view import PhoenixSettingsView
        from widgets.phoenix.views.prompt_view import PhoenixPromptView
        from widgets.phoenix.views.model_manager_view import PhoenixModelManagerView

        self._view_factories = {
            "home": lambda master: PhoenixHomeView(
                master,
                controller=self.controller,
                on_navigate=self.show_view,
            ),
            "dashboard": lambda master: PhoenixDashboard(master, controller=self.controller),
            "plugins": PhoenixPluginView,
            "settings": PhoenixSettingsView,
            "image": lambda master: PhoenixImageView(
                master,
                on_gallery_select=self.select_gallery_image,
            ),
            "gallery": PhoenixGalleryView,
            "compare": PhoenixCompareView,
            "prompt": PhoenixPromptView,
            "models": PhoenixModelManagerView,
        }

    def _build_layout(self) -> None:
        self.header = PhoenixHeader(self)
        self.header.grid(row=0, column=0, columnspan=3, sticky="ew")

        self.sidebar = PhoenixSidebar(
            self,
            controller=self.controller,
            on_navigate=self.show_view,
        )
        self.sidebar.grid(row=1, column=0, sticky="nsw")

        self.content_host = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        self.content_host.grid(row=1, column=1, sticky="nsew", padx=16, pady=16)
        self.content_host.grid_rowconfigure(0, weight=1)
        self.content_host.grid_columnconfigure(0, weight=1)

        self.right_panel = self._create_right_panel()

    def _create_right_panel(self) -> tk.Frame | None:
        try:
            from widgets.phoenix.right_panel import PhoenixRightPanel
            return PhoenixRightPanel(self, controller=self.controller)
        except Exception:
            return None

    def show_view(self, view_name: str) -> None:
        if view_name not in self._view_factories:
            view_name = "home"

        if self.current_view == view_name:
            return

        for view in self._views.values():
            view.grid_forget()

        # Keep global right panel hidden (CN-020 UI simplify)
        if self.right_panel is not None:
            self.right_panel.grid_forget()

        view = self._get_or_create_view(view_name)
        view.grid(row=0, column=0, sticky="nsew")

        self.current_view = view_name
        self.sidebar.set_active(view_name)
        self.header.set_view(self._view_title(view_name))

        refresh = getattr(view, "refresh", None)
        if callable(refresh):
            refresh()

    def _get_or_create_view(self, view_name: str) -> tk.Frame:
        if view_name in self._views:
            return self._views[view_name]

        factory = self._view_factories[view_name]

        try:
            view = factory(self.content_host)
        except Exception as exc:
            view = self._build_error_view(view_name, exc)

        self._views[view_name] = view
        return view

    def _build_error_view(self, view_name: str, exc: Exception) -> tk.Frame:
        frame = tk.Frame(self.content_host, bg=PHOENIX_THEME.content_bg)

        tk.Label(
            frame,
            text=tr(
                "view_load_failed",
                "{view} konnte nicht geladen werden",
                view=self._view_title(view_name),
            ),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 18, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(24, 8))

        tk.Label(
            frame,
            text=str(exc),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            wraplength=640,
        ).pack(fill="x", padx=24, pady=(0, 12))

        PhoenixDashboard(frame, controller=self.controller).pack(fill="both", expand=True)

        return frame

    @classmethod
    def _view_title(cls, view_name: str) -> str:
        key, fallback = cls.VIEW_TITLE_KEYS.get(
            view_name,
            ("unknown_view", view_name.title()),
        )
        return tr(key, fallback)

    def open_home(self) -> None:
        self.show_view("home")

    def open_dashboard(self) -> None:
        self.show_view("dashboard")

    def open_plugins(self) -> None:
        self.show_view("plugins")

    def open_settings(self) -> None:
        self.show_view("settings")

    def open_image(self) -> None:
        self.show_view("image")

    def open_gallery(self) -> None:
        self.show_view("gallery")

    def open_compare(self) -> None:
        self.show_view("compare")

    def open_prompt(self) -> None:
        self.show_view("prompt")

    def open_models(self) -> None:
        self.show_view("models")

    def refresh_dashboard(self) -> None:
        dashboard = self._views.get("dashboard")
        refresh = getattr(dashboard, "refresh", None)
        if callable(refresh):
            refresh()

    def _refresh_views(self) -> None:
        for view in self._views.values():
            refresh = getattr(view, "refresh", None)
            if callable(refresh):
                refresh()

        if self.right_panel is not None:
            refresh = getattr(self.right_panel, "refresh", None)
            if callable(refresh):
                refresh()

        self.after(500, self._refresh_views)

    def show_image(self, filename) -> None:
        """Display an image in the Phoenix Image view."""
        self.show_view("image")
        view = self._get_or_create_view("image")

        if hasattr(view, "show_image"):
            view.show_image(filename)

    def show_image_pair(self, input_filename, output_filename) -> None:
        """Update the Phoenix Image view with an original/output pair."""
        view = self._get_or_create_view("image")

        if hasattr(view, "show_image_pair"):
            view.show_image_pair(input_filename, output_filename)

    def set_gallery_images(self, image_paths) -> None:
        """Update the Phoenix Image gallery thumbnails."""
        view = self._get_or_create_view("image")

        if hasattr(view, "set_gallery_images"):
            view.set_gallery_images(image_paths)

    def select_gallery_image(self, filename) -> None:
        """Store the active Gallery selection in the application."""
        app = self.winfo_toplevel()
        set_selection = getattr(app, "set_gallery_selection", None)

        if callable(set_selection):
            set_selection(filename)

    def clear_image(self) -> None:
        """Clear the current image."""
        view = self._get_or_create_view("image")

        if hasattr(view, "clear_image"):
            view.clear_image()

    def reconstruct_views(self) -> None:
        """Destroys and recreates all cached views to apply dynamic language changes."""
        for view in list(self._views.values()):
            try:
                view.destroy()
            except Exception:
                pass
        self._views.clear()
        
        current = self.current_view
        self.current_view = None
        self.show_view(current)
