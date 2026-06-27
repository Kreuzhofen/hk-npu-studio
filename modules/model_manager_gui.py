import tkinter as tk
from tkinter import ttk, messagebox
from modules.plugin_loader import discover_plugins

BG = "#101418"
PANEL = "#171d23"
PANEL_2 = "#1f2730"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"
ACCENT = "#3b82f6"

class ModelManagerWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Plugin / Model Manager")
        self.geometry("980x620")
        self.configure(bg=BG)
        self.plugins = []
        self._build()
        self.refresh()

    def _label(self, parent, text, size=10, bold=False, color=TEXT, bg=None):
        return tk.Label(parent, text=text, font=("Segoe UI", size, "bold" if bold else "normal"),
                        fg=color, bg=bg if bg else parent["bg"])

    def _button(self, parent, text, command, bg=ACCENT):
        return tk.Button(parent, text=text, command=command, bg=bg, fg="white",
                         relief="flat", padx=14, pady=8, font=("Segoe UI", 10, "bold"), cursor="hand2")

    def _build(self):
        self._label(self, "Plugin / Model Manager", 20, True, TEXT, BG).pack(anchor="w", padx=24, pady=(18, 4))
        self._label(self, "Automatisch erkannte Plugins und Modelle", 10, False, MUTED, BG).pack(anchor="w", padx=24)
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=14)
        self._button(top, "Aktualisieren", self.refresh, bg=ACCENT).pack(side="left")
        self._button(top, "Details", self.show_details, bg=PANEL_2).pack(side="left", padx=8)
        table_frame = tk.Frame(self, bg=PANEL)
        table_frame.pack(fill="both", expand=True, padx=24, pady=(0, 18))
        columns = ("name", "category", "engine", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
        self.tree.heading("name", text="Plugin / Modell")
        self.tree.heading("category", text="Kategorie")
        self.tree.heading("engine", text="Engine")
        self.tree.heading("status", text="Status")
        self.tree.column("name", width=260)
        self.tree.column("category", width=170)
        self.tree.column("engine", width=230)
        self.tree.column("status", width=120)
        self.tree.pack(fill="both", expand=True, padx=12, pady=12)
        self.details = tk.Text(self, height=7, bg="#0b0f14", fg="#dbeafe",
                               relief="flat", wrap="word", font=("Consolas", 9))
        self.details.pack(fill="x", padx=24, pady=(0, 18))

    def refresh(self):
        self.plugins = discover_plugins()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, plugin in enumerate(self.plugins):
            status = plugin.status() if hasattr(plugin, "status") else ("Installiert" if getattr(plugin, "available", False) else "Nicht verfügbar")
            self.tree.insert("", "end", iid=str(idx), values=(
                f"{getattr(plugin, 'icon', '')} {getattr(plugin, 'name', '')}",
                getattr(plugin, "category", ""),
                getattr(plugin, "engine", ""),
                status,
            ))
        self.details.delete("1.0", "end")
        self.details.insert("end", f"{len(self.plugins)} Plugin(s) gefunden.\n")

    def show_details(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Kein Plugin", "Bitte ein Plugin auswählen.")
            return
        idx = int(selected[0])
        plugin = self.plugins[idx]
        text = plugin.details() if hasattr(plugin, "details") else f"{plugin.name}\n\nKeine Details verfügbar."
        self.details.delete("1.0", "end")
        self.details.insert("end", text)
