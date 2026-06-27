import threading
import queue
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from PIL import Image, ImageTk

from modules.splash import show_splash
from modules.plugin_loader import discover_plugins
from modules.compare import CompareWindow
from modules.model_manager_gui import ModelManagerWindow
from modules.generate_gui import GenerateWindow
from modules.about import AboutWindow
from config import INPUT_DIR, OUTPUT_DIR
from engine.phoenix_adapter import PhoenixAdapter

BG = "#101418"
PANEL = "#171d23"
PANEL_2 = "#1f2730"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"
ACCENT = "#3b82f6"
GREEN = "#22c55e"
PURPLE = "#7c3aed"


class SnapdragonAIStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SnapdragonAI Studio v1.1 Identity")
        self.geometry("1080x740")
        self.minsize(960, 660)
        self.configure(bg=BG)

        self.plugins = discover_plugins()
        self.current_plugin = self._find_plugin("realesrgan_qnn")
        self.adapter = PhoenixAdapter()

        self.log_queue = queue.Queue()
        self.selected_image = tk.StringVar(value="")
        self.status_text = tk.StringVar(value="Bereit")
        self.progress_text = tk.StringVar(value="")
        self.progress_value = tk.DoubleVar(value=0)
        self.last_result = None
        self.original_preview = None
        self.result_preview = None

        self._setup_style()
        self._build_ui()
        self.after(100, self._poll_log_queue)

    def _find_plugin(self, plugin_id):
        for plugin in self.plugins:
            if getattr(plugin, "id", "") == plugin_id:
                return plugin
        return None

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor=PANEL_2,
            background=ACCENT,
            bordercolor=PANEL_2,
        )

    def _label(self, parent, text, size=10, bold=False, color=TEXT, bg=None):
        return tk.Label(
            parent,
            text=text,
            font=("Segoe UI", size, "bold" if bold else "normal"),
            fg=color,
            bg=bg if bg else parent["bg"],
        )

    def _button(self, parent, text, command, bg=ACCENT):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg="white",
            activebackground=bg,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )

    def _nav_button(self, parent, text, command=None, active=False):
        bg = ACCENT if active else PANEL
        fg = "white" if active else MUTED
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold" if active else "normal"),
            anchor="w",
            padx=18,
            pady=10,
            cursor="hand2",
        )
        btn.pack(fill="x", padx=10, pady=2)
        return btn

    def _build_ui(self):
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)

        sidebar = tk.Frame(root, bg=PANEL, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        self._label(sidebar, "SnapdragonAI", 18, True, TEXT, PANEL).pack(
            anchor="w", padx=18, pady=(22, 2)
        )
        self._label(sidebar, "Studio v1.1 Identity", 10, False, MUTED, PANEL).pack(
            anchor="w", padx=20, pady=(0, 24)
        )

        self._nav_button(sidebar, "🎨  AI Generate", self.open_generate, active=True)
        self._nav_button(sidebar, "✂  AI Edit / Inpaint", None)
        self._nav_button(sidebar, "🧩  Plugins", self.open_model_manager)
        self._nav_button(sidebar, "🖼  Upscaler", None)
        self._nav_button(sidebar, "📦  Models", self.open_model_manager)
        self._nav_button(sidebar, "🎤  Whisper", None)
        self._nav_button(sidebar, "👀  YOLO", None)
        self._nav_button(sidebar, "💬  Llama", None)
        self._nav_button(sidebar, "ℹ  About", self.open_about)

        self._button(sidebar, "Generate öffnen", self.open_generate, bg=GREEN).pack(
            fill="x", padx=12, pady=(10, 2)
        )
        self._button(sidebar, "Plugin Manager", self.open_model_manager, bg=PURPLE).pack(
            fill="x", padx=12, pady=(6, 2)
        )
        self._button(sidebar, "About", self.open_about, bg=PANEL_2).pack(
            fill="x", padx=12, pady=(6, 2)
        )

        tk.Frame(sidebar, bg=PANEL).pack(fill="both", expand=True)

        hw = tk.Frame(sidebar, bg=PANEL_2)
        hw.pack(fill="x", padx=12, pady=12)
        self._label(hw, "Systemstatus", 10, True, TEXT, PANEL_2).pack(
            anchor="w", padx=10, pady=(10, 2)
        )
        self._label(hw, "Snapdragon X", 9, False, MUTED, PANEL_2).pack(anchor="w", padx=10)
        self._label(hw, f"Plugins: {len(self.plugins)}", 9, False, MUTED, PANEL_2).pack(
            anchor="w", padx=10
        )
        self._label(hw, "NPU / QNN bereit ✔", 9, False, GREEN, PANEL_2).pack(
            anchor="w", padx=10
        )
        self._label(hw, "Created by Holger Kreuzhofen", 8, False, MUTED, PANEL_2).pack(
            anchor="w", padx=10, pady=(4, 10)
        )

        main = tk.Frame(root, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        topbar = tk.Frame(main, bg=BG)
        topbar.pack(fill="x", padx=24, pady=(20, 12))
        self._label(topbar, "ComfyUI Backend", 22, True, TEXT, BG).pack(side="left")
        self._label(
            topbar,
            "AI Generate kann jetzt Workflows an ComfyUI senden",
            10,
            False,
            MUTED,
            BG,
        ).pack(side="left", padx=14, pady=(8, 0))
        tk.Label(
            topbar,
            textvariable=self.status_text,
            bg=PANEL_2,
            fg=GREEN,
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="right")

        generate_card = tk.Frame(main, bg=PANEL)
        generate_card.pack(fill="x", padx=24, pady=(0, 14))
        self._label(generate_card, "Bildgenerierung", 12, True, TEXT, PANEL).pack(
            anchor="w", padx=16, pady=(14, 4)
        )
        self._label(
            generate_card,
            "ComfyUI lokal starten, API-Workflow speichern und Prompt aus SnapdragonAI Studio senden.",
            10,
            False,
            MUTED,
            PANEL,
        ).pack(anchor="w", padx=16, pady=(0, 10))
        self._button(generate_card, "AI Generate öffnen", self.open_generate, bg=GREEN).pack(
            anchor="w", padx=16, pady=(0, 14)
        )

        plugin_card = tk.Frame(main, bg=PANEL)
        plugin_card.pack(fill="x", padx=24, pady=(0, 14))
        self._label(plugin_card, "Aktives NPU-Test-Plugin", 12, True, TEXT, PANEL).pack(
            anchor="w", padx=16, pady=(14, 4)
        )
        active_text = "Kein Plugin gefunden"
        if self.current_plugin:
            active_text = (
                f"{self.current_plugin.icon} {self.current_plugin.name}  ·  "
                f"{self.current_plugin.engine}  ·  {self.current_plugin.status()}"
            )
        self._label(plugin_card, active_text, 10, False, MUTED, PANEL).pack(
            anchor="w", padx=16, pady=(0, 14)
        )

        file_card = tk.Frame(main, bg=PANEL)
        file_card.pack(fill="x", padx=24, pady=(0, 14))
        self._label(file_card, "Upscaler-Testbild auswählen", 11, True, TEXT, PANEL).pack(
            anchor="w", padx=16, pady=(14, 6)
        )

        row = tk.Frame(file_card, bg=PANEL)
        row.pack(fill="x", padx=16, pady=(0, 14))

        self.image_entry = tk.Entry(
            row,
            textvariable=self.selected_image,
            bg=PANEL_2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Segoe UI", 10),
        )
        self.image_entry.pack(side="left", fill="x", expand=True, ipady=8)

        self._button(row, "Auswählen", self.choose_image, bg=ACCENT).pack(
            side="left", padx=(8, 0)
        )
        self.start_button = self._button(row, "Plugin starten", self.start_plugin, bg=GREEN)
        self.start_button.pack(side="left", padx=(8, 0))
        self._button(row, "Plugin Manager", self.open_model_manager, bg=PURPLE).pack(
            side="left", padx=(8, 0)
        )

        preview_area = tk.Frame(main, bg=BG)
        preview_area.pack(fill="both", expand=True, padx=24)

        left = tk.Frame(preview_area, bg=PANEL)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        right = tk.Frame(preview_area, bg=PANEL)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self._label(left, "Input", 11, True, TEXT, PANEL).pack(
            anchor="w", padx=14, pady=(12, 6)
        )
        self.original_canvas = tk.Label(
            left,
            text="Kein Bild ausgewählt",
            bg=PANEL_2,
            fg=MUTED,
            font=("Segoe UI", 11),
        )
        self.original_canvas.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self._label(right, "Output", 11, True, TEXT, PANEL).pack(
            anchor="w", padx=14, pady=(12, 6)
        )
        self.result_canvas = tk.Label(
            right,
            text="Noch kein Ergebnis",
            bg=PANEL_2,
            fg=MUTED,
            font=("Segoe UI", 11),
        )
        self.result_canvas.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        bottom = tk.Frame(main, bg=BG)
        bottom.pack(fill="x", padx=24, pady=(14, 20))

        progress_row = tk.Frame(bottom, bg=BG)
        progress_row.pack(fill="x")

        self.progressbar = ttk.Progressbar(
            progress_row,
            variable=self.progress_value,
            maximum=100,
            mode="determinate",
            style="Horizontal.TProgressbar",
        )
        self.progressbar.pack(side="left", fill="x", expand=True)

        self.progress_label = self._label(progress_row, "", 10, True, TEXT, BG)
        self.progress_label.config(textvariable=self.progress_text)
        self.progress_label.pack(side="left", padx=(8, 0))

        buttons = tk.Frame(bottom, bg=BG)
        buttons.pack(fill="x", pady=(12, 0))

        self._button(buttons, "Input öffnen", self.open_original, bg=PANEL_2).pack(side="left")
        self._button(buttons, "Output öffnen", self.open_last_result, bg=PANEL_2).pack(
            side="left", padx=8
        )
        self._button(buttons, "Vergleich öffnen", self.open_compare, bg=ACCENT).pack(side="left")
        self._button(buttons, "Output-Ordner", self.open_output, bg=PANEL_2).pack(
            side="left", padx=8
        )

        log_card = tk.Frame(bottom, bg=PANEL)
        log_card.pack(fill="x", pady=(12, 0))
        self._label(log_card, "Protokoll", 10, True, TEXT, PANEL).pack(
            anchor="w", padx=12, pady=(10, 4)
        )
        self.log_text = tk.Text(
            log_card,
            height=6,
            bg="#0b0f14",
            fg="#dbeafe",
            insertbackground=TEXT,
            relief="flat",
            wrap="word",
            font=("Consolas", 9),
        )
        self.log_text.pack(fill="x", padx=12, pady=(0, 12))

    def open_generate(self):
        GenerateWindow(self)

    def open_model_manager(self):
        ModelManagerWindow(self)

    def open_about(self):
        AboutWindow(self, plugin_count=len(self.plugins))

    def choose_image(self):
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = filedialog.askopenfilename(
            initialdir=str(INPUT_DIR),
            title="Bild auswählen",
            filetypes=[
                ("Bilder", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if path:
            self.selected_image.set(path)
            self.show_original_preview(path)
            self.result_canvas.config(image="", text="Noch kein Ergebnis")
            self.result_preview = None

    def _fit_image(self, image_path, max_size=(390, 250)):
        img = Image.open(image_path).convert("RGB")
        img.thumbnail(max_size)
        return ImageTk.PhotoImage(img)

    def show_original_preview(self, path):
        try:
            self.original_preview = self._fit_image(path)
            self.original_canvas.config(image=self.original_preview, text="")
        except Exception as e:
            self.original_canvas.config(image="", text=f"Vorschaufehler:\n{e}")

    def show_result_preview(self, path):
        try:
            self.result_preview = self._fit_image(path)
            self.result_canvas.config(image=self.result_preview, text="")
        except Exception as e:
            self.result_canvas.config(image="", text=f"Vorschaufehler:\n{e}")

    def open_output(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        import os

        os.startfile(OUTPUT_DIR)

    def open_original(self):
        import os

        path = self.selected_image.get().strip()
        if path and Path(path).exists():
            os.startfile(path)
        else:
            messagebox.showinfo("Kein Bild", "Es wurde noch kein Bild ausgewählt.")

    def open_last_result(self):
        import os

        if self.last_result and Path(self.last_result).exists():
            os.startfile(self.last_result)
        else:
            messagebox.showinfo("Noch kein Ergebnis", "Es wurde noch kein Ergebnis erzeugt.")

    def open_compare(self):
        original = self.selected_image.get().strip()

        if not original or not Path(original).exists():
            messagebox.showinfo("Kein Input", "Bitte zuerst ein Bild auswählen.")
            return

        if not self.last_result or not Path(self.last_result).exists():
            messagebox.showinfo("Kein Output", "Bitte zuerst ein Plugin ausführen.")
            return

        CompareWindow(self, original, self.last_result)

    def start_plugin(self):
        image_path = self.selected_image.get().strip()

        if not image_path:
            messagebox.showwarning("Kein Bild", "Bitte zuerst ein Bild auswählen.")
            return

        if not Path(image_path).exists():
            messagebox.showerror("Bild nicht gefunden", image_path)
            return

        self.start_button.config(state="disabled")
        self.status_text.set("Phoenix Engine läuft...")
        self.progress_text.set("")
        self.progress_value.set(0)
        self.log_text.delete("1.0", "end")
        self.result_canvas.config(image="", text="Berechnung läuft...")

        thread = threading.Thread(target=self._worker, args=(image_path,), daemon=True)
        thread.start()

    def log(self, text):
        self.log_queue.put(("log", text))

    def set_status(self, text):
        self.log_queue.put(("status", text))

    def set_progress(self, text):
        self.log_queue.put(("progress", text))

    def set_percent(self, value):
        self.log_queue.put(("percent", value))

    def _worker(self, image_path):
        try:
            self.log("Starte Phoenix Engine...")
            self.set_status("Phoenix Engine läuft...")
            self.set_progress("QNN / NPU läuft")
            self.set_percent(10)

            result = self.adapter.run(
                "image.upscale",
                input_path=image_path,
            )

            output_path = result["output_path"]

            self.set_progress("Fertig")
            self.set_percent(100)
            self.log_queue.put(("done", str(output_path)))

        except Exception:
            self.log_queue.put(("error", traceback.format_exc()))

    def _poll_log_queue(self):
        try:
            while True:
                kind, text = self.log_queue.get_nowait()

                if kind == "log":
                    self.log_text.insert("end", text + "\n")
                    self.log_text.see("end")

                elif kind == "status":
                    self.status_text.set(text)

                elif kind == "progress":
                    self.progress_text.set(text)

                elif kind == "percent":
                    self.progress_value.set(float(text))

                elif kind == "done":
                    self.last_result = text
                    self.start_button.config(state="normal")
                    self.status_text.set("Fertig")
                    self.progress_text.set("100 %")
                    self.progress_value.set(100)
                    self.log_text.insert("end", "\nFertig:\n" + text + "\n")
                    self.log_text.see("end")
                    self.show_result_preview(text)

                    if messagebox.askyesno("Fertig", "Plugin abgeschlossen.\n\nVergleich öffnen?"):
                        self.open_compare()

                elif kind == "error":
                    self.start_button.config(state="normal")
                    self.status_text.set("Fehler")
                    self.progress_text.set("")
                    self.progress_value.set(0)
                    self.log_text.insert("end", "\nFEHLER:\n" + text + "\n")
                    self.log_text.see("end")
                    messagebox.showerror(
                        "Fehler",
                        "Beim Plugin-Lauf ist ein Fehler aufgetreten. Details stehen im Protokoll.",
                    )

        except queue.Empty:
            pass

        self.after(100, self._poll_log_queue)


if __name__ == "__main__":
    show_splash()
    app = SnapdragonAIStudio()
    app.mainloop()