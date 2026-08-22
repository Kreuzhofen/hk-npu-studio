from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from collections.abc import Callable

from resources.icons import IconManager
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.layout.workspace import WorkspaceToolbarBase
from widgets.phoenix.theme import PHOENIX_THEME


class GalleryToolbar(WorkspaceToolbarBase):
    """Professional toolbar for the Gallery Workspace."""

    SORT_OPTIONS = ("Name", "Datum", "Größe", "Typ")
    SIZE_OPTIONS = ("Klein", "Mittel", "Groß", "Sehr groß")
    FILTER_OPTIONS = ("Alle", "JPG/JPEG", "PNG", "WEBP", "TIFF", "BMP")
    PLACEHOLDER = "Suchen…"
    BUTTON_WIDTH_OPEN = 200
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
        on_hover_preview_change: Callable[[bool], None] = lambda _enabled: None,
        hover_preview_enabled: bool = True,
    ) -> None:
        from app.i18n import tr
        self.SORT_OPTIONS = (
            tr("sort_name", "Name"),
            tr("sort_date", "Datum"),
            tr("sort_size", "Größe"),
            tr("sort_type", "Typ")
        )
        self.SIZE_OPTIONS = (
            tr("size_small", "Klein"),
            tr("size_medium", "Mittel"),
            tr("size_large", "Groß"),
            tr("size_huge", "Sehr groß")
        )
        self.FILTER_OPTIONS = (
            tr("filter_all", "Alle"),
            "JPG/JPEG", "PNG", "WEBP", "TIFF", "BMP"
        )
        self.PLACEHOLDER = tr("search_placeholder", "Suchen…")

        super().__init__(master)
        self.on_open_folder = on_open_folder
        self.on_refresh = on_refresh
        self.on_thumbnail_size_change = on_thumbnail_size_change
        self.on_search_change = on_search_change
        self.on_sort_change = on_sort_change
        self.on_filter_change = on_filter_change
        self.on_hover_preview_change = on_hover_preview_change
        self.hover_preview_enabled = hover_preview_enabled
        self.search_value = tk.StringVar(value=self.PLACEHOLDER)
        self.sort_value = tk.StringVar(value=self.SORT_OPTIONS[0])
        self.size_value = tk.StringVar(value=self.SIZE_OPTIONS[1])
        self.filter_value = tk.StringVar(value=self.FILTER_OPTIONS[0])
        self._placeholder_active = True

        self._build()

    def _build(self) -> None:
        from app.i18n import tr
        self.output_group = self._build_output_group()
        self.hover_group = self._build_hover_group()
        self.refresh_group = self._build_refresh_group()
        self.search_group = self._build_search_group()
        self.sort_group, self.sort_dropdown = self._build_dropdown_group(
            tr("sort_by", "Sortieren"), self.sort_value, self.SORT_OPTIONS,
            self.DROPDOWN_WIDTH_SORT, self.on_sort_change,
        )
        self.size_group, self.size_dropdown = self._build_dropdown_group(
            tr("size", "Größe"), self.size_value, self.SIZE_OPTIONS,
            self.DROPDOWN_WIDTH_SIZE, self.on_thumbnail_size_change,
        )
        self.filter_group, self.filter_dropdown = self._build_dropdown_group(
            tr("filter", "Filter"), self.filter_value, self.FILTER_OPTIONS,
            self.BUTTON_WIDTH_FILTER, self.on_filter_change,
        )
        self.toolbar_groups = (
            self.output_group,
            self.hover_group,
            self.refresh_group,
            self.search_group,
            self.sort_group,
            self.size_group,
            self.filter_group,
        )
        self._toolbar_layout: tuple[tuple[tk.Frame, ...], ...] = ()
        self._apply_toolbar_layout((self.toolbar_groups,))
        self.bind("<Configure>", self._layout_toolbar_groups, add="+")

    def _build_output_group(self) -> tk.Frame:
        from app.i18n import tr
        group = self.group_frame()
        self.open_output_btn = PhoenixButton(
            group,
            text=tr("menu_open_output", "Output-Ordner öffnen"),
            command=self.on_open_folder,
            button_type="neutral",
            icon_name="folder",
            icon_color=PHOENIX_THEME.warning,
            width=self.BUTTON_WIDTH_OPEN,
            height=30,
            radius=6,
        )
        self.open_output_btn.pack(side="left")
        return group

    def _build_hover_group(self) -> tk.Frame:
        from app.i18n import tr
        group = self.group_frame()
        hover_labels = (
            tr("gallery_hover_preview_on", "Hover-Vorschau: Ein"),
            tr("gallery_hover_preview_off", "Hover-Vorschau: Aus"),
        )
        try:
            hover_font = tkfont.Font(font=PHOENIX_THEME.font_button)
            hover_width = max(hover_font.measure(label) for label in hover_labels) + 30
        except RuntimeError:
            hover_width = max(len(label) for label in hover_labels) * 8 + 30
        self.hover_preview_btn = PhoenixButton(
            group,
            text=hover_labels[0] if getattr(self, "hover_preview_enabled", True) else hover_labels[1],
            command=self._toggle_hover_preview,
            button_type="neutral",
            icon_name="image",
            icon_color=PHOENIX_THEME.danger,
            width=hover_width,
            height=30,
            radius=6,
        )
        self.hover_preview_btn.pack(side="left")
        return group

    def _build_refresh_group(self) -> tk.Frame:
        from app.i18n import tr
        group = self.group_frame()
        self.refresh_btn = PhoenixButton(
            group,
            text=tr("refresh", "Aktualisieren"),
            command=self.on_refresh,
            button_type="neutral",
            icon_name="refresh",
            icon_color=PHOENIX_THEME.accent,
            width=self.BUTTON_WIDTH_REFRESH,
            height=30,
            radius=6,
        )
        self.refresh_btn.pack(side="left")
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

    def _build_dropdown_group(
        self,
        label: str,
        variable: tk.StringVar,
        values: tuple[str, ...],
        width: int,
        callback: Callable[[str], None],
    ) -> tuple[tk.Frame, tk.Widget]:
        group = self.group_frame()
        dropdown = self.toolbar_dropdown(
            group,
            label,
            variable,
            values,
            width,
            callback,
        )
        dropdown.pack(side="left")
        return group, dropdown

    def _layout_toolbar_groups(self, event: tk.Event) -> None:
        available_width = max(1, event.width - 2 * PHOENIX_THEME.space_md)
        group_widths = {group: group.winfo_reqwidth() for group in self.toolbar_groups}
        total_width = sum(group_widths.values()) + PHOENIX_THEME.space_sm * (len(self.toolbar_groups) - 1)
        if total_width <= available_width:
            layout = (self.toolbar_groups,)
        else:
            action_rows = self._wrap_groups(self.toolbar_groups[:3], group_widths, available_width)
            view_rows = self._wrap_groups(self.toolbar_groups[4:], group_widths, available_width)
            layout = (*action_rows, (self.search_group,), *view_rows)
        self._apply_toolbar_layout(layout)

    @staticmethod
    def _wrap_groups(
        groups: tuple[tk.Frame, ...],
        widths: dict[tk.Frame, int],
        available_width: int,
    ) -> tuple[tuple[tk.Frame, ...], ...]:
        rows: list[tuple[tk.Frame, ...]] = []
        row: list[tk.Frame] = []
        row_width = 0
        for group in groups:
            width = widths[group]
            required_width = width if not row else row_width + PHOENIX_THEME.space_sm + width
            if row and required_width > available_width:
                rows.append(tuple(row))
                row = []
                row_width = 0
            row.append(group)
            row_width = width if row_width == 0 else row_width + PHOENIX_THEME.space_sm + width
        if row:
            rows.append(tuple(row))
        return tuple(rows)

    def _apply_toolbar_layout(self, layout: tuple[tuple[tk.Frame, ...], ...]) -> None:
        if layout == self._toolbar_layout:
            return
        for group in self.toolbar_groups:
            group.grid_forget()
        for column in range(len(self.toolbar_groups)):
            self.grid_columnconfigure(column, weight=0)
        for row_index, row_groups in enumerate(layout):
            if row_groups == (self.search_group,):
                self.grid_columnconfigure(0, weight=1)
                self.search_group.grid(
                    row=row_index,
                    column=0,
                    columnspan=len(self.toolbar_groups),
                    sticky="ew",
                    padx=PHOENIX_THEME.space_md,
                    pady=(PHOENIX_THEME.space_md, 0),
                )
                continue
            for column, group in enumerate(row_groups):
                if group is self.search_group:
                    self.grid_columnconfigure(column, weight=1)
                group.grid(
                    row=row_index,
                    column=column,
                    sticky="ew" if group is self.search_group else "w",
                    padx=(PHOENIX_THEME.space_md if column == 0 else PHOENIX_THEME.space_sm, 0),
                    pady=(PHOENIX_THEME.space_md, 0),
                )
        self._toolbar_layout = layout

    def _toggle_hover_preview(self) -> None:
        from app.i18n import tr
        self.hover_preview_enabled = not self.hover_preview_enabled
        self.hover_preview_btn.configure(
            text=tr("gallery_hover_preview_on", "Hover-Vorschau: Ein") if self.hover_preview_enabled else tr("gallery_hover_preview_off", "Hover-Vorschau: Aus"),
            icon_color=PHOENIX_THEME.danger,
        )
        self.on_hover_preview_change(self.hover_preview_enabled)

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
