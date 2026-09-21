"""
HK NPU STUDIO - Phoenix Architecture
AI Photo Restore View

Minimal, commercial-grade workspace view for AI Photo Restore.
Provides input photo selection, upscale factor choice (2x/4x),
auto-colorization toggle, real-time progress feedback, and result preview.
Fully localized via app.i18n.tr.
"""

from __future__ import annotations

import logging
import os
import queue
import subprocess
import time
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

import config
from app.i18n import tr
from controllers.photo_restore_controller import PhotoRestoreController
from engine.backends.photo_restore_backend import PhotoRestoreResult
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.controls.card import PhoenixCard
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME, configure_phoenix_styles

logger = logging.getLogger(__name__)


class PhoenixPhotoRestoreView(WorkspaceFrame):
    """AI Photo Restore Workspace: FiDeSR Strong + DDColor on Snapdragon NPU."""

    def __init__(
        self,
        master: tk.Misc,
        controller: PhotoRestoreController | None = None,
    ) -> None:
        super().__init__(
            master,
            title=tr("photo_restore_title", "AI Photo Restore"),
            subtitle=tr("photo_restore_subtitle", "Historische & Schwarzweiss-Fotos restaurieren, kolorieren und hochskalieren"),
            has_inspector=True,
        )
        self._ui_dispatch_queue: queue.Queue[Callable[[], None]] = queue.Queue()
        self._ui_dispatch_closed: bool = False
        self._ui_pump_id: str | None = None
        self._pump_interval_ms: int = 25

        self.controller = controller or PhotoRestoreController(
            ui_dispatch=self.ui_dispatch
        )

        self.input_path: Path | None = None
        self.result_path: Path | None = None
        self._preview_photo: ImageTk.PhotoImage | None = None
        self._result_photo: ImageTk.PhotoImage | None = None

        self._build_toolbar()
        self._build_content_area()
        self._build_inspector()
        self._build_status()
        self._schedule_ui_pump()
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self.header.toolbar_slot, bg=PHOENIX_THEME.content_bg)
        toolbar.grid(row=0, column=0, sticky="ew")

        self.load_button = PhoenixButton(
            toolbar,
            text=tr("photo_restore_load_photo", "Foto laden"),
            command=self._load_image,
            button_type="neutral",
            icon_name="load_image",
            icon_color=PHOENIX_THEME.warning,
            font=PHOENIX_THEME.font_small,
            height=32,
            radius=6,
        )
        self.load_button.pack(side="left", padx=(0, 8))

        self.clear_button = PhoenixButton(
            toolbar,
            text=tr("photo_restore_clear_photo", "Foto entfernen"),
            command=self._clear_image,
            button_type="neutral",
            icon_name="remove_image",
            font=PHOENIX_THEME.font_small,
            height=32,
            radius=6,
        )
        self.clear_button.pack(side="left", padx=(0, 8))

    def _build_content_area(self) -> None:
        self.content_slot.grid_rowconfigure(0, weight=1)
        self.content_slot.grid_columnconfigure(0, weight=1)
        self.content_slot.grid_columnconfigure(1, weight=1)

        # Left: Original Image Canvas/Card
        self.left_card = PhoenixCard(self.content_slot)
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=8)
        self.left_title = tk.Label(
            self.left_card,
            text=tr("photo_restore_card_original", "Original"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        self.left_title.pack(fill="x", padx=12, pady=(8, 0))
        self.left_canvas = tk.Canvas(
            self.left_card,
            bg=PHOENIX_THEME.card_bg,
            highlightthickness=0,
        )
        self.left_canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.left_placeholder = self.left_canvas.create_text(
            150, 150,
            text=tr("photo_restore_no_photo", "Kein Foto geladen\n\nKlicken Sie auf 'Foto laden'"),
            fill=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            justify="center",
        )
        self.left_canvas.bind("<Configure>", self._on_canvas_resize)

        # Right: Restored Result Canvas/Card
        self.right_card = PhoenixCard(self.content_slot)
        self.right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=8)
        self.right_title = tk.Label(
            self.right_card,
            text=tr("photo_restore_card_result", "Restauriert & Hochskaliert"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        self.right_title.pack(fill="x", padx=12, pady=(8, 0))
        self.right_canvas = tk.Canvas(
            self.right_card,
            bg=PHOENIX_THEME.card_bg,
            highlightthickness=0,
        )
        self.right_canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.right_placeholder = self.right_canvas.create_text(
            150, 150,
            text=tr("photo_restore_result_placeholder", "Ergebnis erscheint hier\n\nnach der NPU-Restaurierung"),
            fill=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            justify="center",
        )
        self.right_canvas.bind("<Configure>", self._on_canvas_resize)

    def _build_inspector(self) -> None:
        host = self.inspector_slot
        host.grid_rowconfigure(0, weight=1)
        host.grid_columnconfigure(0, weight=1)

        panel = tk.Frame(host, bg=PHOENIX_THEME.card_bg, width=320)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_propagate(False)

        pad_x = PHOENIX_THEME.space_md

        # Title
        tk.Label(
            panel,
            text=tr("photo_restore_options", "Optionen"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).pack(fill="x", padx=pad_x, pady=(16, 8))

        # Restoration Mode selection
        tk.Label(
            panel,
            text=tr("photo_restore_mode", "Restaurierungsmodus"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).pack(fill="x", padx=pad_x, pady=(8, 4))

        self.mode_var = tk.StringVar(value="faithful")
        mode_frame = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        mode_frame.pack(fill="x", padx=pad_x, pady=(0, 8))

        self.rb_faithful = tk.Radiobutton(
            mode_frame,
            text=tr("photo_restore_mode_faithful", "Faithful Restoration"),
            variable=self.mode_var,
            value="faithful",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.panel_bg,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
        )
        self.rb_faithful.pack(anchor="w", pady=(0, 2))

        # Enhanced Restoration mode is retained in backend/controller but hidden/deactivated in visible product UI
        self.rb_enhanced = tk.Radiobutton(
            mode_frame,
            text=tr("photo_restore_mode_enhanced", "Enhanced Restoration"),
            variable=self.mode_var,
            value="enhanced",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.panel_bg,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            state="disabled",
        )
        # self.rb_enhanced is intentionally NOT packed to keep it hidden from visible product UI

        # Upscale factor selection
        tk.Label(
            panel,
            text=tr("photo_restore_resolution", "Auflösung / Hochskalierung"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).pack(fill="x", padx=pad_x, pady=(8, 4))

        self.upscale_var = tk.IntVar(value=4)
        radio_frame = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        radio_frame.pack(fill="x", padx=pad_x, pady=(0, 8))

        self.rb_2x = tk.Radiobutton(
            radio_frame,
            text=tr("photo_restore_2x", "2x (Standard)"),
            variable=self.upscale_var,
            value=2,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.panel_bg,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
        )
        self.rb_2x.pack(side="left", padx=(0, 16))

        self.rb_4x = tk.Radiobutton(
            radio_frame,
            text=tr("photo_restore_4x", "4x (Ultra-HD)"),
            variable=self.upscale_var,
            value=4,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.panel_bg,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
        )
        self.rb_4x.pack(side="left")

        # Auto-Colorize option
        self.colorize_var = tk.BooleanVar(value=True)
        self.cb_colorize = tk.Checkbutton(
            panel,
            text=tr("photo_restore_auto_color", "Farbrekonstruktion (DDColor bei SW-Fotos)"),
            variable=self.colorize_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.panel_bg,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        )
        self.cb_colorize.pack(fill="x", padx=pad_x, pady=(8, 16))

        # Action Buttons
        self.start_button = PhoenixButton(
            panel,
            text=tr("photo_restore_start", "Restaurieren starten"),
            command=self._start_restore,
            button_type="primary",
            icon_name="sparkles",
            font=PHOENIX_THEME.font_button,
            height=40,
            radius=8,
        )
        self.start_button.pack(fill="x", padx=pad_x, pady=(8, 8))

        self.cancel_button = PhoenixButton(
            panel,
            text=tr("cancel", "Abbrechen"),
            command=self._cancel_restore,
            button_type="neutral",
            icon_name="close",
            font=PHOENIX_THEME.font_button,
            height=36,
            radius=8,
        )
        self.cancel_button.pack(fill="x", padx=pad_x, pady=(0, 16))

        # Open Output Folder Button
        self.open_folder_button = PhoenixButton(
            panel,
            text=tr("photo_restore_open_folder", "Im Ordner anzeigen"),
            command=self._open_output_folder,
            button_type="neutral",
            icon_name="folder",
            font=PHOENIX_THEME.font_small,
            height=32,
            radius=6,
        )
        self.open_folder_button.pack(fill="x", padx=pad_x, pady=(8, 16))

        # Image Information Labels
        info_frame = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        info_frame.pack(fill="x", padx=pad_x, pady=(8, 8))

        self.info_size_label = tk.Label(
            info_frame,
            text=tr("photo_restore_info_in", "Eingabe: -"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        self.info_size_label.pack(fill="x", pady=2)

        self.info_out_label = tk.Label(
            info_frame,
            text=tr("photo_restore_info_out", "Ausgabe: -"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        self.info_out_label.pack(fill="x", pady=2)

    def _ensure_progress_style(self) -> None:
        configure_phoenix_styles(self)
        try:
            style = ttk.Style(self)
            style.configure(
                "Phoenix.Horizontal.TProgressbar",
                troughcolor=PHOENIX_THEME.elevated_bg,
                background=PHOENIX_THEME.success,
                lightcolor=PHOENIX_THEME.success,
                darkcolor=PHOENIX_THEME.success,
                bordercolor=PHOENIX_THEME.border,
            )
        except Exception:
            pass

    def _build_status(self) -> None:
        status_frame = self.status_slot
        status_frame.grid_columnconfigure(1, weight=1)

        self._ensure_progress_style()

        self.status_label = tk.Label(
            status_frame,
            text=tr("photo_restore_ready", "Bereit"),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=(16, 8), pady=8)

        self.progress_bar = ttk.Progressbar(
            status_frame,
            style="Phoenix.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100,
        )
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=8, pady=8)

        self.progress_percent_label = tk.Label(
            status_frame,
            text="",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        self.progress_percent_label.grid(row=0, column=2, sticky="w", padx=(2, 8), pady=8)

        self.progress_detail_label = tk.Label(
            status_frame,
            text="",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="e",
        )
        self.progress_detail_label.grid(row=0, column=3, sticky="e", padx=(8, 16), pady=8)

    def _load_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title=tr("photo_restore_dialog_title", "Foto zur Restaurierung auswählen"),
            filetypes=[
                (tr("filetype_images", "Bilddateien"), "*.jpg *.jpeg *.png *.webp *.bmp *.tiff"),
                (tr("filetype_all", "Alle Dateien"), "*.*"),
            ],
        )
        if not file_path:
            return

        self.input_path = Path(file_path)
        self.result_path = None
        self._update_input_preview()
        loaded_text = tr("photo_restore_loaded", "Geladen: ") + self.input_path.name
        self.status_label.configure(text=loaded_text)
        self.progress_bar["value"] = 0
        self.progress_detail_label.configure(text="")

    def _clear_image(self) -> None:
        self.input_path = None
        self.result_path = None
        self._preview_photo = None
        self._result_photo = None
        self.left_canvas.delete("all")
        self.right_canvas.delete("all")
        self.left_placeholder = self.left_canvas.create_text(
            150, 150,
            text=tr("photo_restore_no_photo", "Kein Foto geladen\n\nKlicken Sie auf 'Foto laden'"),
            fill=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            justify="center",
        )
        self.right_placeholder = self.right_canvas.create_text(
            150, 150,
            text=tr("photo_restore_result_placeholder", "Ergebnis erscheint hier\n\nnach der NPU-Restaurierung"),
            fill=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            justify="center",
        )
        self.info_size_label.configure(text=tr("photo_restore_info_in", "Eingabe: -"))
        self.info_out_label.configure(text=tr("photo_restore_info_out", "Ausgabe: -"))
        self.status_label.configure(text=tr("photo_restore_ready", "Bereit"))
        self.progress_bar["value"] = 0
        self.progress_percent_label.configure(text="")
        self.progress_detail_label.configure(text="")

    def _on_canvas_resize(self, _event: tk.Event) -> None:
        self._update_input_preview()
        self._update_result_preview()

    def _update_input_preview(self) -> None:
        if not self.input_path or not self.input_path.is_file():
            return
        cw = max(10, self.left_canvas.winfo_width())
        ch = max(10, self.left_canvas.winfo_height())
        try:
            pil_img = Image.open(self.input_path)
            w, h = pil_img.size
            in_label_text = f"{tr('photo_restore_in_prefix', 'Eingabe:')} {w}x{h} px ({self.input_path.name})"
            self.info_size_label.configure(text=in_label_text)

            ratio = min((cw - 16) / w, (ch - 16) / h)
            nw, nh = max(1, int(w * ratio)), max(1, int(h * ratio))
            resized = pil_img.resize((nw, nh), Image.Resampling.BILINEAR)
            self._preview_photo = ImageTk.PhotoImage(resized)

            self.left_canvas.delete("all")
            self.left_canvas.create_image(
                cw // 2, ch // 2,
                image=self._preview_photo,
                anchor="center",
            )
        except Exception:
            pass

    def _update_result_preview(self) -> None:
        if not self.result_path or not self.result_path.is_file():
            return
        cw = max(10, self.right_canvas.winfo_width())
        ch = max(10, self.right_canvas.winfo_height())
        try:
            pil_img = Image.open(self.result_path)
            w, h = pil_img.size
            out_label_text = f"{tr('photo_restore_out_prefix', 'Ausgabe:')} {w}x{h} px"
            self.info_out_label.configure(text=out_label_text)

            ratio = min((cw - 16) / w, (ch - 16) / h)
            nw, nh = max(1, int(w * ratio)), max(1, int(h * ratio))
            resized = pil_img.resize((nw, nh), Image.Resampling.BILINEAR)
            self._result_photo = ImageTk.PhotoImage(resized)

            self.right_canvas.delete("all")
            self.right_canvas.create_image(
                cw // 2, ch // 2,
                image=self._result_photo,
                anchor="center",
            )
        except Exception:
            pass

    def _start_restore(self) -> None:
        if not self.input_path:
            messagebox.showwarning(
                tr("dialog_title_no_image", "Kein Bild"),
                tr("dialog_msg_select_image_first", "Bitte wählen Sie zuerst ein Bild aus."),
            )
            return

        if self.controller.running:
            return

        upscale = self.upscale_var.get()
        auto_color = self.colorize_var.get()
        mode = self.mode_var.get()
        if mode != "faithful":
            mode = "faithful"
            self.mode_var.set("faithful")

        self._ensure_progress_style()
        self.status_label.configure(text=tr("photo_restore_starting", "Restaurierung wird gestartet..."))
        self.progress_bar["value"] = 2
        self.progress_percent_label.configure(text="2 %")
        self.progress_detail_label.configure(text=tr("photo_restore_init_detail", "Initialisierung..."))

        def on_progress(phase: str, pct: float, detail: str | None) -> None:
            val_pct = int(round(pct * 100))
            self.progress_bar["value"] = val_pct
            self.progress_percent_label.configure(text=f"{val_pct} %")
            phase_display = f"{tr('photo_restore_phase', 'Phase:')} {phase.capitalize()}"
            self.status_label.configure(text=phase_display)
            self.progress_detail_label.configure(text=detail or "")

        def on_complete(result: PhotoRestoreResult) -> None:
            if result.success and result.output_path:
                self.result_path = Path(result.output_path)
                self._update_result_preview()
                done_text = f"{tr('photo_restore_done', 'Fertiggestellt')} ({result.generation_time:.1f}s)"
                self.status_label.configure(text=done_text)
                self.progress_bar["value"] = 100
                self.progress_percent_label.configure(text="100 %")
                self.progress_detail_label.configure(text=tr("photo_restore_saved_success", "Erfolgreich gespeichert"))
            elif result.error_code == "PHOTO_RESTORE_CANCELLED":
                self.status_label.configure(text=tr("photo_restore_cancelled", "Restaurierung abgebrochen"))
                self.progress_percent_label.configure(text="")
                self.progress_detail_label.configure(text=tr("photo_restore_cancelled_by_user", "Abgebrochen durch Benutzer"))
            else:
                self.status_label.configure(text=tr("photo_restore_error_status", "Fehler bei der Restaurierung"))
                self.progress_percent_label.configure(text="")
                self.progress_detail_label.configure(text=result.error_code or "Fehler")
                messagebox.showerror(
                    tr("photo_restore_error_title", "Restaurierungsfehler"),
                    f"Fehler ({result.error_code}):\n{result.error_message}",
                )

        self.controller.start(
            image_path=self.input_path,
            output_dir=config.OUTPUT_DIR,
            upscale_factor=upscale,
            auto_colorize=auto_color,
            mode=mode,
            on_progress=on_progress,
            on_complete=on_complete,
            asynchronous=True,
        )

    def _cancel_restore(self) -> None:
        if self.controller.running:
            self.status_label.configure(text=tr("photo_restore_cancelling", "Abbruch angefordert..."))
            self.controller.cancel()

    def _open_output_folder(self) -> None:
        out_dir = config.OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(out_dir))
        else:
            subprocess.run(["explorer", str(out_dir)], check=False)

    def ui_dispatch(self, callback: Callable[[], None]) -> None:
        """
        Thread-safe dispatch of a callback to the Tkinter UI main thread.
        May be called from any thread. Never calls self.after() directly.
        """
        if self._ui_dispatch_closed:
            return
        self._ui_dispatch_queue.put(callback)

    def _schedule_ui_pump(self) -> None:
        """Schedules the next queue drain in the Tk main thread."""
        if self._ui_dispatch_closed:
            return
        try:
            self._ui_pump_id = self.after(self._pump_interval_ms, self._drain_ui_dispatch_queue)
        except Exception:
            self._ui_pump_id = None

    def _drain_ui_dispatch_queue(self) -> None:
        """Drains pending callbacks from the queue exclusively in the Tk main thread."""
        self._ui_pump_id = None
        if self._ui_dispatch_closed:
            return

        while not self._ui_dispatch_queue.empty():
            try:
                callback = self._ui_dispatch_queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback()
            except Exception as exc:
                logger.exception("Error executing UI dispatch callback: %s", exc)

        if not self._ui_dispatch_closed:
            self._schedule_ui_pump()

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget == self:
            self._close_ui_dispatch()

    def _close_ui_dispatch(self) -> None:
        """Stops the queue pump and rejects future dispatches."""
        self._ui_dispatch_closed = True
        if self._ui_pump_id is not None:
            try:
                self.after_cancel(self._ui_pump_id)
            except Exception:
                pass
            self._ui_pump_id = None
        while not self._ui_dispatch_queue.empty():
            try:
                self._ui_dispatch_queue.get_nowait()
            except queue.Empty:
                break

    def destroy(self) -> None:
        """Stops the queue pump and cleanly tears down the view."""
        self._close_ui_dispatch()
        super().destroy()

    @property
    def faithful_visible(self) -> bool:
        """Returns True if Faithful mode is visible in the UI."""
        return bool(self.rb_faithful.winfo_manager())

    @property
    def enhanced_visible(self) -> bool:
        """Returns True if Enhanced mode is visible in the UI."""
        return bool(self.rb_enhanced.winfo_manager())