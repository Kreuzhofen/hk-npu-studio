from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from widgets.phoenix.theme import PHOENIX_THEME


class GalleryToolbar(tk.Frame):
    """Professional toolbar foundation for the Gallery Workspace."""

    SORT_OPTIONS = ("Name", "Datum", "Größe", "Typ")
    SIZE_OPTIONS = ("Klein", "Mittel", "Groß", "Sehr groß")

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.search_value = tk.StringVar(value="Suchen…")
        self.sort_value = tk.StringVar(value=self.SORT_OPTIONS[0])
        self.size_value = tk.StringVar(value=self.SIZE_OPTIONS[1])

        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(2, weight=1)

        self._button("Ordner öffnen", self._noop).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_sm),
            pady=PHOENIX_THEME.space_sm,
        )
        self._button("Aktualisieren", self._noop).grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, PHOENIX_THEME.space_md),
            pady=PHOENIX_THEME.space_sm,
        )

        search_host = self._field_frame()
        search_host.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(0, PHOENIX_THEME.space_md),
            pady=PHOENIX_THEME.space_sm,
        )
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
        self.search_entry.pack(fill="both", expand=True, padx=PHOENIX_THEME.space_md)
        self.search_entry.bind("<FocusIn>", self._clear_search_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_search_placeholder)

        self._dropdown(self.sort_value, self.SORT_OPTIONS).grid(
            row=0,
            column=3,
            sticky="e",
            padx=(0, PHOENIX_THEME.space_sm),
            pady=PHOENIX_THEME.space_sm,
        )
        self._dropdown(self.size_value, self.SIZE_OPTIONS).grid(
            row=0,
            column=4,
            sticky="e",
            padx=(0, PHOENIX_THEME.space_sm),
            pady=PHOENIX_THEME.space_sm,
        )
        self._button("Filter", self._noop).grid(
            row=0,
            column=5,
            sticky="e",
            padx=(0, PHOENIX_THEME.space_md),
            pady=PHOENIX_THEME.space_sm,
        )

    def _button(self, text: str, command: Callable[[], None]) -> tk.Button:
        return tk.Button(
            self,
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
        )

    def _field_frame(self) -> tk.Frame:
        return tk.Frame(
            self,
            bg=PHOENIX_THEME.elevated_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            height=36,
        )

    def _dropdown(self, variable: tk.StringVar, values: tuple[str, ...]) -> tk.Menubutton:
        button = tk.Menubutton(
            self,
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
            menu.add_command(label=value, command=lambda item=value: variable.set(item))
        button.configure(menu=menu)
        return button

    def _clear_search_placeholder(self, _event: tk.Event) -> None:
        if self.search_value.get() == "Suchen…":
            self.search_value.set("")
            self.search_entry.configure(fg=PHOENIX_THEME.text_primary)

    def _restore_search_placeholder(self, _event: tk.Event) -> None:
        if not self.search_value.get():
            self.search_value.set("Suchen…")
            self.search_entry.configure(fg=PHOENIX_THEME.text_muted)

    def _noop(self) -> None:
        return None
