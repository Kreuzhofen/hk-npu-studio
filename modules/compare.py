import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

BG = "#101418"
PANEL = "#171d23"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"

class CompareWindow(tk.Toplevel):
    def __init__(self, master, original_path, result_path):
        super().__init__(master)
        self.title("Vorher / Nachher Vergleich")
        self.geometry("1000x640")
        self.configure(bg=BG)

        self.original_img = Image.open(Path(original_path)).convert("RGB")
        self.result_img = Image.open(Path(result_path)).convert("RGB")
        self.preview_original = None
        self.preview_result = None

        self._build()
        self._load_images()

    def _build(self):
        tk.Label(self, text="Vorher / Nachher Vergleich", bg=BG, fg=TEXT, font=("Segoe UI", 18, "bold")).pack(pady=(16, 8))
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=12)
        left = tk.Frame(body, bg=PANEL)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(body, bg=PANEL)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        tk.Label(left, text="Original", bg=PANEL, fg=TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
        tk.Label(right, text="Ergebnis", bg=PANEL, fg=TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
        self.left_label = tk.Label(left, bg="#0b0f14", fg=MUTED)
        self.left_label.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.right_label = tk.Label(right, bg="#0b0f14", fg=MUTED)
        self.right_label.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        tk.Button(self, text="Schließen", command=self.destroy, bg="#1f2730", fg=TEXT, relief="flat", padx=14, pady=8).pack(pady=(0, 14))

    def _fit(self, img, max_size=(440, 430)):
        cp = img.copy()
        cp.thumbnail(max_size)
        return ImageTk.PhotoImage(cp)

    def _load_images(self):
        self.preview_original = self._fit(self.original_img)
        self.preview_result = self._fit(self.result_img)
        self.left_label.config(image=self.preview_original)
        self.right_label.config(image=self.preview_result)
