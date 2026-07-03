"""
Snapdragon AI Studio

About Dialog

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from engine.brand_manager import BrandManager
from resources.theme import Theme


class AboutDialog(tk.Toplevel):

    def __init__(self, master, brand: BrandManager):
        super().__init__(master)

        self.brand = brand
        self.logo_image = None

        self.title(f"About {self.brand.app_name()}")
        self.resizable(False, False)
        self.configure(bg=Theme.color("background"))

        self.transient(master)
        self.grab_set()

        self._build_ui()
        self._center(master)

    def _build_ui(self):
        container = tk.Frame(
            self,
            bg=Theme.color("card"),
            bd=1,
            relief="solid",
            highlightbackground=Theme.color("border"),
            padx=28,
            pady=24,
        )
        container.pack(fill="both", expand=True, padx=16, pady=16)

        logo_path = self.brand.png(128)
        if logo_path.exists():
            logo = Image.open(logo_path).convert("RGBA")
            self.logo_image = ImageTk.PhotoImage(logo)
            logo_label = tk.Label(
                container,
                image=self.logo_image,
                bg=Theme.color("card"),
                bd=0,
            )
            logo_label.pack(anchor="center", pady=(0, 12))

        title = tk.Label(
            container,
            text=self.brand.app_name(),
            font=Theme.font("title"),
            fg=Theme.color("text"),
            bg=Theme.color("card"),
        )
        title.pack(anchor="center")

        version = tk.Label(
            container,
            text=self.brand.version_string(),
            font=Theme.font("small"),
            fg=Theme.color("muted_text"),
            bg=Theme.color("card"),
        )
        version.pack(anchor="center", pady=(4, 12))

        slogan = tk.Label(
            container,
            text=self.brand.slogan(),
            font=Theme.font("button"),
            fg=Theme.color("text"),
            bg=Theme.color("card"),
        )
        slogan.pack(anchor="center", pady=(0, 18))

        separator_1 = ttk.Separator(container, orient="horizontal")
        separator_1.pack(fill="x", pady=(0, 18))

        description = tk.Label(
            container,
            text=self.brand.about_description(),
            font=Theme.font("small"),
            fg=Theme.color("muted_text"),
            bg=Theme.color("card"),
            justify="center",
        )
        description.pack(anchor="center", pady=(0, 18))

        engine = tk.Label(
            container,
            text=self.brand.engine(),
            font=Theme.font("button"),
            fg=Theme.color("text"),
            bg=Theme.color("card"),
        )
        engine.pack(anchor="center", pady=(0, 18))

        separator_2 = ttk.Separator(container, orient="horizontal")
        separator_2.pack(fill="x", pady=(0, 18))

        created = tk.Label(
            container,
            text="Created and maintained by",
            font=Theme.font("small"),
            fg=Theme.color("muted_text"),
            bg=Theme.color("card"),
        )
        created.pack(anchor="center")

        author = tk.Label(
            container,
            text=self.brand.author(),
            font=Theme.font("button"),
            fg=Theme.color("text"),
            bg=Theme.color("card"),
        )
        author.pack(anchor="center", pady=(4, 12))

        copyright_label = tk.Label(
            container,
            text=self.brand.copyright(),
            font=Theme.font("small"),
            fg=Theme.color("muted_text"),
            bg=Theme.color("card"),
        )
        copyright_label.pack(anchor="center", pady=(0, 18))

        assistance_label = tk.Label(
            container,
            text=self.brand.ai_assistance(),
            font=Theme.font("small"),
            fg=Theme.color("muted_text"),
            bg=Theme.color("card"),
        )
        assistance_label.pack(anchor="center", pady=(0, 18))

        ok_button = tk.Button(
            container,
            text="OK",
            command=self.destroy,
            font=Theme.font("button"),
            width=12,
        )
        ok_button.pack(anchor="center")

        self.bind("<Escape>", lambda _event: self.destroy())

    def _center(self, master):
        self.update_idletasks()

        width = self.winfo_width()
        height = self.winfo_height()

        master_x = master.winfo_rootx()
        master_y = master.winfo_rooty()
        master_width = master.winfo_width()
        master_height = master.winfo_height()

        x = master_x + (master_width // 2) - (width // 2)
        y = master_y + (master_height // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")
