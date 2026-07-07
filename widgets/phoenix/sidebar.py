from __future__ import annotations

import tkinter as tk
from typing import Callable

from engine.brand_manager import BrandManager
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixSidebar(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        controller: object | None = None,
        on_navigate: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(master, bg=PHOENIX_THEME.panel_bg, width=220)
        self.controller = controller
        self.on_navigate = on_navigate
        self.grid_propagate(False)
        self.pack_propagate(False)

        self._buttons: dict[str, tk.Button] = {}

        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            text=BrandManager.ENGINE_NAME,
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.space_lg, pady=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_sm))

        tk.Label(
            self,
            text="Workspace 1.0",
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.space_lg, pady=(0, PHOENIX_THEME.space_xl))

        self._nav_button("home", "Home")
        self._nav_button("plugins", "Plugins")
        self._nav_button("settings", "Settings")
        self._nav_button("image", "Image")
        self._nav_button("gallery", "Gallery")
        self._nav_button("compare", "Compare")
        self._nav_button("prompt", "AI Generate")

    def _nav_button(self, view_name: str, text: str) -> None:
        button = tk.Button(
            self,
            text=text,
            command=lambda: self._navigate(view_name),
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_secondary,
            activebackground=PHOENIX_THEME.elevated_bg,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_button,
            anchor="w",
            padx=PHOENIX_THEME.button_pad_x,
            pady=PHOENIX_THEME.space_sm,
            cursor="hand2",
        )
        button.pack(fill="x", padx=PHOENIX_THEME.space_md, pady=PHOENIX_THEME.space_xs)
        self._buttons[view_name] = button

    def _navigate(self, view_name: str) -> None:
        if self.on_navigate is not None:
            self.on_navigate(view_name)

    def set_active(self, view_name: str) -> None:
        for name, button in self._buttons.items():
            if name == view_name:
                button.configure(
                    bg=PHOENIX_THEME.accent,
                    fg=PHOENIX_THEME.text_on_accent,
                    activebackground=PHOENIX_THEME.accent_dark,
                    activeforeground=PHOENIX_THEME.text_on_accent,
                )
            else:
                button.configure(
                    bg=PHOENIX_THEME.panel_bg,
                    fg=PHOENIX_THEME.text_secondary,
                    activebackground=PHOENIX_THEME.elevated_bg,
                    activeforeground=PHOENIX_THEME.text_on_accent,
                )
