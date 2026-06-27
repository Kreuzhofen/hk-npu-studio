import platform
import sys
import tkinter as tk

import version

BG = "#101418"
PANEL = "#171d23"
PANEL_2 = "#1f2730"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"
ACCENT = "#3b82f6"
GREEN = "#22c55e"


class AboutWindow(tk.Toplevel):
    def __init__(self, master=None, plugin_count=0):
        super().__init__(master)

        self.title("About SnapdragonAI Studio")
        self.geometry("620x560")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.plugin_count = plugin_count

        self._build_ui()

    def _label(self, parent, text, size=10, bold=False, color=TEXT, bg=None):
        return tk.Label(
            parent,
            text=text,
            font=("Segoe UI", size, "bold" if bold else "normal"),
            fg=color,
            bg=bg if bg else parent["bg"],
            justify="center",
        )

    def _build_ui(self):
        card = tk.Frame(self, bg=PANEL)
        card.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(
            card,
            text="SAI",
            bg=PANEL,
            fg=ACCENT,
            font=("Segoe UI", 34, "bold"),
        ).pack(pady=(24, 2))

        self._label(card, version.APP_NAME, 22, True, TEXT, PANEL).pack()
        self._label(
            card,
            f'Version {version.VERSION} "{version.CODENAME}"',
            11,
            False,
            MUTED,
            PANEL,
        ).pack(pady=(4, 18))

        self._label(card, "Created by", 10, False, MUTED, PANEL).pack()
        self._label(card, version.AUTHOR, 15, True, TEXT, PANEL).pack(pady=(0, 14))

        sep1 = tk.Frame(card, bg=PANEL_2, height=1)
        sep1.pack(fill="x", padx=42, pady=10)

        self._label(
            card,
            version.AI_ASSISTANCE,
            10,
            False,
            MUTED,
            PANEL,
        ).pack(pady=(4, 12))

        info = tk.Frame(card, bg=PANEL_2)
        info.pack(fill="x", padx=40, pady=10)

        rows = [
            ("Build", getattr(version, "BUILD", "unknown")),
            ("Python", sys.version.split()[0]),
            ("Platform", platform.platform()),
            ("Machine", platform.machine()),
            ("Plugin Engine", "v1"),
            ("Installed Plugins", str(self.plugin_count)),
        ]

        for label, value in rows:
            row = tk.Frame(info, bg=PANEL_2)
            row.pack(fill="x", padx=14, pady=4)

            tk.Label(
                row,
                text=label,
                bg=PANEL_2,
                fg=MUTED,
                font=("Segoe UI", 9),
                anchor="w",
                width=18,
            ).pack(side="left")

            tk.Label(
                row,
                text=value,
                bg=PANEL_2,
                fg=TEXT,
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

        sep2 = tk.Frame(card, bg=PANEL_2, height=1)
        sep2.pack(fill="x", padx=42, pady=12)

        self._label(
            card,
            getattr(version, "DESCRIPTION", "SnapdragonAI Studio"),
            10,
            False,
            MUTED,
            PANEL,
        ).pack(padx=42, pady=(4, 10))

        self._label(card, getattr(version, "COPYRIGHT", ""), 9, False, MUTED, PANEL).pack(pady=(0, 12))

        tk.Button(
            card,
            text="Schließen",
            command=self.destroy,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        ).pack(pady=(0, 20))
