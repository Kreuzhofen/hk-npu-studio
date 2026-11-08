from __future__ import annotations

import os
import queue
import random
import shutil
import subprocess
import time
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from app.i18n import tr
from config import OUTPUT_DIR, TEMP_DIR
from controllers.image_to_image_controller import ImageToImageController
from engine.backends.sd15_qnn_inpainting_adapter import SD15QnnInpaintingResult
from engine.theme_manager import ThemeManager
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.controls.card import PhoenixCard
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME, configure_phoenix_styles


class PhoenixImageToImageView(WorkspaceFrame):
    """Phoenix Image Lab: SD 1.5 Image-to-Image on Qualcomm Hexagon HTP."""

    def __init__(
        self,
        master: tk.Misc,
        controller: ImageToImageController | None = None,
        on_navigate: Callable[[str], None] | None = None,
        output_dir: Path | str | None = None,
        temp_dir: Path | str | None = None,
    ) -> None:
        super().__init__(
            master,
            title=tr("image_to_image_title", "Bild-zu-Bild (Image-to-Image)"),
            subtitle=tr(
                "image_to_image_subtitle",
                "Stil- und Motivtransformation mit Stable Diffusion 1.5 auf Qualcomm Hexagon NPU",
            ),
            has_inspector=True,
        )
        self._ui_dispatch_queue: queue.Queue[Callable[[], None]] = queue.Queue()
        self._ui_dispatch_closed: bool = False
        self._ui_pump_id: str | None = None
        self._pump_interval_ms: int = 25

        self.controller = controller or ImageToImageController(ui_dispatch=self.ui_dispatch)
        self.controller.ui_dispatch = self.ui_dispatch
        self.on_navigate = on_navigate
        self.output_dir: Path = Path(output_dir) if output_dir is not None else OUTPUT_DIR
        self.temp_dir: Path = Path(temp_dir) if temp_dir is not None else (TEMP_DIR / "image_to_image")
        self.input_path: Path | None = None
        self.result_path: Path | None = None
        self._preview_photo: ImageTk.PhotoImage | None = None
        self._result_photo: ImageTk.PhotoImage | None = None
        self.custom_ref_path: Path | None = None

        self._build_toolbar()
        self._build_content_area()
        self._build_inspector()
        self._build_status()
        self._setup_drag_and_drop()
        self._schedule_ui_pump()
        self.bind("<Destroy>", self._on_destroy, add="+")

    def ui_dispatch(self, callback: Callable[[], None]) -> None:
        if self._ui_dispatch_closed:
            return
        self._ui_dispatch_queue.put(callback)

    def _schedule_ui_pump(self) -> None:
        if self._ui_dispatch_closed:
            return
        self._ui_pump_id = self.after(self._pump_interval_ms, self._drain_ui_dispatch)

    def _drain_ui_dispatch(self) -> None:
        if self._ui_dispatch_closed:
            return
        start_time = time.monotonic()
        while not self._ui_dispatch_queue.empty():
            try:
                callback = self._ui_dispatch_queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback()
            except Exception:
                pass
            if time.monotonic() - start_time > 0.05:
                break
        self._schedule_ui_pump()

    def _on_destroy(self, _event: tk.Event) -> None:
        self._ui_dispatch_closed = True
        if self._ui_pump_id is not None:
            try:
                self.after_cancel(self._ui_pump_id)
            except Exception:
                pass
            self._ui_pump_id = None

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self.header.toolbar_slot, bg=PHOENIX_THEME.content_bg)
        toolbar.grid(row=0, column=0, sticky="ew")

        self.overview_button = PhoenixButton(
            toolbar,
            text=tr("nav_overview", "Übersicht"),
            command=self._on_back_to_overview,
            button_type="neutral",
            icon_name="back",
            font=PHOENIX_THEME.font_small,
            height=32,
            radius=6,
        )
        self.overview_button.pack(side="left", padx=(0, 8))

        self.load_button = PhoenixButton(
            toolbar,
            text=tr("load_image", "Bild laden"),
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
            text=tr("inpainting_remove_image", "Bild entfernen"),
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

        # Left: Original Image Card
        self.left_card = PhoenixCard(self.content_slot)
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=8)
        self.left_title = tk.Label(
            self.left_card,
            text=tr("original_image_label", "Originalbild"),
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
            text=tr("img2img_no_photo", "Kein Bild geladen\n\nKlicken Sie auf 'Bild laden' oder\nziehen Sie ein Bild hierher"),
            fill=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            justify="center",
        )
        self.left_canvas.bind("<Configure>", self._on_canvas_resize)

        # Right: Result Image Card
        self.right_card = PhoenixCard(self.content_slot)
        self.right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=8)
        self.right_title = tk.Label(
            self.right_card,
            text=tr("img2img_card_result", "Transformiertes Ergebnis"),
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
            text=tr("img2img_result_placeholder", "Transformiertes Bild erscheint hier\n\nnach der NPU-Generierung"),
            fill=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            justify="center",
        )
        self.right_canvas.bind("<Configure>", self._on_canvas_resize)

    def _build_inspector(self) -> None:
        host = self.inspector_slot
        host.grid_rowconfigure(0, weight=1)
        host.grid_columnconfigure(0, weight=1)

        scroll = tk.Canvas(host, width=320, bg=PHOENIX_THEME.card_bg, highlightthickness=0)
        bar = ttk.Scrollbar(host, orient="vertical", command=scroll.yview, style="Phoenix.Vertical.TScrollbar")
        scroll.grid(row=0, column=0, sticky="nsew")
        bar.grid(row=0, column=1, sticky="ns")
        scroll.configure(yscrollcommand=bar.set)

        panel = tk.Frame(scroll, bg=PHOENIX_THEME.card_bg)
        window = scroll.create_window((0, 0), window=panel, anchor="nw")
        panel.bind("<Configure>", lambda _event: scroll.configure(scrollregion=scroll.bbox("all")))
        scroll.bind("<Configure>", lambda event: scroll.itemconfigure(window, width=event.width))

        pad_x = 16

        # Model Badge
        self.model_badge = tk.Label(
            panel,
            text="SD 1.5 NPU • Image-to-Image",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        )
        self.model_badge.pack(fill="x", padx=pad_x, pady=(16, 4))

        # Prompt
        tk.Label(
            panel, text=tr("prompt_label", "Prompt"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w",
        ).pack(fill="x", padx=pad_x, pady=(8, 4))
        self.prompt = tk.Text(
            panel, height=5, wrap="word", bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary, insertbackground=PHOENIX_THEME.text_primary,
            relief="flat", font=PHOENIX_THEME.font_body,
        )
        self.prompt.pack(fill="x", padx=pad_x)

        # Negative Prompt
        tk.Label(
            panel, text=tr("inpainting_negative_prompt", "Negativer Prompt"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w",
        ).pack(fill="x", padx=pad_x, pady=(10, 4))
        self.negative_prompt = tk.Text(
            panel, height=3, wrap="word", bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary, insertbackground=PHOENIX_THEME.text_primary,
            relief="flat", font=PHOENIX_THEME.font_body,
        )
        self.negative_prompt.pack(fill="x", padx=pad_x)

        # Denoising Strength
        strength_header = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        strength_header.pack(fill="x", padx=pad_x, pady=(14, 2))
        tk.Label(
            strength_header, text=tr("inpainting_strength_label", "Stärke (Denoising)"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small,
        ).pack(side="left")
        self.strength_var = tk.DoubleVar(value=0.65)
        self.strength_spin = tk.Spinbox(
            strength_header, from_=0.10, to=1.00, increment=0.05, format="%.2f",
            textvariable=self.strength_var, width=5, bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary, buttonbackground=PHOENIX_THEME.card_bg,
            relief="flat", font=PHOENIX_THEME.font_small, command=self._on_strength_change,
        )
        self.strength_spin.pack(side="right")

        self.strength_scale = tk.Scale(
            panel, from_=0.10, to=1.00, resolution=0.05, orient="horizontal",
            variable=self.strength_var, command=lambda _v: self._on_strength_change(),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            showvalue=False,
        )
        self.strength_scale.pack(fill="x", padx=pad_x, pady=(0, 2))

        # Strength description hint
        self.strength_hint = tk.Label(
            panel,
            text="0.60–0.75: Ausgewogen ★ Sweet Spot (Balancierte Neukomposition)",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            wraplength=280,
            justify="left",
        )
        self.strength_hint.pack(fill="x", padx=pad_x, pady=(0, 8))

        # Steps
        steps_header = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        steps_header.pack(fill="x", padx=pad_x, pady=(8, 2))
        tk.Label(
            steps_header, text="Steps", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small,
        ).pack(side="left")
        self.steps = tk.IntVar(value=20)
        self.steps_spin = tk.Spinbox(
            steps_header, from_=10, to=50, textvariable=self.steps, width=5,
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            buttonbackground=PHOENIX_THEME.card_bg, relief="flat", font=PHOENIX_THEME.font_small,
        )
        self.steps_spin.pack(side="right")

        self.steps_scale = tk.Scale(
            panel, from_=10, to=50, orient="horizontal", variable=self.steps,
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            showvalue=False,
        )
        self.steps_scale.pack(fill="x", padx=pad_x, pady=(0, 8))

        # CFG Scale (Texttreue)
        cfg_header = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        cfg_header.pack(fill="x", padx=pad_x, pady=(8, 2))
        tk.Label(
            cfg_header, text=tr("inpainting_cfg_label", "Texttreue (CFG Scale)"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small,
        ).pack(side="left")
        self.cfg_var = tk.DoubleVar(value=7.5)
        self.cfg_spin = tk.Spinbox(
            cfg_header, from_=1.0, to=15.0, increment=0.5, format="%.1f",
            textvariable=self.cfg_var, width=5, bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary, buttonbackground=PHOENIX_THEME.card_bg,
            relief="flat", font=PHOENIX_THEME.font_small,
        )
        self.cfg_spin.pack(side="right")

        self.cfg_scale = tk.Scale(
            panel, from_=1.0, to=15.0, resolution=0.5, orient="horizontal",
            variable=self.cfg_var, bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            showvalue=False,
        )
        self.cfg_scale.pack(fill="x", padx=pad_x, pady=(0, 8))

        # Seed
        seed_header = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        seed_header.pack(fill="x", padx=pad_x, pady=(8, 2))
        tk.Label(
            seed_header, text="Seed", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small,
        ).pack(side="left")
        self.seed = tk.StringVar(value="42")
        seed_entry = tk.Entry(
            seed_header, textvariable=self.seed, bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary, relief="flat", font=PHOENIX_THEME.font_small, width=12,
        )
        seed_entry.pack(side="left", padx=(8, 4))
        self.rand_btn = PhoenixButton(
            seed_header, text="🎲", command=self._randomize_seed, button_type="neutral",
            font=PHOENIX_THEME.font_small, height=26, radius=4,
        )
        self.rand_btn.pack(side="left")

        # Presets
        tk.Label(
            panel, text=tr("inpainting_presets_title", "Presets"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w",
        ).pack(fill="x", padx=pad_x, pady=(12, 4))
        preset_frame = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        preset_frame.pack(fill="x", padx=pad_x, pady=(0, 8))
        preset_frame.grid_columnconfigure(0, weight=1)
        preset_frame.grid_columnconfigure(1, weight=1)

        self.btn_subtle = PhoenixButton(
            preset_frame, text=tr("img2img_preset_subtle", "Subtil (0.30)"),
            command=lambda: self._apply_preset(0.30, 20, 7.5),
            button_type="neutral", font=PHOENIX_THEME.font_caption, height=28, radius=4,
        )
        self.btn_subtle.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)

        self.btn_moderate = PhoenixButton(
            preset_frame, text=tr("img2img_preset_moderate", "Moderat (0.45)"),
            command=lambda: self._apply_preset(0.45, 20, 7.5),
            button_type="neutral", font=PHOENIX_THEME.font_caption, height=28, radius=4,
        )
        self.btn_moderate.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)

        self.btn_balanced = PhoenixButton(
            preset_frame, text=tr("img2img_preset_balanced", "Ausgewogen (0.65)"),
            command=lambda: self._apply_preset(0.65, 20, 7.5),
            button_type="secondary", font=PHOENIX_THEME.font_caption, height=28, radius=4,
        )
        self.btn_balanced.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=2)

        self.btn_creative = PhoenixButton(
            preset_frame, text=tr("img2img_preset_creative", "Kreativ (0.80)"),
            command=lambda: self._apply_preset(0.80, 20, 8.0),
            button_type="neutral", font=PHOENIX_THEME.font_caption, height=28, radius=4,
        )
        self.btn_creative.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=2)

        self.btn_regen = PhoenixButton(
            preset_frame, text=tr("img2img_preset_regen", "Neugenerierung (1.00)"),
            command=lambda: self._apply_preset(1.00, 20, 7.5),
            button_type="neutral", font=PHOENIX_THEME.font_caption, height=28, radius=4,
        )
        self.btn_regen.grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=2)

        self._preset_buttons = {
            0.30: self.btn_subtle,
            0.45: self.btn_moderate,
            0.65: self.btn_balanced,
            0.80: self.btn_creative,
            1.00: self.btn_regen,
        }
        self._update_preset_highlights()

        # Reference Image Control (Modus A: Canny QNN, Modus B: Latent Anchor)
        self.ref_card = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        self.ref_card.pack(fill="x", padx=pad_x, pady=(10, 4))

        ref_header = tk.Frame(self.ref_card, bg=PHOENIX_THEME.card_bg)
        ref_header.pack(fill="x", pady=(2, 2))

        self.ref_enabled_var = tk.BooleanVar(value=False)
        self.ref_check = tk.Checkbutton(
            ref_header,
            text=tr("img2img_ref_control_enable", "Referenzbindung aktivieren"),
            variable=self.ref_enabled_var,
            command=self._on_ref_toggle,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.elevated_bg,
            font=PHOENIX_THEME.font_small,
            relief="flat",
            highlightthickness=0,
        )
        self.ref_check.pack(side="left")

        # Container frame for reference options
        self.ref_options_frame = tk.Frame(self.ref_card, bg=PHOENIX_THEME.card_bg)

        # Mode Selection (Adaptive Reference Control: Modus A Canny QNN vs Modus B Latent Anchor)
        self.ref_mode_var = tk.StringVar(value="canny_qnn")
        try:
            self.ref_mode_var.trace_add("write", lambda *_: self._on_ref_mode_var_changed())
        except Exception:
            pass

        self.ref_mode_label = tk.Label(
            self.ref_options_frame,
            text=tr("img2img_ref_mode_title", "Steuerungsmodus:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        self.ref_mode_label.pack(fill="x", pady=(4, 2))

        mode_btn_grid = tk.Frame(self.ref_options_frame, bg=PHOENIX_THEME.card_bg)
        mode_btn_grid.pack(fill="x", pady=(0, 4))
        mode_btn_grid.grid_columnconfigure(0, weight=1)
        mode_btn_grid.grid_columnconfigure(1, weight=1)

        self.btn_mode_contour = PhoenixButton(
            mode_btn_grid,
            text=tr("img2img_ref_mode_contour_btn", "A · Konturtreue (Canny QNN)"),
            command=lambda: self.select_reference_mode("canny_qnn", apply_default_fidelity=True),
            button_type="secondary",
            font=PHOENIX_THEME.font_caption,
            height=28,
            radius=4,
        )
        self.btn_mode_contour.grid(row=0, column=0, sticky="ew", padx=(0, 2))

        self.btn_mode_structure = PhoenixButton(
            mode_btn_grid,
            text=tr("img2img_ref_mode_structure_btn", "B · Strukturtreue (Latent Anchor)"),
            command=lambda: self.select_reference_mode("latent_anchor", apply_default_fidelity=True),
            button_type="neutral",
            font=PHOENIX_THEME.font_caption,
            height=28,
            radius=4,
        )
        self.btn_mode_structure.grid(row=0, column=1, sticky="ew", padx=(2, 0))

        # Contextual recommendation and use cases box
        self.ref_mode_desc_frame = tk.Frame(
            self.ref_options_frame,
            bg=PHOENIX_THEME.elevated_bg,
            padx=8,
            pady=6,
        )
        self.ref_mode_desc_frame.pack(fill="x", pady=(2, 6))

        self.ref_mode_desc_title = tk.Label(
            self.ref_mode_desc_frame,
            text=tr("img2img_ref_mode_desc_contour_title", "Architektur · Logos · CAD · Gegenstände · Geometrie"),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left",
        )
        self.ref_mode_desc_title.pack(fill="x")

        self.ref_mode_desc_detail = tk.Label(
            self.ref_mode_desc_frame,
            text=tr("img2img_ref_mode_desc_contour_detail", "Standard-Fidelity: 0.75 | Qualcomm Hexagon ControlNet (13 Residuals)"),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left",
        )
        self.ref_mode_desc_detail.pack(fill="x", pady=(2, 0))

        # Backwards compatibility radio buttons (kept initialized for testing introspection)
        self._compat_radio_frame = tk.Frame(self.ref_options_frame, bg=PHOENIX_THEME.card_bg)
        self.rb_canny = tk.Radiobutton(
            self._compat_radio_frame,
            text=tr("img2img_ref_mode_contour", "Kontur (Canny QNN)"),
            variable=self.ref_mode_var,
            value="canny_qnn",
            command=lambda: self.select_reference_mode("canny_qnn", apply_default_fidelity=True),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.elevated_bg,
            font=PHOENIX_THEME.font_caption,
            relief="flat",
            highlightthickness=0,
        )
        self.rb_anchor = tk.Radiobutton(
            self._compat_radio_frame,
            text=tr("img2img_ref_mode_structure", "Struktur (Latent Anchor)"),
            variable=self.ref_mode_var,
            value="latent_anchor",
            command=lambda: self.select_reference_mode("latent_anchor", apply_default_fidelity=True),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.elevated_bg,
            font=PHOENIX_THEME.font_caption,
            relief="flat",
            highlightthickness=0,
        )
        self.rb_canny.pack(side="left")
        self.rb_anchor.pack(side="left")

        # Reference Fidelity (Binding strength)
        fidelity_header = tk.Frame(self.ref_options_frame, bg=PHOENIX_THEME.card_bg)
        fidelity_header.pack(fill="x", pady=(4, 2))
        self.ref_fidelity_label = tk.Label(
            fidelity_header,
            text=tr("img2img_ref_fidelity_label", "Bindungsstärke"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_small,
        )
        self.ref_fidelity_label.pack(side="left")

        self.btn_fidelity_default = PhoenixButton(
            fidelity_header,
            text=tr("img2img_ref_fidelity_default_btn", "Standard ({val})").replace("{val}", "0.75"),
            command=self._reset_to_default_fidelity,
            button_type="neutral",
            font=PHOENIX_THEME.font_caption,
            height=22,
            radius=4,
        )
        self.btn_fidelity_default.pack(side="right", padx=(4, 0))

        self.ref_fidelity_var = tk.DoubleVar(value=0.75)
        self.ref_fidelity_spin = tk.Spinbox(
            fidelity_header,
            from_=0.10,
            to=1.50,
            increment=0.05,
            format="%.2f",
            textvariable=self.ref_fidelity_var,
            width=5,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            buttonbackground=PHOENIX_THEME.card_bg,
            relief="flat",
            font=PHOENIX_THEME.font_small,
        )
        self.ref_fidelity_spin.pack(side="right")

        self.ref_fidelity_scale = tk.Scale(
            self.ref_options_frame,
            from_=0.10,
            to=1.50,
            resolution=0.05,
            orient="horizontal",
            variable=self.ref_fidelity_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            highlightthickness=0,
            font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent,
            troughcolor=PHOENIX_THEME.elevated_bg,
            showvalue=False,
        )
        self.ref_fidelity_scale.pack(fill="x", pady=(0, 4))

        # Reference Source selection
        src_header = tk.Frame(self.ref_options_frame, bg=PHOENIX_THEME.card_bg)
        src_header.pack(fill="x", pady=(4, 2))
        self.ref_source_var = tk.StringVar(value="same")
        self.rb_src_same = tk.Radiobutton(
            src_header,
            text=tr("img2img_ref_source_same", "Referenz: Eingabebild (Standard)"),
            variable=self.ref_source_var,
            value="same",
            command=self._on_ref_source_change,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.elevated_bg,
            font=PHOENIX_THEME.font_caption,
            relief="flat",
            highlightthickness=0,
        )
        self.rb_src_same.pack(anchor="w")

        self.rb_src_custom = tk.Radiobutton(
            src_header,
            text=tr("img2img_ref_source_custom", "Referenz: Eigenes Bild"),
            variable=self.ref_source_var,
            value="custom",
            command=self._on_ref_source_change,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.elevated_bg,
            font=PHOENIX_THEME.font_caption,
            relief="flat",
            highlightthickness=0,
        )
        self.rb_src_custom.pack(anchor="w", pady=(2, 0))

        # Custom Reference Image controls
        self.custom_ref_frame = tk.Frame(self.ref_options_frame, bg=PHOENIX_THEME.card_bg)

        custom_btn_row = tk.Frame(self.custom_ref_frame, bg=PHOENIX_THEME.card_bg)
        custom_btn_row.pack(fill="x", pady=(2, 2))

        self.btn_load_ref = PhoenixButton(
            custom_btn_row,
            text=tr("img2img_ref_load_btn", "Referenzbild wählen"),
            command=self._load_custom_reference_image,
            button_type="neutral",
            font=PHOENIX_THEME.font_caption,
            height=26,
            radius=4,
        )
        self.btn_load_ref.pack(side="left", padx=(0, 4))

        self.btn_reset_ref = PhoenixButton(
            custom_btn_row,
            text=tr("img2img_ref_reset_btn", "Zurücksetzen"),
            command=self._reset_custom_reference_image,
            button_type="neutral",
            font=PHOENIX_THEME.font_caption,
            height=26,
            radius=4,
        )
        self.btn_reset_ref.pack(side="left")

        self.ref_image_label = tk.Label(
            self.custom_ref_frame,
            text="(Kein separates Referenzbild)",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        self.ref_image_label.pack(fill="x", pady=(2, 4))

        # Action Buttons
        self.start_button = PhoenixButton(
            panel,
            text=tr("img2img_generate", "Generieren (HTP NPU)"),
            command=self._start_generation,
            button_type="primary",
            icon_name="sparkles",
            font=PHOENIX_THEME.font_button,
            height=40,
            radius=8,
        )
        self.start_button.pack(fill="x", padx=pad_x, pady=(12, 6))

        self.cancel_button = PhoenixButton(
            panel,
            text=tr("cancel", "Abbrechen"),
            command=self._cancel_generation,
            button_type="neutral",
            icon_name="close",
            font=PHOENIX_THEME.font_button,
            height=34,
            radius=6,
        )
        self.cancel_button.pack(fill="x", padx=pad_x, pady=(0, 6))

        self.save_button = PhoenixButton(
            panel,
            text=tr("img2img_save_gallery", "In Galerie speichern"),
            command=self._save_result,
            button_type="neutral",
            icon_name="save",
            font=PHOENIX_THEME.font_small,
            height=32,
            radius=6,
        )
        self.save_button.pack(fill="x", padx=pad_x, pady=(0, 6))

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
        self.open_folder_button.pack(fill="x", padx=pad_x, pady=(0, 16))

        # Information Labels
        info_frame = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        info_frame.pack(fill="x", padx=pad_x, pady=(0, 16))

        self.info_size_label = tk.Label(
            info_frame, text=tr("photo_restore_info_in", "Eingabe: -"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_caption, anchor="w",
        )
        self.info_size_label.pack(fill="x", pady=1)

        self.info_out_label = tk.Label(
            info_frame, text=tr("photo_restore_info_out", "Ausgabe: -"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_caption, anchor="w",
        )
        self.info_out_label.pack(fill="x", pady=1)

        self.timing_label = tk.Label(
            info_frame, text="NPU-Laufzeit: -",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_caption, anchor="w",
        )
        self.timing_label.pack(fill="x", pady=1)

    def _ensure_progress_style(self) -> None:
        configure_phoenix_styles(self)
        try:
            style = ttk.Style(self)
            style.configure(
                "Phoenix.Horizontal.TProgressbar",
                troughcolor=PHOENIX_THEME.elevated_bg,
                background=PHOENIX_THEME.accent,
                lightcolor=PHOENIX_THEME.accent,
                darkcolor=PHOENIX_THEME.accent,
                bordercolor=PHOENIX_THEME.border,
            )
        except Exception:
            pass

    def _build_status(self) -> None:
        status_frame = self.status_slot
        status_frame.grid_columnconfigure(1, weight=1)

        self.status_label = tk.Label(
            status_frame,
            text=tr("photo_restore_ready", "Bereit"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=(12, 8), pady=6)

        self._ensure_progress_style()
        self.progress_bar = ttk.Progressbar(
            status_frame,
            orient="horizontal",
            mode="determinate",
            style="Phoenix.Horizontal.TProgressbar",
        )
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        self.progress_percent_label = tk.Label(
            status_frame,
            text="",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_caption,
            width=6,
            anchor="e",
        )
        self.progress_percent_label.grid(row=0, column=2, sticky="e", padx=(4, 8), pady=6)

        self.progress_detail_label = tk.Label(
            status_frame,
            text="",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        self.progress_detail_label.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 4))

    def _setup_drag_and_drop(self) -> None:
        try:
            from widgets.phoenix.dnd_utils import register_dnd_target
            from tkinterdnd2 import DND_FILES
        except ImportError:
            return

        targets = [
            self,
            getattr(self, "left_canvas", None),
            getattr(self, "right_canvas", None),
            getattr(self, "left_card", None),
            getattr(self, "right_card", None),
        ]
        for target in targets:
            if target is not None:
                register_dnd_target(target, DND_FILES, self._on_file_drop, recursive=True)

    def _on_file_drop(self, event) -> None:
        from widgets.phoenix.dnd_utils import parse_dnd_paths
        raw_data = getattr(event, "data", "")
        paths = parse_dnd_paths(raw_data)
        if not paths:
            return
        self.load_dropped_image(paths[0])

    def load_dropped_image(self, file_path: str | Path) -> bool:
        path = Path(file_path)
        if not path.is_file():
            return False
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
        if path.suffix.lower() not in valid_extensions:
            messagebox.showerror(
                tr("dialog_title_unsupported", "Nicht unterstütztes Format"),
                tr("photo_restore_unsupported", "Die Datei hat kein unterstütztes Bildformat."),
            )
            return False

        self.input_path = path.resolve()
        self.result_path = None
        self._update_input_preview()
        self._clear_result_preview()
        self.status_label.configure(text=tr("photo_restore_loaded", "Geladen: ") + self.input_path.name)
        self.progress_bar["value"] = 0
        self.progress_detail_label.configure(text="")
        return True

    def _load_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title=tr("select_image", "Bild auswählen"),
            filetypes=[
                ("Bilddateien", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tiff"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if file_path:
            self.load_dropped_image(file_path)

    def _clear_image(self) -> None:
        self.input_path = None
        self.result_path = None
        self._preview_photo = None
        self._result_photo = None
        self.left_canvas.delete("all")
        self.right_canvas.delete("all")
        self.left_placeholder = self.left_canvas.create_text(
            150, 150,
            text=tr("img2img_no_photo", "Kein Bild geladen\n\nKlicken Sie auf 'Bild laden' oder\nziehen Sie ein Bild hierher"),
            fill=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            justify="center",
        )
        self.right_placeholder = self.right_canvas.create_text(
            150, 150,
            text=tr("img2img_result_placeholder", "Transformiertes Bild erscheint hier\n\nnach der NPU-Generierung"),
            fill=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            justify="center",
        )
        self.info_size_label.configure(text=tr("photo_restore_info_in", "Eingabe: -"))
        self.info_out_label.configure(text=tr("photo_restore_info_out", "Ausgabe: -"))
        self.timing_label.configure(text="NPU-Laufzeit: -")
        self.status_label.configure(text=tr("photo_restore_ready", "Bereit"))
        self.progress_bar["value"] = 0
        self.progress_percent_label.configure(text="")
        self.progress_detail_label.configure(text="")

    def _clear_result_preview(self) -> None:
        self.result_path = None
        self._result_photo = None
        self.right_canvas.delete("all")
        self.right_placeholder = self.right_canvas.create_text(
            150, 150,
            text=tr("img2img_result_placeholder", "Transformiertes Bild erscheint hier\n\nnach der NPU-Generierung"),
            fill=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            justify="center",
        )
        self.info_out_label.configure(text=tr("photo_restore_info_out", "Ausgabe: -"))
        self.timing_label.configure(text="NPU-Laufzeit: -")

    def _on_canvas_resize(self, _event: tk.Event) -> None:
        self._update_input_preview()
        self._update_result_preview()

    def _update_input_preview(self) -> None:
        if not self.input_path or not self.input_path.is_file():
            return
        cw = max(10, self.left_canvas.winfo_width())
        ch = max(10, self.left_canvas.winfo_height())
        try:
            with Image.open(self.input_path) as pil_img:
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
            with Image.open(self.result_path) as pil_img:
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

    def _update_preset_highlights(self) -> None:
        try:
            val = round(float(self.strength_var.get()), 2)
        except (ValueError, tk.TclError):
            return

        for preset_val, btn in getattr(self, "_preset_buttons", {}).items():
            if abs(val - preset_val) < 0.01:
                if getattr(btn, "button_type", None) != "secondary":
                    btn.configure(button_type="secondary")
            else:
                if getattr(btn, "button_type", None) != "neutral":
                    btn.configure(button_type="neutral")

    def _on_strength_change(self) -> None:
        try:
            val = round(float(self.strength_var.get()), 2)
        except (ValueError, tk.TclError):
            val = 0.65

        if val <= 0.35:
            hint = "0.10–0.35: Subtile Retusche & Detail-Finishing (Original dominiert)"
        elif val <= 0.55:
            hint = "0.40–0.55: Moderat – Material- & Stilwechsel (Strukturtreu)"
        elif val <= 0.75:
            hint = "0.60–0.75: Ausgewogen ★ Sweet Spot (Balancierte Neukomposition)"
        elif val <= 0.90:
            hint = "0.80–0.90: Kreativ – Freie Variation (Prompt dominiert)"
        else:
            hint = "0.95–1.00: Neugenerierung – Reines Text-to-Image Re-Sampling"

        self.strength_hint.configure(text=hint)
        self._update_preset_highlights()

    def _apply_preset(self, strength: float, steps: int = 20, cfg: float = 7.5) -> None:
        self.strength_var.set(strength)
        self.steps.set(steps)
        self.cfg_var.set(cfg)
        self._on_strength_change()

    def select_reference_mode(self, mode: str, apply_default_fidelity: bool = True) -> None:
        """Select reference control mode manually (canny_qnn or latent_anchor)."""
        if mode not in ("canny_qnn", "latent_anchor"):
            mode = "canny_qnn"
        self.ref_mode_var.set(mode)
        if apply_default_fidelity:
            default_fidelity = 0.75 if mode == "canny_qnn" else 0.65
            self.ref_fidelity_var.set(default_fidelity)
        self._update_ref_mode_ui()

    def _on_ref_mode_var_changed(self) -> None:
        """Synchronize UI when ref_mode_var is modified."""
        self._update_ref_mode_ui()

    def _reset_to_default_fidelity(self) -> None:
        """Reset fidelity slider/spinbox to default for the active mode."""
        mode = self.ref_mode_var.get()
        default_val = 0.65 if mode == "latent_anchor" else 0.75
        self.ref_fidelity_var.set(default_val)

    def _update_ref_mode_ui(self) -> None:
        """Update button highlights, description cards and default reset text."""
        mode = self.ref_mode_var.get()
        if mode == "latent_anchor":
            if hasattr(self, "btn_mode_contour") and self.btn_mode_contour:
                self.btn_mode_contour.configure(button_type="neutral")
            if hasattr(self, "btn_mode_structure") and self.btn_mode_structure:
                self.btn_mode_structure.configure(button_type="secondary")
            if hasattr(self, "ref_mode_desc_title") and self.ref_mode_desc_title:
                self.ref_mode_desc_title.configure(
                    text=tr("img2img_ref_mode_desc_structure_title", "Porträts · Landschaften · Organische Motive · Beleuchtung")
                )
            if hasattr(self, "ref_mode_desc_detail") and self.ref_mode_desc_detail:
                self.ref_mode_desc_detail.configure(
                    text=tr("img2img_ref_mode_desc_structure_detail", "Standard-Fidelity: 0.65 | Latent Anchor (0 MB Zusatzgewichte, +14% Tempo)")
                )
            if hasattr(self, "btn_fidelity_default") and self.btn_fidelity_default:
                self.btn_fidelity_default.configure(
                    text=tr("img2img_ref_fidelity_default_btn", "Standard ({val})").replace("{val}", "0.65")
                )
        else:
            if hasattr(self, "btn_mode_contour") and self.btn_mode_contour:
                self.btn_mode_contour.configure(button_type="secondary")
            if hasattr(self, "btn_mode_structure") and self.btn_mode_structure:
                self.btn_mode_structure.configure(button_type="neutral")
            if hasattr(self, "ref_mode_desc_title") and self.ref_mode_desc_title:
                self.ref_mode_desc_title.configure(
                    text=tr("img2img_ref_mode_desc_contour_title", "Architektur · Logos · CAD · Gegenstände · Geometrie")
                )
            if hasattr(self, "ref_mode_desc_detail") and self.ref_mode_desc_detail:
                self.ref_mode_desc_detail.configure(
                    text=tr("img2img_ref_mode_desc_contour_detail", "Standard-Fidelity: 0.75 | Qualcomm Hexagon ControlNet (13 Residuals)")
                )
            if hasattr(self, "btn_fidelity_default") and self.btn_fidelity_default:
                self.btn_fidelity_default.configure(
                    text=tr("img2img_ref_fidelity_default_btn", "Standard ({val})").replace("{val}", "0.75")
                )

    def _on_ref_toggle(self) -> None:
        if self.ref_enabled_var.get():
            self.ref_options_frame.pack(fill="x", pady=(4, 0))
        else:
            self.ref_options_frame.pack_forget()

    def _on_ref_source_change(self) -> None:
        if self.ref_source_var.get() == "custom":
            self.custom_ref_frame.pack(fill="x", pady=(4, 0))
        else:
            self.custom_ref_frame.pack_forget()

    def _load_custom_reference_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title=tr("select_image", "Bild auswählen"),
            filetypes=[
                ("Bilddateien", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tiff"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if file_path:
            p = Path(file_path).resolve()
            if p.is_file():
                self.custom_ref_path = p
                self.ref_image_label.configure(text=f"Ref: {p.name}")

    def _reset_custom_reference_image(self) -> None:
        self.custom_ref_path = None
        self.ref_image_label.configure(text="(Kein separates Referenzbild)")

    def _randomize_seed(self) -> None:
        self.seed.set(str(random.randint(1, 2147483647)))

    def _start_generation(self) -> None:
        if self.controller.running:
            return
        if not self.input_path or not self.input_path.is_file():
            messagebox.showwarning(
                tr("dialog_title_missing_image", "Kein Bild geladen"),
                tr("img2img_load_first", "Bitte laden Sie zuerst ein Eingabebild."),
            )
            return

        prompt_text = self.prompt.get("1.0", "end").strip()
        if not prompt_text:
            messagebox.showwarning(
                tr("dialog_title_missing_prompt", "Prompt erforderlich"),
                tr("inpainting_prompt_required", "Bitte geben Sie einen Prompt für die Bildtransformation ein."),
            )
            return

        neg_prompt_text = self.negative_prompt.get("1.0", "end").strip()
        try:
            seed_val = int(self.seed.get().strip())
        except ValueError:
            seed_val = 42
            self.seed.set("42")

        steps_val = int(self.steps.get())
        cfg_val = float(self.cfg_var.get())
        strength_val = float(self.strength_var.get())

        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        unique_suffix = f"{seed_val}_{timestamp}"
        out_name = f"img2img_{unique_suffix}.png"
        output_file = self.output_dir / out_name

        self.start_button.configure(state="disabled")
        self.status_label.configure(text="QNN/HTP Inferenz läuft...")
        self.progress_bar["value"] = 5
        self.progress_percent_label.configure(text="5%")
        self.progress_detail_label.configure(text="Pipeline wird vorbereitet...")

        enable_ref = bool(self.ref_enabled_var.get())
        ref_mode = str(self.ref_mode_var.get())
        ref_fidelity = float(self.ref_fidelity_var.get())
        if enable_ref and self.ref_source_var.get() == "custom" and self.custom_ref_path:
            ref_path = self.custom_ref_path
        else:
            ref_path = self.input_path

        self.controller.start(
            input_image_path=self.input_path,
            prompt=prompt_text,
            output_path=output_file,
            steps=steps_val,
            seed=seed_val,
            negative_prompt=neg_prompt_text,
            cfg_scale=cfg_val,
            denoising_strength=strength_val,
            enable_reference_control=enable_ref,
            reference_mode=ref_mode,
            reference_fidelity=ref_fidelity,
            reference_image_path=ref_path if enable_ref else None,
            on_progress=self._on_progress,
            on_complete=self._on_complete,
            asynchronous=True,
        )

    def _on_progress(self, phase: str, value: float, detail: str | None) -> None:
        pct = max(0, min(100, int(value * 100)))
        self.progress_bar["value"] = pct
        self.progress_percent_label.configure(text=f"{pct}%")
        if detail:
            self.progress_detail_label.configure(text=detail)

    def _on_complete(self, result: SD15QnnInpaintingResult) -> None:
        self.start_button.configure(state="normal")
        if result.success and result.output_path:
            self.result_path = Path(result.output_path)
            self._update_result_preview()
            self.status_label.configure(text="Generierung abgeschlossen")
            self.progress_bar["value"] = 100
            self.progress_percent_label.configure(text="100%")
            self.progress_detail_label.configure(text="Bild in Galerie gespeichert")

            exec_times = result.metadata.get("execution_times", {})
            total_ms = exec_times.get("total_inference_ms")
            if total_ms is not None:
                self.timing_label.configure(text=f"NPU-Laufzeit: {total_ms:.1f} ms ({total_ms / 1000.0:.2f} s)")
        else:
            err_msg = result.error_message or "Unbekannter Fehler bei der Generierung."
            self.status_label.configure(text="Fehler")
            self.progress_detail_label.configure(text=err_msg)
            messagebox.showerror(
                tr("dialog_title_error", "Fehler"),
                f"Image-to-Image fehlgeschlagen:\n{err_msg}",
            )

    def _cancel_generation(self) -> None:
        if self.controller.running:
            self.controller.cancel()
            self.status_label.configure(text="Abgebrochen")
            self.progress_detail_label.configure(text="Inferenz durch Benutzer abgebrochen.")
            self.start_button.configure(state="normal")

    def _save_result(self) -> None:
        if not self.result_path or not self.result_path.is_file():
            messagebox.showinfo(
                tr("dialog_title_info", "Kein Ergebnis"),
                tr("img2img_no_result_to_save", "Es liegt noch kein generiertes Ergebnis zum Speichern vor."),
            )
            return

        target_file = filedialog.asksaveasfilename(
            title=tr("inpainting_save", "Bild speichern"),
            defaultextension=".png",
            initialfile=self.result_path.name,
            filetypes=[("PNG-Bild", "*.png"), ("JPEG-Bild", "*.jpg;*.jpeg"), ("Alle Dateien", "*.*")],
        )
        if target_file:
            try:
                shutil.copy2(self.result_path, target_file)
                # Copy sidecar json if present
                sidecar_src = self.result_path.with_suffix(".json")
                if sidecar_src.is_file():
                    sidecar_dst = Path(target_file).with_suffix(".json")
                    shutil.copy2(sidecar_src, sidecar_dst)
                messagebox.showinfo(
                    tr("dialog_title_success", "Gespeichert"),
                    f"Bild erfolgreich gespeichert:\n{target_file}",
                )
            except Exception as e:
                messagebox.showerror(
                    tr("dialog_title_error", "Fehler"),
                    f"Fehler beim Speichern der Datei:\n{e}",
                )

    def _open_output_folder(self) -> None:
        target_dir = self.output_dir
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(str(target_dir))
            else:
                subprocess.Popen(["xdg-open", str(target_dir)])
        except Exception as e:
            messagebox.showerror(
                tr("dialog_title_error", "Fehler"),
                f"Ordner konnte nicht geöffnet werden:\n{e}",
            )

    def _on_back_to_overview(self) -> None:
        if callable(self.on_navigate):
            self.on_navigate("overview")

    def apply_generation_settings(self, settings: dict) -> None:
        """Apply generation settings from gallery or presets into the UI controls."""
        if not isinstance(settings, dict):
            return

        # 1. Prompt
        prompt_text = settings.get("prompt")
        if prompt_text is not None and hasattr(self, "prompt"):
            self.prompt.delete("1.0", "end")
            self.prompt.insert("1.0", str(prompt_text))

        # 2. Negative Prompt
        neg_prompt = settings.get("negative_prompt")
        if neg_prompt is not None and hasattr(self, "negative_prompt"):
            self.negative_prompt.delete("1.0", "end")
            self.negative_prompt.insert("1.0", str(neg_prompt))

        # 3. Seed
        seed_val = settings.get("seed")
        if seed_val is not None and hasattr(self, "seed"):
            self.seed.set(str(seed_val))

        # 4. Steps
        steps_val = settings.get("steps")
        if steps_val is not None and hasattr(self, "steps"):
            try:
                self.steps.set(int(steps_val))
            except (ValueError, TypeError):
                pass

        # 5. CFG Scale
        cfg_val = settings.get("cfg") or settings.get("cfg_scale")
        if cfg_val is not None and hasattr(self, "cfg_var"):
            try:
                self.cfg_var.set(float(cfg_val))
            except (ValueError, TypeError):
                pass

        # 6. Denoising Strength & Presets
        denoising_val = settings.get("denoising_strength")
        if denoising_val is not None and hasattr(self, "strength_var"):
            try:
                d_flt = float(denoising_val)
                self.strength_var.set(d_flt)
                self._on_strength_change()
            except (ValueError, TypeError):
                pass

        # 7. Reference Control (Modus A vs Modus B, Fidelity)
        ref_ctrl = settings.get("reference_control")
        if isinstance(ref_ctrl, dict):
            enabled = bool(ref_ctrl.get("enabled", False))
            if hasattr(self, "ref_enabled_var"):
                self.ref_enabled_var.set(enabled)
                self._on_ref_toggle()

            mode = ref_ctrl.get("mode")
            fidelity = ref_ctrl.get("fidelity")
            if mode in ("canny_qnn", "latent_anchor") and hasattr(self, "select_reference_mode"):
                self.select_reference_mode(mode, apply_default_fidelity=False)
            if fidelity is not None and hasattr(self, "ref_fidelity_var"):
                try:
                    self.ref_fidelity_var.set(float(fidelity))
                except (ValueError, TypeError):
                    pass

        # 8. Input Image Path (restore if on disk)
        input_path_str = settings.get("input_image_path")
        if input_path_str:
            p = Path(input_path_str)
            if p.is_file():
                self.load_dropped_image(p)

    def apply_theme(self) -> None:
        """Apply theme updates for Dark/Light mode parity."""
        self.configure(bg=PHOENIX_THEME.content_bg)
        if hasattr(self, "left_canvas") and self.left_canvas:
            self.left_canvas.configure(bg=PHOENIX_THEME.card_bg)
        if hasattr(self, "right_canvas") and self.right_canvas:
            self.right_canvas.configure(bg=PHOENIX_THEME.card_bg)
        self._ensure_progress_style()
        self._update_input_preview()
        self._update_result_preview()
        for btn in getattr(self, "_preset_buttons", {}).values():
            if hasattr(btn, "_resolve_colors"):
                btn._resolve_colors()
                btn._redraw()
        for ref_btn in [
            getattr(self, "btn_mode_contour", None),
            getattr(self, "btn_mode_structure", None),
            getattr(self, "btn_fidelity_default", None),
            getattr(self, "btn_load_ref", None),
            getattr(self, "btn_reset_ref", None),
        ]:
            if ref_btn and hasattr(ref_btn, "_resolve_colors"):
                ref_btn._resolve_colors()
                ref_btn._redraw()
        if hasattr(self, "ref_card"):
            self.ref_card.configure(bg=PHOENIX_THEME.card_bg)
        if hasattr(self, "ref_check"):
            self.ref_check.configure(
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_primary,
                activebackground=PHOENIX_THEME.card_bg,
                activeforeground=PHOENIX_THEME.text_primary,
                selectcolor=PHOENIX_THEME.elevated_bg,
            )
        if hasattr(self, "ref_options_frame"):
            self.ref_options_frame.configure(bg=PHOENIX_THEME.card_bg)
        if hasattr(self, "ref_mode_label"):
            self.ref_mode_label.configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary)
        if hasattr(self, "ref_mode_desc_frame"):
            self.ref_mode_desc_frame.configure(bg=PHOENIX_THEME.elevated_bg)
        if hasattr(self, "ref_mode_desc_title"):
            self.ref_mode_desc_title.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary)
        if hasattr(self, "ref_mode_desc_detail"):
            self.ref_mode_desc_detail.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_muted)
        for rb in [getattr(self, "rb_canny", None), getattr(self, "rb_anchor", None),
                   getattr(self, "rb_src_same", None), getattr(self, "rb_src_custom", None)]:
            if rb:
                rb.configure(
                    bg=PHOENIX_THEME.card_bg,
                    fg=PHOENIX_THEME.text_primary,
                    activebackground=PHOENIX_THEME.card_bg,
                    activeforeground=PHOENIX_THEME.text_primary,
                    selectcolor=PHOENIX_THEME.elevated_bg,
                )
        if hasattr(self, "ref_fidelity_label"):
            self.ref_fidelity_label.configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary)
        if hasattr(self, "ref_fidelity_spin"):
            self.ref_fidelity_spin.configure(
                bg=PHOENIX_THEME.elevated_bg,
                fg=PHOENIX_THEME.text_primary,
                buttonbackground=PHOENIX_THEME.card_bg,
            )
        if hasattr(self, "ref_fidelity_scale"):
            self.ref_fidelity_scale.configure(
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_primary,
                activebackground=PHOENIX_THEME.accent,
                troughcolor=PHOENIX_THEME.elevated_bg,
            )
        if hasattr(self, "ref_image_label"):
            self.ref_image_label.configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted)
