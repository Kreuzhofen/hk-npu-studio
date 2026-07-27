from __future__ import annotations

import tkinter as tk
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
        self.grid_columnconfigure(3, weight=1)

        self._build_file_group().grid(
            row=0,
            column=0,
            sticky="w",
            padx=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_md),
            pady=PHOENIX_THEME.space_md,
        )
        self._build_zoom_group().grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, PHOENIX_THEME.space_md),
            pady=PHOENIX_THEME.space_md,
        )
        self._build_compare_group().grid(
            row=0,
            column=2,
            sticky="w",
            padx=(0, PHOENIX_THEME.space_sm),
            pady=PHOENIX_THEME.space_md,
        )

    def _build_file_group(self) -> tk.Frame:
        group = self.group_frame()
        self.toolbar_button(
            group,
            IconManager.get_label("folder", "Original"),
            self.on_open_original,
            self.BUTTON_WIDTH_WIDE,
        ).pack(side="left")
        self.separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self.toolbar_button(
            group,
            IconManager.get_label("output", tr("output_title", "Ausgabe")),
            self.on_open_output,
            self.BUTTON_WIDTH_WIDE,
        ).pack(side="left")
        return group

    def _build_zoom_group(self) -> tk.Frame:
        group = self.group_frame()
        self.zoom_buttons = {}

        btn_fit = self.toolbar_button(group, "Fit", self.on_fit, self.BUTTON_WIDTH_SMALL)
        btn_fit.pack(side="left")
        self.zoom_buttons["Fit"] = btn_fit

        btn_50 = self.toolbar_button(group, "50 %", self.on_zoom_50, self.BUTTON_WIDTH_SMALL)
        btn_50.pack(side="left", padx=(PHOENIX_THEME.space_sm, 0))
        self.zoom_buttons["50 %"] = btn_50

        btn_100 = self.toolbar_button(group, "100 %", self.on_zoom_100, self.BUTTON_WIDTH_SMALL)
        btn_100.pack(side="left", padx=(PHOENIX_THEME.space_sm, 0))
        self.zoom_buttons["100 %"] = btn_100

        btn_200 = self.toolbar_button(group, "200 %", self.on_zoom_200, self.BUTTON_WIDTH_SMALL)
        btn_200.pack(side="left", padx=(PHOENIX_THEME.space_sm, 0))
        self.zoom_buttons["200 %"] = btn_200

        return group

    def set_zoom_mode(self, zoom_label: str) -> None:
        """Visually mark the active zoom mode button using theme colors."""
        if not hasattr(self, "zoom_buttons"):
            return
        for label, button in self.zoom_buttons.items():
            if label == zoom_label:
                button.configure(
                    bg=PHOENIX_THEME.accent,
                    fg=PHOENIX_THEME.text_on_accent,
                )
            else:
                button.configure(
                    bg=PHOENIX_THEME.elevated_bg,
                    fg=PHOENIX_THEME.text_secondary,
                )


    def _build_compare_group(self) -> tk.Frame:
        group = self.group_frame()
        self.toolbar_button(
            group,
            IconManager.get_label("refresh", "Sync"),
            self.on_sync,
            self.BUTTON_WIDTH_MEDIUM,
        ).pack(side="left")
        self.separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self.toolbar_button(
            group,
            IconManager.get_label("compare", "Swap"),
            self.on_swap,
            self.BUTTON_WIDTH_MEDIUM,
        ).pack(side="left")
        self.separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self.toolbar_button(
            group,
            tr("compare_metadata", "Metadaten vergleichen"),
            self.on_compare_metadata,
            160,
        ).pack(side="left")
        return group
