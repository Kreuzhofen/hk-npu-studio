from __future__ import annotations

import tkinter as tk

from engine.brand_manager import BrandManager
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixHeader(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.header_bg, height=60)
        self.grid_propagate(False)
        self.pack_propagate(False)

        self.title_label: tk.Label
        self.view_label: tk.Label
        self.brand = getattr(self.winfo_toplevel(), "brand", BrandManager())
        self.logo_image: tk.PhotoImage | None = None

        self._build()

    def _build(self) -> None:
        left = tk.Frame(self, bg=PHOENIX_THEME.header_bg)
        left.pack(side="left", fill="y", padx=PHOENIX_THEME.space_lg)

        logo_path = BrandManager.png(32)
        if logo_path.exists():
            self.logo_image = tk.PhotoImage(file=str(logo_path))
            tk.Label(
                left,
                image=self.logo_image,
                bg=PHOENIX_THEME.header_bg,
                bd=0,
            ).pack(side="left", padx=(0, PHOENIX_THEME.space_md), pady=14)

        title_group = tk.Frame(left, bg=PHOENIX_THEME.header_bg)
        title_group.pack(side="left", fill="y")

        self.title_label = tk.Label(
            title_group,
            text=self.brand.app_name(),
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        )
        self.title_label.pack(side="top", anchor="w", pady=(8, 0))

        self.view_label = tk.Label(
            title_group,
            text="Home",
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        self.view_label.pack(side="top", anchor="w", pady=(0, 7))

        badge = tk.Label(
            self,
            text=self.brand.slogan(),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_card_title,
            padx=PHOENIX_THEME.space_md,
            pady=PHOENIX_THEME.space_xs,
        )
        badge.pack(side="right", padx=PHOENIX_THEME.space_lg)

    def set_view(self, title: str) -> None:
        self.view_label.configure(text=title)
