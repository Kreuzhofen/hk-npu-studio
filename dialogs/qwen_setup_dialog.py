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

logger = logging.getLogger("QwenSetup")

from app.i18n import tr
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from engine.ollama_status import OllamaStatusService
from widgets.phoenix.theme import PHOENIX_THEME
from widgets.phoenix.controls.button import PhoenixButton


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
            size=(540, 340),
            min_size=(480, 300),
            resizable=False,
        )

        self._build_ui()
        self.center(master)

        # Start download in background thread
        threading.Thread(target=self._run_pull, daemon=True).start()

        self.wait_window(self)

    def _build_ui(self) -> None:
        # Title and Steps
        self._title_frame = self.add_title(
            tr("boost_ai_title", "Phoenix Boost einrichten"),
            tr("boost_qwen_setup_subtitle", "Schritt 2/2")
        )

        card = self.add_card()
        content = tk.Frame(card, bg=PHOENIX_THEME.elevated_bg)
        content.pack(fill="both", expand=True, padx=PHOENIX_THEME.card_pad_x, pady=PHOENIX_THEME.card_pad_y)

        # Instruction / Progress Title
        self._status_lbl = tk.Label(
            content,
            text=tr("boost_qwen_downloading", "Qwen2.5 3B wird heruntergeladen"),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        )
        self._status_lbl.pack(fill="x", pady=(0, PHOENIX_THEME.space_sm))

        # Progress bar
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure(
            "Phoenix.Horizontal.TProgressbar",
            thickness=12,
            troughcolor=PHOENIX_THEME.card_bg,
            background=PHOENIX_THEME.accent,
            bordercolor=PHOENIX_THEME.border,
            lightcolor=PHOENIX_THEME.accent,
            darkcolor=PHOENIX_THEME.accent,
        )
        
        self._progress_bar = ttk.Progressbar(
            content,
            style="Phoenix.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100,
        )
        self._progress_bar.pack(fill="x", pady=PHOENIX_THEME.space_md)

        # Detail text / speed / state
        self._detail_lbl = tk.Label(
            content,
            text=tr("boost_qwen_preparing", "Vorbereiten..."),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
            justify="left",
            wraplength=440,
        )
        self._detail_lbl.pack(fill="x")

        # Action button in footer
        self._action_btn = PhoenixButton(
            self.footer,
            text=tr("cancel", "Abbrechen"),
            command=self._cancel_download,
            button_type="secondary",
            width=150,
        )
        self._action_btn.pack(anchor="center")

    def _run_pull(self) -> None:
        # Find executable using same fallback as detect
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

            # Character-by-character parser to handle carriage returns (\r)
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
                self.after(0, self._on_failed, tr("boost_qwen_pull_failed", "Herunterladen des Modells fehlgeschlagen."))

        except Exception as e:
            if not self._is_cancelled:
                self.after(0, self._on_failed, str(e))

    def _parse_output_line(self, line: str) -> None:
        # Parse status and percentage
        # Format example: downloading 862a5e4d2b27... 45.2% 72 MB/1.6 GB 12 MB/s
        if "manifest" in line:
            if "writing" in line:
                self._detail_lbl.configure(text=tr("boost_status_installing", "Installation wird abgeschlossen …"))
            else:
                self._detail_lbl.configure(text=tr("boost_qwen_preparing", "Vorbereitung …"))
        elif "verifying" in line:
            self._detail_lbl.configure(text=tr("boost_status_verifying", "Installation wird abgeschlossen …"))
        elif "downloading" in line:
            # Extract percentage if present
            match = re.search(r"(\d+(?:\.\d+)?)%", line)
            if match:
                try:
                    pct = int(float(match.group(1)))
                except ValueError:
                    pct = 0
                self._progress_bar["value"] = pct
                self._detail_lbl.configure(text=tr("boost_pct_downloaded", "{pct} % heruntergeladen", pct=pct))
            else:
                self._detail_lbl.configure(text=tr("boost_qwen_downloading_start", "Qwen2.5 3B wird heruntergeladen"))
        elif "success" in line:
            self._progress_bar["value"] = 100
            self._detail_lbl.configure(text=tr("boost_status_completed", "Installation wird abgeschlossen …"))

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
        self._detail_lbl.configure(text=tr("boost_status_success_desc", "Das Modell wurde erfolgreich installiert."))
        self._progress_bar["value"] = 100

        self._action_btn.configure(
            text=tr("done", "Fertigstellen"),
            command=self._finish_success,
            button_type="primary",
        )

    def _on_failed(self, error_msg: str) -> None:
        logger.error("Qwen installation failed: %s", error_msg)
        self._status_lbl.configure(text=tr("error", "Fehler"), fg=PHOENIX_THEME.danger)
        self._detail_lbl.configure(
            text=tr(
                "boost_qwen_install_failed_friendly",
                "Qwen2.5 3B konnte nicht installiert werden. Bitte prüfen Sie, ob Ollama ausgeführt wird, und versuchen Sie es erneut."
            ),
            fg=PHOENIX_THEME.danger
        )
        self._progress_bar["value"] = 0
        self._action_btn.configure(
            text=tr("close", "Schließen"),
            command=self.close,
        )

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
