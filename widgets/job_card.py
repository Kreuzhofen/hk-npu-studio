"""
SnapdragonAI Studio

Job Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

from tkinter import ttk


class JobCard(ttk.LabelFrame):
    """
    Zeigt die zuletzt ausgeführten Jobs an.
    """

    def __init__(self, master):
        super().__init__(master, text="Jobs")

        self.tree = ttk.Treeview(
            self,
            columns=("status", "skill"),
            show="headings",
            height=6,
        )

        self.tree.heading("status", text="Status")
        self.tree.heading("skill", text="Aufgabe")

        self.tree.column("status", width=110, anchor="center")
        self.tree.column("skill", width=260)

        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

    def add_job(self, job):
        """
        Fügt einen Job der Anzeige hinzu.
        """

        self.tree.insert(
            "",
            "end",
            values=(
                job.status,
                job.skill,
            ),
        )

    def clear(self):
        """
        Löscht die Anzeige.
        """

        for item in self.tree.get_children():
            self.tree.delete(item)