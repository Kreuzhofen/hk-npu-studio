from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import shutil
import os
import re
import logging
from typing import Callable
from pathlib import Path

from app.i18n import tr
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from engine.ollama_status import OllamaStatusService
from widgets.phoenix.theme import PHOENIX_THEME
from widgets.phoenix.controls.button import PhoenixButton

logger = logging.getLogger("QwenSetup")


class QwenSetupDialog(StudioDialog):
    """Step 2/2: Guided installation dialog for Qwen2.5 3B model."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_success: Callable[[], None],
        brand: BrandManager | None = None,
    ) -> None:
        self._on_success = on_success
        self._process: subprocess.Popen | None = None
        self._is_cancelled = False
        self._success = False
        self._is_active = True

        super().__init__(
            master,
            title=tr("boost_ai_title_dialog", "Phoenix Boost AI"),
            brand=brand,
            size=(540, 380),
            min_size=(480, 340),
            resizable=False,
        )

        self._build_ui()
        self.center(master)
        self.wait_window(self)

    def _build_ui(self) -> None:
        # Title and Steps
        self._title_frame = self.add_title(
            tr("boost_ai_title_dialog", "Phoenix Boost AI"),
            tr("boost_qwen_setup_subtitle", "Schritt 2/2 – Qwen2.5 3B")
        )

        card = self.add_card()
        self._content = tk.Frame(card, bg=PHOENIX_THEME.elevated_bg)
        self._content.pack(fill="both", expand=True, padx=PHOENIX_THEME.card_pad_x, pady=PHOENIX_THEME.card_pad_y)

        # Component Header Frame
        comp_frame = tk.Frame(self._content, bg=PHOENIX_THEME.elevated_bg)
        comp_frame.pack(fill="x", pady=(0, PHOENIX_THEME.space_xs))

        # Try to load icon
        project_root = Path(__file__).resolve().parent.parent
        icon_path = project_root / "assets" / "integrations" / "qwen.jpg"
        self._icon_photo = self._load_icon_asset(icon_path, target_height=24)
        if self._icon_photo:
            self._icon_lbl = tk.Label(comp_frame, image=self._icon_photo, bg=PHOENIX_THEME.elevated_bg)
            self._icon_lbl.pack(side="left", padx=(0, PHOENIX_THEME.space_sm))
            self._icon_image_ref = self._icon_photo

        self._comp_lbl = tk.Label(
            comp_frame,
            text="Qwen2.5 3B",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        )
        self._comp_lbl.pack(side="left")

        # Instruction / Progress Title
        self._desc_lbl = tk.Label(
            self._content,
            text=tr(
                "boost_qwen_setup_desc_prompt",
                "Jetzt wird das lokale KI-Modell für Phoenix Boost eingerichtet.\n\n"
                "Snapdragon AI Studio lädt Qwen2.5 3B automatisch herunter."
            ),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            justify="left",
            wraplength=440,
        )
        self._desc_lbl.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))

        # Progress bar (hidden initially)
        self._progress_bar = ttk.Progressbar(
            self._content,
            style="Phoenix.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100,
        )

        # Status label (hidden initially, packed after progress bar)
        self._status_lbl = tk.Label(
            self._content,
            text="",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
            justify="left",
        )

        # Actions in footer
        self._btn_container = tk.Frame(self.footer, bg=self.footer.cget("bg"))
        self._btn_container.pack(anchor="center", expand=True)

        self._secondary_btn = PhoenixButton(
            self._btn_container,
            text=tr("cancel", "Abbrechen"),
            command=self._cancel_download,
            button_type="secondary",
            width=120,
        )
        self._secondary_btn.pack(side="left", padx=6)

        self._primary_btn = PhoenixButton(
            self._btn_container,
            text=tr("boost_qwen_install_action", "Qwen2.5 3B installieren"),
            command=self._start_download_workflow,
            button_type="primary",
            width=180,
        )
        self._primary_btn.pack(side="left", padx=6)

    def _start_download_workflow(self) -> None:
        self._primary_btn.pack_forget()
        self._desc_lbl.configure(text=tr("boost_qwen_downloading_msg", "Qwen2.5 3B wird heruntergeladen …"))
        self._progress_bar.pack(fill="x", pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.space_xs))
        self._status_lbl.pack(fill="x", pady=(0, PHOENIX_THEME.space_sm))
        self._status_lbl.configure(text="0 % heruntergeladen", fg=PHOENIX_THEME.text_muted)

        # Start download in background thread
        threading.Thread(target=self._run_pull, daemon=True).start()

    def _run_pull(self) -> None:
        # Find executable
        executable = shutil.which("ollama")
        if not executable:
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                default_path = Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe"
                if default_path.is_file():
                    executable = str(default_path)
        if not executable:
            self._safe_after(
                0,
                self._on_failed,
                tr("boost_ollama_not_found", "Ollama-Programm wurde nicht gefunden.")
            )
            return
        try:
            self._process = subprocess.Popen(
                [executable, "pull", OllamaStatusService.MODEL],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                bufsize=0,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )

            buffer = b""
            while not self._is_cancelled:
                char_bytes = self._process.stdout.read(1)
                if not char_bytes:
                    break
                if char_bytes in (b"\r", b"\n"):
                    try:
                        line = buffer.decode("utf-8", errors="ignore").strip()
                    except Exception:
                        line = ""
                    if line:
                        self._safe_after(0, self._parse_output_line, line)
                    buffer = b""
                else:
                    buffer += char_bytes

            # Wait for exit status
            exit_code = self._process.wait()
            if self._is_cancelled:
                return

            # Invalidate cache and force a fresh model check
            OllamaStatusService.invalidate_cache()
            status = OllamaStatusService.detect(force=True)
            if status.model_available:
                self._safe_after(0, self._on_success_state)
            else:
                self._safe_after(0, self._on_failed, f"Qwen model not found after pull. Exit code: {exit_code}")
        except Exception as e:
            if not self._is_cancelled:
                self._safe_after(0, self._on_failed, str(e))

    def _parse_output_line(self, line: str) -> None:
        line_lower = line.lower()

        # Check for active download progress percentage first.
        # Ollama updates multiple lines using ANSI escape/cursor sequences. As a result,
        # a single read buffer can contain both "pulling c5396e06af29: 45%" and "pulling manifest".
        # We must prioritize percentage parsing to avoid getting stuck in indeterminate mode.
        # We identify actual layer progress lines matching "pulling <layer/hash>: <percent>%"
        match = re.search(r"(?:pulling|downloading)\s+([a-f0-9]{12}):\s*(\d+(?:\.\d+)?)%", line_lower)
        if match:
            try:
                pct = int(float(match.group(2)))
            except ValueError:
                pct = 0

            # Cap the download percentage at 99% to ensure 100% is only shown after verification
            pct = min(pct, 99)

            self._update_progressbar("determinate", pct)
            self._status_lbl.configure(
                text=tr("boost_pct_downloaded", "{pct} % heruntergeladen", pct=pct),
                fg=PHOENIX_THEME.text_secondary
            )
            self._desc_lbl.configure(text=tr("boost_qwen_downloading_msg", "Qwen2.5 3B wird heruntergeladen …"))
        elif "manifest" in line_lower:
            if "writing" in line_lower:
                self._update_progressbar("indeterminate")
                self._desc_lbl.configure(text=tr("boost_status_installing", "Installation wird abgeschlossen …"))
                self._status_lbl.configure(text=tr("boost_status_installing", "Installation wird abgeschlossen …"), fg=PHOENIX_THEME.warning)
            else:
                self._update_progressbar("indeterminate")
                self._desc_lbl.configure(text=tr("boost_qwen_preparing", "Vorbereitung …"))
                self._status_lbl.configure(text=tr("boost_qwen_preparing", "Vorbereitung …"), fg=PHOENIX_THEME.warning)
        elif "verifying" in line_lower:
            self._update_progressbar("indeterminate")
            self._desc_lbl.configure(text=tr("boost_status_verifying", "Installation wird abgeschlossen …"))
            self._status_lbl.configure(text=tr("boost_status_verifying", "Installation wird abgeschlossen …"), fg=PHOENIX_THEME.warning)
        elif "success" in line_lower:
            # We don't jump to 100% immediately on seeing "success" in output;
            # the final 100% and success state is set in _on_success_state() after verification.
            pass

    def _on_success_state(self) -> None:
        self._success = True
        OllamaStatusService.invalidate_cache()
        self._update_progressbar("determinate", 100)

        # Update Dialog title/steps
        for child in self._title_frame.winfo_children():
            child.destroy()

        tk.Label(
            self._title_frame,
            text=tr("boost_ai_title_dialog", "Phoenix Boost AI"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            self._title_frame,
            text=tr("boost_qwen_setup_subtitle_done", "Schritt 2/2"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).pack(fill="x", pady=(PHOENIX_THEME.space_xs, 0))

        # Update Status and button
        self._status_lbl.configure(
            text=tr("boost_ai_status_ready", "✓ Phoenix Boost ist bereit"),
            fg=PHOENIX_THEME.success,
        )
        self._desc_lbl.configure(text=tr("boost_status_success_desc", "Qwen2.5 3B wurde erfolgreich eingerichtet."))

        self._secondary_btn.pack_forget()
        self._primary_btn = PhoenixButton(
            self._btn_container,
            text=tr("done", "Fertig"),
            command=self._finish_success,
            button_type="primary",
            width=120,
        )
        self._primary_btn.pack(side="left", padx=6)

    def _on_failed(self, error_msg: str) -> None:
        logger.error("Qwen installation failed: %s", error_msg)
        self._update_progressbar("determinate", 0)
        self._progress_bar.pack_forget()
        self._status_lbl.configure(text=tr("error", "Fehler"), fg=PHOENIX_THEME.danger)
        self._desc_lbl.configure(
            text=tr(
                "boost_qwen_install_failed_friendly_new",
                "Die Einrichtung konnte nicht abgeschlossen werden.\n"
                "Bitte prüfen Sie Ihre Internetverbindung und versuchen Sie es erneut."
            ),
            fg=PHOENIX_THEME.danger
        )
        self._progress_bar["value"] = 0

        # Show Retry (primary) and Cancel (secondary) side-by-side
        for child in self._btn_container.winfo_children():
            child.pack_forget()

        self._secondary_btn = PhoenixButton(
            self._btn_container,
            text=tr("cancel", "Abbrechen"),
            command=self._cancel_download,
            button_type="secondary",
            width=120,
        )
        self._secondary_btn.pack(side="left", padx=6)

        self._primary_btn = PhoenixButton(
            self._btn_container,
            text=tr("retry", "Erneut versuchen"),
            command=self._retry_download_workflow,
            button_type="primary",
            width=180,
        )
        self._primary_btn.pack(side="left", padx=6)

    def _retry_download_workflow(self) -> None:
        self._is_cancelled = False
        self._success = False
        self._desc_lbl.configure(fg=PHOENIX_THEME.text_primary)
        self._start_download_workflow()

    def _cancel_download(self) -> None:
        self._is_cancelled = True
        if self._process:
            try:
                self._process.terminate()
            except OSError:
                pass
        self.close()

    def _finish_success(self) -> None:
        self.close()
        self._on_success()

    def close(self) -> None:
        self._is_active = False
        self._is_cancelled = True
        super().close()

    def _safe_after(self, ms: int, func: Callable, *args) -> None:
        try:
            if self._is_active and self.winfo_exists():
                self.after(ms, func, *args)
        except (tk.TclError, RuntimeError):
            pass

    def _process_image_for_theme(self, img: Image.Image, path: Path) -> Image.Image:
        try:
            from PIL import Image
            from engine.theme_manager import ThemeManager
            is_light_theme = (ThemeManager.active_theme() == ThemeManager.PROFESSIONAL_LIGHT)
            name_lower = path.name.lower()
            if "ollama" in name_lower:
                if is_light_theme:
                    img = img.convert("RGBA")
                    pixels = img.load()
                    w, h = img.size
                    for y in range(h):
                        for x in range(w):
                            r, g, b, a = pixels[x, y]
                            pixels[x, y] = (24, 33, 44, a)
            elif "qwen" in name_lower:
                img = img.convert("RGBA")
                w, h = img.size
                thresh = Image.new("L", (w, h), 0)
                pixels = img.load()
                thresh_pixels = thresh.load()
                for y in range(h):
                    for x in range(w):
                        r, g, b, a = pixels[x, y]
                        if r > 240 and g > 240 and b > 240:
                            thresh_pixels[x, y] = 255

                from PIL import ImageDraw
                for start_pt in [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1)]:
                    if thresh_pixels[start_pt[0], start_pt[1]] == 255:
                        ImageDraw.floodfill(thresh, start_pt, 128)

                mask = Image.new("L", (w, h), 255)
                mask_pixels = mask.load()
                thresh_pixels = thresh.load()
                for y in range(h):
                    for x in range(w):
                        if thresh_pixels[x, y] == 128:
                            mask_pixels[x, y] = 0

                img.putalpha(mask)
        except Exception as e:
            logger.debug(f"Failed to process image for theme: {e}")
        return img

    def _load_icon_asset(self, path_str: str, target_height: int = 24) -> ImageTk.PhotoImage | None:
        try:
            path = Path(path_str)
            if not path.is_file():
                return None
            from PIL import Image, ImageTk
            with Image.open(path) as img:
                w, h = img.size
                if w <= 0 or h <= 0:
                    return None
                img = self._process_image_for_theme(img, path)
                aspect = w / h
                target_width = int(target_height * aspect)
                try:
                    resample = Image.Resampling.LANCZOS
                except AttributeError:
                    try:
                        resample = Image.LANCZOS
                    except AttributeError:
                        resample = Image.ANTIALIAS
                resized_img = img.resize((target_width, target_height), resample)
                photo = ImageTk.PhotoImage(resized_img)
                return photo
        except Exception as e:
            logger.debug(f"Failed to load icon from {path_str}: {e}")
            return None

    def _update_progressbar(self, mode: str, value: int | None = None) -> None:
        try:
            current_mode = str(self._progress_bar.cget("mode"))
            if current_mode != mode:
                self._progress_bar.stop()
                self._progress_bar.configure(mode=mode)
                if mode == "indeterminate":
                    self._progress_bar.start(10)
            if mode == "determinate" and value is not None:
                self._progress_bar["value"] = value
        except Exception:
            pass
