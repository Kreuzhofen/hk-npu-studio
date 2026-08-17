from __future__ import annotations

import tkinter as tk
import threading
from typing import Callable

from app.i18n import tr
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from engine.ollama_status import OllamaStatusService
from widgets.phoenix.theme import PHOENIX_THEME
from widgets.phoenix.controls.button import PhoenixButton


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

        super().__init__(
            master,
            title=tr("boost_ollama_setup_title", "Ollama vorbereiten"),
            brand=brand,
            size=(540, 320),
            min_size=(480, 280),
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
            tr("boost_ollama_setup_title", "Ollama vorbereiten"),
            tr("boost_ollama_setup_subtitle", "Schritt 1/2")
        )

        card = self.add_card()
        content = tk.Frame(card, bg=PHOENIX_THEME.elevated_bg)
        content.pack(fill="both", expand=True, padx=PHOENIX_THEME.card_pad_x, pady=PHOENIX_THEME.card_pad_y)

        # Instructions
        tk.Label(
            content,
            text=tr("boost_ollama_setup_desc", "Snapdragon AI Studio benötigt Ollama für den optionalen lokalen KI-Boost."),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            justify="left",
            wraplength=440,
        ).pack(fill="x", pady=(0, PHOENIX_THEME.space_md))

        tk.Label(
            content,
            text=tr("boost_ollama_setup_desc_3", "Bitte kehren Sie zu Snapdragon AI Studio zurück."),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
            justify="left",
            wraplength=440,
        ).pack(fill="x", pady=(0, PHOENIX_THEME.space_lg))

        # Status Label
        self._status_lbl = tk.Label(
            content,
            text=tr("boost_ollama_setup_status_waiting", "Warten auf Ollama-Installation..."),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.warning,
            font=PHOENIX_THEME.font_card_title,
            anchor="center",
        )
        self._status_lbl.pack(fill="x", pady=(PHOENIX_THEME.space_sm, 0))

        # Close button in footer
        self._close_btn = PhoenixButton(
            self.footer,
            text=tr("cancel", "Abbrechen"),
            command=self.close,
            button_type="secondary",
            width=150,
        )
        self._close_btn.pack(anchor="center")

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
        self._close_btn.configure(
            text=tr("continue", "Weiter"),
            command=self._finish,
            button_type="primary",
        )

    def _finish(self) -> None:
        self.close()
        self._on_detected()

    def close(self) -> None:
        self._is_active = False
        super().close()
