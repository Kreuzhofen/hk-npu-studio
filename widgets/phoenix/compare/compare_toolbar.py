from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from collections.abc import Callable

from resources.icons import IconManager
from widgets.phoenix.layout.workspace import WorkspaceToolbarBase
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr


class CompareToolbar(WorkspaceToolbarBase):
    """Toolbar component for Compare Workspace actions."""

    BUTTON_WIDTH_WIDE = 100
    BUTTON_WIDTH_MEDIUM = 80
    BUTTON_WIDTH_SMALL = 58

    def __init__(
        self,
        master: tk.Misc,
        on_open_original: Callable[[], None],
        on_open_output: Callable[[], None],
        on_fit: Callable[[], None],
        on_zoom_50: Callable[[], None],
        on_zoom_100: Callable[[], None],
        on_zoom_200: Callable[[], None],
        on_sync: Callable[[], None],
        on_swap: Callable[[], None],
        on_compare_metadata: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self.on_open_original = on_open_original
        self.on_open_output = on_open_output
        self.on_fit = on_fit
        self.on_zoom_50 = on_zoom_50
        self.on_zoom_100 = on_zoom_100
        self.on_zoom_200 = on_zoom_200
        self.on_sync = on_sync
        self.on_swap = on_swap
        self.on_compare_metadata = on_compare_metadata
        self._build()

    def _build(self) -> None:
        self.file_group = self._build_file_group()
        self.zoom_group = self._build_zoom_group()
        self.compare_group = self._build_compare_group()
        self.bind("<Configure>", lambda event: self._layout_groups(event.width), add="+")
        self._layout_groups(0)

    def _layout_groups(self, width: int) -> None:
        """Keep complete comparison actions visible when logical width shrinks."""
        two_rows = width < 820
        three_rows = width < 540
        for column in range(3):
            self.grid_columnconfigure(column, weight=0)
        self.file_group.grid(
            row=0, column=0, sticky="w", padx=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_md),
            pady=PHOENIX_THEME.space_md,
        )
        self.zoom_group.grid(
            row=1 if three_rows else 0, column=0 if three_rows else 1, sticky="w",
            padx=(PHOENIX_THEME.space_xs if three_rows else 0, PHOENIX_THEME.space_md),
            pady=(0, PHOENIX_THEME.space_md) if three_rows else PHOENIX_THEME.space_md,
        )
        self.compare_group.grid(
            row=2 if three_rows else 1 if two_rows else 0,
            column=0 if two_rows else 2,
            columnspan=2 if two_rows else 1, sticky="w",
            padx=(PHOENIX_THEME.space_xs if two_rows else 0, PHOENIX_THEME.space_sm),
            pady=(0, PHOENIX_THEME.space_md) if two_rows else PHOENIX_THEME.space_md,
        )

    def _build_file_group(self) -> tk.Frame:
        group = self.group_frame()
        self.toolbar_button(
            group,
            IconManager.get_label("folder", tr("compare_left_title", "Original")),
            self.on_open_original,
            self._button_width(IconManager.get_label("folder", tr("compare_left_title", "Original"))),
        ).pack(side="left")
        self.separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self.toolbar_button(
            group,
            IconManager.get_label("output", tr("output_title", "Ausgabe")),
            self.on_open_output,
            self._button_width(IconManager.get_label("output", tr("output_title", "Ausgabe"))),
        ).pack(side="left")
        return group

    def _build_zoom_group(self) -> tk.Frame:
        group = self.group_frame()
        self.zoom_buttons = {}

        btn_fit = self.toolbar_button(group, "Fit", self.on_fit, self._button_width("Fit"))
        btn_fit.pack(side="left")
        self.zoom_buttons["Fit"] = btn_fit

        btn_50 = self.toolbar_button(group, "50 %", self.on_zoom_50, self._button_width("50 %"))
        btn_50.pack(side="left", padx=(PHOENIX_THEME.space_sm, 0))
        self.zoom_buttons["50 %"] = btn_50

        btn_100 = self.toolbar_button(group, "100 %", self.on_zoom_100, self._button_width("100 %"))
        btn_100.pack(side="left", padx=(PHOENIX_THEME.space_sm, 0))
        self.zoom_buttons["100 %"] = btn_100

        btn_200 = self.toolbar_button(group, "200 %", self.on_zoom_200, self._button_width("200 %"))
        btn_200.pack(side="left", padx=(PHOENIX_THEME.space_sm, 0))
        self.zoom_buttons["200 %"] = btn_200

        return group

    def set_zoom_mode(self, zoom_label: str) -> None:
        """Visually mark the active zoom mode button using theme colors."""
        if not hasattr(self, "zoom_buttons"):
            return
        for label, button in self.zoom_buttons.items():
            if label == zoom_label:
                button.configure(button_type="primary")
            else:
                button.configure(button_type="neutral")


    def _build_compare_group(self) -> tk.Frame:
        group = self.group_frame()
        self.sync_button = self.toolbar_button(
            group,
            IconManager.get_label("refresh", tr("compare_sync_on", "Synchron: Ein")),
            self.on_sync,
            self._button_width(IconManager.get_label("refresh", tr("compare_sync_on", "Synchron: Ein"))),
        )
        self.sync_button.pack(side="left")
        self.separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self.toolbar_button(
            group,
            IconManager.get_label("compare", tr("compare_swap", "Tauschen")),
            self.on_swap,
            self._button_width(IconManager.get_label("compare", tr("compare_swap", "Tauschen"))),
        ).pack(side="left")
        self.separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self.toolbar_button(
            group,
            tr("compare_metadata", "Metadaten vergleichen"),
            self.on_compare_metadata,
            self._button_width(tr("compare_metadata", "Metadaten vergleichen")),
        ).pack(side="left")
        return group

    def set_sync_enabled(self, enabled: bool) -> None:
        text = tr("compare_sync_on", "Synchron: Ein") if enabled else tr("compare_sync_off", "Synchron: Aus")
        self.sync_button.configure(text=text, button_type="primary" if enabled else "neutral")

    @staticmethod
    def _button_width(text: str) -> int:
        """Size toolbar buttons from their translated label instead of a fixed pixel cap."""
        label = text.partition("  ")[2] or text
        return tkfont.Font(font=PHOENIX_THEME.font_button).measure(label) + 40
