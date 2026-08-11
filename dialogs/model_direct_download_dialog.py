from __future__ import annotations

import threading
import tkinter as tk
from queue import Empty, Queue
from tkinter import ttk
from typing import Any, Callable

from app.i18n import tr
from config import MODELS_DIR
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.theme import PHOENIX_THEME, configure_phoenix_styles


class ModelDirectDownloadDialog(StudioDialog):
    """Confirmation and responsive progress UI for a DIRECT model package."""

    PROGRESS_STYLE = "Phoenix.Horizontal.TProgressbar"
    DIALOG_SIZE = (660, 520)
    MIN_SIZE = (580, 470)
    START_BUTTON_WIDTH = 290
    CANCEL_BUTTON_WIDTH = 130

    def __init__(
        self,
        master: tk.Misc,
        *,
        model_name: str,
        download_size: float | int | None,
        start_install: Callable[[Callable[[Any], None]], bool],
        on_installed: Callable[[], None],
        on_open_generate: Callable[[], None],
        brand: BrandManager | None = None,
    ) -> None:
        self._start_install = start_install
        self._on_installed = on_installed
        self._on_open_generate = on_open_generate
        self._running = False
        self._failure_message_shown = False
        self._events: Queue[tuple[str, object]] = Queue()
        super().__init__(
            master,
            title=tr("direct_model_install_title", "Install model"),
            brand=brand,
            size=self.DIALOG_SIZE,
            min_size=self.MIN_SIZE,
            resizable=True,
        )
        configure_phoenix_styles(self)
        self._build_ui(model_name, download_size)
        self.center(master)
        self.wait_window(self)

    def _build_ui(self, model_name: str, download_size: float | int | None) -> None:
        self.add_title(
            tr("direct_model_install_title", "Install model"),
            tr("direct_model_install_automatic", "Snapdragon AI Studio installs the model automatically."),
        )
        if download_size:
            size_text = tr("direct_model_download_size", "Download size: approximately {size:g} GB", size=download_size)
        else:
            size_text = tr("direct_model_download_size_unknown", "Download size: determined during download")

        details_card = self.add_card()
        details = tk.Frame(details_card, bg=PHOENIX_THEME.elevated_bg)
        details.pack(
            fill="x",
            padx=PHOENIX_THEME.card_pad_x,
            pady=PHOENIX_THEME.card_pad_y,
        )
        tk.Label(
            details,
            text=model_name,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_value,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, PHOENIX_THEME.space_md))
        tk.Label(
            details, text=size_text,
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body, anchor="w",
        ).pack(fill="x", pady=(0, PHOENIX_THEME.space_md))
        tk.Label(
            details,
            text=tr("direct_model_target_name", "Destination: Snapdragon AI Studio Models"),
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title, anchor="w",
        ).pack(fill="x")
        tk.Label(
            details,
            text=tr("direct_model_target_path", "Folder: {path}", path=str(MODELS_DIR)),
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption, anchor="w", wraplength=540,
        ).pack(fill="x", pady=(PHOENIX_THEME.space_xs, 0))

        tk.Label(
            self.body,
            text=tr(
                "direct_model_automatic_steps",
                "✓ Download\n✓ Automatic installation\n✓ No manual file steps",
            ),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body, justify="left", anchor="w",
        ).pack(fill="x", pady=(0, PHOENIX_THEME.space_lg))

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress = ttk.Progressbar(
            self.body, variable=self.progress_var, maximum=100.0,
            style=self.PROGRESS_STYLE,
        )
        self.progress.pack(fill="x", ipady=3, pady=(0, PHOENIX_THEME.space_sm))
        self.status_label = tk.Label(
            self.body,
            text=tr("direct_model_ready_to_download", "Ready to download."),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        self.status_label.pack(fill="x")

        self.footer.grid_columnconfigure(0, weight=1)
        self.footer.grid_columnconfigure(1, weight=0)
        self.footer.grid_columnconfigure(2, weight=0)
        self.start_button = PhoenixButton(
            self.footer,
            text=tr("direct_model_start", "Start download and installation"),
            command=self._start,
            button_type="primary",
            width=self.START_BUTTON_WIDTH,
        )
        self.start_button.grid(row=0, column=1, padx=(0, PHOENIX_THEME.space_md))
        self.cancel_button = PhoenixButton(
            self.footer, text=tr("cancel", "Cancel"), command=self.close,
            button_type="neutral", width=self.CANCEL_BUTTON_WIDTH,
        )
        self.cancel_button.grid(row=0, column=2)

    def _start(self) -> None:
        if self._running:
            return
        self._running = True
        self.start_button.grid_remove()
        self.status_label.configure(
            text=tr("direct_model_downloading", "Model is being downloaded …"),
            fg=PHOENIX_THEME.success,
        )
        threading.Thread(target=self._worker, daemon=True, name="DirectModelInstall").start()
        self.after(100, self._poll_events)

    def _worker(self) -> None:
        try:
            success = self._start_install(self._queue_progress)
        except Exception:
            success = False
        self._events.put(("finished", success))

    def _queue_progress(self, update: Any) -> None:
        self._events.put(("progress", update))

    def _poll_events(self) -> None:
        try:
            while True:
                event, value = self._events.get_nowait()
                if event == "progress":
                    self._set_progress(value)
                elif event == "finished":
                    self._finish(bool(value))
                    return
        except Empty:
            pass
        if self._running and self.winfo_exists():
            self.after(100, self._poll_events)

    def _set_progress(self, update: Any) -> None:
        phase = "downloading"
        percent = update
        if isinstance(update, dict):
            phase = str(update.get("phase") or phase)
            percent = update.get("percent", 0.0)
        value = max(0.0, min(100.0, float(percent)))
        self.progress_var.set(value)
        messages = {
            "downloading": tr("direct_model_downloading_percent", "Model is being downloaded … {percent:.0f}%", percent=value),
            "download_complete": tr("direct_model_download_complete", "Download completed."),
            "checking": tr("direct_model_checking", "Model package is being checked …"),
            "installing": tr("direct_model_installing", "Model is being installed …"),
            "activating": tr("direct_model_activating", "Model is being activated …"),
            "ready": tr("direct_model_ready", "✓ Model is ready"),
            "download_failed": tr("direct_model_download_failed", "Download failed. Please check your connection and try again."),
            "validation_failed": tr("direct_model_validation_failed", "The downloaded model package could not be verified."),
            "install_failed": tr("direct_model_installation_failed", "The verified model package could not be installed."),
            "activation_failed": tr("direct_model_activation_failed", "The model was installed but could not be activated."),
        }
        failed = phase.endswith("_failed")
        self._failure_message_shown = failed
        self.status_label.configure(
            text=messages.get(phase, messages["downloading"]),
            fg=PHOENIX_THEME.danger if failed else PHOENIX_THEME.success,
        )

    def _finish(self, success: bool) -> None:
        self._running = False
        if success:
            self.progress_var.set(100.0)
            self.status_label.configure(
                text=tr("direct_model_ready", "✓ Model is ready"),
                fg=PHOENIX_THEME.success,
            )
            self._on_installed()
            self.start_button.configure(
                text=tr("home_create_first_image", "Create first image"),
                command=self._open_generate,
            )
            self.start_button.grid()
            return
        self.start_button.grid()
        if not self._failure_message_shown:
            self.status_label.configure(
                text=tr("direct_model_install_error", "The model could not be downloaded or installed. Please check your connection and try again."),
                fg=PHOENIX_THEME.danger,
            )

    def _open_generate(self) -> None:
        self._on_open_generate()
        self.close()
