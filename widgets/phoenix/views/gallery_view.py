from __future__ import annotations

import tkinter as tk
import subprocess

from config import OUTPUT_DIR
from controllers.gallery_controller import GalleryController
from controllers.gallery_model import GalleryImage
from widgets.phoenix.gallery.status_bar import GalleryStatusBar
from widgets.phoenix.gallery.thumbnail_area import GalleryThumbnailArea
from widgets.phoenix.gallery.toolbar import GalleryToolbar
from widgets.phoenix.layout.workspace import WorkspaceFrame
from app.i18n import tr
from app.settings_manager import SettingsManager


class PhoenixGalleryView(WorkspaceFrame):
    """Phoenix Gallery Workspace with a responsive placeholder Thumbnail-Grid."""

    # Klassenkonstanten zur Vermeidung von Magic Numbers
    DEFAULT_THUMBNAIL_SIZE = 124

    def __init__(self, master: tk.Misc, controller: object | None = None) -> None:
        super().__init__(
            master,
            title=tr("gallery_title", "Gallery Workspace"),
            subtitle=tr("gallery_subtitle", "Bildkatalog durchsuchen und verwalten"),
            has_inspector=True,
        )
        self.controller = controller or GalleryController()
        self.hover_preview_enabled = self._load_hover_preview_enabled()

        self.thumbnail_area: GalleryThumbnailArea
        self.toolbar: GalleryToolbar
        self.status_bar: GalleryStatusBar
        self.inspector: GalleryInspector

        self._build_shell()
        self._refresh_ui()

        # Register drag & drop for library view if tkinterdnd2 is available
        app = self.winfo_toplevel()
        app_ctrl = getattr(app, "application_controller", None)
        if app_ctrl and getattr(app_ctrl, "dnd_available", False):
            try:
                self.drop_target_register(app_ctrl.dnd_files)
                self.dnd_bind("<<Drop>>", self._on_drop)
            except Exception:
                pass

    def _on_drop(self, event) -> None:
        try:
            from pathlib import Path
            from config import OUTPUT_DIR
            from engine.asset_files import copy_asset_with_sidecar

            app = self.winfo_toplevel()
            paths = app.tk.splitlist(event.data)

            dest_dir = self.controller.current_folder or OUTPUT_DIR
            dest_dir.mkdir(parents=True, exist_ok=True)

            imported_any = False
            for p_str in paths:
                p = Path(p_str)
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}:
                    dest_path = dest_dir / p.name
                    copy_asset_with_sidecar(p, dest_path)
                    imported_any = True

            if imported_any:
                changed = self.controller.refresh()
                self._refresh_ui(force=changed)
        except Exception:
            pass

    def _build_shell(self) -> None:
        # 1. Build Toolbar and place in self.header.toolbar_slot
        self.toolbar = GalleryToolbar(
            self.header.toolbar_slot,
            on_open_folder=self._open_output_directory,
            on_refresh=self._on_refresh,
            on_thumbnail_size_change=self._on_thumbnail_size_change,
            on_search_change=self._on_search_change,
            on_sort_change=self._on_sort_change,
            on_filter_change=self._on_filter_change,
            on_hover_preview_change=self._on_hover_preview_change,
            hover_preview_enabled=self.hover_preview_enabled,
        )
        self.toolbar.grid(row=0, column=0, sticky="ew")

        # 2. Build Thumbnail Area and place in self.content_slot
        self.content_slot.grid_rowconfigure(0, weight=1)
        self.content_slot.grid_columnconfigure(0, weight=1)

        self.thumbnail_area = GalleryThumbnailArea(
            self.content_slot,
            on_select=self._select_image,
            on_clear_selection=self._clear_selection,
            on_double_click=self._on_double_click,
            hover_preview_enabled=lambda: self.hover_preview_enabled,
        )
        self.thumbnail_area.grid(row=0, column=0, sticky="nsew")

        # 3. Build Status Bar and place in self.status_slot
        self.status_bar = GalleryStatusBar(self.status_slot, self.controller.get_status())
        self.status_bar.grid(row=0, column=0, sticky="ew")

        # 4. Build Inspector and place in self.inspector_slot
        if self.inspector_slot:
            from widgets.phoenix.gallery.inspector import GalleryInspector
            self.inspector = GalleryInspector(
                self.inspector_slot,
                on_apply_settings=self._apply_image_settings,
                on_show_in_explorer=self._on_show_in_explorer,
                on_delete_image=self._on_delete_image,
            )
            self.inspector.grid(row=0, column=0, sticky="nsew")

    def _apply_image_settings(self, settings: dict) -> None:
        try:
            import logging
            app = self.winfo_toplevel()
            if hasattr(app, "phoenix_workspace") and app.phoenix_workspace is not None:
                workspace = app.phoenix_workspace
                prompt_view = workspace._get_or_create_view("prompt")
                if hasattr(prompt_view, "apply_generation_settings"):
                    prompt_view.apply_generation_settings(settings)
                workspace.show_view("prompt")
        except Exception as e:
            import logging
            logging.getLogger("PhoenixGalleryView").error(f"Failed to apply generation settings: {e}")

    def _on_show_in_explorer(self, image: GalleryImage) -> None:
        try:
            import subprocess
            subprocess.run(["explorer", "/select,", str(image.path)])
        except Exception as e:
            import logging
            logging.getLogger("PhoenixGalleryView").error(f"Failed to show in explorer: {e}")

    def _on_delete_image(self, image: GalleryImage) -> None:
        from tkinter import messagebox
        from app.i18n import tr
        if messagebox.askyesno(
            tr("confirm_delete_title", "Bild löschen"),
            tr("confirm_delete_message", "Möchtest du das ausgewählte Bild wirklich dauerhaft von der Festplatte löschen?")
        ):
            try:
                # Delete image and sidecar json
                image.path.unlink(missing_ok=True)
                image.path.with_suffix(".json").unlink(missing_ok=True)
                
                # Refresh
                self.controller.clear_selection()
                changed = self.controller.refresh()
                self._refresh_ui(force=changed)
            except Exception as e:
                import logging
                logging.getLogger("PhoenixGalleryView").error(f"Failed to delete image: {e}")

    def _on_open_folder(self) -> None:
        from tkinter import filedialog
        folder = filedialog.askdirectory(
            title=tr("open_folder_dialog_title", "Bilderordner auswählen"),
            initialdir=self.controller.current_folder or ""
        )
        if folder:
            self.controller.open_folder(folder)
            self._refresh_ui(force=True)

    def _open_output_directory(self) -> None:
        try:
            subprocess.Popen(["explorer", str(OUTPUT_DIR.resolve())])
        except Exception as error:
            import logging
            logging.getLogger("PhoenixGalleryView").error(
                "Failed to open output directory in explorer: %s", error
            )

    def _on_refresh(self) -> None:
        changed = self.controller.refresh()
        self._refresh_ui(force=changed)

    def _on_thumbnail_size_change(self, size_label: str) -> None:
        self.controller.set_thumbnail_size(size_label)
        self._refresh_ui()

    def _on_search_change(self, value: str) -> None:
        self.controller.set_search_text(value)
        self._refresh_ui()

    def _on_sort_change(self, value: str) -> None:
        self.controller.set_sort_mode(value)
        self._refresh_ui()

    def _on_filter_change(self, value: str) -> None:
        self.controller.set_filter_mode(value)
        self._refresh_ui()

    def _on_hover_preview_change(self, enabled: bool) -> None:
        self.hover_preview_enabled = enabled
        settings = SettingsManager.load_settings()
        settings["gallery_hover_preview_enabled"] = enabled
        SettingsManager.save_settings(settings)
        self.thumbnail_area.set_hover_preview_enabled(enabled)

    @staticmethod
    def _load_hover_preview_enabled() -> bool:
        value = SettingsManager.load_settings().get("gallery_hover_preview_enabled", True)
        return value if isinstance(value, bool) else True

    def _select_image(self, image: GalleryImage, event: tk.Event) -> None:
        """Behandelt das Anklicken einer Karte zur visuellen Markierung."""
        # Einzelbildauswahl (Mehrfachauswahl laut Sprintumfang nicht implementiert)
        self.controller.select_image(image, ctrl=False, shift=False)
        self._refresh_selection_ui()

    def _clear_selection(self) -> None:
        """Löscht die visuelle Selektionsmarkierung."""
        self.controller.clear_selection()
        self._refresh_selection_ui()

    def _on_double_click(self, image: GalleryImage) -> None:
        # First ensure the image is selected in the controller
        self.controller.select_image(image, ctrl=False, shift=False)
        path = self.controller.prepare_compare_source()
        self._refresh_selection_ui()

        if path:
            app = self.winfo_toplevel()
            if hasattr(app, "application_controller") and app.application_controller is not None:
                app.application_controller.open_compare_with_image(path)

    def refresh(self) -> None:
        """Aktualisiert die Galerie beim Wechseln/Periodisch."""
        changed = self.controller.refresh()
        self._refresh_ui(force=changed)

    def show_generated_image(self, image_path: str) -> None:
        """Load the generated image into the Asset Library and select it."""
        self.controller.show_image(image_path)
        self._refresh_ui(force=True)

    def _refresh_ui(self, force: bool = False) -> None:
        """Aktualisiert die Galerie-Ansicht."""
        self.thumbnail_area.set_images(
            images=self.controller.visible_images,
            selected_paths=self.controller.selected_paths,
            thumbnail_size=self.controller.get_thumbnail_size(),
            force=force,
        )
        from app.i18n import tr
        size_mapping = {
            "Klein": tr("size_small", "Klein"),
            "Mittel": tr("size_medium", "Mittel"),
            "Groß": tr("size_large", "Groß"),
            "Sehr groß": tr("size_huge", "Sehr groß"),
        }
        size_label = size_mapping.get(self.controller.thumbnail_size_label, self.controller.thumbnail_size_label)
        self.status_bar.update_values(
            image_count=self.controller.get_image_count(),
            selection_count=self.controller.get_selection_count(),
            thumbnail_size=size_label,
            status=self.controller.get_status(),
        )
        if hasattr(self, "inspector"):
            self.inspector.update_selection(self.controller.selected_images)

    def _refresh_selection_ui(self) -> None:
        """Refresh selection/status without rebuilding the thumbnail grid."""
        self.thumbnail_area.set_selection(self.controller.selected_paths)
        from app.i18n import tr
        size_mapping = {
            "Klein": tr("size_small", "Klein"),
            "Mittel": tr("size_medium", "Mittel"),
            "Groß": tr("size_large", "Groß"),
            "Sehr groß": tr("size_huge", "Sehr groß"),
        }
        size_label = size_mapping.get(self.controller.thumbnail_size_label, self.controller.thumbnail_size_label)
        self.status_bar.update_values(
            image_count=self.controller.get_image_count(),
            selection_count=self.controller.get_selection_count(),
            thumbnail_size=size_label,
            status=self.controller.get_status(),
        )
        if hasattr(self, "inspector"):
            self.inspector.update_selection(self.controller.selected_images)
