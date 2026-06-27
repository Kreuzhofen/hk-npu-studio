"""
SnapdragonAI Studio

Dashboard Page

Created by Holger Kreuzhofen
Phoenix Architecture
"""

import tkinter as tk

from engine.hardware_manager import HardwareManager


BG = "#101418"
PANEL = "#171d23"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"
GREEN = "#22c55e"
WARNING = "#f59e0b"


class DashboardPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)

        self.hardware = HardwareManager()
        self.info = self.hardware.get_system_info()

        self.build()

    def card(self, parent, title, lines, status=None, color=GREEN):
        box = tk.Frame(parent, bg=PANEL)
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
        tk.Label(
            self,
            text="Willkommen zurück, Holger 👋",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 24, "bold"),
        ).pack(anchor="w", padx=24, pady=(24, 6))

        tk.Label(
            self,
            text="SnapdragonAI Studio Phoenix Preview",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 11),
        ).pack(anchor="w", padx=24, pady=(0, 18))

        arm_status = "🟢 ARM64 erkannt" if self.info["is_arm64"] else "🟡 Nicht ARM64"
        qnn_status = "🟢 QNN bereit" if self.info["qnn_available"] else "🟡 QNN nicht gefunden"

        self.card(
            self,
            "💻 System",
            [
                f"Windows: {self.info['windows']}",
                f"Architektur: {self.info['machine']}",
                f"Prozessor: {self.info['processor']}",
                f"Python: {self.info['python']}",
                f"RAM: {self.info['ram_gb']} GB",
            ],
            arm_status,
            GREEN if self.info["is_arm64"] else WARNING,
        )

        self.card(
            self,
            "⚡ Snapdragon / QNN",
            [
                "Qualcomm AI Stack wird geprüft",
                r"QNN Backend: C:\Qualcomm\AIStack\2.47.0.260601",
                "NPU-Ziel: Snapdragon X",
            ],
            qnn_status,
            GREEN if self.info["qnn_available"] else WARNING,
        )

        self.card(
            self,
            "📦 AI Library",
            [
                "Modelle, Plugins, Workflows und spätere Downloads",
                "RealESRGAN als erstes NPU-Modul vorhanden",
                "AI Generate vorbereitet",
            ],
            "🟡 Im Aufbau",
            WARNING,
        )

        self.card(
            self,
            "🚀 Quick Actions",
            [
                "Generate",
                "Upscale",
                "AI Edit",
                "Whisper",
                "Chat",
            ],
            "🟡 Phoenix Preview",
            WARNING,
        )