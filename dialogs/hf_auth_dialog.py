from __future__ import annotations

import threading
import tkinter as tk
from queue import Empty, Queue

from app.i18n import tr
from app.settings_manager import SettingsManager
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.theme import PHOENIX_THEME


class HuggingFaceAuthDialog(StudioDialog):
    """Request and verify a token only for a model contract that requires it."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        model_name: str,
        brand: BrandManager | None = None,
    ) -> None:
        self.authenticated = False
        self.token = ""
        self._events: Queue[tuple[bool, str, bool]] = Queue()
        super().__init__(
            master,
            title=tr("hf_auth_title", "Hugging Face sign-in"),
            brand=brand,
            size=(620, 440),
            min_size=(560, 400),
            resizable=True,
        )
        self._build_ui(model_name)
        self.center(master)
        existing = str(SettingsManager.get_hf_token() or "").strip()
        if existing:
            self.token_entry.insert(0, existing)
            self.status_label.configure(text=tr("hf_auth_checking_saved", "Checking the saved token …"))
            self.submit_button.configure(state="disabled")
            self.after(50, lambda: self._start_validation(existing, False))
        self.wait_window(self)

    def _build_ui(self, model_name: str) -> None:
        self.add_title(model_name, tr("hf_auth_title", "Hugging Face sign-in"))
        card = self.add_card()
        content = tk.Frame(card, bg=PHOENIX_THEME.elevated_bg)
        content.pack(fill="x", padx=PHOENIX_THEME.card_pad_x, pady=PHOENIX_THEME.card_pad_y)
        tk.Label(
            content,
            text=tr(
                "hf_auth_required_explanation",
                "This model requires a Hugging Face sign-in for downloading.",
            ),
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body, anchor="w", justify="left", wraplength=500,
        ).pack(fill="x", pady=(0, PHOENIX_THEME.space_md))
        tk.Label(
            content, text=tr("hf_auth_token_label", "Hugging Face token"),
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small, anchor="w",
        ).pack(fill="x", pady=(0, PHOENIX_THEME.space_xs))
        self.token_entry = tk.Entry(
            content, show="*", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightthickness=1,
            relief="flat", font=PHOENIX_THEME.font_body,
        )
        self.token_entry.pack(fill="x", ipady=7)

        self.status_label = tk.Label(
            self.body, text=tr("hf_auth_enter_token", "Enter your token and select Check token."),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small, anchor="w", justify="left", wraplength=500,
        )
        self.status_label.pack(fill="x")

        self.footer.grid_columnconfigure(0, weight=1)
        self.footer.grid_columnconfigure(1, weight=0)
        self.footer.grid_columnconfigure(2, weight=0)
        self.submit_button = PhoenixButton(
            self.footer, text=tr("hf_auth_check", "Check token"),
            command=self._submit, button_type="primary", width=190,
        )
        self.submit_button.grid(row=0, column=1, padx=(0, PHOENIX_THEME.space_md))
        self.cancel_button = PhoenixButton(
            self.footer, text=tr("cancel", "Cancel"), command=self.close,
            button_type="neutral", width=130,
        )
        self.cancel_button.grid(row=0, column=2)

    def _submit(self) -> None:
        token = self.token_entry.get().strip()
        if not token:
            self.status_label.configure(
                text=tr("hf_auth_missing", "Enter a Hugging Face token."),
                fg=PHOENIX_THEME.warning,
            )
            return
        self._start_validation(token, True)

    def _start_validation(self, token: str, save_on_success: bool) -> None:
        self.submit_button.configure(state="disabled")
        self.status_label.configure(
            text=tr("hf_auth_checking", "Hugging Face sign-in is being checked …"),
            fg=PHOENIX_THEME.text_muted,
        )
        threading.Thread(
            target=self._validate_worker,
            args=(token, save_on_success),
            daemon=True,
            name="HuggingFaceTokenCheck",
        ).start()
        self.after(100, self._poll_result)

    def _validate_worker(self, token: str, save_on_success: bool) -> None:
        valid, _message = SettingsManager.test_hf_token(token)
        self._events.put((valid, token, save_on_success))

    def _poll_result(self) -> None:
        try:
            valid, token, save_on_success = self._events.get_nowait()
        except Empty:
            if self.winfo_exists():
                self.after(100, self._poll_result)
            return
        self._apply_result(valid, token, save_on_success)

    def _apply_result(self, valid: bool, token: str, save_on_success: bool) -> None:
        if not valid:
            self.submit_button.configure(state="normal")
            self.status_label.configure(
                text=tr("hf_auth_invalid", "The token could not be verified. Check it and try again."),
                fg=PHOENIX_THEME.danger,
            )
            return
        if save_on_success:
            settings = SettingsManager.load_settings()
            settings["hf_token"] = token
            if not SettingsManager.save_settings(settings):
                self.submit_button.configure(state="normal")
                self.status_label.configure(
                    text=tr("hf_auth_save_failed", "The token is valid but could not be saved."),
                    fg=PHOENIX_THEME.danger,
                )
                return
        self.authenticated = True
        self.token = token
        self.close()
