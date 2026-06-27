import tkinter as tk
from tkinter import messagebox
from modules.plugin_loader import discover_plugins
from config import WORKFLOWS_DIR

BG = "#101418"
PANEL = "#171d23"
PANEL_2 = "#1f2730"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"
ACCENT = "#3b82f6"
GREEN = "#22c55e"

class GenerateWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("AI Generate")
        self.geometry("880x640")
        self.configure(bg=BG)
        self.generate_plugin = None
        for p in discover_plugins():
            if getattr(p, "id", "") == "ai_generate":
                self.generate_plugin = p
                break
        self._build()

    def _label(self, parent, text, size=10, bold=False, color=TEXT, bg=None):
        return tk.Label(parent, text=text, font=("Segoe UI", size, "bold" if bold else "normal"),
                        fg=color, bg=bg if bg else parent["bg"])

    def _button(self, parent, text, command, bg=ACCENT):
        return tk.Button(parent, text=text, command=command, bg=bg, fg="white",
                         relief="flat", padx=14, pady=8, font=("Segoe UI", 10, "bold"),
                         cursor="hand2")

    def _build(self):
        self._label(self, "AI Generate", 22, True, TEXT, BG).pack(anchor="w", padx=24, pady=(20, 4))
        self._label(self, "Text-zu-Bild über lokalen ComfyUI-Server", 10, False, MUTED, BG).pack(anchor="w", padx=24)
        form = tk.Frame(self, bg=PANEL)
        form.pack(fill="x", padx=24, pady=18)
        self._label(form, "Prompt", 11, True, TEXT, PANEL).pack(anchor="w", padx=14, pady=(14, 4))
        self.prompt = tk.Text(form, height=5, bg=PANEL_2, fg=TEXT, insertbackground=TEXT, relief="flat", wrap="word")
        self.prompt.pack(fill="x", padx=14, pady=(0, 12))
        self.prompt.insert("1.0", "A cinematic photo of a futuristic Snapdragon AI workstation, detailed, realistic")
        self._label(form, "Negative Prompt", 11, True, TEXT, PANEL).pack(anchor="w", padx=14, pady=(0, 4))
        self.negative = tk.Text(form, height=3, bg=PANEL_2, fg=TEXT, insertbackground=TEXT, relief="flat", wrap="word")
        self.negative.pack(fill="x", padx=14, pady=(0, 12))
        self.negative.insert("1.0", "blurry, low quality, distorted")
        info = f"Workflow-Datei: {WORKFLOWS_DIR / 'text2image_api.json'}"
        self._label(form, info, 9, False, MUTED, PANEL).pack(anchor="w", padx=14, pady=(0, 14))
        actions = tk.Frame(self, bg=BG)
        actions.pack(fill="x", padx=24)
        self._button(actions, "ComfyUI prüfen", self.details, bg=PANEL_2).pack(side="left")
        self._button(actions, "An ComfyUI senden", self.generate, bg=GREEN).pack(side="left", padx=8)
        self._button(actions, "Workflows-Ordner öffnen", self.open_workflows, bg=ACCENT).pack(side="left")
        self.log = tk.Text(self, height=12, bg="#0b0f14", fg="#dbeafe", relief="flat", wrap="word", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, padx=24, pady=18)
        self.log.insert("end", "Schritt 1: ComfyUI starten.\n")
        self.log.insert("end", "Schritt 2: In ComfyUI einen Workflow als API-JSON exportieren.\n")
        self.log.insert("end", "Schritt 3: Datei als C:\\SnapdragonAI\\workflows\\text2image_api.json speichern.\n")

    def open_workflows(self):
        import os
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(WORKFLOWS_DIR)

    def generate(self):
        prompt = self.prompt.get("1.0", "end").strip()
        negative = self.negative.get("1.0", "end").strip()
        if not self.generate_plugin:
            messagebox.showerror("Plugin fehlt", "AI Generate Plugin wurde nicht gefunden.")
            return
        try:
            result = self.generate_plugin.run_prompt(prompt, negative, log=self._log)
            self._log("")
            self._log("Prompt wurde an ComfyUI gesendet.")
            self._log(str(result))
            messagebox.showinfo("Gesendet", "Prompt wurde an ComfyUI gesendet.")
        except Exception as e:
            self._log("")
            self._log("Fehler:")
            self._log(str(e))
            messagebox.showerror("Generate fehlgeschlagen", str(e))

    def details(self):
        if self.generate_plugin:
            self._log(self.generate_plugin.details())

    def _log(self, text):
        self.log.insert("end", text + "\n")
        self.log.see("end")
