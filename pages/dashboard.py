"""
HK NPU STUDIO

Live Dashboard Page

Created by Holger Kreuzhofen
Phoenix Architecture
"""

import tkinter as tk

from engine.phoenix_core import PhoenixCore


BG = "#101418"
PANEL = "#171d23"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"
GREEN = "#22c55e"
WARNING = "#f59e0b"


class DashboardPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.core = PhoenixCore()
        self.status = self.core.system.get_status()
        self.build()

    def card(self, title, lines, status=None, color=GREEN):
        box = tk.Frame(self, bg=PANEL)
        box.pack(fill="x", padx=24, pady=10)

        tk.Label(
            box,
            text=title,
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 6))

        tk.Label(
            box,
            text="\n".join(lines),
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 10),
            justify="left",
        ).pack(anchor="w", padx=18)

        if status:
            tk.Label(
                box,
                text=status,
                bg=PANEL,
                fg=color,
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", padx=18, pady=(8, 16))

    def build(self):
        hardware = self.status["hardware"]

        qnn_status = "🟢 QNN bereit" if self.status["qnn_available"] else "🟡 QNN nicht gefunden"
        qnn_backend = "detected" if self.status["qnn_available"] else "not detected"
        arm_status = "🟢 ARM64 erkannt" if self.status["is_arm64"] else "🟡 Nicht ARM64"

        tk.Label(
            self,
            text="HK NPU STUDIO",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 24, "bold"),
        ).pack(anchor="w", padx=24, pady=(24, 6))

        tk.Label(
            self,
            text=f'{self.status["app_name"]} v{self.status["version"]} "{self.status["codename"]}" · Created by {self.status["author"]}',
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 11),
        ).pack(anchor="w", padx=24, pady=(0, 18))

        self.card(
            "🧠 Local AI Engine",
            [
                "Status: Online",
                f"Plugins geladen: {self.status['plugin_count']}",
                f"Skills verfügbar: {self.status['skill_count']}",
                f"Skills: {', '.join(self.status['skills']) if self.status['skills'] else 'Keine'}",
            ],
            "🟢 Engine bereit",
            GREEN,
        )

        self.card(
            "💻 System",
            [
                f"Windows: {hardware['windows']}",
                f"Architektur: {hardware['machine']}",
                f"Prozessor: {hardware['processor']}",
                f"Python: {hardware['python']}",
                f"RAM: {hardware['ram_gb']} GB",
            ],
            arm_status,
            GREEN if self.status["is_arm64"] else WARNING,
        )

        self.card(
            "⚡ Snapdragon / QNN",
            [
                "Qualcomm AI Stack wird geprüft",
                f"QNN Backend: {qnn_backend}",
                "NPU-Ziel: Snapdragon X",
            ],
            qnn_status,
            GREEN if self.status["qnn_available"] else WARNING,
        )

        self.card(
            "🚀 Quick Actions",
            [
                "Generate",
                "Upscale",
                "AI Edit",
                "Whisper",
                "Chat",
            ],
            "🟡 In Vorbereitung",
            WARNING,
        )
