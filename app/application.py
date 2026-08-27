"""
HK NPU STUDIO

Phoenix Application

Created by Holger Kreuzhofen
"""

import tkinter as tk

import version
from widgets.sidebar import Sidebar
from pages.dashboard import DashboardPage
from pages.library import LibraryPage


BG = "#101418"
PANEL = "#171d23"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"


class PlaceholderPage(tk.Frame):
    def __init__(self, parent, title, subtitle):
        super().__init__(parent, bg=BG)

        tk.Label(
            self,
            text=title,
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 24, "bold"),
        ).pack(anchor="w", padx=24, pady=(24, 6))

        tk.Label(
            self,
            text=subtitle,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 11),
        ).pack(anchor="w", padx=24, pady=(0, 18))


class PhoenixApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(version.APP_NAME)
        self.root.geometry("1400x800")
        self.root.configure(bg=BG)

        self.pages = {}
        self.current_page = None

    def run(self):
        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True)

        self.sidebar = Sidebar(container, self.show_page)
        self.sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(container, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        self.create_pages()
        self.show_page("dashboard")

        self.root.mainloop()

    def create_pages(self):
        self.pages["dashboard"] = DashboardPage(self.content)
        self.pages["library"] = LibraryPage(self.content)

        self.pages["generate"] = PlaceholderPage(
            self.content,
            "AI Generate",
            "Prompt-zu-Bild wird hier integriert.",
        )

        self.pages["edit"] = PlaceholderPage(
            self.content,
            "AI Edit",
            "Inpainting, Objekt entfernen und Bildbearbeitung werden hier integriert.",
        )

        self.pages["upscale"] = PlaceholderPage(
            self.content,
            "Upscale",
            "RealESRGAN und andere Upscaler werden hier integriert.",
        )

        self.pages["video"] = PlaceholderPage(
            self.content,
            "Video",
            "Bild-zu-Video und Videoverarbeitung werden hier vorbereitet.",
        )

        self.pages["audio"] = PlaceholderPage(
            self.content,
            "Audio",
            "Whisper und Audiofunktionen werden hier integriert.",
        )

        self.pages["chat"] = PlaceholderPage(
            self.content,
            "Chat",
            "Lokale Sprachmodelle werden hier integriert.",
        )

        self.pages["settings"] = PlaceholderPage(
            self.content,
            "Settings",
            "Einstellungen für Modelle, Pfade, Performance und Design.",
        )

        self.pages["about"] = PlaceholderPage(
            self.content,
            "About",
            f"{version.APP_NAME}\nCreated by {version.AUTHOR}",
        )

    def show_page(self, key):
        if self.current_page:
            self.current_page.pack_forget()

        page = self.pages.get(key)

        if page is None:
            return

        page.pack(fill="both", expand=True)
        self.current_page = page
