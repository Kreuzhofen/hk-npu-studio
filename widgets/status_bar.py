"""
Snapdragon AI Studio

Status Bar Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk

from engine.brand_manager import BrandManager
from resources.theme import Theme


class StatusBar(tk.Frame):

    def __init__(self, master):
        super().__init__(
            master,
            bd=1,
            relief="solid",
            padx=Theme.spacing("medium"),
            pady=3,
            bg=Theme.color("card"),
            highlightbackground=Theme.color("border"),
        )

        self._build_ui()

    def _build_ui(self):

        self.status_label = tk.Label(
            self,
            text="",
            anchor="w",
            font=Theme.font("small"),
            bg=Theme.color("card"),
            fg=Theme.color("muted_text"),
        )
        self.status_label.pack(fill="x")

        self.set_status(
            engine_status="Ready",
            queue_count=0,
            worker_status="Idle",
            backend="QNN",
            percent=0,
        )

    def set_status(
        self,
        engine_status="Ready",
        queue_count=0,
        worker_status="Idle",
        backend="QNN",
        percent=0,
    ):
        text = (
            f"{BrandManager.ENGINE_NAME} │ "
            f"{engine_status} │ "
            f"Queue: {queue_count} │ "
            f"Worker: {worker_status} │ "
            f"Backend: {backend} │ "
            f"{percent}% │ "
            f"v{BrandManager.APP_VERSION}"
        )

        self.status_label.configure(text=text)

        status_lower = engine_status.lower()

        if "running" in status_lower or "läuft" in status_lower:
            self.status_label.configure(fg=Theme.color("info"))
        elif "fehler" in status_lower or "error" in status_lower:
            self.status_label.configure(fg=Theme.color("error"))
        elif "stopped" in status_lower or "abbruch" in status_lower:
            self.status_label.configure(fg=Theme.color("warning"))
        else:
            self.status_label.configure(fg=Theme.color("muted_text"))