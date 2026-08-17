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
        self.wait_window(self)

    def _build_ui(self) -> None:
        # Title and Steps
        self._title_frame = self.add_title(
            tr("boost_ai_title", "Phoenix Boost einrichten"),
            tr("boost_qwen_setup_subtitle", "Schritt 2/2 – Qwen2.5 3B")
        )

        card = self.add_card()
        self._content = tk.Frame(card, bg=PHOENIX_THEME.elevated_bg)
        self._content.pack(fill="both", expand=True, padx=PHOENIX_THEME.card_pad_x, pady=PHOENIX_THEME.card_pad_y)

        # Instruction / Progress Title
        self._desc_lbl = tk.Label(
            self._content,
            text=tr(
                "boost_qwen_setup_desc_prompt",
                "Jetzt wird das lokale KI-Modell für Phoenix Boost eingerichtet.\n\n"
                "Snapdragon AI Studio lädt Qwen2.5 3B automatisch herunter."
            ),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            justify="left",
            wraplength=440,
        )
        self._desc_lbl.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))

        # Status label (initially hidden or empty)
        self._status_lbl = tk.Label(
            self._content,
            text="",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        )

        # Progress bar (hidden initially)
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure(
            "Qwen.Horizontal.TProgressbar",
            thickness=12,
            troughcolor=PHOENIX_THEME.card_bg,
            background=PHOENIX_THEME.accent,
            bordercolor=PHOENIX_THEME.border,
            lightcolor=PHOENIX_THEME.accent,
            darkcolor=PHOENIX_THEME.accent,
        )

        self._progress_bar = ttk.Progressbar(
            self._content,
            style="Qwen.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100,
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
        self._status_lbl.pack(fill="x", pady=(0, PHOENIX_THEME.space_sm))
        self._status_lbl.configure(text="0 % heruntergeladen", fg=PHOENIX_THEME.text_muted)
        self._progress_bar.pack(fill="x", pady=PHOENIX_THEME.space_md)

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
            self.after(0, self._on_failed, tr("boost_ollama_not_found", "Ollama-Programm wurde nicht gefunden."))
            return

        try:
            self._process = subprocess.Popen(
                [executable, "pull", OllamaStatusService.MODEL],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )

            buffer = ""
            while not self._is_cancelled:
                char = self._process.stdout.read(1)
                if not char:
                    break
                if char in ("\r", "\n"):
                    line = buffer.strip()
                    if line:
                        self.after(0, self._parse_output_line, line)
                    buffer = ""
                else:
                    buffer += char

            # Wait for exit status
            exit_code = self._process.wait()
            if self._is_cancelled:
                return

            if exit_code == 0:
                self.after(0, self._on_success_state)
            else:
                self.after(0, self._on_failed, f"pull process returned non-zero exit code: {exit_code}")

        except Exception as e:
            if not self._is_cancelled:
                self.after(0, self._on_failed, str(e))

    def _parse_output_line(self, line: str) -> None:
        # Parse status and percentage
        if "manifest" in line:
            if "writing" in line:
                self._desc_lbl.configure(text=tr("boost_status_installing", "Installation wird abgeschlossen …"))
            else:
                self._desc_lbl.configure(text=tr("boost_qwen_preparing", "Vorbereitung …"))
        elif "verifying" in line:
            self._desc_lbl.configure(text=tr("boost_status_verifying", "Installation wird abgeschlossen …"))
        elif "downloading" in line:
            match = re.search(r"(\d+(?:\.\d+)?)%", line)
            if match:
                try:
                    pct = int(float(match.group(1)))
                except ValueError:
                    pct = 0
                self._progress_bar["value"] = pct
                self._status_lbl.configure(text=tr("boost_pct_downloaded", "{pct} % heruntergeladen", pct=pct))
            else:
                self._status_lbl.configure(text=tr("boost_qwen_downloading_start", "Qwen2.5 3B wird heruntergeladen"))
        elif "success" in line:
            self._progress_bar["value"] = 100
            self._desc_lbl.configure(text=tr("boost_status_completed", "Installation wird abgeschlossen …"))

    def _on_success_state(self) -> None:
        self._success = True
        OllamaStatusService.invalidate_cache()

        # Update Dialog title/steps
        for child in self._title_frame.winfo_children():
            child.destroy()

        tk.Label(
            self._title_frame,
            text=tr("boost_ai_title", "Phoenix Boost einrichten"),
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
        self._progress_bar["value"] = 100

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
        self._is_cancelled = True
        super().close()
