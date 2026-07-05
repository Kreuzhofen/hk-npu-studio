from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox

from controllers.compare_workspace_controller import CompareWorkspaceController
from widgets.phoenix.compare.inspector import CompareInspector
from widgets.phoenix.compare.split_view import CompareSplitView
from widgets.phoenix.compare.status_bar import CompareStatusBar
from widgets.phoenix.compare.toolbar import CompareToolbar
from widgets.phoenix.layout.workspace import WorkspaceFrame


class PhoenixCompareView(WorkspaceFrame):
    """Professional Compare Workspace for manual before/after image review."""

    FILE_TYPES = (
        ("Bilddateien", "*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff"),
        ("JPEG", "*.jpg *.jpeg"),
        ("PNG", "*.png"),
        ("TIFF", "*.tif *.tiff"),
        ("Alle Dateien", "*.*"),
    )

    def __init__(
        self,
        master: tk.Misc,
        controller: CompareWorkspaceController | None = None,
    ) -> None:
        super().__init__(
            master,
            title="Compare Workspace",
            subtitle="Lade Original und Ergebnis, um AI-Outputs direkt nebeneinander zu prüfen.",
            has_inspector=True,
        )
        self.controller = controller or CompareWorkspaceController()
        self.toolbar: CompareToolbar
        self.split_view: CompareSplitView
        self.inspector: CompareInspector
        self.status_bar: CompareStatusBar
        self._build()
        self.refresh()

    def _build(self) -> None:
        self._build_toolbar()
        self._build_main_area()
        self._build_status_bar()

    def _build_toolbar(self) -> None:
        self.toolbar = CompareToolbar(
            self.header.toolbar_slot,
            on_open_original=self._open_original,
            on_open_output=self._open_output,
            on_fit=lambda: self._set_zoom("Fit"),
            on_zoom_50=lambda: self._set_zoom("50 %"),
            on_zoom_100=lambda: self._set_zoom("100 %"),
            on_zoom_200=lambda: self._set_zoom("200 %"),
            on_sync=self._prepare_sync,
            on_swap=self._swap_images,
        )
        self.toolbar.grid(row=0, column=0, sticky="ew")

    def _build_main_area(self) -> None:
        self.split_view = CompareSplitView(self.content_slot)
        self.split_view.grid(row=0, column=0, sticky="nsew")

        if self.inspector_slot is None:
            return

        self.inspector = CompareInspector(self.inspector_slot)
        self.inspector.grid(row=0, column=0, sticky="nsew")

    def _build_status_bar(self) -> None:
        self.status_bar = CompareStatusBar(self.status_slot, self.controller.status_items())
        self.status_bar.grid(row=0, column=0, sticky="ew")

    def refresh(self) -> None:
        state = self.controller.get_state()
        self.split_view.update_images(
            self.controller.get_original_image(),
            self.controller.get_output_image(),
            state,
        )
        self.inspector.update_sections(self.controller.inspector_sections())
        self.status_bar.update_values(self.controller.status_items())

    def _open_original(self) -> None:
        filename = self._ask_image_filename("Originalbild öffnen")
        if not filename:
            return
        try:
            self.controller.load_original(filename)
        except Exception as error:
            self._handle_error(error)
        self.refresh()

    def _open_output(self) -> None:
        filename = self._ask_image_filename("Ausgabebild öffnen")
        if not filename:
            return
        try:
            self.controller.load_output(filename)
        except Exception as error:
            self._handle_error(error)
        self.refresh()

    def _set_zoom(self, zoom_label: str) -> None:
        self.controller.set_zoom(zoom_label)
        self.refresh()

    def _prepare_sync(self) -> None:
        self.controller.prepare_sync()
        self.refresh()

    def _swap_images(self) -> None:
        self.controller.swap_images()
        self.refresh()

    def _ask_image_filename(self, title: str) -> str:
        return filedialog.askopenfilename(title=title, filetypes=self.FILE_TYPES)

    def _handle_error(self, error: Exception) -> None:
        message = str(error) or error.__class__.__name__
        self.controller.set_error(message)
        messagebox.showerror("Compare Workspace", message)
