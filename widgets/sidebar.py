"""
HK NPU STUDIO

Sidebar Widget

Created by Holger Kreuzhofen
"""

import tkinter as tk

from engine.brand_manager import BrandManager


BG = "#171d23"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"
ACCENT = "#3b82f6"


class Sidebar(tk.Frame):
    def __init__(self, parent, on_navigate):
        super().__init__(parent, bg=BG, width=230)

        self.on_navigate = on_navigate
        self.buttons = {}

        self.pack_propagate(False)
        self.build()

    def nav_button(self, key, text):
        b = tk.Button(
            self,
            text=text,
            anchor="w",
            relief="flat",
            bd=0,
            bg=BG,
            fg=TEXT,
            activebackground=ACCENT,
            activeforeground="white",
            font=("Segoe UI", 11),
            padx=18,
            pady=10,
            cursor="hand2",
            command=lambda: self.navigate(key),
        )

        b.pack(fill="x", pady=2)
        self.buttons[key] = b

    def navigate(self, key):
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, active_key):
        for key, button in self.buttons.items():
            if key == active_key:
                button.configure(bg=ACCENT, fg="white")
            else:
                button.configure(bg=BG, fg=TEXT)

    def build(self):
        tk.Label(
            self,
            text=BrandManager.HEADER_BRAND_NAME,
            bg=BG,
            fg="white",
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(24, 4))

        tk.Label(
            self,
            text=BrandManager.SLOGAN,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(pady=(0, 18))

        self.nav_button("dashboard", "🏠 Dashboard")
        self.nav_button("generate", "🎨 Generate")
        self.nav_button("edit", "🖌 AI Edit")
        self.nav_button("upscale", "🖼 Upscale")
        self.nav_button("video", "🎬 Video")
        self.nav_button("audio", "🎤 Audio")
        self.nav_button("chat", "💬 Chat")
        self.nav_button("library", "📦 AI Library")
        self.nav_button("settings", "⚙ Settings")
        self.nav_button("about", "❓ About")

        self.set_active("dashboard")
