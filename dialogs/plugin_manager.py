"""
Snapdragon AI Studio

Plugin Manager Dialog

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk


class PluginManagerDialog(tk.Toplevel):

    def __init__(self, master):
        super().__init__(master)

        self.title("Plugin Manager")
        self.geometry("520x360")
        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):

        title = tk.Label(
            self,
            text="Snapdragon AI Studio Plugin Manager",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        title.pack(fill="x", padx=15, pady=(15, 8))

        info = tk.Label(
            self,
            text=(
                "Aktuell installiert:\n\n"
                "• RealESRGAN\n"
                "  Typ: Image Upscale\n"
                "  Backend: QNN / Snapdragon NPU\n"
                "  Status: Bereit\n\n"
                "Weitere Plugins folgen in späteren Sprints."
            ),
            justify="left",
            anchor="nw",
        )
        info.pack(fill="both", expand=True, padx=15, pady=8)

        close_button = tk.Button(
            self,
            text="Schließen",
            command=self.destroy,
        )
        close_button.pack(pady=(0, 15))
