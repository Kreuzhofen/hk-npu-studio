"""
SnapdragonAI Studio

Job Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import time
import tkinter as tk
from tkinter import ttk
from pathlib import Path

from resources.theme import Theme


class JobCard(tk.Frame):

    def __init__(self, master):
        super().__init__(
            master,
            bd=1,
            relief="solid",
            padx=Theme.spacing("card_pad"),
            pady=Theme.spacing("card_pad"),
            bg=Theme.color("card"),
            highlightbackground=Theme.color("border"),
        )

        self.start_time = None
        self.running = False

        self._build_ui()
        self.reset()

    def _build_ui(self):

        self.title_label = tk.Label(
            self,
            text="Job",
            font=Theme.font("card_title"),
            anchor="w",
            bg=Theme.color("card"),
            fg=Theme.color("text"),
        )
        self.title_label.pack(fill="x")

        self.plugin_label = self._make_label()
        self.plugin_label.pack(fill="x", pady=(5, 0))

        self.backend_label = self._make_label()
        self.backend_label.pack(fill="x")

        self.input_label = self._make_label()
        self.input_label.pack(fill="x", pady=(8, 0))

        self.output_label = self._make_label()
        self.output_label.pack(fill="x")

        self.status_label = self._make_label(fg=Theme.color("muted_text"))
        self.status_label.pack(fill="x", pady=(8, 0))

        self.progress_bar = ttk.Progressbar(
            self,
            mode="determinate",
            maximum=100,
            value=0,
        )
        self.progress_bar.pack(fill="x", pady=5)

        self.batch_label = self._make_label()
        self.batch_label.pack(fill="x")

        self.runtime_label = self._make_label()
        self.runtime_label.pack(fill="x")

    def _make_label(self, fg=None):
        return tk.Label(
            self,
            anchor="w",
            font=Theme.font("body"),
            bg=Theme.color("card"),
            fg=fg or Theme.color("text"),
        )

    def reset(self):
        self.start_time = None
        self.running = False

        self.title_label.configure(text="Job")
        self.plugin_label.configure(text="Plugin: -")
        self.backend_label.configure(text="Backend: -")
        self.input_label.configure(text="Eingabe: -")
        self.output_label.configure(text="Ausgabe: -")
        self.status_label.configure(
            text="Status: Bereit",
            fg=Theme.color("muted_text"),
        )
        self.batch_label.configure(text="Batch: 0 / 0 (0%)")
        self.runtime_label.configure(text="Laufzeit: 00:00")

        self.progress_bar.stop()
        self.progress_bar.configure(
            mode="determinate",
            value=0,
        )

    def start_job(self, plugin, backend, input_path):
        self.start_time = time.time()
        self.running = True

        input_name = Path(input_path).name

        self.title_label.configure(text="Aktueller Job")
        self.plugin_label.configure(text=f"Plugin: {plugin}")
        self.backend_label.configure(text=f"Backend: {backend}")
        self.input_label.configure(text=f"Eingabe: {input_name}")
        self.output_label.configure(text="Ausgabe: wird erstellt...")
        self.status_label.configure(
            text="Status: Bild wird verarbeitet...",
            fg=Theme.color("info"),
        )
        self.runtime_label.configure(text="Laufzeit: 00:00")

    def finish_job(self, output_path):
        self.running = False

        output_name = Path(output_path).name

        self.output_label.configure(text=f"Ausgabe: {output_name}")
        self.status_label.configure(
            text="Status: Fertig",
            fg=Theme.color("success"),
        )

        self.update_runtime()

    def fail_job(self):
        self.running = False

        self.output_label.configure(text="Ausgabe: -")
        self.status_label.configure(
            text="Status: Fehler",
            fg=Theme.color("error"),
        )

        self.update_runtime()

    def set_batch_progress(self, current, total, percent):
        self.progress_bar.configure(
            mode="determinate",
            value=percent,
        )
        self.batch_label.configure(
            text=f"Batch: {current} / {total} ({percent}%)"
        )

    def update_runtime(self):
        if not self.start_time:
            return

        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60

        self.runtime_label.configure(
            text=f"Laufzeit: {minutes:02d}:{seconds:02d}"
        )