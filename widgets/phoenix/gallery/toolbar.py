from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from widgets.phoenix.theme import PHOENIX_THEME


class GalleryToolbar(tk.Frame):
    """Professional toolbar for the Gallery Workspace."""

    SORT_OPTIONS = ("Name", "Datum", "Größe", "Typ")
    SIZE_OPTIONS = ("Klein", "Mittel", "Groß", "Sehr groß")
    PLACEHOLDER = "Suchen…"
    BUTTON_WIDTH_OPEN = 136
    BUTTON_WIDTH_REFRESH = 128
    BUTTON_WIDTH_FILTER = 96
    DROPDOWN_WIDTH_SORT = 122
    DROPDOWN_WIDTH_SIZE = 136

    def __init__(
        self,
        master: tk.Misc,
        on_open_folder: Callable[[], None],
        on_refresh: Callable[[], None],
        on_thumbnail_size_change: Callable[[str], None],
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.on_open_folder = on_open_folder
        self.on_refresh = on_refresh
        self.on_thumbnail_size_change = on_thumbnail_size_change
        self.search_value = tk.StringVar(value=self.PLACEHOLDER)
        self.sort_value = tk.StringVar(value=self.SORT_OPTIONS[0])
        self.size_value = tk.StringVar(value=self.SIZE_OPTIONS[1])

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
        group = self._group_frame()
        self._button(group, "▣  Ordner öffnen", self.on_open_folder, self.BUTTON_WIDTH_OPEN).pack(
            side="left"
        )
        self._separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self._button(group, "↻  Aktualisieren", self.on_refresh, self.BUTTON_WIDTH_REFRESH).pack(
            side="left"
        )
        return group

    def _build_search_group(self) -> tk.Frame:
        group = self._group_frame()
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
            text="⌕",
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
        return group

    def _build_view_group(self) -> tk.Frame:
        group = self._group_frame()
        self._dropdown(
            group,
            "Sortieren",
            self.sort_value,
            self.SORT_OPTIONS,
            self.DROPDOWN_WIDTH_SORT,
            None,
        ).pack(side="left")
        self._dropdown(
            group,
            "Größe",
            self.size_value,
            self.SIZE_OPTIONS,
            self.DROPDOWN_WIDTH_SIZE,
            self.on_thumbnail_size_change,
        ).pack(side="left", padx=(PHOENIX_THEME.space_sm, 0))
        self._separator(group).pack(side="left", fill="y", padx=PHOENIX_THEME.space_sm)
        self._button(group, "⧉  Filter", self._noop, self.BUTTON_WIDTH_FILTER).pack(side="left")
        return group

    def _group_frame(self) -> tk.Frame:
        return tk.Frame(self, bg=PHOENIX_THEME.card_bg)

    def _button(
        self,
        master: tk.Misc,
        text: str,
        command: Callable[[], None],
        width_px: int,
    ) -> tk.Button:
        button = tk.Button(
            master,
            text=text,
            command=command,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_button,
            padx=PHOENIX_THEME.button_pad_x,
            pady=PHOENIX_THEME.button_pad_y,
            cursor="hand2",
            anchor="center",
        )
        button.configure(width=max(1, width_px // 9))
        return button

    def _dropdown(
        self,
        master: tk.Misc,
        label: str,
        variable: tk.StringVar,
        values: tuple[str, ...],
        width_px: int,
        callback: Callable[[str], None] | None,
    ) -> tk.Menubutton:
        button = tk.Menubutton(
            master,
            textvariable=variable,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_button,
            padx=PHOENIX_THEME.button_pad_x,
            pady=PHOENIX_THEME.button_pad_y,
            cursor="hand2",
            indicatoron=True,
            width=max(1, width_px // 9),
        )
        menu = tk.Menu(
            button,
            tearoff=False,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_body,
        )
        for value in values:
            menu.add_command(
                label=f"{label}: {value}",
                command=lambda item=value: self._set_dropdown_value(variable, item, callback),
            )
        button.configure(menu=menu)
        return button

    def _set_dropdown_value(
        self,
        variable: tk.StringVar,
        value: str,
        callback: Callable[[str], None] | None,
    ) -> None:
        variable.set(value)
        if callback is not None:
            callback(value)

    def _separator(self, master: tk.Misc) -> tk.Frame:
        return tk.Frame(master, bg=PHOENIX_THEME.border, width=1)

    def _clear_search_placeholder(self, _event: tk.Event) -> None:
        if self.search_value.get() == self.PLACEHOLDER:
            self.search_value.set("")
            self.search_entry.configure(fg=PHOENIX_THEME.text_primary)

    def _restore_search_placeholder(self, _event: tk.Event) -> None:
        if not self.search_value.get():
            self.search_value.set(self.PLACEHOLDER)
            self.search_entry.configure(fg=PHOENIX_THEME.text_muted)

    def _noop(self) -> None:
        return None
