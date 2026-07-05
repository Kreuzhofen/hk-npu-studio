from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from resources.icons import IconManager
from widgets.phoenix.layout.workspace import WorkspaceToolbarBase
from widgets.phoenix.theme import PHOENIX_THEME


class GalleryToolbar(WorkspaceToolbarBase):
    """Professional toolbar for the Gallery Workspace."""

    SORT_OPTIONS = ("Name", "Datum", "Größe", "Typ")
    SIZE_OPTIONS = ("Klein", "Mittel", "Groß", "Sehr groß")
    FILTER_OPTIONS = ("Alle", "JPG/JPEG", "PNG", "WEBP", "TIFF", "BMP")
    PLACEHOLDER = "Suchen…"
    BUTTON_WIDTH_OPEN = 136
    BUTTON_WIDTH_REFRESH = 128
    BUTTON_WIDTH_FILTER = 104
    DROPDOWN_WIDTH_SORT = 122
    DROPDOWN_WIDTH_SIZE = 136

    def __init__(
        self,
        master: tk.Misc,
        on_open_folder: Callable[[], None],
        on_refresh: Callable[[], None],
        on_thumbnail_size_change: Callable[[str], None],
        on_search_change: Callable[[str], None],
        on_sort_change: Callable[[str], None],
        on_filter_change: Callable[[str], None],
    ) -> None:
        super().__init__(master)
        self.on_open_folder = on_open_folder
        self.on_refresh = on_refresh
        self.on_thumbnail_size_change = on_thumbnail_size_change
        self.on_search_change = on_search_change
        self.on_sort_change = on_sort_change
        self.on_filter_change = on_filter_change
        self.search_value = tk.StringVar(value=self.PLACEHOLDER)
        self.sort_value = tk.StringVar(value=self.SORT_OPTIONS[0])
        self.size_value = tk.StringVar(value=self.SIZE_OPTIONS[1])
        self.filter_value = tk.StringVar(value=self.FILTER_OPTIONS[0])
        self._placeholder_active = True

        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        self._build_action_group().grid(
            row=0,
            column=0,
            sticky="w",
            padx=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_lg),
            pady=PHOENIX_THEME.space_md,
        )
        self._build_search_group().grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, PHOENIX_THEME.space_lg),
            pady=PHOENIX_THEME.space_md,
        )
        self._build_view_group().grid(
            row=0,
            column=2,
            sticky="e",
            padx=(0, PHOENIX_THEME.space_md),
            pady=PHOENIX_THEME.space_md,
        )

    def _build_action_group(self) -> tk.Frame:
        group = self.group_frame()
        self.toolbar_button(
            group,
            IconManager.get_label("folder", "Ordner öffnen"),
            self.on_open_folder,
            self.BUTTON_WIDTH_OPEN,
        ).pack(side="left")
        self.separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self.toolbar_button(
            group,
            IconManager.get_label("refresh", "Aktualisieren"),
            self.on_refresh,
            self.BUTTON_WIDTH_REFRESH,
        ).pack(side="left")
        return group

    def _build_search_group(self) -> tk.Frame:
        group = self.group_frame()
        group.grid_columnconfigure(0, weight=1)

        search_host = tk.Frame(
            group,
            bg=PHOENIX_THEME.elevated_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        search_host.grid(row=0, column=0, sticky="ew")
        search_host.grid_columnconfigure(1, weight=1)

        tk.Label(
            search_host,
            text=IconManager.get_symbol("search"),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="center",
            width=2,
        ).grid(row=0, column=0, sticky="ns", padx=(PHOENIX_THEME.space_sm, 0))

        self.search_entry = tk.Entry(
            search_host,
            textvariable=self.search_value,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            insertbackground=PHOENIX_THEME.text_primary,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_body,
        )
        self.search_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_md),
            pady=PHOENIX_THEME.button_pad_y,
        )
        self.search_entry.bind("<FocusIn>", self._clear_search_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_search_placeholder)
        self.search_value.trace_add("write", self._on_search_changed)
        return group

    def _build_view_group(self) -> tk.Frame:
        group = self.group_frame()
        self.toolbar_dropdown(
            group,
            "Sortieren",
            self.sort_value,
            self.SORT_OPTIONS,
            self.DROPDOWN_WIDTH_SORT,
            self.on_sort_change,
        ).pack(side="left")
        self.toolbar_dropdown(
            group,
            "Größe",
            self.size_value,
            self.SIZE_OPTIONS,
            self.DROPDOWN_WIDTH_SIZE,
            self.on_thumbnail_size_change,
        ).pack(side="left", padx=(PHOENIX_THEME.space_sm, 0))
        self.separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self.toolbar_dropdown(
            group,
            "Filter",
            self.filter_value,
            self.FILTER_OPTIONS,
            self.BUTTON_WIDTH_FILTER,
            self.on_filter_change,
        ).pack(side="left")
        return group

    def _clear_search_placeholder(self, _event: tk.Event) -> None:
        if self._placeholder_active:
            self._placeholder_active = False
            self.search_value.set("")
            self.search_entry.configure(fg=PHOENIX_THEME.text_primary)

    def _restore_search_placeholder(self, _event: tk.Event) -> None:
        if not self.search_value.get():
            self._placeholder_active = True
            self.search_value.set(self.PLACEHOLDER)
            self.search_entry.configure(fg=PHOENIX_THEME.text_muted)

    def _on_search_changed(self, *_args: object) -> None:
        if self._placeholder_active:
            return
        self.on_search_change(self.search_value.get())
