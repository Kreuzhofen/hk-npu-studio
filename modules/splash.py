import time
import tkinter as tk
from tkinter import ttk

import version

BG = "#101418"
PANEL = "#171d23"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"
ACCENT = "#3b82f6"


def show_splash():
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg=BG)

    width = 520
    height = 340

    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()

    x = int((screen_w - width) / 2)
    y = int((screen_h - height) / 2)

    splash.geometry(f"{width}x{height}+{x}+{y}")

    frame = tk.Frame(splash, bg=PANEL)
    frame.pack(fill="both", expand=True, padx=2, pady=2)

    tk.Label(
        frame,
        text="SAI",
        bg=PANEL,
        fg=ACCENT,
        font=("Segoe UI", 32, "bold"),
    ).pack(pady=(28, 4))

    tk.Label(
        frame,
        text=version.APP_NAME,
        bg=PANEL,
        fg=TEXT,
        font=("Segoe UI", 20, "bold"),
    ).pack()

    tk.Label(
        frame,
        text=f"Version {version.VERSION}",
        bg=PANEL,
        fg=MUTED,
        font=("Segoe UI", 10),
    ).pack(pady=(4, 16))

    tk.Label(
        frame,
        text="Created by",
        bg=PANEL,
        fg=MUTED,
        font=("Segoe UI", 10),
    ).pack()

    tk.Label(
        frame,
        text=version.AUTHOR,
        bg=PANEL,
        fg=TEXT,
        font=("Segoe UI", 13, "bold"),
    ).pack(pady=(0, 14))

    status = tk.Label(
        frame,
        text="Initializing AI Engine...",
        bg=PANEL,
        fg=MUTED,
        font=("Segoe UI", 10),
    )
    status.pack(pady=(8, 6))

    progress = ttk.Progressbar(frame, mode="determinate", length=360)
    progress.pack()

    steps = [
        "Loading Plugin Engine...",
        "Checking Snapdragon Runtime...",
        "Loading Models...",
        "Loading User Interface...",
        "Ready.",
    ]

    for i, text in enumerate(steps, start=1):
        status.config(text=text)
        progress["value"] = i * 20
        splash.update()
        time.sleep(0.35)

    splash.destroy()
