from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixStatusCard(tk.Frame):
    """Reusable dashboard status card."""

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        value: str,
        detail: str = "",
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            height=156,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._title_var = tk.StringVar(value=title)
        self._value_var = tk.StringVar(value=value)
        self._detail_var = tk.StringVar(value=detail)

        self._build()
        self.bind("<Configure>", self._update_wraplengths)

    def _build(self) -> None:
        tk.Label(
            self,
            textvariable=self._title_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
            height=1,
        ).pack(fill="x", padx=PHOENIX_THEME.card_pad_x, pady=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_sm))

        self._value_label = tk.Label(
            self,
            textvariable=self._value_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_value,
            anchor="w",
            justify="left",
        )
        self._value_label.pack(fill="x", padx=PHOENIX_THEME.card_pad_x)

        self._detail_label = tk.Label(
            self,
            textvariable=self._detail_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left",
            wraplength=360,
        )
        self._detail_label.pack(fill="x", padx=PHOENIX_THEME.card_pad_x, pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.space_lg))

        self._update_detail_visibility()

    def _update_wraplengths(self, _event: tk.Event | None = None) -> None:
        wraplength = max(80, self.winfo_width() - (PHOENIX_THEME.card_pad_x * 2))
        self._value_label.configure(wraplength=wraplength)
        self._detail_label.configure(wraplength=wraplength)

    def update(
        self,
        *,
        title: str | None = None,
        value: str | None = None,
        detail: str | None = None,
    ) -> None:
        """Update the card content without recreating widgets."""

        if title is not None:
            self._title_var.set(title)

        if value is not None:
            self._value_var.set(value)

        if detail is not None:
            self._detail_var.set(detail)

        self._update_detail_visibility()

    def configure_content(
        self,
        *,
        title: str | None = None,
        value: str | None = None,
        detail: str | None = None,
    ) -> None:
        """Compatibility wrapper for older code."""
        self.update(title=title, value=value, detail=detail)

    def _update_detail_visibility(self) -> None:
        if self._detail_var.get().strip():
            self._detail_label.pack_configure(pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.space_lg))
        else:
            self._detail_label.pack_configure(pady=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_lg))
