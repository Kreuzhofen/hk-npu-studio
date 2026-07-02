from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixProgressCard(tk.Frame):
    """Reusable dashboard progress card."""

    def __init__(
        self,
        master: tk.Misc,
        title: str = "Progress",
        current: int = 0,
        total: int = 0,
        percent: int = 0,
        detail: str = "",
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )

        self._title_var = tk.StringVar(value=title)
        self._progress_var = tk.StringVar(value=self._format_progress(current, total, percent))
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
        ).pack(fill="x", padx=16, pady=(14, 4))

        tk.Label(
            self,
            textvariable=self._progress_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16)

        self._bar_outer = tk.Frame(
            self,
            bg=PHOENIX_THEME.border,
            height=8,
        )
        self._bar_outer.pack(fill="x", padx=16, pady=(10, 6))
        self._bar_outer.pack_propagate(False)

        self._bar_inner = tk.Frame(
            self._bar_outer,
            bg=PHOENIX_THEME.accent,
            height=8,
        )
        self._bar_inner.place(x=0, y=0, relheight=1.0, relwidth=0.0)

        tk.Label(
            self,
            textvariable=self._detail_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=520,
        ).pack(fill="x", padx=16, pady=(4, 14))

    def update(
        self,
        *,
        title: str | None = None,
        current: int | None = None,
        total: int | None = None,
        percent: int | None = None,
        detail: str | None = None,
    ) -> None:
        if title is not None:
            self._title_var.set(title)

        resolved_current = current if current is not None else 0
        resolved_total = total if total is not None else 0
        resolved_percent = percent if percent is not None else 0

        self._progress_var.set(
            self._format_progress(
                resolved_current,
                resolved_total,
                resolved_percent,
            )
        )
        self._bar_inner.place_configure(
            relwidth=max(0.0, min(1.0, resolved_percent / 100))
        )

        if detail is not None:
            self._detail_var.set(detail)

    def configure_content(
        self,
        *,
        title: str | None = None,
        current: int | None = None,
        total: int | None = None,
        percent: int | None = None,
        detail: str | None = None,
    ) -> None:
        self.update(
            title=title,
            current=current,
            total=total,
            percent=percent,
            detail=detail,
        )

    def _format_progress(self, current: int, total: int, percent: int) -> str:
        if total <= 0:
            return "0 / 0 · 0 %"

        return f"{current} / {total} · {percent} %"