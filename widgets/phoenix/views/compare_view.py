from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox

from controllers.compare_workspace_controller import CompareWorkspaceController
from widgets.phoenix.compare.compare_panel import ComparePanel
from widgets.phoenix.compare.status_bar import CompareStatusBar
from widgets.phoenix.compare.compare_toolbar import CompareToolbar
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME


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
            has_inspector=False,  # Inspector is not implemented in this sprint
        )
        self.controller = controller or CompareWorkspaceController()
        self.toolbar: CompareToolbar
        self.original_panel: ComparePanel
        self.result_panel: ComparePanel
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
        # Create a container frame for the responsive split layout
        self.split_container = tk.Frame(self.content_slot, bg=PHOENIX_THEME.content_bg)
        self.split_container.grid(row=0, column=0, sticky="nsew")
        self.split_container.grid_columnconfigure(0, weight=1, uniform="compare_panel")
        self.split_container.grid_columnconfigure(1, weight=1, uniform="compare_panel")
        self.split_container.grid_rowconfigure(0, weight=1)

        self.original_panel = ComparePanel(
            self.split_container,
            title="Original",
            empty_title="Originalbild laden",
            empty_text="Öffne links ein Ausgangsbild für den Qualitätsvergleich.",
            icon_name="image",
        )
        self.original_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, PHOENIX_THEME.space_sm),
        )

        self.result_panel = ComparePanel(
            self.split_container,
            title="Ergebnis",
            empty_title="Ausgabe laden",
            empty_text="Öffne rechts ein Ergebnisbild, z. B. einen AI-Output.",
            icon_name="output",
        )
        self.result_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(PHOENIX_THEME.space_sm, 0),
        )

    def _build_status_bar(self) -> None:
        self.status_bar = CompareStatusBar(self.status_slot, self.controller.status_items())
        self.status_bar.grid(row=0, column=0, sticky="ew")

    def refresh(self) -> None:
        state = self.controller.get_state()
        self.status_bar.update_values(self.controller.status_items())
        self.original_panel.update_panel(self.controller.get_original_image(), state.zoom_scale)
        self.result_panel.update_panel(self.controller.get_output_image(), state.zoom_scale)

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
