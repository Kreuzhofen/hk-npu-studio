import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk

from config import INPUT_DIR, OUTPUT_DIR
from modules.photo_edit import apply_adjustments

BG = "#101418"
PANEL = "#171d23"
PANEL_2 = "#1f2730"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"
ACCENT = "#3b82f6"
GREEN = "#22c55e"

class PhotoEditWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Bild bearbeiten")
        self.geometry("980x680")
        self.configure(bg=BG)

        self.image_path = None
        self.preview_original = None
        self.preview_edited = None
        self.last_output = None

        self.brightness = tk.DoubleVar(value=1.0)
        self.contrast = tk.DoubleVar(value=1.0)
        self.color = tk.DoubleVar(value=1.0)
        self.sharpness = tk.DoubleVar(value=1.0)
        self.warm = tk.DoubleVar(value=0.0)

        self._build()

    def _label(self, parent, text, size=10, bold=False, color=TEXT, bg=None):
        return tk.Label(parent, text=text, font=("Segoe UI", size, "bold" if bold else "normal"),
                        fg=color, bg=bg if bg else parent["bg"])

    def _button(self, parent, text, command, bg=ACCENT):
        return tk.Button(parent, text=text, command=command, bg=bg, fg="white",
                         activebackground=bg, activeforeground="white",
                         relief="flat", bd=0, padx=14, pady=8,
                         font=("Segoe UI", 10, "bold"), cursor="hand2")

    def _build(self):
        self._label(self, "Bild bearbeiten", 20, True, TEXT, BG).pack(anchor="w", padx=24, pady=(18, 6))
        self._label(self, "Klassische Bildanpassung: Helligkeit, Kontrast, Farbe, Schärfe und Wärme", 10, False, MUTED, BG).pack(anchor="w", padx=24)

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=14)
        self._button(top, "Bild auswählen", self.choose_image, bg=ACCENT).pack(side="left")
        self._button(top, "Speichern", self.save_image, bg=GREEN).pack(side="left", padx=8)
        self._button(top, "Letztes Ergebnis öffnen", self.open_last, bg=PANEL_2).pack(side="left")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        controls = tk.Frame(body, bg=PANEL, width=250)
        controls.pack(side="left", fill="y")
        controls.pack_propagate(False)

        preview = tk.Frame(body, bg=BG)
        preview.pack(side="left", fill="both", expand=True, padx=(14, 0))

        self._label(controls, "Regler", 13, True, TEXT, PANEL).pack(anchor="w", padx=14, pady=(14, 8))
        self._slider(controls, "Helligkeit", self.brightness, 0.5, 1.8)
        self._slider(controls, "Kontrast", self.contrast, 0.5, 1.8)
        self._slider(controls, "Farbe", self.color, 0.0, 2.0)
        self._slider(controls, "Schärfe", self.sharpness, 0.0, 2.5)
        self._slider(controls, "Wärme / Bräune", self.warm, 0.0, 1.5)

        self._button(controls, "Zurücksetzen", self.reset, bg=PANEL_2).pack(fill="x", padx=14, pady=(14, 4))
        self._button(controls, "Vorschau aktualisieren", self.update_preview, bg=ACCENT).pack(fill="x", padx=14, pady=4)

        row = tk.Frame(preview, bg=BG)
        row.pack(fill="both", expand=True)

        left = tk.Frame(row, bg=PANEL)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(row, bg=PANEL)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self._label(left, "Original", 11, True, TEXT, PANEL).pack(anchor="w", padx=12, pady=(12, 4))
        self.original_label = tk.Label(left, text="Kein Bild", bg="#0b0f14", fg=MUTED)
        self.original_label.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._label(right, "Bearbeitet", 11, True, TEXT, PANEL).pack(anchor="w", padx=12, pady=(12, 4))
        self.edited_label = tk.Label(right, text="Keine Vorschau", bg="#0b0f14", fg=MUTED)
        self.edited_label.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _slider(self, parent, title, var, frm, to):
        box = tk.Frame(parent, bg=PANEL)
        box.pack(fill="x", padx=14, pady=7)
        tk.Label(box, text=title, bg=PANEL, fg=TEXT, font=("Segoe UI", 10)).pack(anchor="w")
        scale = tk.Scale(box, from_=frm, to=to, resolution=0.05, orient="horizontal",
                         variable=var, bg=PANEL, fg=TEXT, troughcolor=PANEL_2,
                         highlightthickness=0, command=lambda _=None: self.update_preview())
        scale.pack(fill="x")

    def _fit(self, img, max_size=(320, 420)):
        cp = img.copy()
        cp.thumbnail(max_size)
        return ImageTk.PhotoImage(cp)

    def choose_image(self):
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = filedialog.askopenfilename(
            initialdir=str(INPUT_DIR),
            title="Bild auswählen",
            filetypes=[("Bilder", "*.jpg *.jpeg *.png *.bmp *.webp"), ("Alle Dateien", "*.*")]
        )
        if path:
            self.image_path = Path(path)
            img = Image.open(self.image_path).convert("RGB")
            self.preview_original = self._fit(img)
            self.original_label.config(image=self.preview_original, text="")
            self.update_preview()

    def _edited_image(self):
        if not self.image_path:
            return None
        tmp = OUTPUT_DIR / "_preview_edit_temp.png"
        apply_adjustments(
            self.image_path,
            tmp,
            brightness=self.brightness.get(),
            contrast=self.contrast.get(),
            color=self.color.get(),
            sharpness=self.sharpness.get(),
            warm=self.warm.get(),
        )
        return Image.open(tmp).convert("RGB")

    def update_preview(self):
        if not self.image_path:
            return
        try:
            img = self._edited_image()
            self.preview_edited = self._fit(img)
            self.edited_label.config(image=self.preview_edited, text="")
        except Exception as e:
            self.edited_label.config(image="", text=f"Fehler:\n{e}")

    def save_image(self):
        if not self.image_path:
            messagebox.showinfo("Kein Bild", "Bitte zuerst ein Bild auswählen.")
            return
        out = OUTPUT_DIR / f"{self.image_path.stem}_edited.png"
        apply_adjustments(
            self.image_path,
            out,
            brightness=self.brightness.get(),
            contrast=self.contrast.get(),
            color=self.color.get(),
            sharpness=self.sharpness.get(),
            warm=self.warm.get(),
        )
        self.last_output = out
        messagebox.showinfo("Gespeichert", str(out))

    def open_last(self):
        import os
        if self.last_output and Path(self.last_output).exists():
            os.startfile(self.last_output)
        else:
            messagebox.showinfo("Kein Ergebnis", "Noch kein bearbeitetes Bild gespeichert.")

    def reset(self):
        self.brightness.set(1.0)
        self.contrast.set(1.0)
        self.color.set(1.0)
        self.sharpness.set(1.0)
        self.warm.set(0.0)
        self.update_preview()
