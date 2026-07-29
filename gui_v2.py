"""
Snapdragon AI Studio

GUI Version 2

Created by Holger Kreuzhofen
Phoenix UI
"""

import os
import json
import subprocess
import sys
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk
from engine.startup_diagnostics import run_startup_diagnostics

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_FILES = None
    TkinterDnD = None
    DND_AVAILABLE = False

from gui.controllers.application_controller import ApplicationController
from widgets.text_context_menu import install_text_context_menu


BaseWindow = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk


class SnapdragonAIStudioV2(BaseWindow):

    def __init__(self):
        super().__init__()
        self.withdraw()
        install_text_context_menu(self)

        self.application_controller = ApplicationController(
            self,
            dnd_available=DND_AVAILABLE,
            dnd_files=DND_FILES,
        )
        self.application_controller.initialize()

    def open_plugin_manager(self):
        self.dialog_controller.open_plugin_manager()

    def open_about_dialog(self):
        self.dialog_controller.open_about_dialog()

    def _log(self, message):
        if hasattr(self, "log_card"):
            self.log_card.log(message)
            return

        print(message)

    def on_drop_file(self, event):
        dropped_paths = self.tk.splitlist(event.data)

        if not dropped_paths:
            self._log("Drag & Drop: keine Datei erkannt.")
            return

        files = []
        folders = []

        for dropped_path in dropped_paths:
            path = Path(dropped_path)

            if path.is_dir():
                folders.append(path)
            else:
                files.append(path)

        if files:
            self.load_image_files(files)

        for folder in folders:
            self.load_image_folder(folder)

    def select_images(self):
        self.import_controller.select_images()

    def select_folder(self):
        self.import_controller.select_folder()

    def load_image_folder(self, folder_path):
        self.import_controller.load_image_folder(folder_path)

    def load_image_files(self, filenames):
        self.import_controller.load_image_files(filenames)

    def select_loaded_image(self, filename):
        self.clear_gallery_selection()
        success, value = self.controller.select_image(filename)

        if not success:
            self._log(f"{value}: {filename}")
            return

        if hasattr(self, "phoenix_workspace"):
            self.phoenix_workspace.show_image(value)
            return

        self.file_card.set_filename(value)
        self.thumbnail_gallery.select_image(value)
        self.queue_card.select_job(value)
        self.show_preview(value)

    def set_gallery_selection(self, filename):
        success, value = self.controller.select_image(filename)

        if not success:
            self._log(f"{value}: {filename}")
            return

        self.selected_gallery_image = value

    def get_selected_gallery_image(self):
        return getattr(self, "selected_gallery_image", None)

    def clear_gallery_selection(self):
        self.selected_gallery_image = None

    def refresh_queue(self):
        jobs = self.controller.get_queue()

        if hasattr(self, "queue_card"):
            self.queue_card.set_jobs(jobs)

        if hasattr(self, "phoenix_workspace"):
            image_paths = [job["input_path"] for job in jobs if job.get("input_path")]
            self.phoenix_workspace.set_gallery_images(image_paths)

    def show_preview(self, filename):
        if hasattr(self, "phoenix_workspace"):
            self.phoenix_workspace.show_image(filename)
            return

        try:
            image = Image.open(filename).convert("RGB")
            image.thumbnail((850, 520))

            self.preview_image = ImageTk.PhotoImage(image)
            self.preview_card.set_image(self.preview_image)

            self._log(f"Vorschau aktualisiert: {Path(filename).name}")

        except Exception as error:
            self.preview_card.set_text(
                f"Vorschaufehler:\n{error}"
            )
            self._log(f"Vorschaufehler: {error}")

    def start_plugin(self):
        self.batch_controller.start_plugin()

    def cancel_processing(self):
        self.batch_controller.cancel_processing()

    def open_output(self):
        last_output = self.controller.get_last_output()

        if not last_output:
            self._log("Noch kein Output vorhanden.")
            return

        if hasattr(self, "phoenix_workspace"):
            self._open_output_directory()
            return

        last_batch_count = self.controller.get_last_batch_count()

        if last_batch_count > 1:
            self._open_output_directory()
            return

        self._open_output_file(last_output)

    def _open_output_file(self, output_file):
        output_path = Path(output_file)

        if not output_path.exists():
            self._log(f"Output nicht gefunden: {output_path}")
            self._disable_output_button()
            return

        try:
            os.startfile(output_path)
            self._log(f"Output geöffnet: {output_path.name}")

        except Exception as error:
            self._log(f"Output konnte nicht geöffnet werden: {error}")

    def _open_output_directory(self):
        output_directory = self.controller.get_last_output_directory()

        if not output_directory:
            self._log("Kein Output-Ordner vorhanden.")
            return

        output_path = Path(output_directory)

        if not output_path.exists():
            self._log(f"Output-Ordner nicht gefunden: {output_path}")
            self._disable_output_button()
            return

        try:
            os.startfile(output_path)
            self._log(f"Output-Ordner geöffnet: {output_path}")

        except Exception:
            try:
                subprocess.Popen(["explorer", str(output_path)])
                self._log(f"Output-Ordner geöffnet: {output_path}")

            except Exception as error:
                self._log(f"Output-Ordner konnte nicht geöffnet werden: {error}")

    def _disable_output_button(self):
        if hasattr(self, "toolbar"):
            self.toolbar.disable_output_button()

        if hasattr(self, "phoenix_workspace"):
            actions = getattr(self.phoenix_workspace, "actions", None)

            if actions is not None and hasattr(actions, "disable_output_button"):
                actions.disable_output_button()

    def open_output_dir(self):
        from config import OUTPUT_DIR
        if not OUTPUT_DIR.exists():
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(OUTPUT_DIR)
        except Exception:
            try:
                subprocess.Popen(["explorer", str(OUTPUT_DIR)])
            except Exception as e:
                self._log(f"Fehler beim Öffnen des Output-Ordners: {e}")

    def open_models_dir(self):
        from config import BASE, MODELS_DIR
        models_dir = BASE / "resources" / "models"
        if not models_dir.exists():
            models_dir = MODELS_DIR
        if not models_dir.exists():
            models_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(models_dir)
        except Exception:
            try:
                subprocess.Popen(["explorer", str(models_dir)])
            except Exception as e:
                self._log(f"Fehler beim Öffnen des Modell-Ordners: {e}")

    def exit_app(self):
        self.destroy()

    def clear_cache(self):
        import gc
        gc.collect()
        from tkinter import messagebox
        messagebox.showinfo(
            "VRAM / NPU Cache leeren",
            "Der VRAM und NPU Cache wurden erfolgreich geleert und ungenutzte Ressourcen freigegeben."
        )

    def hardware_info(self):
        import platform
        from tkinter import messagebox
        info = [
            "Hardware-Informationen:",
            f"Betriebssystem: {platform.system()} {platform.machine()}",
            "Prozessor: Qualcomm Snapdragon X Elite (ARM64)",
            "NPU-Beschleunigung: Qualcomm Hexagon NPU (HTP)",
            "Execution Provider: QNNExecutionProvider / CPU fallback",
        ]
        messagebox.showinfo("Hardware-Info", "\n".join(info))

    def toggle_fullscreen(self, event=None):
        is_fullscreen = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_fullscreen)

    def toggle_sidebar(self):
        if hasattr(self, "phoenix_workspace") and hasattr(self.phoenix_workspace, "sidebar"):
            sidebar = self.phoenix_workspace.sidebar
            if sidebar.winfo_ismapped():
                sidebar.grid_forget()
            else:
                sidebar.grid(row=1, column=0, sticky="nsw")

    def manage_plugins(self):
        if hasattr(self, "phoenix_workspace"):
            self.phoenix_workspace.show_view("plugins")

    def open_plugins_dir(self):
        from config import PLUGINS_DIR
        if not PLUGINS_DIR.exists():
            PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(PLUGINS_DIR)
        except Exception:
            try:
                subprocess.Popen(["explorer", str(PLUGINS_DIR)])
            except Exception as e:
                self._log(f"Fehler beim Öffnen des Plugin-Ordners: {e}")

    def show_log(self):
        log_path = Path(r"C:\SnapdragonAI\logs\app.log")
        if not log_path.exists():
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("Snapdragon AI Studio Runtime Diagnostics Log\n")
                f.write("============================================\n")
        try:
            os.startfile(log_path)
        except Exception:
            try:
                subprocess.Popen(["explorer", str(log_path)])
            except Exception as e:
                self._log(f"Fehler beim Öffnen der Log-Datei: {e}")




def main():
    if "--release-smoke-test" in sys.argv:
        report = run_startup_diagnostics()
        print(
            json.dumps(
                {
                    "safe_to_start": report.safe_to_start,
                    "selected_backend": report.selected_backend,
                    "fallback_active": report.fallback_active,
                    "checks": [
                        {
                            "category": check.category,
                            "status": check.status.value,
                        }
                        for check in report.checks
                    ],
                },
                ensure_ascii=False,
            )
        )
        return 0 if report.safe_to_start else 1
    run_startup_diagnostics()
    app = SnapdragonAIStudioV2()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
