"""
Snapdragon AI Studio

Phoenix Header

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk

from engine.brand_manager import BrandManager
from resources.theme import Theme


class Header(tk.Frame):

    def __init__(self, master, brand: BrandManager):
        super().__init__(
            master,
            bg=Theme.color("card"),
            bd=1,
            relief="solid",
            highlightbackground=Theme.color("border"),
            padx=16,
            pady=10,
        )

        self.brand = brand
        self._build_ui()

    def _build_ui(self):

        content = tk.Frame(self, bg=Theme.color("card"))
        content.pack(fill="x")

        logo_frame = tk.Frame(
            content,
            bg=Theme.color("card"),
            width=48,
            height=48,
        )
        logo_frame.pack(side="left", padx=(0, 16))
        logo_frame.pack_propagate(False)

        left = tk.Frame(content, bg=Theme.color("card"))
        left.pack(side="left", fill="y")

        self.title_label = tk.Label(
            left,
            text=self.brand.app_name(),
            font=Theme.font("title"),
            fg=Theme.color("text"),
            bg=Theme.color("card"),
            anchor="w",
        )
        self.title_label.pack(anchor="w")

        self.slogan_label = tk.Label(
            left,
            text=self.brand.slogan(),
            font=Theme.font("small"),
            fg=Theme.color("muted_text"),
            bg=Theme.color("card"),
            anchor="w",
        )
        self.slogan_label.pack(anchor="w")

        right = tk.Frame(content, bg=Theme.color("card"))
        right.pack(side="right", fill="y")

        self.version_label = tk.Label(
            right,
            text=f"Version {self.brand.version()}",
            font=Theme.font("small"),
            fg=Theme.color("muted_text"),
            bg=Theme.color("card"),
        )
        self.version_label.pack(anchor="e")