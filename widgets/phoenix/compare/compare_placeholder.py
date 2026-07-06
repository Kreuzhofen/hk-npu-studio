from __future__ import annotations

import tkinter as tk

from resources.icons import IconManager
from widgets.phoenix.theme import PHOENIX_THEME


class ComparePlaceholder(tk.Frame):
    """A premium, responsive placeholder widget for the Compare Workspace panels."""

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        subtitle: str,
        icon_name: str,
    ) -> None:
        super().__init__(master, bg=PHOENIX_THEME.card_bg)
        self.title = title
        self.subtitle = subtitle
        self.icon_name = icon_name
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = tk.Frame(self, bg=PHOENIX_THEME.card_bg)
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # Center content frame to keep elements grouped and centered
        center_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        center_frame.grid(row=0, column=0, sticky="")
        center_frame.grid_columnconfigure(0, weight=1)

        # 1. Accentuated Symbol
        icon_label = tk.Label(
            center_frame,
            text=IconManager.get_symbol(self.icon_name),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=(PHOENIX_THEME.font_title[0], 42, "bold"),
            anchor="center",
        )
        icon_label.grid(row=0, column=0, pady=(0, PHOENIX_THEME.space_md))

        # 2. Main Title
        title_label = tk.Label(
            center_frame,
            text=self.title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="center",
        )
        title_label.grid(row=1, column=0, pady=(0, PHOENIX_THEME.space_xs))

        # 3. Subtitle / Guidance
        subtitle_label = tk.Label(
            center_frame,
            text=self.subtitle,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="center",
            justify="center",
            wraplength=340,
        )
        subtitle_label.grid(row=2, column=0)
