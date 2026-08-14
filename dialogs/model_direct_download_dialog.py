from __future__ import annotations

import threading
import logging
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

logger = logging.getLogger("ModelDirectDownloadDialog")


class ModelDirectDownloadDialog(StudioDialog):
    """Confirmation and responsive progress UI for a DIRECT model package."""

    PROGRESS_STYLE = "Phoenix.Horizontal.TProgressbar"
    DIALOG_SIZE = (700, 790)
    MIN_SIZE = (620, 720)
    START_BUTTON_WIDTH = 290
    CANCEL_BUTTON_WIDTH = 130
    NAVIGATION_DELAY_MS = 180
    SD35_DIALOG_SIZE = (760, 890)
    SD35_MIN_SIZE = (680, 810)
    SD35_LOG_VISIBLE_LINES = 6

    def __init__(
        self,
        master: tk.Misc,
        *,
        model_name: str,
        download_size: float | int | None,
        start_install: Callable[[Callable[[Any], None]], bool],
        on_installed: Callable[[], None],
        on_open_generate: Callable[[], None],
        cancel_install: Callable[[], Any] | None = None,
        start_redownload: Callable[[Callable[[Any], None]], bool] | None = None,
        operation: str = "direct",
        auto_start: bool = False,
        requires_hf_token: bool = False,
        description_key: str | None = None,
        brand: BrandManager | None = None,
    ) -> None:
        self._start_install = start_install
        self._on_installed = on_installed
        self._on_open_generate = on_open_generate
        self._cancel_install = cancel_install
        self._start_redownload = start_redownload
        self._operation = operation
        self._requires_hf_token = bool(requires_hf_token)
        self._description_key = str(description_key or "").strip()
        self._running = False
        self._failure_message_shown = False
        self._redownload_required = False
        self._activation_failed = False
        self._events: Queue[tuple[str, object]] = Queue()
        guided_sd35 = self._operation in ("sd35_folder", "sd35_auto")
        size = self.SD35_DIALOG_SIZE if guided_sd35 else self.DIALOG_SIZE
        min_size = self.SD35_MIN_SIZE if guided_sd35 else self.MIN_SIZE
        super().__init__(
            master,
            title=tr("sd35_install_title", "Install Stable Diffusion 3.5 Medium") if guided_sd35 else tr("direct_model_install_title", "Install model"),
            brand=brand,
            size=size,
            min_size=min_size,
            resizable=True,
        )
        configure_phoenix_styles(self)
        self._build_ui(model_name, download_size)
        self.center(master)
        if auto_start:
            self.after(0, self._start)
        self.wait_window(self)

    def _build_ui(self, model_name: str, download_size: float | int | None) -> None:
        guided_sd35 = self._operation in ("sd35_folder", "sd35_auto")
        self.add_title(
            tr("sd35_install_title", "Install Stable Diffusion 3.5 Medium") if guided_sd35 else tr("direct_model_install_title", "Install model"),
            tr("sd35_folder_processing", "Snapdragon AI Studio checks and installs the Qualcomm model folder automatically.") if guided_sd35 else tr("direct_model_install_automatic", "Snapdragon AI Studio installs the model automatically."),
        )
        if guided_sd35:
            size_text = tr("sd35_folder_selected", "Qualcomm model folder selected")
        elif download_size:
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
        if getattr(self, "_description_key", ""):
            tk.Label(
                details,
                text=tr(
                    self._description_key,
                    "Snapdragon AI Studio downloads and sets up the compatible model automatically.",
                ),
                bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_body, anchor="w", justify="left", wraplength=540,
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
            details,
            text=tr(
                "model_hf_token_required" if getattr(self, "_requires_hf_token", False) else "model_hf_token_not_required",
                "Hugging Face Access Token: Required." if getattr(self, "_requires_hf_token", False) else "Hugging Face Access Token: Not required.",
            ),
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small, anchor="w",
        ).pack(fill="x", pady=(PHOENIX_THEME.space_sm, 0))

        if self._operation == "sd35_auto":
            steps_text = tr(
                "sd35_auto_steps",
                "✓ ZIP archive automatic search and extraction\n✓ Automatic installation of Python requirements\n✓ Automatic execution of the Qualcomm script\n✓ Manifest creation and staging\n✓ Final target model validation and activation"
            )
        elif guided_sd35:
            steps_text = tr("sd35_folder_automatic_steps", "✓ Check model files\n✓ Create manifest and checksums\n✓ Automatic installation and activation")
        else:
            steps_text = "\n".join((
                tr("direct_step_prepare", "Prepare download"),
                tr("direct_step_download", "Download model files"),
                tr("direct_step_check", "Check model package"),
                tr("direct_step_install", "Install model"),
                tr("direct_step_validate", "Validate model"),
                tr("direct_step_activate", "Activate model"),
            ))

        self.steps_label = tk.Label(
            self.body,
            text="",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body, justify="left", anchor="w",
        )
        self.steps_label.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))
        self._step_texts = [line.lstrip("✓○…✗ ").strip() for line in steps_text.splitlines() if line.strip()]
        self._step_states = ["NOT_STARTED"] * len(self._step_texts)
        self._render_step_states()

        self.download_desc_label = tk.Label(
            self.body,
            text="",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        )
        self.download_desc_label.pack(fill="x", pady=(0, PHOENIX_THEME.space_xs))

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress = ttk.Progressbar(
            self.body, variable=self.progress_var, maximum=100.0,
            style=self.PROGRESS_STYLE,
        )
        self.progress.pack(fill="x", ipady=3, pady=(0, PHOENIX_THEME.space_sm))
        self.status_label = tk.Label(
            self.body,
            text=tr("sd35_folder_ready", "Ready to check the model folder.") if guided_sd35 else tr("direct_model_ready_to_download", "Ready to download."),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))

        self.download_metrics_label = tk.Label(
            self.body,
            text="",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            justify="left",
            anchor="w",
        )
        self.download_metrics_label.pack(fill="x", pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.space_md))

        log_frame = tk.Frame(self.body, bg=PHOENIX_THEME.card_bg, highlightbackground=PHOENIX_THEME.border, highlightthickness=1)
        log_frame.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))

        self.log_widget = tk.Text(
            log_frame,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            borderwidth=0,
            highlightthickness=0,
            wrap="word",
            padx=8,
            pady=6,
            height=self.SD35_LOG_VISIBLE_LINES,
        )
        self.log_widget.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_widget.yview)
        scrollbar.pack(fill="y", side="right")
        self.log_widget.configure(yscrollcommand=scrollbar.set)

        self.log_widget.tag_config("success", foreground=PHOENIX_THEME.success)
        self.log_widget.tag_config("error", foreground=PHOENIX_THEME.danger)
        self.log_widget.tag_config("warning", foreground=PHOENIX_THEME.warning)
        self.log_widget.tag_config("info", foreground=PHOENIX_THEME.text_secondary)
        self.log_widget.configure(state="disabled")
        self._logged_phases = set()

        self.warning_label = tk.Label(
            self.body,
            text=tr("sd35_install_warning", "This process may take some time. Please do not close Snapdragon AI Studio during setup.")
            if guided_sd35 else tr("direct_model_install_warning", "The installation may take some time. You can cancel the download at any time."),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
            justify="left",
            wraplength=540,
        )
        self.warning_label.pack(fill="x", pady=(0, PHOENIX_THEME.space_sm))

        self.footer.grid_columnconfigure(0, weight=1)
        self.footer.grid_columnconfigure(1, weight=0)
        self.footer.grid_columnconfigure(2, weight=0)
        self.start_button = PhoenixButton(
            self.footer,
            text=tr("continue", "Continue") if guided_sd35 else tr("direct_model_start", "Start download and installation"),
            command=self._start,
            button_type="primary",
            width=self.START_BUTTON_WIDTH,
        )
        self.start_button.grid(row=0, column=1, padx=(0, PHOENIX_THEME.space_md))
        self.cancel_button = PhoenixButton(
            self.footer, text=tr("cancel", "Cancel"), command=self._cancel_or_close,
            button_type="neutral", width=self.CANCEL_BUTTON_WIDTH,
        )
        self.cancel_button.grid(row=0, column=2)

    def _cancel_or_close(self) -> None:
        if self._running and callable(self._cancel_install):
            self._cancel_install()
        self.close()

    def _start(self) -> None:
        if self._running:
            return
        self._running = True
        self.start_button.grid_remove()
        self._set_progress({"phase": "download_preparing", "percent": 0.0})
        threading.Thread(target=self._worker, daemon=True, name="DirectModelInstall").start()
        self.after(100, self._poll_events)

    def _worker(self) -> None:
        try:
            success = self._start_install(self._queue_progress)
        except Exception as exc:
            logger.exception("DIRECT model installation worker failed")
            self._queue_progress({
                "phase": "install_failed",
                "percent": 0.0,
                "error": type(exc).__name__,
            })
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

    def _log_message(self, text: str, tag: str = "info") -> None:
        if not hasattr(self, "log_widget") or not self.log_widget.winfo_exists():
            return
        import datetime
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", f"{timestamp} ", "info")
        self.log_widget.insert("end", f"{text}\n", tag)
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")

    def _render_step_states(self) -> None:
        symbols = {
            "NOT_STARTED": "○",
            "RUNNING": "…",
            "SUCCESS": "✓",
            "FAILED": "✗",
        }
        self.steps_label.configure(
            text="\n".join(
                f"{symbols.get(state, '○')} {text}"
                for state, text in zip(self._step_states, self._step_texts)
            )
        )

    def _update_step_states(self, phase: str, update: Any) -> None:
        if not getattr(self, "_step_states", None):
            return
        running_step = {
            "download_preparing": 0,
            "downloading": 1,
            "download_complete": 2,
            "sd35_find_zip": 0,
            "sd35_extracting": 0,
            "checking": 2,
            "sd35_installing_deps": 1,
            "sd35_downloading_weights": 3,
            "sd35_reusing_models": 4,
            "sd35_importing": 4,
            "preparing": 2,
            "installing": 3,
            "validating": 4,
            "activating": 5,
            "validation_ready": 5,
        }.get(phase)
        if phase == "sd35_downloading_weights":
            for index in range(min(3, len(self._step_states))):
                self._step_states[index] = "SUCCESS"
        if running_step is not None:
            for index in range(min(running_step, len(self._step_states))):
                if self._step_states[index] != "FAILED":
                    self._step_states[index] = "SUCCESS"
            if running_step < len(self._step_states):
                self._step_states[running_step] = "RUNNING"
        if phase in ("ready", "cleanup_warning"):
            self._step_states = ["SUCCESS"] * len(self._step_states)
        failed_step = update.get("failed_step") if isinstance(update, dict) else None
        if isinstance(failed_step, int) and 0 <= failed_step < len(self._step_states):
            self._step_states[failed_step] = "FAILED"
            for index in range(failed_step + 1, len(self._step_states)):
                self._step_states[index] = "NOT_STARTED"
        self._render_step_states()

    def _set_progress(self, update: Any) -> None:
        phase = "downloading"
        percent = update
        if isinstance(update, dict):
            phase = str(update.get("phase") or phase)
            percent = update.get("percent", 0.0)
        value = max(0.0, min(100.0, float(percent)))
        self.progress_var.set(value)
        guided_sd35 = getattr(self, "_operation", None) in ("sd35_folder", "sd35_auto")
        self._update_step_states(phase, update)
        messages = {
            "download_preparing": tr("direct_model_preparing_download", "Download is being prepared …"),
            "downloading": tr("direct_model_downloading_percent", "Model is being downloaded … {percent:.0f}%", percent=value),
            "download_complete": tr("direct_model_download_complete", "Download completed."),
            "checking": tr("direct_model_checking", "Model package is being checked …"),
            "preparing": tr("sd35_model_preparing", "Model is being prepared …"),
            "installing": tr("direct_model_installing", "Model is being installed …"),
            "validating": tr("direct_model_validating", "Model is being validated …"),
            "activating": tr("direct_model_activating", "Model is being activated …"),
            "ready": tr("sd35_ready_clean", "✓ Stable Diffusion 3.5 Medium was successfully installed. The temporary Qualcomm installation files have been removed.") if guided_sd35 else tr("home_studio_ready", "✓ Snapdragon AI Studio is ready"),
            "cleanup_warning": tr("sd35_cleanup_warning", "✓ Stable Diffusion 3.5 Medium was successfully installed. However, the temporary Qualcomm files could not be automatically removed."),
            "sd35_find_zip": tr("sd35_find_zip", "Locating ZIP file …"),
            "sd35_extracting": tr("sd35_extracting", "Preparing Qualcomm files (extracting) …"),
            "sd35_installing_deps": tr("sd35_installing_deps", "Setting up required components (Python packages) …"),
            "sd35_downloading_weights": tr("sd35_downloading_weights", "Downloading model files (Qualcomm script) …"),
            "sd35_importing": tr("sd35_importing", "Preparing and importing model into Snapdragon AI Studio …"),
            "download_failed": tr("direct_model_download_failed", "Download failed. Please check your connection and try again."),
            "validation_failed": tr("direct_model_validation_failed", "The downloaded model package could not be verified."),
            "sd35_folder_incomplete": tr("sd35_folder_incomplete", "Not all required Stable Diffusion 3.5 files were found in this folder. Please select the folder created by the Qualcomm sample after the download."),
            "install_failed": tr("direct_model_installation_failed", "The verified model package could not be installed."),
            "activation_failed": tr("direct_model_activation_failed", "The model was installed but could not be activated."),
            "final_validation_failed": tr("direct_model_final_validation_failed", "The installed model could not be validated."),
            "redownload_required": tr("sd35_redownload_required", "The existing model files are incomplete or damaged."),
            "source_validation_failed": tr("sd35_source_validation_failed", "The required Qualcomm model files are incomplete."),
            "dependency_failed": tr("sd35_dependency_failed", "The required components could not be prepared."),
        }

        # Log milestones to text widget if guided/auto SD3.5
        if hasattr(self, "log_widget") and phase not in self._logged_phases:
            self._logged_phases.add(phase)
            log_messages = {
                "sd35_find_zip": (tr("sd35_log_find", "Searching for ZIP archive qai-appbuilder-main.zip …"), "info"),
                "sd35_extracting": (tr("sd35_log_extracting", "ZIP archive found. Extraction started …"), "info"),
                "checking": (tr("direct_model_checking", "Model package is being checked …"), "info"),
                "sd35_installing_deps": (tr("sd35_log_deps", "Installing Python dependencies …"), "info"),
                "sd35_downloading_weights": (tr("sd35_log_weights", "Qualcomm SD3.5 preparation & download started …"), "warning"),
                "sd35_importing": (tr("sd35_log_import", "Importing model files into Snapdragon AI Studio …"), "info"),
                "installing": (tr("direct_model_installing", "Model is being installed …"), "info"),
                "activating": (tr("direct_model_activating", "Model is being activated …"), "info"),
                "ready": ((tr("sd35_log_ready", "Stable Diffusion 3.5 Medium successfully set up!") if guided_sd35 else tr("home_studio_ready", "Snapdragon AI Studio is ready")), "success"),
                "cleanup_warning": (tr("sd35_log_cleanup_warn", "⚠ Temporary setup files could not be automatically deleted."), "warning"),
                "install_failed": (tr("sd35_log_failed", "❌ Setup failed."), "error"),
                "activation_failed": (tr("direct_model_activation_failed", "The model was installed but could not be activated."), "error"),
                "redownload_required": (tr("sd35_redownload_required", "The existing model files are incomplete or damaged."), "error"),
                "source_validation_failed": (tr("sd35_source_validation_failed", "The required Qualcomm model files are incomplete."), "error"),
                "dependency_failed": (tr("sd35_dependency_failed", "The required components could not be prepared."), "error"),
                "download_preparing": (tr("direct_model_preparing_download", "Download is being prepared …"), "info"),
                "downloading": (tr("direct_model_downloading", "Model is being downloaded …"), "info"),
                "download_complete": (tr("direct_model_download_complete", "Download completed."), "success"),
                "preparing": (tr("sd35_model_preparing", "Model is being prepared …"), "info"),
                "validating": (tr("direct_model_validating", "Model is being validated …"), "info"),
                "validation_failed": (tr("direct_model_validation_failed", "The downloaded model package could not be verified."), "error"),
                "final_validation_failed": (tr("direct_model_final_validation_failed", "The installed model could not be validated."), "error"),
            }
            if phase in log_messages:
                msg, tag = log_messages[phase]
                self._log_message(msg, tag)
                if guided_sd35 and phase in ("ready", "cleanup_warning"):
                    self._log_message(tr("sd35_log_path_info", "The model is now permanently located under: C:\\SnapdragonAI\\models\\stable_diffusion_v3_5_qai"), "success")

        failed = phase.endswith("_failed") or phase == "redownload_required"
        self._failure_message_shown = failed
        self._redownload_required = phase in {
            "redownload_required", "validation_failed", "install_failed",
            "final_validation_failed",
        }
        if phase == "activation_failed":
            self._activation_failed = True
        default_message = next(iter(messages.values()))
        self.status_label.configure(
            text=messages.get(phase, default_message),
            fg=PHOENIX_THEME.danger if failed else PHOENIX_THEME.success,
        )
        if failed and isinstance(update, dict) and update.get("error"):
            self._log_message(f"{phase}: {update['error']}", "error")

        # Handle live download metrics in UI
        if phase in ("downloading", "sd35_downloading_weights") and isinstance(update, dict):
            if hasattr(self, "progress") and self.progress.winfo_exists() and self.progress.cget("mode") == "indeterminate":
                self.progress.stop()
                self.progress.configure(mode="determinate", variable=self.progress_var)

            downloaded = float(update.get("downloaded_bytes", 0))
            total = float(update.get("total_bytes", 0))
            speed = update.get("speed")
            download_percent = float(update.get("download_percent", 0.0))

            def format_size(bytes_val):
                if bytes_val >= 1024*1024*1024:
                    return f"{bytes_val / (1024*1024*1024):.2f} GB"
                return f"{bytes_val / (1024*1024):.1f} MB"

            downloaded_str = format_size(downloaded)
            raw_kb = int(downloaded / 1024)
            raw_kb_str = f"{raw_kb:,}".replace(",", ".")

            if hasattr(self, "download_desc_label"):
                self.download_desc_label.configure(
                    text=tr("sd35_download_desc", "Stable Diffusion 3.5 Medium wird heruntergeladen")
                    if guided_sd35 else tr("direct_model_downloading", "Model is being downloaded …")
                )

            if total > 0:
                total_str = format_size(total)
                remaining = max(0.0, total - downloaded)
                remaining_str = format_size(remaining)

                percent_val = max(0.0, min(100.0, download_percent))
                remaining_percent = max(0.0, 100.0 - percent_val)

                percent_str = tr("sd35_metric_percent", "{percent:.0f}% downloaded\n{remaining:.0f}% remaining", percent=percent_val, remaining=remaining_percent)
                bytes_str = tr("sd35_metric_bytes", "{downloaded} of {total} downloaded\n{remaining} remaining", downloaded=downloaded_str, total=total_str, remaining=remaining_str)
            else:
                percent_str = tr("sd35_downloaded_only", "{downloaded} downloaded", downloaded=downloaded_str)
                bytes_str = tr("sd35_total_size_unknown", "Total size is being determined …")

            if speed is not None and speed > 0:
                raw_str = tr("sd35_metric_speed", "{raw_kb} KB received • {speed:.1f} MB/s", raw_kb=raw_kb_str, speed=speed)
            else:
                raw_str = tr("sd35_metric_raw_kb", "{raw_kb} KB received", raw_kb=raw_kb_str)

            metrics_text = f"{percent_str}\n\n{bytes_str}\n\n{raw_str}"
            if hasattr(self, "download_metrics_label"):
                self.download_metrics_label.configure(text=metrics_text)
                if not self.download_metrics_label.winfo_manager():
                    self.download_metrics_label.pack(fill="x", pady=(PHOENIX_THEME.space_sm, 0))
        else:
            if phase in ("download_preparing", "sd35_find_zip", "sd35_extracting", "checking", "sd35_installing_deps"):
                if hasattr(self, "progress") and self.progress.winfo_exists() and self.progress.cget("mode") == "determinate":
                    self.progress.configure(mode="indeterminate")
                    self.progress.start(10)

                if hasattr(self, "download_desc_label"):
                    self.download_desc_label.configure(
                        text=tr("sd35_download_desc", "Stable Diffusion 3.5 Medium wird heruntergeladen")
                    )

                current_step_text = messages.get(phase, tr("sd35_preparing_download", "Preparing setup …"))
                if hasattr(self, "download_metrics_label"):
                    self.download_metrics_label.configure(
                        text=f"{current_step_text}\n\n{tr('sd35_total_size_unknown', 'Total size is being determined …')}"
                    )
                    if not self.download_metrics_label.winfo_manager():
                        self.download_metrics_label.pack(fill="x", pady=(PHOENIX_THEME.space_sm, 0))
            else:
                if hasattr(self, "progress") and self.progress.winfo_exists() and self.progress.cget("mode") == "indeterminate":
                    self.progress.stop()
                    self.progress.configure(mode="determinate", variable=self.progress_var)

                if hasattr(self, "download_desc_label"):
                    self.download_desc_label.configure(text="")
                if hasattr(self, "download_metrics_label"):
                    self.download_metrics_label.configure(text="")

    def _finish(self, success: bool) -> None:
        self._running = False
        if success:
            self.progress_var.set(100.0)
            if getattr(self, "_operation", None) not in ("sd35_folder", "sd35_auto"):
                self.status_label.configure(
                    text=tr("home_studio_ready", "✓ Snapdragon AI Studio is ready"),
                    fg=PHOENIX_THEME.success,
                )
            self._on_installed()
            cancel_btn = getattr(self, "cancel_button", None)
            if cancel_btn:
                cancel_btn.configure(text=tr("close", "Close"))
            if getattr(self, "_activation_failed", False):
                self.start_button.grid_remove()
                return
            self.start_button.configure(
                text=tr("home_create_first_image", "Create first image"),
                command=self._open_generate,
            )
            self.start_button.grid()
            return
        self.start_button.grid()
        if getattr(self, "_redownload_required", False) and callable(getattr(self, "_start_redownload", None)):
            self.start_button.configure(
                text=tr("sd35_redownload_action", "Download model files again"),
                command=self._start_explicit_redownload,
            )
        if not self._failure_message_shown:
            err_msg = tr("sd35_install_error", "The required model files could not be fully provided. Your already installed models have not been modified.") if getattr(self, "_operation", None) in ("sd35_folder", "sd35_auto") else tr("direct_model_install_error", "The model could not be downloaded or installed. Please check your connection and try again.")
            self.status_label.configure(
                text=err_msg,
                fg=PHOENIX_THEME.danger,
            )
            if getattr(self, "_operation", None) in ("sd35_folder", "sd35_auto"):
                self._log_message(tr("sd35_log_failed", "❌ Setup failed."), "error")

    def _start_explicit_redownload(self) -> None:
        if not callable(self._start_redownload):
            return
        self._start_install = self._start_redownload
        self._failure_message_shown = False
        self._redownload_required = False
        self._step_states = ["NOT_STARTED"] * len(self._step_states)
        self._render_step_states()
        self._start()

    def _open_generate(self) -> None:
        callback = self._on_open_generate
        self.master.after(
            self.NAVIGATION_DELAY_MS,
            lambda: self._close_and_navigate(callback),
        )

    def _close_and_navigate(self, callback: Callable[[], None]) -> None:
        self.close()
        callback()
