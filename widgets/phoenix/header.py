from __future__ import annotations

import tkinter as tk

from PIL import Image, ImageTk

from app.i18n import tr
from engine.brand_manager import BrandManager
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixHeader(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.header_bg)
        self.pack_propagate(True)

        self.title_label: tk.Label
        self.view_label: tk.Label
        self.brand = getattr(self.winfo_toplevel(), "brand", BrandManager())
        self.logo_image: ImageTk.PhotoImage | None = None

        self._build()

    def _build(self) -> None:
        left = tk.Frame(self, bg=PHOENIX_THEME.header_bg)
        left.pack(side="left", fill="y", padx=PHOENIX_THEME.space_lg)

        logo = self.brand.logo_image(48)
        logo = logo.resize((77, 77), Image.Resampling.LANCZOS)
        self.logo_image = ImageTk.PhotoImage(logo, master=self)
        tk.Label(
            left,
            image=self.logo_image,
            bg=PHOENIX_THEME.header_bg,
            bd=0,
        ).pack(side="left", padx=(0, PHOENIX_THEME.space_lg), pady=(6, 7))

        title_group = tk.Frame(left, bg=PHOENIX_THEME.header_bg)
        title_group.pack(side="left", fill="y")

        self.title_label = tk.Label(
            title_group,
            text=self.brand.engine_name(),
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        )
        self.title_label.pack(side="top", anchor="w", pady=(6, 0))

        self.view_label = tk.Label(
            title_group,
            text=f"{self.brand.app_name()} · {tr('nav_home', 'Home')}",
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        self.view_label.pack(side="top", anchor="w", pady=(0, 7))

        release_group = tk.Frame(self, bg=PHOENIX_THEME.header_bg)
        release_group.pack(side="right", fill="y", padx=PHOENIX_THEME.space_lg)

        tk.Label(
            release_group,
            text="Version 2.0.0 RC1",
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_section,
            anchor="e",
        ).pack(side="top", fill="x", anchor="e", pady=(14, 0))

        tk.Label(
            release_group,
            text="© 2026 Holger Kreuzhofen",
            bg=PHOENIX_THEME.header_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="e",
        ).pack(side="top", fill="x", anchor="e", pady=(0, 14))

    def set_view(self, title: str) -> None:
        self.view_label.configure(text=f"{self.brand.app_name()} · {title}")
