from __future__ import annotations

import threading
import tkinter as tk
from queue import Empty, Queue
from tkinter import ttk
from typing import Any, Callable

from app.i18n import tr
from dialogs.studio_dialog import StudioDialog
from engine.application_update_service import (
    ApplicationUpdateManifest,
    ApplicationUpdateService,
)
from engine.release_config import RELEASE
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.theme import PHOENIX_THEME, configure_phoenix_styles


class ApplicationUpdateWorkflow:
    """Thread-safe orchestration; the service never owns application shutdown."""

    def __init__(
        self,
        service: ApplicationUpdateService,
        *,
        on_state: Callable[[str, dict[str, Any]], None],
        exit_app: Callable[[], None],
        schedule: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self.service = service
        self.on_state = on_state
        self.exit_app = exit_app
        self.schedule = schedule or (lambda callback: callback())
        self._cancelled = False

    def check_async(self) -> None:
        threading.Thread(target=self.run_check, daemon=True).start()

    def run_check(self) -> None:
        self._emit("CHECKING")
        result = self.service.fetch_latest_github_release()
        if result.available and result.manifest is not None:
            self._emit("AVAILABLE", manifest=result.manifest)
        elif result.error_code:
            self._emit("ERROR", message=result.message, error_code=result.error_code)
        else:
            self._emit("UP_TO_DATE", message=result.message)

    def install_async(self, manifest: ApplicationUpdateManifest) -> None:
        self._cancelled = False
        threading.Thread(
            target=self.run_install, args=(manifest,), daemon=True
        ).start()

    def run_install(self, manifest: ApplicationUpdateManifest) -> None:
        self._emit("DOWNLOADING", downloaded=0, total=manifest.asset_size, percent=0.0)

        def progress(downloaded: int, total: int | None, percent: float) -> None:
            state = "VERIFYING" if total and downloaded >= total else "DOWNLOADING"
            self._emit(
                state,
                downloaded=downloaded,
                total=total or manifest.asset_size,
                percent=percent,
            )

        staged = self.service.stage_update(manifest, progress_callback=progress)
        if not staged.success or staged.installer_path is None:
            self._emit(
                "ERROR", message=staged.message, error_code=staged.error_code
            )
            return
        if self._cancelled:
            self._emit("ERROR", message=tr("update_cancelled", "Update abgebrochen."))
            return
        self._emit("VERIFYING", downloaded=manifest.asset_size, total=manifest.asset_size, percent=100.0)
        launched = self.service.launch_installer(staged.installer_path)
        if not launched.success:
            self._emit(
                "ERROR", message=launched.message, error_code=launched.error_code
            )
            return
        self._emit("INSTALLER_STARTED", message=launched.message)
        self.schedule(self.exit_app)

    def cancel(self) -> None:
        self._cancelled = True
        self.service.cancel_download()

    def _emit(self, state: str, **payload: Any) -> None:
        self.schedule(lambda: self.on_state(state, payload))


class UpdateDialog(StudioDialog):
    """Phoenix update check, verified download, and installer launch dialog."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        exit_app: Callable[[], None],
        service: ApplicationUpdateService | None = None,
    ) -> None:
        super().__init__(
            master,
            title=tr("update_dialog_title", "HK NPU STUDIO Update"),
            size=(640, 540),
            min_size=(560, 460),
            resizable=True,
        )
        configure_phoenix_styles(self)
        self._manifest: ApplicationUpdateManifest | None = None
        self._running = False
        self._events: Queue[Callable[[], None]] = Queue()
        self._poll_after: str | None = None
        self._build_ui()
        self.workflow = ApplicationUpdateWorkflow(
            service or ApplicationUpdateService(),
            on_state=self._on_state,
            exit_app=exit_app,
            schedule=self._events.put,
        )
        self.center(master)
        self._poll_after = self.after(50, self._poll_events)
        self.after(0, self.workflow.check_async)

    def _build_ui(self) -> None:
        self.add_title(tr("update_dialog_title", "HK NPU STUDIO Update"))
        card = self.add_card()
        content = tk.Frame(card, bg=PHOENIX_THEME.elevated_bg)
        content.pack(
            fill="both",
            expand=True,
            padx=PHOENIX_THEME.card_pad_x,
            pady=PHOENIX_THEME.card_pad_y,
        )
        self.status_label = tk.Label(
            content,
            text=tr("update_checking", "Suche nach Updates..."),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self.status_label.pack(fill="x")
        self.details_label = tk.Label(
            content,
            text="",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self.details_label.pack(fill="x", pady=(PHOENIX_THEME.space_md, 0))
        self.progress = ttk.Progressbar(
            content,
            mode="determinate",
            maximum=100,
            style="Phoenix.Horizontal.TProgressbar",
        )
        self.progress_label = tk.Label(
            content,
            text="",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        self.notes_label = tk.Label(
            content,
            text="",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="nw",
            justify="left",
            wraplength=520,
        )
        self.notes_label.pack(fill="both", expand=True, pady=(PHOENIX_THEME.space_md, 0))

        self.cancel_button = PhoenixButton(
            self.footer,
            text=tr("cancel", "Abbrechen"),
            command=self._cancel,
            button_type="neutral",
            width=130,
        )
        self.cancel_button.pack(side="right")
        self.install_button = PhoenixButton(
            self.footer,
            text=tr("update_download_install", "Download & Installieren"),
            command=self._install,
            button_type="primary",
            width=220,
            state="disabled",
        )
        self.install_button.pack(side="right", padx=(0, PHOENIX_THEME.space_sm))

    def _on_state(self, state: str, payload: dict[str, Any]) -> None:
        message = str(payload.get("message", ""))
        if state == "CHECKING":
            self._hide_progress()
            self.status_label.configure(text=tr("update_checking", "Suche nach Updates..."))
            self.details_label.configure(text="")
            self.notes_label.configure(text="")
            self.install_button.configure(state="disabled")
            self.cancel_button.configure(text=tr("cancel", "Abbrechen"))
        elif state == "UP_TO_DATE":
            self._running = False
            self._hide_progress()
            self.status_label.configure(
                text=tr("update_up_to_date", "HK NPU STUDIO ist auf dem neuesten Stand.")
            )
            self.details_label.configure(text="")
            self.notes_label.configure(text="")
            self.install_button.configure(state="disabled")
            self.cancel_button.configure(text=tr("close", "Schließen"))
        elif state == "AVAILABLE":
            self._running = False
            self._hide_progress()
            self._manifest = payload["manifest"]
            manifest = self._manifest
            self.status_label.configure(text=tr("update_available", "Update verfügbar"))
            self.details_label.configure(
                text="\n".join(
                    (
                        f"{tr('update_current_version', 'Aktuelle Version')}: {RELEASE.package_version}",
                        f"{tr('update_new_version', 'Neue Version')}: {manifest.version}",
                        manifest.release_name,
                        f"{tr('update_download_size', 'Downloadgröße')}: {self._format_bytes(manifest.asset_size)}",
                    )
                )
            )
            self.notes_label.configure(text=manifest.release_notes[:1200])
            self.install_button.configure(state="normal")
            self.cancel_button.configure(text=tr("cancel", "Abbrechen"))
        elif state in ("DOWNLOADING", "VERIFYING"):
            self._running = True
            self._show_progress()
            if state == "VERIFYING":
                label = tr("update_verifying", "Update wird überprüft...")
            else:
                label = tr("update_downloading", "Update wird heruntergeladen...")
            self.status_label.configure(text=label)
            downloaded = int(payload.get("downloaded") or 0)
            total = int(payload.get("total") or 0)
            percent = float(payload.get("percent") or 0.0)
            self.progress.configure(value=percent)
            self.progress_label.configure(
                text=f"{self._format_bytes(downloaded)} / {self._format_bytes(total)} ({percent:.0f}%)"
            )
            self.install_button.configure(state="disabled")
            self.cancel_button.configure(text=tr("cancel", "Abbrechen"))
        elif state == "INSTALLER_STARTED":
            self.status_label.configure(
                text=tr("update_installer_starting", "Installer wird gestartet...")
            )
        elif state == "ERROR":
            self._running = False
            self._hide_progress()
            self.status_label.configure(
                text=self._localized_error(message, payload.get("error_code"))
            )
            self.install_button.configure(state="disabled")
            self.cancel_button.configure(text=tr("close", "Schließen"))

    def _show_progress(self) -> None:
        if not self.progress.winfo_manager():
            self.progress.pack(
                fill="x",
                pady=(PHOENIX_THEME.space_lg, 0),
                before=self.notes_label,
            )
        if not self.progress_label.winfo_manager():
            self.progress_label.pack(
                fill="x",
                pady=(PHOENIX_THEME.space_xs, 0),
                before=self.notes_label,
            )

    def _hide_progress(self) -> None:
        self.progress.pack_forget()
        self.progress_label.pack_forget()
        self.progress.configure(value=0)
        self.progress_label.configure(text="")

    def _install(self) -> None:
        if self._manifest is None or self._running:
            return
        self.workflow.install_async(self._manifest)

    def _cancel(self) -> None:
        if self._running:
            self.workflow.cancel()
        else:
            self.close()

    def _poll_events(self) -> None:
        try:
            while True:
                self._events.get_nowait()()
        except Empty:
            pass
        try:
            if self.winfo_exists():
                self._poll_after = self.after(50, self._poll_events)
        except tk.TclError:
            self._poll_after = None

    def close(self) -> None:
        if self._running:
            self.workflow.cancel()
        if self._poll_after is not None:
            try:
                self.after_cancel(self._poll_after)
            except tk.TclError:
                pass
            self._poll_after = None
        super().close()

    @staticmethod
    def _format_bytes(value: int) -> str:
        if value <= 0:
            return "—"
        amount = float(value)
        for unit in ("B", "KB", "MB", "GB"):
            if amount < 1024.0 or unit == "GB":
                return f"{amount:.1f} {unit}"
            amount /= 1024.0
        return f"{amount:.1f} GB"

    @staticmethod
    def _localized_error(message: str, error_code: object) -> str:
        localized = {
            "network": tr("update_github_failed", "Verbindung zu GitHub fehlgeschlagen."),
            "rate_limit": tr("update_rate_limit", "GitHub API-Limit erreicht."),
            "invalid_response": tr("update_invalid_response", "GitHub-Antwort ist ungültig."),
            "installer_missing": tr("update_installer_missing", "Kein passender ARM64-Installer gefunden."),
            "digest_missing": tr("update_digest_missing", "Der Installer besitzt keinen gültigen SHA-256-Digest."),
            "invalid_file": tr("update_integrity_failed", "Integritätsprüfung fehlgeschlagen."),
            "integrity": tr("update_integrity_failed", "Integritätsprüfung fehlgeschlagen."),
            "installer_launch": tr("update_installer_failed", "Installer konnte nicht gestartet werden."),
        }
        return localized.get(str(error_code or ""), message)
