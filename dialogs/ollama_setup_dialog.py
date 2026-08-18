from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import shutil
import os
import urllib.request
import time
import logging
from typing import Callable
from pathlib import Path

from config import TEMP_DIR
from app.i18n import tr
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from engine.ollama_status import OllamaStatusService, OllamaStatus
from widgets.phoenix.theme import PHOENIX_THEME
from widgets.phoenix.controls.button import PhoenixButton

logger = logging.getLogger("OllamaSetup")


class OllamaSetupDialog(StudioDialog):
    """Step 1/2: Guided setup dialog for Ollama installation."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_detected: Callable[[], None],
        brand: BrandManager | None = None,
    ) -> None:
        self._on_detected = on_detected
        self._is_active = True
        self._is_cancelled = False
        self._download_thread: threading.Thread | None = None
        self._process: subprocess.Popen | None = None
        self._success = False

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

        # Start checking for Ollama availability
        self._check_status_loop()

        self.wait_window(self)

    def _build_ui(self) -> None:
        # Title and Subtitle
        self.add_title(
            tr("boost_ai_title_dialog", "Phoenix Boost AI"),
            tr("boost_ollama_setup_subtitle_step1", "Schritt 1/2 – Ollama")
        )

        card = self.add_card()
        content = tk.Frame(card, bg=PHOENIX_THEME.elevated_bg)
        content.pack(fill="both", expand=True, padx=PHOENIX_THEME.card_pad_x, pady=PHOENIX_THEME.card_pad_y)

        # Component Header Frame
        comp_frame = tk.Frame(content, bg=PHOENIX_THEME.elevated_bg)
        comp_frame.pack(fill="x", pady=(0, PHOENIX_THEME.space_xs))

        # Try to load icon
        project_root = Path(__file__).resolve().parent.parent
        icon_path = project_root / "assets" / "integrations" / "ollama.png"
        self._icon_photo = self._load_icon_asset(icon_path, target_height=24)
        if self._icon_photo:
            self._icon_lbl = tk.Label(comp_frame, image=self._icon_photo, bg=PHOENIX_THEME.elevated_bg)
            self._icon_lbl.pack(side="left", padx=(0, PHOENIX_THEME.space_sm))
            self._icon_image_ref = self._icon_photo

        self._comp_lbl = tk.Label(
            comp_frame,
            text="Ollama",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        )
        self._comp_lbl.pack(side="left")

        # Instructions
        self._desc_lbl = tk.Label(
            content,
            text=tr(
                "boost_ollama_setup_desc_prompt",
                "Für den optionalen lokalen KI-Boost benötigt Snapdragon AI Studio Ollama.\n\n"
                "Snapdragon AI Studio lädt die benötigte Ollama-Installation herunter und führt Sie anschließend automatisch weiter."
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
            content,
            style="Phoenix.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100,
        )

        # Status Label (hidden initially, packed after progress bar)
        self._status_lbl = tk.Label(
            content,
            text="",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
            justify="left",
        )

        # Actions in footer packed side-by-side centered
        self._btn_container = tk.Frame(self.footer, bg=self.footer.cget("bg"))
        self._btn_container.pack(anchor="center", expand=True)

        self._secondary_btn = PhoenixButton(
            self._btn_container,
            text=tr("cancel", "Abbrechen"),
            command=self._cancel_install,
            button_type="secondary",
            width=120,
        )
        self._secondary_btn.pack(side="left", padx=6)

        self._primary_btn = PhoenixButton(
            self._btn_container,
            text=tr("boost_ollama_install_action", "Ollama installieren"),
            command=self._start_install_workflow,
            button_type="primary",
            width=160,
        )
        self._primary_btn.pack(side="left", padx=6)

    def _start_install_workflow(self) -> None:
        self._primary_btn.pack_forget()
        self._desc_lbl.configure(text=tr("boost_ollama_downloading_msg", "Ollama wird heruntergeladen …"))
        self._progress_bar.pack(fill="x", pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.space_xs))
        self._status_lbl.pack(fill="x", pady=(0, PHOENIX_THEME.space_sm))
        self._status_lbl.configure(text="0 % heruntergeladen", fg=PHOENIX_THEME.text_muted)

        self._download_thread = threading.Thread(target=self._run_download_and_install, daemon=True)
        self._download_thread.start()

    def _run_download_and_install(self) -> None:
        temp_file = Path(TEMP_DIR) / "OllamaSetup.exe"
        try:
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
            self._safe_delete(temp_file)

            # 1. Download
            req = urllib.request.Request(
                "https://ollama.com/download/OllamaSetup.exe",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req) as response:
                content_length = response.getheader("Content-Length")
                total_size = int(content_length) if content_length else None

                downloaded = 0
                last_update_time = 0.0
                chunk_size = 262144  # 256 KB

                with open(temp_file, "wb") as f:
                    while not self._is_cancelled:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        now = time.time()
                        # Throttle UI updates to at most 10 times per second (every 0.1s)
                        if now - last_update_time >= 0.1 or (total_size and downloaded >= total_size):
                            if total_size:
                                pct = int((downloaded / total_size) * 100)
                                downloaded_mb = downloaded / (1024 * 1024)
                                total_mb = total_size / (1024 * 1024)
                                detail = tr(
                                    "boost_download_progress_mb",
                                    "{downloaded:.1f} MB von {total:.1f} MB",
                                    downloaded=downloaded_mb,
                                    total=total_mb
                                )
                            else:
                                pct = 0
                                downloaded_mb = downloaded / (1024 * 1024)
                                detail = tr(
                                    "boost_download_progress_mb_unknown",
                                    "{downloaded:.1f} MB heruntergeladen",
                                    downloaded=downloaded_mb
                                )
                            self._safe_after(0, self._update_download_progress, pct, detail)
                            last_update_time = now

            if self._is_cancelled:
                self._safe_delete(temp_file)
                return

            # Validate completeness
            if total_size is not None:
                if downloaded < total_size:
                    raise RuntimeError(
                        f"Incomplete download: received {downloaded} bytes of expected {total_size} bytes."
                    )
            else:
                if downloaded <= 0 or not temp_file.is_file() or temp_file.stat().st_size <= 0:
                    raise RuntimeError(
                        "Incomplete download: empty file or no bytes received."
                    )

            # Final 100% UI update occurs ONLY after successful validation
            if total_size:
                pct = 100
                downloaded_mb = total_size / (1024 * 1024)
                detail = tr(
                    "boost_download_progress_mb",
                    "{downloaded:.1f} MB von {total:.1f} MB",
                    downloaded=downloaded_mb,
                    total=downloaded_mb
                )
            else:
                pct = 100
                downloaded_mb = downloaded / (1024 * 1024)
                detail = tr(
                    "boost_download_progress_mb_unknown",
                    "{downloaded:.1f} MB heruntergeladen",
                    downloaded=downloaded_mb
                )
            self._safe_after(0, self._update_download_progress, pct, detail)
            time.sleep(1.0)

            # 2. Installation
            self._safe_after(0, self._transition_to_installing)
            self._process = subprocess.Popen(
                [str(temp_file), "/VERYSILENT", "/SUPPRESSMSGBOXES"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            exit_code = self._process.wait()
            self._safe_delete(temp_file)

            if self._is_cancelled:
                return

            if exit_code != 0:
                self._safe_after(0, self._on_install_failed, f"OllamaSetup.exe returned non-zero exit code: {exit_code}")
                return

            # Suppress/close the desktop GUI (ollama app.exe) if it was launched by the installer
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "ollama app.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                )
            except Exception:
                pass

            # 3. Post-install verification and auto-start
            self._safe_after(0, self._transition_to_verification)

            # Start service if it doesn't automatically start
            executable = shutil.which("ollama")
            if not executable:
                local_app_data = os.environ.get("LOCALAPPDATA")
                if local_app_data:
                    default_path = Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe"
                    if default_path.is_file():
                        executable = str(default_path)

            # Wait up to 15 seconds for Ollama API to be reachable
            start_time = time.monotonic()
            verified = False
            service_started = False
            while time.monotonic() - start_time < 15.0 and not self._is_cancelled:
                status = OllamaStatusService.detect(force=True)
                if status.reachable:
                    verified = True
                    break

                # If executable found but not reachable, try to invoke it to start daemon AT MOST ONCE
                if executable and not service_started and time.monotonic() - start_time > 3.0:
                    try:
                        subprocess.Popen([executable], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                        service_started = True
                    except Exception:
                        pass

                time.sleep(1.0)

            if self._is_cancelled:
                return

            if verified:
                self._safe_after(0, self._on_install_success)
            else:
                self._safe_after(0, self._on_install_failed, "Ollama API konnte nach der Installation nicht erreicht werden.")

        except Exception as e:
            self._safe_delete(temp_file)
            if not self._is_cancelled:
                self._safe_after(0, self._on_install_failed, str(e))

    def _update_download_progress(self, pct: int, detail: str) -> None:
        self._update_progressbar("determinate", pct)
        status_text = tr("boost_pct_downloaded", "{pct} % heruntergeladen", pct=pct) + f" ({detail})"
        self._status_lbl.configure(text=status_text, fg=PHOENIX_THEME.text_secondary)
        self._desc_lbl.configure(text=f"Ollama wird heruntergeladen …\n\n{detail}")

    def _transition_to_installing(self) -> None:
        self._update_progressbar("indeterminate")
        self._desc_lbl.configure(text=tr("boost_ollama_installing_msg", "Ollama wird installiert …"))
        self._status_lbl.configure(text="Installation läuft …", fg=PHOENIX_THEME.warning)

    def _transition_to_verification(self) -> None:
        self._update_progressbar("indeterminate")
        self._desc_lbl.configure(text=tr("boost_ollama_verifying_msg", "Installation wird überprüft …"))
        self._status_lbl.configure(text="Bitte einen Moment …", fg=PHOENIX_THEME.warning)

    def _check_status_loop(self) -> None:
        if not self._is_active or self._download_thread is not None or self._success:
            return

        def check():
            status = OllamaStatusService.detect(force=True)
            if self._is_active and not self._success and self._download_thread is None:
                if status.available:
                    self._safe_after(0, self._on_detected_success)
                else:
                    self._safe_after(1000, self._check_status_loop)

        threading.Thread(target=check, daemon=True).start()

    def _on_detected_success(self) -> None:
        self._success = True
        self._update_progressbar("determinate", 100)
        self._status_lbl.configure(
            text=tr("boost_ollama_ready", "✓ Ollama ist bereit"),
            fg=PHOENIX_THEME.success,
        )
        self._desc_lbl.configure(
            text=tr("boost_ollama_detected_desc", "Die Installation wurde erkannt."),
            fg=PHOENIX_THEME.text_primary,
        )
        self._secondary_btn.pack_forget()
        self._primary_btn.configure(
            text=tr("continue", "Weiter"),
            command=self._finish,
            button_type="primary",
        )
        self._primary_btn.pack(side="left", padx=6)

    def _on_install_success(self) -> None:
        self._success = True
        self._update_progressbar("determinate", 100)
        self._desc_lbl.configure(
            text=tr("boost_ollama_success_desc", "Die Installation wurde erfolgreich erkannt."),
            fg=PHOENIX_THEME.text_primary,
        )
        self._status_lbl.configure(
            text=tr("boost_ollama_ready", "✓ Ollama ist bereit"),
            fg=PHOENIX_THEME.success,
        )
        self._secondary_btn.pack_forget()
        self._primary_btn.configure(
            text=tr("continue", "Weiter"),
            command=self._finish,
            button_type="primary",
        )
        self._primary_btn.pack(side="left", padx=6)

    def _on_install_failed(self, error_msg: str) -> None:
        logger.error("Ollama installation failed: %s", error_msg)
        self._update_progressbar("determinate", 0)
        self._progress_bar.pack_forget()
        self._status_lbl.configure(
            text=tr("error", "Fehler"),
            fg=PHOENIX_THEME.danger,
        )
        self._desc_lbl.configure(
            text=tr(
                "boost_ollama_install_failed_friendly",
                "Die Ollama-Installation konnte nicht abgeschlossen werden. "
                "Bitte prüfen Sie Ihre Internetverbindung und versuchen Sie es erneut."
            ),
            fg=PHOENIX_THEME.danger,
        )

        # Show Retry (primary) and Cancel (secondary) side-by-side
        for child in self._btn_container.winfo_children():
            child.pack_forget()

        self._secondary_btn = PhoenixButton(
            self._btn_container,
            text=tr("cancel", "Abbrechen"),
            command=self._cancel_install,
            button_type="secondary",
            width=120,
        )
        self._secondary_btn.pack(side="left", padx=6)

        self._primary_btn = PhoenixButton(
            self._btn_container,
            text=tr("retry", "Erneut versuchen"),
            command=self._retry_install_workflow,
            button_type="primary",
            width=160,
        )
        self._primary_btn.pack(side="left", padx=6)

    def _retry_install_workflow(self) -> None:
        self._is_cancelled = False
        self._success = False
        self._desc_lbl.configure(fg=PHOENIX_THEME.text_primary)
        self._start_install_workflow()

    def _cancel_install(self) -> None:
        self._is_cancelled = True
        if self._process:
            try:
                self._process.terminate()
            except OSError:
                pass
        self.close()

    def _finish(self) -> None:
        self.close()
        self._on_detected()

    def _safe_delete(self, path: Path) -> None:
        try:
            if path.is_file():
                path.unlink()
        except Exception:
            pass

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
