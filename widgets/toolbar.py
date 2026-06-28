"""
SnapdragonAI Studio

Toolbar Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk


class Toolbar(tk.Frame):

    def __init__(
        self,
        master,
        on_select_images=None,
        on_start=None,
        on_open_output=None,
        on_open_plugin_manager=None,
    ):
        super().__init__(master, bd=1, relief="groove", padx=8, pady=6)

        self.on_select_images = on_select_images
        self.on_start = on_start
        self.on_open_output = on_open_output
        self.on_open_plugin_manager = on_open_plugin_manager

        self._build_ui()

    def _build_ui(self):

        self.select_button = tk.Button(
            self,
            text="Bilder auswählen",
            command=self.on_select_images,
            width=18,
        )
        self.select_button.pack(side="left", padx=4)

        self.start_button = tk.Button(
            self,
            text="Start",
            command=self.on_start,
            width=12,
        )
        self.start_button.pack(side="left", padx=4)

        self.output_button = tk.Button(
            self,
            text="Output öffnen",
            command=self.on_open_output,
            state="disabled",
            width=16,
        )
        self.output_button.pack(side="left", padx=4)

        self.plugin_manager_button = tk.Button(
            self,
            text="Plugin Manager",
            command=self.on_open_plugin_manager,
            width=18,
        )
        self.plugin_manager_button.pack(side="left", padx=4)

    def enable_output_button(self):
        self.output_button.configure(state="normal")

    def disable_output_button(self):
        self.output_button.configure(state="disabled")

    def enable_start_button(self):
        self.start_button.configure(state="normal")

    def disable_start_button(self):
        self.start_button.configure(state="disabled")

    def enable_select_button(self):
        self.select_button.configure(state="normal")

    def disable_select_button(self):
        self.select_button.configure(state="disabled")