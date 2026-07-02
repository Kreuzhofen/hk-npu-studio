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
            height=140,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._title_var = tk.StringVar(value=title)
        self._value_var = tk.StringVar(value=value)
        self._detail_var = tk.StringVar(value=detail)

        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            textvariable=self._title_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            height=1,
        ).pack(fill="x", padx=20, pady=(18, 6))

        tk.Label(
            self,
            textvariable=self._value_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 17, "bold"),
            anchor="w",
            height=1,
        ).pack(fill="x", padx=20)

        self._detail_label = tk.Label(
            self,
            textvariable=self._detail_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 8),
            anchor="w",
            justify="left",
            wraplength=360,
        )
        self._detail_label.pack(fill="x", padx=20, pady=(8, 18))

        self._update_detail_visibility()

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
            self._detail_label.pack_configure(pady=(8, 18))
        else:
            self._detail_label.pack_configure(pady=(2, 18))
