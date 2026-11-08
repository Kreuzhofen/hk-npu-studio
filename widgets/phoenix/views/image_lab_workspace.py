from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable

from app.i18n import tr
from engine.theme_manager import ThemeManager
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.theme import PHOENIX_THEME
from widgets.phoenix.views.image_lab_view import PhoenixImageLabView
from widgets.phoenix.views.inpainting_view import PhoenixInpaintingView
from widgets.phoenix.views.photo_restore_view import PhoenixPhotoRestoreView
from widgets.phoenix.views.image_to_image_view import PhoenixImageToImageView

logger = logging.getLogger(__name__)


class PhoenixImageLabWorkspace(PhoenixPhotoRestoreView):
    """
    Phoenix Image Lab: Central workspace for AI image processing & restoration
    on Qualcomm Snapdragon X NPU.
    
    Provides 4 sub-views navigated via the central Overview hub and toolbar back-buttons:
    1. Übersicht (Overview - feature cards)
    2. Generatives Füllen (Generative Fill - SD1.5 Inpainting on Hexagon HTP)
    3. Retusche (Retouch - shared inpainting canvas)
    4. Foto-Restaurierung (Photo Restoration - FiDeSR Strong on Hexagon HTP)
    """

    def __init__(
        self,
        master: tk.Misc,
        controller: object | None = None,
        on_navigate: Callable[[str], None] | None = None,
        initial_subview: str = "overview",
    ) -> None:
        # Initialize as clean tk.Frame, bypassing PhoenixPhotoRestoreView.__init__
        tk.Frame.__init__(self, master, bg=PHOENIX_THEME.content_bg)
        self.controller = controller
        self.on_navigate = on_navigate
        self._ui_pump_id: str | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._subviews: dict[str, tk.Frame] = {}
        self._nav_buttons: dict[str, PhoenixButton] = {}
        self.active_subview: str | None = None

        self._build_subview_host()
        self.select_subview(initial_subview)

    def _build_subview_host(self) -> None:
        self.subview_host = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        self.subview_host.grid(row=0, column=0, sticky="nsew")
        self.subview_host.grid_rowconfigure(0, weight=1)
        self.subview_host.grid_columnconfigure(0, weight=1)

    def select_subview(self, key: str) -> None:
        normalized_map = {
            "overview": "overview",
            "uebersicht": "overview",
            "image_lab": "overview",
            "generative_fill": "generative_fill",
            "inpainting": "generative_fill",
            "fill": "generative_fill",
            "retouch": "retouch",
            "retusche": "retouch",
            "photo_restore": "photo_restore",
            "restore": "photo_restore",
            "image_to_image": "image_to_image",
            "img2img": "image_to_image",
            "bild_zu_bild": "image_to_image",
        }
        subview_key = normalized_map.get(str(key).lower(), "overview")

        if self.active_subview == subview_key and subview_key in self._subviews:
            return

        # Hide current subview
        for view in self._subviews.values():
            view.grid_forget()

        # Get or create requested subview
        subview = self._get_or_create_subview(subview_key)
        subview.grid(row=0, column=0, sticky="nsew")
        self.active_subview = subview_key

        # Update button highlights (if any compatibility buttons registered)
        self._update_button_states()

    def _get_or_create_subview(self, key: str) -> tk.Frame:
        if key == "retouch":
            # Retouch shares the functional inpainting workspace view
            if "generative_fill" not in self._subviews:
                self._subviews["generative_fill"] = PhoenixInpaintingView(self.subview_host, on_navigate=self.select_subview)
            self._subviews["retouch"] = self._subviews["generative_fill"]
            return self._subviews["retouch"]

        if key in self._subviews:
            return self._subviews[key]

        if key == "overview":
            view = PhoenixImageLabView(self.subview_host, on_navigate=self.select_subview)
        elif key == "generative_fill":
            view = PhoenixInpaintingView(self.subview_host, on_navigate=self.select_subview)
        elif key == "photo_restore":
            view = PhoenixPhotoRestoreView(self.subview_host, on_navigate=self.select_subview)
        elif key == "image_to_image":
            view = PhoenixImageToImageView(self.subview_host, on_navigate=self.select_subview)
        else:
            view = PhoenixImageLabView(self.subview_host, on_navigate=self.select_subview)

        self._subviews[key] = view
        return view

    def _update_button_states(self) -> None:
        for key, button in self._nav_buttons.items():
            if key == self.active_subview:
                button.configure(
                    button_type="nav_active",
                    bg=PHOENIX_THEME.accent_soft,
                    fg=PHOENIX_THEME.accent,
                    icon_color=PHOENIX_THEME.accent,
                )
            else:
                button.configure(
                    button_type="nav",
                    bg=PHOENIX_THEME.content_bg,
                    fg=PHOENIX_THEME.text_secondary,
                    icon_color=PHOENIX_THEME.text_secondary,
                )

    def open_image_to_image_with_image(self, filename) -> None:
        """Switch to image_to_image subview and load dropped/selected image."""
        self.select_subview("image_to_image")
        i2i_view = self._get_or_create_subview("image_to_image")
        if hasattr(i2i_view, "load_dropped_image"):
            i2i_view.load_dropped_image(filename)

    def open_photo_restore_with_image(self, filename) -> None:
        """Switch to photo_restore subview and load dropped/selected image."""
        self.select_subview("photo_restore")
        restore_view = self._get_or_create_subview("photo_restore")
        if hasattr(restore_view, "load_dropped_image"):
            restore_view.load_dropped_image(filename)

    def load_dropped_image(self, filename) -> None:
        """Compatibility entry point for drag-and-drop into Photo Restore."""
        self.open_photo_restore_with_image(filename)

    def refresh(self) -> None:
        self.configure(bg=PHOENIX_THEME.content_bg)
        if hasattr(self, "local_sidebar") and self.local_sidebar:
            self.local_sidebar.configure(bg=PHOENIX_THEME.content_bg)
        if hasattr(self, "divider") and self.divider:
            self.divider.configure(bg=PHOENIX_THEME.border)
        if hasattr(self, "nav_header") and self.nav_header:
            self.nav_header.configure(
                bg=PHOENIX_THEME.content_bg,
                fg=PHOENIX_THEME.text_muted,
            )
        self.subview_host.configure(bg=PHOENIX_THEME.content_bg)
        self._update_button_states()

        for subview in self._subviews.values():
            refresh_method = getattr(subview, "refresh", None)
            if callable(refresh_method):
                try:
                    refresh_method()
                except Exception:
                    pass

    def destroy(self) -> None:
        for subview in list(self._subviews.values()):
            try:
                subview.destroy()
            except Exception:
                pass
        self._subviews.clear()
        tk.Frame.destroy(self)
