from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from resources.icons import IconManager
from widgets.phoenix.layout.workspace import WorkspaceToolbarBase
from widgets.phoenix.theme import PHOENIX_THEME


class CompareToolbar(WorkspaceToolbarBase):
    """Toolbar component for Compare Workspace actions."""

    BUTTON_WIDTH_WIDE = 128
    BUTTON_WIDTH_MEDIUM = 96
    BUTTON_WIDTH_SMALL = 74

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
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(3, weight=1)

        self._build_file_group().grid(
            row=0,
            column=0,
            sticky="w",
            padx=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_lg),
            pady=PHOENIX_THEME.space_md,
        )
        self._build_zoom_group().grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, PHOENIX_THEME.space_lg),
            pady=PHOENIX_THEME.space_md,
        )
        self._build_compare_group().grid(
            row=0,
            column=2,
            sticky="w",
            padx=(0, PHOENIX_THEME.space_md),
            pady=PHOENIX_THEME.space_md,
        )

    def _build_file_group(self) -> tk.Frame:
        group = self.group_frame()
        self.toolbar_button(
            group,
            IconManager.get_label("folder", "Original öffnen"),
            self.on_open_original,
            self.BUTTON_WIDTH_WIDE,
        ).pack(side="left")
        self.separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self.toolbar_button(
            group,
            IconManager.get_label("output", "Ausgabe öffnen"),
            self.on_open_output,
            self.BUTTON_WIDTH_WIDE,
        ).pack(side="left")
        return group

    def _build_zoom_group(self) -> tk.Frame:
        group = self.group_frame()
        self.toolbar_button(group, "Fit", self.on_fit, self.BUTTON_WIDTH_SMALL).pack(side="left")
        self.toolbar_button(group, "50 %", self.on_zoom_50, self.BUTTON_WIDTH_SMALL).pack(
            side="left", padx=(PHOENIX_THEME.space_sm, 0)
        )
        self.toolbar_button(group, "100 %", self.on_zoom_100, self.BUTTON_WIDTH_SMALL).pack(
            side="left", padx=(PHOENIX_THEME.space_sm, 0)
        )
        self.toolbar_button(group, "200 %", self.on_zoom_200, self.BUTTON_WIDTH_SMALL).pack(
            side="left", padx=(PHOENIX_THEME.space_sm, 0)
        )
        return group

    def _build_compare_group(self) -> tk.Frame:
        group = self.group_frame()
        self.toolbar_button(
            group,
            IconManager.get_label("refresh", "Synchronisieren"),
            self.on_sync,
            self.BUTTON_WIDTH_WIDE,
        ).pack(side="left")
        self.separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self.toolbar_button(
            group,
            IconManager.get_label("compare", "Swap"),
            self.on_swap,
            self.BUTTON_WIDTH_MEDIUM,
        ).pack(side="left")
        return group
