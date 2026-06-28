"""
SnapdragonAI Studio

Queue Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

import tkinter as tk
from pathlib import Path


class QueueCard(tk.Frame):

    def __init__(self, master, on_select=None):
        super().__init__(master, bd=1, relief="groove", padx=8, pady=8)

        self.on_select = on_select
        self.items = []

        self._build_ui()

    def _build_ui(self):

        self.title_label = tk.Label(
            self,
            text="Batch Queue",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.title_label.pack(fill="x")

        self.info_label = tk.Label(
            self,
            text="Keine Jobs in der Warteschlange.",
            anchor="w",
        )
        self.info_label.pack(fill="x", pady=(4, 6))

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            height=10,
            exportselection=False,
        )
        self.listbox.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.scrollbar = tk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.listbox.yview,
        )
        self.scrollbar.pack(
            side="right",
            fill="y",
        )

        self.listbox.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.listbox.bind(
            "<<ListboxSelect>>",
            self._on_select,
        )

    def set_jobs(self, jobs):
        self.items = jobs
        self._refresh()

    def _refresh(self):

        self.listbox.delete(0, tk.END)

        if not self.items:
            self.info_label.configure(
                text="Keine Jobs in der Warteschlange."
            )
            return

        self.info_label.configure(
            text=f"Jobs: {len(self.items)}"
        )

        for index, job in enumerate(self.items, start=1):
            filename = Path(job["input_path"]).name
            status = job["status"]

            self.listbox.insert(
                tk.END,
                f"{index}. [{status}] {filename}",
            )

    def select_job(self, input_path):

        for index, job in enumerate(self.items):
            if job["input_path"] == input_path:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(index)
                self.listbox.activate(index)
                self.listbox.see(index)
                return

    def _on_select(self, event):
        selection = self.listbox.curselection()

        if not selection:
            return

        index = selection[0]
        job = self.items[index]

        if self.on_select:
            self.on_select(job["input_path"])