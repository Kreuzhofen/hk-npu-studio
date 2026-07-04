from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixActivityCard(tk.Frame):
    """Reusable card for recent Phoenix dashboard activity."""

    def __init__(
        self,
        master: tk.Misc,
        title: str = "Aktivität",
        activity: tuple[str, ...] = (),
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            height=150,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._title_var = tk.StringVar(value=title)
        self._activity_var = tk.StringVar(value=self._format_activity(activity))

        self._build()

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

        tk.Label(
            self,
            textvariable=self._activity_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="nw",
            justify="left",
            wraplength=760,
        ).pack(fill="both", expand=True, padx=PHOENIX_THEME.card_pad_x, pady=(PHOENIX_THEME.space_xs, PHOENIX_THEME.card_pad_y))

    def update(
        self,
        *,
        title: str | None = None,
        activity: tuple[str, ...] | None = None,
    ) -> None:
        if title is not None:
            self._title_var.set(title)

        if activity is not None:
            self._activity_var.set(self._format_activity(activity))

    def configure_content(
        self,
        *,
        title: str | None = None,
        activity: tuple[str, ...] | None = None,
    ) -> None:
        self.update(title=title, activity=activity)

    def _format_activity(self, activity: tuple[str, ...]) -> str:
        if not activity:
            return "Noch keine Aktivität"

        return "\n".join(activity[-5:])

