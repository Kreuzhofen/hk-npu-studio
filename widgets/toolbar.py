"""
Snapdragon AI Studio

Toolbar Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk

from resources.icons import Icons
from resources.theme import Theme


class Toolbar(tk.Frame):

    def __init__(
        self,
        master,
        on_select_images=None,
        on_select_folder=None,
        on_start=None,
        on_cancel=None,
        on_open_output=None,
        on_open_plugin_manager=None,
    ):
        super().__init__(
            master,
            bg=Theme.color("card"),
            bd=1,
            relief="solid",
            padx=10,
            pady=8,
            highlightbackground=Theme.color("border"),
        )

        self.on_select_images = on_select_images
        self.on_select_folder = on_select_folder
        self.on_start = on_start
        self.on_cancel = on_cancel
        self.on_open_output = on_open_output
        self.on_open_plugin_manager = on_open_plugin_manager

        self._build_ui()

    def _create_group(self, title):
        frame = tk.Frame(self, bg=Theme.color("card"))

        label = tk.Label(
            frame,
            text=title,
            font=Theme.font("small"),
            fg=Theme.color("muted_text"),
            bg=Theme.color("card"),
            anchor="w",
        )
        label.pack(anchor="w")

        button_frame = tk.Frame(frame, bg=Theme.color("card"))
        button_frame.pack(anchor="w", pady=(2, 0))

        return frame, button_frame

    def _button(
        self,
        master,
        text,
        command,
        icon_name=None,
        width=12,
        state="normal",
    ):
        image = Icons.get(icon_name) if icon_name else None

        return tk.Button(
            master,
            text=text,
            image=image,
            compound="left",
            command=command,
            width=width,
            state=state,
            font=Theme.font("button"),
            padx=6,
        )

    def _separator(self):
        separator = tk.Frame(
            self,
            bg=Theme.color("border"),
            width=1,
            height=44,
        )
        separator.pack(side="left", padx=(0, 18), fill="y")

    def _build_ui(self):

        group, frame = self._create_group("IMPORT")

        self.select_button = self._button(
            frame,
            "Bilder",
            self.on_select_images,
            icon_name="images",
            width=105,
        )
        self.select_button.pack(side="left", padx=(0, 4))

        self.folder_button = self._button(
            frame,
            "Ordner",
            self.on_select_folder,
            icon_name="folder",
            width=105,
        )
        self.folder_button.pack(side="left")

        group.pack(side="left", padx=(0, 18))
        self._separator()

        group, frame = self._create_group("VERARBEITUNG")

        self.start_button = self._button(
            frame,
            "Start",
            self.on_start,
            icon_name="play",
            width=95,
        )
        self.start_button.pack(side="left", padx=(0, 4))

        self.cancel_button = self._button(
            frame,
            "Stop",
            self.on_cancel,
            icon_name="stop",
            width=95,
            state="disabled",
        )
        self.cancel_button.pack(side="left")

        group.pack(side="left", padx=(0, 18))
        self._separator()

        group, frame = self._create_group("AUSGABE")

        self.output_button = self._button(
            frame,
            "Output",
            self.on_open_output,
            icon_name="output",
            width=105,
            state="disabled",
        )
        self.output_button.pack(side="left")

        group.pack(side="left", padx=(0, 18))
        self._separator()

        group, frame = self._create_group("SYSTEM")

        self.plugin_manager_button = self._button(
            frame,
            "Plugins",
            self.on_open_plugin_manager,
            icon_name="plugin",
            width=105,
        )
        self.plugin_manager_button.pack(side="left")

        group.pack(side="left")

    def enable_output_button(self):
        self.output_button.configure(state="normal")

    def disable_output_button(self):
        self.output_button.configure(state="disabled")

    def enable_start_button(self):
        self.start_button.configure(state="normal")

    def disable_start_button(self):
        self.start_button.configure(state="disabled")

    def enable_cancel_button(self):
        self.cancel_button.configure(state="normal")

    def disable_cancel_button(self):
        self.cancel_button.configure(state="disabled")

    def enable_select_button(self):
        self.select_button.configure(state="normal")
        self.folder_button.configure(state="normal")

    def disable_select_button(self):
        self.select_button.configure(state="disabled")
        self.folder_button.configure(state="disabled")