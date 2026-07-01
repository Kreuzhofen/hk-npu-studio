from pathlib import Path
import sys
import tkinter as tk

# Projektwurzel dem Python-Pfad hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from widgets.phoenix.workspace import PhoenixWorkspace


def main():
    root = tk.Tk()
    root.title("Phoenix Smoke Test")
    root.geometry("1400x900")

    workspace = PhoenixWorkspace(root)
    workspace.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()