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
            title=tr("boost_ai_title", "Phoenix Boost einrichten"),
            brand=brand,
            size=(540, 360),
            min_size=(480, 320),
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
            tr("boost_ai_title", "Phoenix Boost einrichten"),
            tr("boost_ollama_setup_subtitle_step1", "Schritt 1/2 – Ollama")
        )

        card = self.add_card()
        content = tk.Frame(card, bg=PHOENIX_THEME.elevated_bg)
        content.pack(fill="both", expand=True, padx=PHOENIX_THEME.card_pad_x, pady=PHOENIX_THEME.card_pad_y)

        # Instructions
        self._desc_lbl = tk.Label(
            content,
            text=tr(
                "boost_ollama_setup_desc_prompt",
                "Für den optionalen lokalen KI-Boost benötigt Snapdragon AI Studio Ollama.\n\n"
                "Snapdragon AI Studio lädt die benötigte Ollama-Installation herunter und führt Sie anschließend automatisch weiter."
            ),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            justify="left",
            wraplength=440,
        )
        self._desc_lbl.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))

        # Progress bar (hidden initially)
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure(
            "Ollama.Horizontal.TProgressbar",
            thickness=12,
            troughcolor=PHOENIX_THEME.card_bg,
            background=PHOENIX_THEME.accent,
            bordercolor=PHOENIX_THEME.border,
            lightcolor=PHOENIX_THEME.accent,
            darkcolor=PHOENIX_THEME.accent,
        )

        self._progress_bar = ttk.Progressbar(
            content,
            style="Ollama.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100,
        )

        # Status Label
        self._status_lbl = tk.Label(
            content,
            text="",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.warning,
            font=PHOENIX_THEME.font_card_title,
            anchor="center",
        )
        self._status_lbl.pack(fill="x", pady=(PHOENIX_THEME.space_sm, 0))

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
        self._progress_bar.pack(fill="x", pady=PHOENIX_THEME.space_md)
        self._status_lbl.configure(text="0 % heruntergeladen", fg=PHOENIX_THEME.text_muted)

        self._download_thread = threading.Thread(target=self._run_download_and_install, daemon=True)
        self._download_thread.start()

    def _run_download_and_install(self) -> None:
        temp_file = Path(TEMP_DIR) / "OllamaSetup.exe"
        try:
            TEMP_DIR.mkdir(parents=True, exist_ok=True)

            # 1. Download
            req = urllib.request.Request(
                "https://ollama.com/download/OllamaSetup.exe",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req) as response:
                content_length = response.getheader("Content-Length")
                total_size = int(content_length) if content_length else None

                downloaded = 0
                with open(temp_file, "wb") as f:
                    while not self._is_cancelled:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size:
                            pct = int((downloaded / total_size) * 100)
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            detail = f"{downloaded_mb:.1f} MB von {total_mb:.1f} MB"
                        else:
                            pct = 0
                            downloaded_mb = downloaded / (1024 * 1024)
                            detail = f"{downloaded_mb:.1f} MB heruntergeladen"

                        self.after(0, self._update_download_progress, pct, detail)

            if self._is_cancelled:
                self._safe_delete(temp_file)
                return

            # Validate download
            if not temp_file.is_file() or temp_file.stat().st_size == 0:
                raise RuntimeError("Download validation failed: empty file or not created.")

            # 2. Installation
            self.after(0, self._transition_to_installing)
            self._process = subprocess.Popen(
                [str(temp_file), "/VERYSILENT", "/SUPPRESSMSGBOXES"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            exit_code = self._process.wait()
            self._safe_delete(temp_file)

            if self._is_cancelled:
                return

            if exit_code != 0:
                self.after(0, self._on_install_failed, f"OllamaSetup.exe returned non-zero exit code: {exit_code}")
                return

            # 3. Post-install verification and auto-start
            self.after(0, self._transition_to_verification)

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
                self.after(0, self._on_install_success)
            else:
                self.after(0, self._on_install_failed, "Ollama API konnte nach der Installation nicht erreicht werden.")

        except Exception as e:
            self._safe_delete(temp_file)
            if not self._is_cancelled:
                self.after(0, self._on_install_failed, str(e))

    def _update_download_progress(self, pct: int, detail: str) -> None:
        self._progress_bar["value"] = pct
        self._status_lbl.configure(text=f"{pct} % heruntergeladen")
        self._desc_lbl.configure(text=f"Ollama wird heruntergeladen …\n\n{detail}")

    def _transition_to_installing(self) -> None:
        self._progress_bar.pack_forget()
        self._status_lbl.configure(text="", fg=PHOENIX_THEME.warning)
        self._desc_lbl.configure(text=tr("boost_ollama_installing_msg", "Ollama wird installiert …"))

    def _transition_to_verification(self) -> None:
        self._desc_lbl.configure(text=tr("boost_ollama_verifying_msg", "Installation wird überprüft …"))

    def _check_status_loop(self) -> None:
        if not self._is_active:
            return

        def check():
            status = OllamaStatusService.detect(force=True)
            if status.available:
                self.after(0, self._on_detected_success)
            else:
                self.after(1000, self._check_status_loop)

        threading.Thread(target=check, daemon=True).start()

    def _on_detected_success(self) -> None:
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

    def _on_install_success(self) -> None:
        self._success = True
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
