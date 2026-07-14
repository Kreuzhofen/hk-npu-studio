from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
import datetime
from tkinter import messagebox, ttk
from pathlib import Path

from controllers.prompt_workspace_controller import PromptWorkspaceController
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME


logger = logging.getLogger("PhoenixPromptView")


class PhoenixPromptView(WorkspaceFrame):
    """
    Phoenix Workspace View for AI Image Generation.
    Professional two-column layout with grouped parameters on the left
    and a unified AI Generation Inspector on the right.
    """
    COMPACT_PREVIEW_MODE = True

    def __init__(self, master: tk.Misc, controller: PromptWorkspaceController | None = None) -> None:
        super().__init__(
            master,
            "AI Image Generation",
            "Bilder mittels Text-Prompts lokal auf der Snapdragon NPU generieren",
            has_inspector=True
        )
        self.controller = controller or PromptWorkspaceController()
        self._generation_running = False
        self._generation_thread: threading.Thread | None = None
        self._generation_events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._progress_after_id: str | None = None
        self._result_after_id: str | None = None
        self._progress_percent = 0
        self._progress_current_step = 0
        self._progress_total_steps = 0

        self._build_input_area()
        self._build_inspector()
        self._build_status_bar()
        self.refresh()

    # ==================================================================
    # LEFT COLUMN – Scrollable Parameters + Fixed Generate Button
    # ==================================================================

    def _build_input_area(self) -> None:
        self.content_slot.grid_rowconfigure(0, weight=1)
        self.content_slot.grid_columnconfigure(0, weight=1)

        # Outer Card Frame
        self.input_card = tk.Frame(
            self.content_slot,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1
        )
        self.input_card.grid(row=0, column=0, sticky="nsew", padx=PHOENIX_THEME.space_sm, pady=PHOENIX_THEME.space_sm)
        self.input_card.grid_rowconfigure(0, weight=1)   # Scrollable parameters
        self.input_card.grid_rowconfigure(1, weight=0)   # Fixed generate button
        self.input_card.grid_columnconfigure(0, weight=1)

        # ── Scrollable parameter area (Canvas) ────────
        self.param_canvas = tk.Canvas(
            self.input_card, bg=PHOENIX_THEME.card_bg,
            bd=0, highlightthickness=0,
        )
        self.param_canvas.grid(row=0, column=0, sticky="nsew")

        self.param_content = tk.Frame(self.param_canvas, bg=PHOENIX_THEME.card_bg)
        self.param_canvas_wid = self.param_canvas.create_window(
            (0, 0), window=self.param_content, anchor="nw"
        )
        self.param_content.columnconfigure(0, weight=1)
        self.param_content.columnconfigure(1, weight=1)

        self.param_content.bind(
            "<Configure>",
            lambda e: self.param_canvas.configure(scrollregion=self.param_canvas.bbox("all"))
        )
        self.param_canvas.bind(
            "<Configure>",
            lambda e: self.param_canvas.itemconfig(self.param_canvas_wid, width=e.width)
        )

        # Mouse wheel scrolling on left panel
        def _on_param_mousewheel(event: tk.Event) -> None:
            self.param_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.input_card.bind("<Enter>", lambda e: self.param_canvas.bind_all("<MouseWheel>", _on_param_mousewheel))
        self.input_card.bind("<Leave>", lambda e: self.param_canvas.unbind_all("<MouseWheel>"))

        # Build all parameter groups inside param_content
        self._build_parameters()

        # ── Fixed primary action (always visible) ─────
        action_bar = tk.Frame(
            self.input_card,
            bg=PHOENIX_THEME.surface,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        action_bar.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.space_md),
        )
        action_bar.grid_columnconfigure(0, weight=1, uniform="generation_actions")
        action_bar.grid_columnconfigure(1, weight=1, uniform="generation_actions")

        tk.Label(
            action_bar,
            text="Bereit für deine nächste Idee",
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(PHOENIX_THEME.space_sm, 0),
        )
        tk.Label(
            action_bar,
            text="Die Generierung wird lokal auf dem ausgewählten Backend ausgeführt.",
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(0, PHOENIX_THEME.space_sm),
        )

        self.gen_btn = tk.Button(
            action_bar,
            text="BILD GENERIEREN  →",
            command=self._on_generate,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_section,
            cursor="hand2",
            padx=PHOENIX_THEME.button_pad_x,
            pady=PHOENIX_THEME.button_pad_y,
        )
        self.gen_btn.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_xs),
            pady=(0, PHOENIX_THEME.space_md),
        )
        self.cancel_btn = tk.Button(
            action_bar,
            text="ABBRECHEN",
            command=self._on_cancel_generation,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_disabled,
            activebackground=PHOENIX_THEME.button_active,
            activeforeground=PHOENIX_THEME.text_on_accent,
            disabledforeground=PHOENIX_THEME.text_disabled,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_section,
            cursor="hand2",
            state="disabled",
            padx=PHOENIX_THEME.button_pad_x,
            pady=PHOENIX_THEME.button_pad_y,
        )
        self.cancel_btn.grid(
            row=2,
            column=1,
            sticky="nsew",
            padx=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_md),
            pady=(0, PHOENIX_THEME.space_md),
        )
        self._layout_generation_actions(False)

    def _build_parameters(self) -> None:
        """Build all parameter groups inside the scrollable param_content frame."""
        # Shared variables for layout synchronization
        self.width_var = tk.StringVar(value="512")
        self.height_var = tk.StringVar(value="512")
        self.sampler_var = tk.StringVar(value="Euler")
        self.scheduler_var = tk.StringVar(value="Normal")
        self.batch_var = tk.StringVar(value="1")
        self.cfg_var = tk.DoubleVar(value=7.5)
        self.steps_var = tk.IntVar(value=20)
        self.seed_var = tk.StringVar(value="-1")

        p = self.param_content  # shorthand
        r = 0

        # ── Group: Model ──────────────────────────────
        r = self._section_header(p, "Model", r)

        model_frame = tk.Frame(p, bg=PHOENIX_THEME.card_bg)
        model_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        model_frame.grid_columnconfigure(0, weight=0)
        model_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            model_frame, text="KI-Modell:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=2)

        active_model_id = self.controller.repository.get_active_model_id()
        default_model = active_model_id if active_model_id in self.controller.AVAILABLE_MODELS else self.controller.AVAILABLE_MODELS[0]
        self.model_var = tk.StringVar(value=default_model)
        self.model_var.trace_add("write", self._on_model_changed)
        model_dropdown = tk.OptionMenu(model_frame, self.model_var, *self.controller.AVAILABLE_MODELS)
        model_dropdown.configure(
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_button,
        )
        model_dropdown["menu"].configure(
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
            font=PHOENIX_THEME.font_body, relief="flat", bd=0,
        )
        model_dropdown.grid(row=0, column=1, sticky="ew", pady=2)
        r += 1

        # ── Group: Prompt ─────────────────────────────
        prompt_card = tk.Frame(
            p,
            bg=PHOENIX_THEME.surface,
            highlightbackground=PHOENIX_THEME.accent,
            highlightthickness=2,
        )
        prompt_card.grid(
            row=r,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_sm),
        )
        prompt_card.grid_columnconfigure(0, weight=1)

        # Header frame for DEIN PROMPT and history button
        prompt_header_frame = tk.Frame(prompt_card, bg=PHOENIX_THEME.surface)
        prompt_header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(PHOENIX_THEME.space_md, 0),
        )
        prompt_header_frame.grid_columnconfigure(0, weight=1)
        prompt_header_frame.grid_columnconfigure(1, weight=0)
        prompt_header_frame.grid_columnconfigure(2, weight=0)
        prompt_header_frame.grid_columnconfigure(3, weight=0)

        tk.Label(
            prompt_header_frame,
            text="DEIN PROMPT",
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.templates_btn = tk.Button(
            prompt_header_frame,
            text="Vorlagen ▼",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_caption,
            cursor="hand2",
            padx=8,
            pady=2,
            command=self._show_templates_popup,
        )
        self.templates_btn.grid(row=0, column=1, sticky="e", padx=(0, 6))

        self.history_btn = tk.Button(
            prompt_header_frame,
            text="🕘",
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_secondary,
            activebackground=PHOENIX_THEME.surface,
            activeforeground=PHOENIX_THEME.accent,
            relief="flat",
            bd=0,
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            command=self._show_prompt_history_popup,
        )
        self.history_btn.grid(row=0, column=2, sticky="e", padx=(0, 6))

        self.maximize_btn = tk.Button(
            prompt_header_frame,
            text="⛶ Maximieren",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_caption,
            cursor="hand2",
            padx=8,
            pady=2,
            command=self._open_expandable_prompt_popup,
        )
        self.maximize_btn.grid(row=0, column=3, sticky="e")
        tk.Label(
            prompt_card,
            text="Beschreibe Motiv, Licht, Perspektive und Stil möglichst konkret.",
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(0, PHOENIX_THEME.space_sm),
        )

        self.prompt_text = tk.Text(
            prompt_card, height=5, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body, wrap="word",
            padx=PHOENIX_THEME.space_sm, pady=PHOENIX_THEME.space_sm,
        )
        self.prompt_text.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(0, PHOENIX_THEME.space_xs),
        )
        self.prompt_text.insert("1.0", "A futuristic cyberpunk cityscape, neon lights, high resolution, highly detailed")
        self.prompt_text.bind("<KeyRelease>", lambda e: self._on_main_prompt_key())

        # Live Prompt Counter Label
        self.prompt_counter_lbl = tk.Label(
            prompt_card,
            text="Zeichen: 0 | Wörter: 0",
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="e"
        )
        self.prompt_counter_lbl.grid(
            row=3,
            column=0,
            sticky="e",
            padx=PHOENIX_THEME.space_md,
            pady=(0, PHOENIX_THEME.space_sm)
        )

        tk.Label(
            prompt_card,
            text="AUSSCHLIESSEN",
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(
            row=4,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(0, PHOENIX_THEME.space_xs),
        )

        self.neg_prompt_text = tk.Text(
            prompt_card, height=2, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body, wrap="word",
            padx=PHOENIX_THEME.space_sm, pady=PHOENIX_THEME.space_sm,
        )
        self.neg_prompt_text.grid(
            row=5,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(0, PHOENIX_THEME.space_md),
        )
        self.neg_prompt_text.insert("1.0", "blurry, low quality, distorted, extra limbs, bad anatomy")
        self._update_prompt_counters()
        r += 1

        # ── Group: Image Size ─────────────────────────
        r = self._section_header(p, "Image Size", r)

        self.size_frame = tk.Frame(p, bg=PHOENIX_THEME.card_bg)
        self.size_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        self.size_frame.row_idx = r
        self.size_frame.grid_columnconfigure(0, weight=0)
        self.size_frame.grid_columnconfigure(1, weight=1)
        self.size_frame.grid_columnconfigure(2, weight=0)
        self.size_frame.grid_columnconfigure(3, weight=1)

        self.width_label = tk.Label(self.size_frame, text="Breite:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.width_label.grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        self.width_menu = tk.OptionMenu(self.size_frame, self.width_var, "256", "512", "768", "1024")
        self.width_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.width_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.width_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        self.height_label = tk.Label(self.size_frame, text="Höhe:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.height_label.grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        self.height_menu = tk.OptionMenu(self.size_frame, self.height_var, "256", "512", "768", "1024")
        self.height_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.height_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.height_menu.grid(row=0, column=3, sticky="ew", pady=2)

        # Build Locked Resolution View (initially hidden)
        from resources.icons import IconManager
        self.locked_res_frame = tk.Frame(self.size_frame, bg=PHOENIX_THEME.card_bg)
        self.locked_res_frame.grid_columnconfigure(0, weight=1)
        self.locked_res_frame.grid_columnconfigure(1, weight=1)

        self.res_512_btn = tk.Button(
            self.locked_res_frame,
            text="512 × 512",
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_button,
            state="normal",
            cursor="arrow",
            padx=10,
            pady=8
        )
        self.res_512_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(4, 4))

        lock_symbol = IconManager.get_symbol("lock")
        self.res_1024_btn = tk.Button(
            self.locked_res_frame,
            text=f"{lock_symbol} 1024 × 1024 (Demnächst)",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_disabled,
            activebackground=PHOENIX_THEME.elevated_bg,
            activeforeground=PHOENIX_THEME.text_disabled,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_button,
            state="disabled",
            disabledforeground=PHOENIX_THEME.text_disabled,
            padx=10,
            pady=8
        )
        self.res_1024_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(4, 4))

        self.locked_hint_lbl = tk.Label(
            self.locked_res_frame,
            text="Höhere Auflösungen benötigen ein kompatibles Qualcomm-Modell.",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left",
            wraplength=280
        )
        self.locked_hint_lbl.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        r += 1

        sampling_frame = tk.Frame(p, bg=PHOENIX_THEME.card_bg)
        sampling_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        sampling_frame.grid_columnconfigure(0, weight=1)
        sampling_frame.grid_columnconfigure(1, weight=1)

        self.cfg_label = tk.Label(sampling_frame, text="CFG Scale:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.cfg_label.grid(row=0, column=0, sticky="w", pady=(0, 1))
        self.cfg_scale = tk.Scale(
            sampling_frame, from_=1.0, to=20.0, resolution=0.5, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            width=12, variable=self.cfg_var
        )
        self.cfg_scale.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 2))

        # Advanced settings button for compact mode
        self.adv_label = tk.Label(sampling_frame, text="Einstellungen:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.adv_settings_btn = tk.Button(
            sampling_frame, text="Erweiterte Einstellungen ⚙️",
            font=PHOENIX_THEME.font_caption, cursor="hand2", relief="flat", bd=0, padx=8, pady=6,
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_secondary,
            activebackground=PHOENIX_THEME.elevated_bg, activeforeground=PHOENIX_THEME.text_primary,
            command=self._open_advanced_settings_popup
        )

        tk.Label(sampling_frame, text="Steps:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=1, sticky="w", pady=(0, 1))
        self.steps_scale = tk.Scale(
            sampling_frame, from_=1, to=100, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            width=12, variable=self.steps_var
        )
        self.steps_scale.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 2))

        # Quality presets for standard mode (locked resolution models)
        self.active_steps_preset = "Standard"
        self.steps_preset_frame = tk.Frame(sampling_frame, bg=PHOENIX_THEME.card_bg)
        self.steps_preset_frame.grid_columnconfigure(0, weight=1)

        self.btn_preset_schnell = tk.Button(
            self.steps_preset_frame, text="⚡ Schnell",
            font=PHOENIX_THEME.font_caption, cursor="hand2", relief="flat", bd=0, padx=4, pady=4,
            command=lambda: self._select_steps_preset("Schnell")
        )
        self.btn_preset_schnell.grid(row=0, column=0, sticky="ew", pady=(0, 2))

        self.btn_preset_standard = tk.Button(
            self.steps_preset_frame, text="⭐ Standard",
            font=PHOENIX_THEME.font_caption, cursor="hand2", relief="flat", bd=0, padx=4, pady=4,
            command=lambda: self._select_steps_preset("Standard")
        )
        self.btn_preset_standard.grid(row=1, column=0, sticky="ew", pady=2)

        self.btn_preset_beste = tk.Button(
            self.steps_preset_frame, text="💎 Beste Qualität",
            font=PHOENIX_THEME.font_caption, cursor="hand2", relief="flat", bd=0, padx=4, pady=4,
            command=lambda: self._select_steps_preset("Beste Qualität")
        )
        self.btn_preset_beste.grid(row=2, column=0, sticky="ew", pady=(2, 0))

        self._update_steps_preset_colors()

        self.dropdown_frame = tk.Frame(sampling_frame, bg=PHOENIX_THEME.card_bg)
        self.dropdown_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self.dropdown_frame.grid_columnconfigure(0, weight=0)
        self.dropdown_frame.grid_columnconfigure(1, weight=1)
        self.dropdown_frame.grid_columnconfigure(2, weight=0)
        self.dropdown_frame.grid_columnconfigure(3, weight=1)

        tk.Label(self.dropdown_frame, text="Sampler:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        self.sampler_menu = tk.OptionMenu(self.dropdown_frame, self.sampler_var, "Euler a", "Euler", "DPM++ 2M", "DDIM", "LMS")
        self.sampler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.sampler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.sampler_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        tk.Label(self.dropdown_frame, text="Sched.:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        self.scheduler_menu = tk.OptionMenu(self.dropdown_frame, self.scheduler_var, "Normal", "Karras", "Exponential", "SGM Uniform")
        self.scheduler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.scheduler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.scheduler_menu.grid(row=0, column=3, sticky="ew", pady=2)
        r += 1

        # ── Group: Output ─────────────────────────────
        r = self._section_header(p, "Output", r)

        self.output_frame = tk.Frame(p, bg=PHOENIX_THEME.card_bg)
        self.output_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        self.output_frame.row_idx = r
        self.output_frame.grid_columnconfigure(0, weight=0)
        self.output_frame.grid_columnconfigure(1, weight=1)
        self.output_frame.grid_columnconfigure(2, weight=0)
        self.output_frame.grid_columnconfigure(3, weight=1)

        tk.Label(self.output_frame, text="Seed:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        self.seed_entry = tk.Entry(
            self.output_frame, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body,
            textvariable=self.seed_var
        )
        self.seed_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        tk.Label(self.output_frame, text="Batch:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        batch_menu = tk.OptionMenu(self.output_frame, self.batch_var, "1", "2", "4", "8")
        batch_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        batch_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        batch_menu.grid(row=0, column=3, sticky="ew", pady=2)

        self._apply_generation_contract(self.model_var.get())

    @staticmethod
    def _configure_option_contract(widget: tk.OptionMenu, variable: tk.StringVar, spec: dict) -> None:
        """Apply a metadata-owned list contract to an option control."""
        values = [str(value) for value in spec.get("values", [])]
        default = str(spec.get("default", values[0] if values else variable.get()))
        if default not in values:
            values.insert(0, default)
        menu = widget["menu"]
        menu.delete(0, "end")
        for value in values:
            menu.add_command(label=value, command=tk._setit(variable, value))
        variable.set(default)
        widget.configure(state="normal" if spec.get("editable", True) and len(values) > 1 else "disabled")

    def _apply_generation_contract(self, model_id: str) -> None:
        """Render the selected model's generic metadata contract without model-specific logic."""
        contract = self.controller.select_model(model_id)
        if not contract:
            return

        option_controls = {
            "width": (self.width_menu, self.width_var),
            "height": (self.height_menu, self.height_var),
            "sampler": (self.sampler_menu, self.sampler_var),
            "scheduler": (self.scheduler_menu, self.scheduler_var),
        }
        for name, (widget, variable) in option_controls.items():
            spec = contract.get(name)
            if isinstance(spec, dict):
                self._configure_option_contract(widget, variable, spec)

        # Manage visibility based on COMPACT_PREVIEW_MODE
        if self.COMPACT_PREVIEW_MODE:
            # Hide the entire Image Size group, dropdown frame, and Output group from main panel
            self.size_frame.grid_remove()
            self.dropdown_frame.grid_remove()
            self.output_frame.grid_remove()
            if hasattr(self, "_section_labels"):
                if "Image Size" in self._section_labels:
                    self._section_labels["Image Size"].grid_remove()
                if "Output" in self._section_labels:
                    self._section_labels["Output"].grid_remove()

            # Hide standard CFG scale and show advanced settings button
            self.cfg_label.grid_remove()
            self.cfg_scale.grid_remove()
            self.adv_label.grid(row=0, column=0, sticky="w", pady=(0, 1))
            self.adv_settings_btn.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 2))
        else:
            # Show standard CFG scale and hide advanced settings button
            self.adv_label.grid_remove()
            self.adv_settings_btn.grid_remove()
            self.cfg_label.grid(row=0, column=0, sticky="w", pady=(0, 1))
            self.cfg_scale.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 2))

            # Show the entire Image Size group, dropdown frame, and Output group in main panel
            if hasattr(self, "_section_labels"):
                if "Image Size" in self._section_labels:
                    lbl = self._section_labels["Image Size"]
                    lbl.grid(row=lbl.row_idx, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 1))
                if "Output" in self._section_labels:
                    lbl = self._section_labels["Output"]
                    lbl.grid(row=lbl.row_idx, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 1))

            self.size_frame.grid(row=self.size_frame.row_idx, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
            self.dropdown_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
            self.output_frame.grid(row=self.output_frame.row_idx, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))

            # Layout resolution inside size_frame
            if contract.get("resolution_locked") is True:
                self.width_menu.configure(state="disabled")
                self.height_menu.configure(state="disabled")
                self.width_label.grid_remove()
                self.width_menu.grid_remove()
                self.height_label.grid_remove()
                self.height_menu.grid_remove()
                self.locked_res_frame.grid(row=0, column=0, columnspan=4, sticky="ew")
                self.width_var.set("512")
                self.height_var.set("512")
            else:
                self.locked_res_frame.grid_remove()
                self.width_label.grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
                self.width_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)
                self.height_label.grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
                self.height_menu.grid(row=0, column=3, sticky="ew", pady=2)

        # Always configure scale ranges
        scale_controls = {"steps": self.steps_scale, "cfg": self.cfg_scale}
        for name, widget in scale_controls.items():
            spec = contract.get(name)
            if not isinstance(spec, dict):
                continue
            options = {}
            if "min" in spec:
                options["from_"] = spec["min"]
            if "max" in spec:
                options["to"] = spec["max"]
            if "resolution" in spec:
                options["resolution"] = spec["resolution"]
            if options:
                widget.configure(**options)
            if "default" in spec:
                widget.set(spec["default"])

        # Layout steps scale or quality presets inside sampling_frame (column 1)
        if contract.get("resolution_locked") is True:
            # Hide steps scale and show preset frame
            self.steps_scale.grid_remove()
            self.steps_preset_frame.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 2))

            # Re-sync preset based on current step scale value
            current_steps = self.steps_scale.get()
            if current_steps == 10:
                self._select_steps_preset("Schnell")
            elif current_steps == 30:
                self._select_steps_preset("Beste Qualität")
            else:
                self._select_steps_preset("Standard")
        else:
            # Hide steps preset frame and show scale
            self.steps_preset_frame.grid_remove()
            self.steps_scale.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 2))

        # Always configure seed default
        seed_spec = contract.get("seed")
        if isinstance(seed_spec, dict) and "default" in seed_spec:
            self.seed_var.set(str(seed_spec["default"]))

        # If advanced settings popup is currently open and active, refresh it so it stays synced
        if hasattr(self, "_advanced_popup") and self._advanced_popup.winfo_exists():
            self._advanced_popup.destroy()
            self._open_advanced_settings_popup()

    def _section_header(self, parent: tk.Frame, title: str, row: int) -> int:
        """Create a subtle section divider label and return the next row index."""
        lbl = tk.Label(
            parent, text=title, bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title, anchor="w"
        )
        lbl.grid(row=row, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 1))
        lbl.row_idx = row
        if not hasattr(self, "_section_labels"):
            self._section_labels = {}
        self._section_labels[title] = lbl
        return row + 1

    # ==================================================================
    # RIGHT COLUMN – AI Generation Inspector
    # ==================================================================

    def _build_inspector(self) -> None:
        if self.inspector_slot is None:
            return

        self.inspector_slot.grid_rowconfigure(0, weight=1)
        self.inspector_slot.grid_columnconfigure(0, weight=1)

        # Inspector Card
        self.inspector_panel = tk.Frame(
            self.inspector_slot, bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border, highlightthickness=1,
        )
        self.inspector_panel.grid(row=0, column=0, sticky="nsew", padx=PHOENIX_THEME.space_sm, pady=PHOENIX_THEME.space_sm)
        self.inspector_panel.grid_rowconfigure(0, weight=1)
        self.inspector_panel.grid_columnconfigure(0, weight=1)

        self.insp_content = tk.Frame(self.inspector_panel, bg=PHOENIX_THEME.card_bg)
        self.insp_content.grid(row=0, column=0, sticky="nsew")
        self.insp_content.columnconfigure(0, weight=0)
        self.insp_content.columnconfigure(1, weight=1)
        self.insp_content.columnconfigure(2, weight=0)
        self.insp_content.columnconfigure(3, weight=1)

        row = 0

        # ── Section: Generation Status ────────────────
        row = self._inspector_section_header("Generation Status", row)

        # Selected Model
        tk.Label(
            self.insp_content, text="Model:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_model = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_model.grid(row=row, column=1, columnspan=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        # Backend & Queue
        tk.Label(
            self.insp_content, text="Backend:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_backend = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_backend.grid(row=row, column=1, sticky="w", padx=(4, 16), pady=1)

        tk.Label(
            self.insp_content, text="Queue:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=2, sticky="w", padx=(16, 4), pady=1)
        self.insp_queue = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_queue.grid(row=row, column=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        # Status
        tk.Label(
            self.insp_content, text="Status:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_gen_status = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_gen_status.grid(row=row, column=1, columnspan=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        tk.Label(
            self.insp_content, text="Fortschritt:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.progress_var = tk.DoubleVar(value=0.0)
        self._ensure_progress_style()
        self.progress_bar = ttk.Progressbar(
            self.insp_content,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            style="Phoenix.Horizontal.TProgressbar",
        )
        self.progress_bar.grid(row=row, column=1, columnspan=3, sticky="ew", padx=(4, 16), pady=1)
        row += 1

        tk.Label(
            self.insp_content, text="Phase:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.progress_stage_label = tk.Label(
            self.insp_content, text="Bereit", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.progress_stage_label.grid(row=row, column=1, sticky="w", padx=(4, 16), pady=1)

        tk.Label(
            self.insp_content, text="Steps:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=2, sticky="w", padx=(16, 4), pady=1)
        self.progress_step_label = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.progress_step_label.grid(row=row, column=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        # ── Section: Generation Information ───────────
        row = self._inspector_section_header("Generation Information", row)

        # Row 0: Size & Steps
        tk.Label(
            self.insp_content, text="Size:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_size = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_size.grid(row=row, column=1, sticky="w", padx=(4, 16), pady=1)

        tk.Label(
            self.insp_content, text="Steps:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=2, sticky="w", padx=(16, 4), pady=1)
        self.insp_steps = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_steps.grid(row=row, column=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        # Row 1: CFG & Seed
        tk.Label(
            self.insp_content, text="CFG:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_cfg = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_cfg.grid(row=row, column=1, sticky="w", padx=(4, 16), pady=1)

        tk.Label(
            self.insp_content, text="Seed:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=2, sticky="w", padx=(16, 4), pady=1)
        self.insp_seed = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_seed.grid(row=row, column=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        # Row 2: Sampler & Scheduler
        tk.Label(
            self.insp_content, text="Sampler:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_sampler = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_sampler.grid(row=row, column=1, sticky="w", padx=(4, 16), pady=1)

        tk.Label(
            self.insp_content, text="Sched.:", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=2, sticky="w", padx=(16, 4), pady=1)
        self.insp_scheduler = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_scheduler.grid(row=row, column=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        # ── Section: Preview ──────────────────────────
        row = self._inspector_section_header("Preview", row)

        preview_frame = tk.Frame(
            self.insp_content, bg=PHOENIX_THEME.content_bg,
            highlightbackground=PHOENIX_THEME.border, highlightthickness=1
        )
        preview_frame.grid(row=row, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 4))
        preview_frame.grid_columnconfigure(0, weight=1)

        self.preview_center = tk.Frame(preview_frame, bg=PHOENIX_THEME.content_bg)
        self.preview_center.grid(row=0, column=0, sticky="", pady=8)

        from resources.icons import IconManager
        tk.Label(
            self.preview_center, text=IconManager.get_symbol("image"),
            bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.accent,
            font=(PHOENIX_THEME.font_title[0], 20, "bold"),
        ).pack(anchor="center", pady=(0, 2))

        tk.Label(
            self.preview_center, text="No image generated",
            bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small, justify="center"
        ).pack(anchor="center")
        row += 1

        # ── Future Action Buttons (placeholders) ──────
        btn_frame = tk.Frame(self.insp_content, bg=PHOENIX_THEME.card_bg)
        btn_frame.grid(row=row, column=0, columnspan=4, sticky="ew", padx=16, pady=(2, 6))
        btn_frame.columnconfigure((0, 1, 2), weight=1)

        btn_style = {
            "bg": PHOENIX_THEME.elevated_bg, "fg": PHOENIX_THEME.text_muted,
            "activebackground": PHOENIX_THEME.elevated_bg, "activeforeground": PHOENIX_THEME.text_muted,
            "bd": 1, "relief": "flat", "font": PHOENIX_THEME.font_caption,
            "state": "disabled", "height": 1,
        }

        self.btn_open_library = tk.Button(btn_frame, text="Open in Library", command=self._on_open_library, **btn_style)
        self.btn_open_library.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        
        self.btn_open_review = tk.Button(btn_frame, text="Open in Review", command=self._on_open_review, **btn_style)
        self.btn_open_review.grid(row=0, column=1, sticky="ew", padx=1, pady=1)
        
        self.btn_save_as = tk.Button(btn_frame, text="Save As", command=self._on_save_as, **btn_style)
        self.btn_save_as.grid(row=0, column=2, sticky="ew", padx=1, pady=1)

    def _inspector_section_header(self, title: str, row: int) -> int:
        tk.Label(
            self.insp_content, text=title, bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_card_title, anchor="w",
        ).grid(row=row, column=0, columnspan=4, sticky="ew", padx=16, pady=(4, 2))
        return row + 1

    def _insp_value_label(self, r: int, c: int) -> tk.Label:
        lbl = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        lbl.grid(row=r, column=c, sticky="w", padx=(4, 16), pady=2)
        return lbl

    # ==================================================================
    # BOTTOM STATUS BAR (aligned with card edges)
    # ==================================================================

    def _build_status_bar(self) -> None:
        self.status_bar_frame = tk.Frame(
            self.status_slot, bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border, highlightthickness=1
        )
        # padx=space_sm aligns the status bar with the card edges above
        self.status_bar_frame.grid(row=0, column=0, sticky="ew", padx=PHOENIX_THEME.space_sm)

        self.status_label = tk.Label(
            self.status_bar_frame, text="Status: Bereit",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption, anchor="w", padx=16, pady=6
        )
        self.status_label.pack(side="left")

        self.model_status_label = tk.Label(
            self.status_bar_frame, text="Modell: -",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption, anchor="w", padx=16, pady=6
        )
        self.model_status_label.pack(side="left")

        self.backend_status_label = tk.Label(
            self.status_bar_frame, text="Backend: -",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption, anchor="w", padx=16, pady=6
        )
        self.backend_status_label.pack(side="left")

        self.env_status_label = tk.Label(
            self.status_bar_frame, text="Environment: -",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption, anchor="w", padx=16, pady=6
        )
        self.env_status_label.pack(side="left")

        self.qnn_status_label = tk.Label(
            self.status_bar_frame, text="QNN: -",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption, anchor="w", padx=16, pady=6
        )
        self.qnn_status_label.pack(side="left")

        self.queue_status_label = tk.Label(
            self.status_bar_frame, text="Queue: 0 Job(s)",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption, anchor="w", padx=16, pady=6
        )
        self.queue_status_label.pack(side="right")

    # ==================================================================
    # ACTIONS
    # ==================================================================

    def _on_generate(self) -> None:
        if self._generation_running:
            return

        prompt = self.prompt_text.get("1.0", "end-1c").strip()
        neg_prompt = self.neg_prompt_text.get("1.0", "end-1c").strip()

        try:
            seed = int(self.seed_entry.get().strip())
        except ValueError:
            seed = -1

        steps = int(self.steps_scale.get())
        cfg = float(self.cfg_scale.get())

        try:
            width = int(self.width_var.get())
        except ValueError:
            width = 512

        try:
            height = int(self.height_var.get())
        except ValueError:
            height = 512

        selected_model = self.model_var.get()

        try:
            batch_size = int(self.batch_var.get())
        except ValueError:
            batch_size = 1

        sampler = self.sampler_var.get()
        scheduler = self.scheduler_var.get()

        self.controller.update_parameters(
            prompt=prompt, negative_prompt=neg_prompt,
            seed=seed, steps=steps, cfg=cfg,
            width=width, height=height, selected_model=selected_model,
            sampler=sampler, scheduler=scheduler, batch_size=batch_size,
        )

        self._generation_running = True
        self._progress_total_steps = max(1, steps)
        self._progress_current_step = 0
        self._progress_percent = 0
        self._set_generation_busy(True)
        self._set_progress(3, "Vorbereiten", "-")

        while not self._generation_events.empty():
            try:
                self._generation_events.get_nowait()
            except queue.Empty:
                break

        self._generation_thread = threading.Thread(
            target=self._run_generation_worker,
            name="PromptGenerationWorker",
            daemon=True,
        )
        self._generation_thread.start()
        self._schedule_progress_tick()
        self._schedule_result_poll()

    def _run_generation_worker(self) -> None:
        try:
            result = self.controller.generate_image(notify_workflow=False)
            self._generation_events.put(("result", result))
        except Exception as error:
            logger.exception("Prompt-to-image generation failed")
            self._generation_events.put(("error", error))

    def _on_cancel_generation(self) -> None:
        if not self._generation_running:
            return
        self.cancel_btn.configure(state="disabled", fg=PHOENIX_THEME.text_disabled)
        self.controller.cancel_generation()
        self._cancel_progress_tick()
        self._set_progress(self._progress_percent, "CANCELLED", self._step_text())
        self._configure_if_alive(self.status_label, text="Status: CANCELLED")
        self._configure_if_alive(self.insp_gen_status, text="CANCELLED")

    def _schedule_result_poll(self) -> None:
        if not self._is_view_alive():
            return
        self._result_after_id = self.after(250, self._poll_generation_events)

    def _poll_generation_events(self) -> None:
        if not self._is_view_alive():
            return

        try:
            event, payload = self._generation_events.get_nowait()
        except queue.Empty:
            if self._generation_running:
                self._schedule_result_poll()
            return

        if event == "result":
            self._handle_generation_result(payload)
        elif event == "error":
            self._handle_generation_error(payload)

    def _handle_generation_result(self, result) -> None:
        if not self._is_view_alive():
            return

        self._generation_running = False
        self._cancel_progress_tick()
        cancelled = result.status == "CANCELLED"
        if cancelled:
            self._set_progress(self._progress_percent, "CANCELLED", self._step_text())
        else:
            self._set_progress(100, "Fertig" if result.success else "Fehler", self._step_text())
        self._set_generation_busy(False)

        if result.success:
            self._append_generation_diagnostic(result, "before_finish_callback")
            self._notify_generation_finished(result)
            self._append_generation_diagnostic(result, "after_finish_callback")
            self._append_generation_diagnostic(result, "before_gallery_open_callback")
            self._show_generated_output_in_library(result.image_path)
            self._append_generation_diagnostic(result, "after_gallery_open_callback")
        elif not cancelled:
            self._append_generation_diagnostic(result, "generation_failed", result.message)
            messagebox.showerror("AI Generate", result.message)

        self.refresh()

    def _handle_generation_error(self, error: object) -> None:
        if not self._is_view_alive():
            return

        self._generation_running = False
        self._cancel_progress_tick()
        self.controller.model.update_state(status=f"Fehler: {error}")
        self._set_progress(100, "Fehler", self._step_text())
        self._set_generation_busy(False)
        messagebox.showerror("AI Generate", str(error))
        self.refresh()

    def _notify_generation_finished(self, result) -> None:
        try:
            from controllers.workflow_controller import WorkflowController
            WorkflowController.get_instance().on_generation_finished(result)
        except Exception as error:
            self._append_generation_diagnostic(result, "finish_callback_exception", str(error))
            logger.warning("Workflow notification skipped after generation: %s", error)

    def _append_generation_diagnostic(self, result, step: str, details: str = "") -> None:
        metadata = getattr(result, "metadata", None)
        if not isinstance(metadata, dict):
            return
        log_path = metadata.get("diagnostic_log_path")
        if not log_path:
            return
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        line = f"[{timestamp}] {step}"
        if details:
            line = f"{line} | {details}"
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(line + "\n")
        except Exception as error:
            logger.warning("Generation diagnostic append failed: %s", error)

    def _set_generation_busy(self, busy: bool) -> None:
        if not self._is_view_alive():
            return
        self._layout_generation_actions(busy)
        state = "disabled" if busy else "normal"
        self.gen_btn.configure(state=state)
        self.cancel_btn.configure(
            state="normal" if busy else "disabled",
            bg=PHOENIX_THEME.button_active if busy else PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_on_accent if busy else PHOENIX_THEME.text_disabled,
        )
        status_text = "Generierung läuft" if busy else self.controller.get_state().status
        self._configure_if_alive(self.status_label, text=f"Status: {status_text}")
        self._configure_if_alive(self.insp_gen_status, text=status_text)

    def _layout_generation_actions(self, busy: bool) -> None:
        """Switch between the single and split action-bar layouts."""
        if busy:
            self.gen_btn.grid_configure(
                column=0,
                columnspan=1,
                padx=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_xs),
            )
            self.cancel_btn.grid()
        else:
            self.cancel_btn.grid_remove()
            self.gen_btn.grid_configure(
                column=0,
                columnspan=2,
                padx=PHOENIX_THEME.space_md,
            )

    def _schedule_progress_tick(self) -> None:
        if not self._is_view_alive() or not self._generation_running:
            return
        self._progress_after_id = self.after(1000, self._update_generation_progress)

    def _cancel_progress_tick(self) -> None:
        if self._progress_after_id and self._is_view_alive():
            try:
                self.after_cancel(self._progress_after_id)
            except Exception:
                pass
        self._progress_after_id = None

    def _update_generation_progress(self) -> None:
        if not self._is_view_alive() or not self._generation_running:
            return

        if self._progress_percent < 12:
            self._set_progress(self._progress_percent + 3, "Vorbereiten", "-")
        elif self._progress_percent < 30:
            self._set_progress(self._progress_percent + 2, "Text Encoding", "-")
        elif self._progress_percent < 86:
            next_percent = min(86, self._progress_percent + 2)
            span = max(1, 86 - 30)
            self._progress_current_step = min(
                self._progress_total_steps,
                max(1, int(((next_percent - 30) / span) * self._progress_total_steps)),
            )
            self._set_progress(next_percent, "UNet Steps", self._step_text())
        elif self._progress_percent < 94:
            self._set_progress(self._progress_percent + 1, "VAE Decode", self._step_text())
        elif self._progress_percent < 98:
            self._set_progress(self._progress_percent + 1, "Speichern", self._step_text())
        else:
            self._set_progress(98, "Speichern", self._step_text())

        self._schedule_progress_tick()

    def _set_progress(self, percent: float, stage: str, step_text: str) -> None:
        if not self._is_view_alive():
            return
        self._ensure_progress_style()
        self._progress_percent = max(0, min(100, int(percent)))
        self.progress_var.set(self._progress_percent)
        self._configure_if_alive(self.progress_stage_label, text=f"{stage} · {self._progress_percent} %")
        self._configure_if_alive(self.progress_step_label, text=step_text)

    def _step_text(self) -> str:
        if self._progress_total_steps <= 0:
            return "-"
        current = min(self._progress_total_steps, max(0, self._progress_current_step))
        return f"{current} / {self._progress_total_steps}"

    def _is_view_alive(self) -> bool:
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def _configure_if_alive(self, widget: tk.Misc, **kwargs) -> None:
        try:
            if widget.winfo_exists():
                widget.configure(**kwargs)
        except tk.TclError:
            pass

    def _show_generated_output_in_library(self, image_path: str | None) -> None:
        if not image_path:
            return

        app = self.winfo_toplevel()
        application_controller = getattr(app, "application_controller", None)
        open_library = getattr(application_controller, "open_gallery_with_image", None)
        if callable(open_library):
            open_library(image_path)

    def _on_open_library(self) -> None:
        response = getattr(self.controller, "last_response", None)
        if response and response.image_path:
            app = self.winfo_toplevel()
            application_controller = getattr(app, "application_controller", None)
            open_library = getattr(application_controller, "open_gallery_with_image", None)
            if callable(open_library):
                open_library(response.image_path)

    def _on_open_review(self) -> None:
        response = getattr(self.controller, "last_response", None)
        if response and response.image_path:
            app = self.winfo_toplevel()
            application_controller = getattr(app, "application_controller", None)
            open_review = getattr(application_controller, "open_compare_with_output", None)
            if callable(open_review):
                open_review(response.image_path)

    def _on_save_as(self) -> None:
        response = getattr(self.controller, "last_response", None)
        if response and response.image_path:
            from tkinter import filedialog
            import shutil
            initial_name = Path(response.image_path).name
            dest = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png")],
                initialfile=initial_name
            )
            if dest:
                try:
                    shutil.copy(response.image_path, dest)
                    print(f"Saved image to: {dest}")
                except Exception as e:
                    print(f"Failed to save image copy: {e}")

    def _enable_action_buttons(self, enable: bool) -> None:
        state = "normal" if enable else "disabled"
        # Phoenix theme accent color for enabled buttons
        fg_color = PHOENIX_THEME.accent if enable else PHOENIX_THEME.text_muted
        
        self.btn_open_library.configure(state=state, fg=fg_color)
        self.btn_open_review.configure(state=state, fg=fg_color)
        self.btn_save_as.configure(state=state, fg=fg_color)

    # ==================================================================
    # REFRESH
    # ==================================================================

    def refresh(self) -> None:
        # Reload repository data from disk so it stays in sync with Model Manager installs/uninstalls
        if hasattr(self.controller, "repository") and self.controller.repository is not None:
            self.controller.repository.load_repository()

        state = self.controller.get_state()
        if not self._generation_running:
            self.status_label.configure(text=f"Status: {state.status}")

        active_backend_name = "None"
        queued_count = 0

        gen_ctrl = getattr(self.controller, "generation_controller", None)
        if gen_ctrl is not None:
            queued_count = gen_ctrl.queue.get_queued_count()
            active_backend = gen_ctrl.backend_manager.get_active_backend()
            if active_backend is not None:
                active_backend_name = active_backend.get_backend_name()

        # Check if the active model in the single source of truth changed
        active_model_id = self.controller.repository.get_active_model_id()
        if active_model_id and self.model_var.get() != active_model_id:
            self.model_var.set(active_model_id)
            state = self.controller.get_state()

        # Update Inspector – Generation Status
        self.insp_model.configure(text=state.selected_model if state.selected_model else "-")
        self.insp_backend.configure(text=active_backend_name)
        if not self._generation_running:
            self.insp_gen_status.configure(text=state.status)
        self.insp_queue.configure(text=f"{queued_count} Job(s)")

        # Update Inspector – Generation Information
        self.insp_size.configure(text=f"{state.width} × {state.height}")
        self.insp_steps.configure(text=str(state.steps))
        self.insp_cfg.configure(text=str(state.cfg))
        self.insp_seed.configure(text=str(state.seed))
        self.insp_sampler.configure(text=self.sampler_var.get())
        self.insp_scheduler.configure(text=self.scheduler_var.get())

        # Update Status Bar
        self.model_status_label.configure(text=f"Modell: {state.selected_model if state.selected_model else '-'}")
        self.backend_status_label.configure(text=f"Backend: {active_backend_name}")
        self.queue_status_label.configure(text=f"Queue: {queued_count} Job(s)")

        # Update environment diagnostics status labels (Sprint P-061)
        env_text = "Environment: -"
        qnn_text = "QNN: -"
        if gen_ctrl is not None and getattr(gen_ctrl, "backend_manager", None) is not None:
            res = gen_ctrl.backend_manager.get_discovery_result()
            if res:
                env_text = f"Environment: {res.os_name} {res.architecture}"
                qnn_text = f"QNN: {'Gefunden' if res.qnn_sdk_found else 'Nicht gefunden'}"

        self.env_status_label.configure(text=env_text)
        self.qnn_status_label.configure(text=qnn_text)

        # Update Preview Area based on last response
        for widget in self.preview_center.winfo_children():
            widget.destroy()

        last_resp = getattr(self.controller, "last_response", None)
        has_preview = False
        if last_resp and last_resp.success and last_resp.image_path:
            img_path = Path(last_resp.image_path)
            if img_path.exists():
                try:
                    from PIL import Image, ImageTk
                    with Image.open(img_path) as pil_img:
                        pil_img.thumbnail((250, 250))
                        self._preview_photo = ImageTk.PhotoImage(pil_img)
                        
                    img_label = tk.Label(self.preview_center, image=self._preview_photo, bg=PHOENIX_THEME.content_bg)
                    img_label.pack(anchor="center")
                    has_preview = True
                except Exception as e:
                    logger.error(f"Failed to load preview image: {e}")
                    print(f"Failed to load preview image: {e}")

        if not has_preview:
            from resources.icons import IconManager
            tk.Label(
                self.preview_center, text=IconManager.get_symbol("image"),
                bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.accent,
                font=(PHOENIX_THEME.font_title[0], 20, "bold"),
            ).pack(anchor="center", pady=(0, 2))

            tk.Label(
                self.preview_center, text="No image generated",
                bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_small, justify="center"
            ).pack(anchor="center")

        # Enable/Disable Action Buttons
        self._enable_action_buttons(has_preview)

    def _on_model_changed(self, *args) -> None:
        """Trace callback when the model variable is updated in the UI."""
        new_model = self.model_var.get()
        if hasattr(self, "seed_entry"):
            self._apply_generation_contract(new_model)

        try:
            prompt = self.prompt_text.get("1.0", "end-1c")
            neg_prompt = self.neg_prompt_text.get("1.0", "end-1c")
            seed = int(self.seed_entry.get().strip() or -1)
            steps = int(self.steps_scale.get())
            cfg = float(self.cfg_scale.get())
            width = int(self.width_var.get() or 512)
            height = int(self.height_var.get() or 512)
            sampler = self.sampler_var.get()
            scheduler = self.scheduler_var.get()
            batch_size = int(self.batch_var.get() or 1)
        except Exception:
            prompt, neg_prompt = "", ""
            seed, steps, cfg, width, height = -1, 20, 7.5, 512, 512
            sampler, scheduler, batch_size = "Euler", "Euler", 1

        self.controller.update_parameters(
            prompt=prompt, negative_prompt=neg_prompt,
            seed=seed, steps=steps, cfg=cfg,
            width=width, height=height, selected_model=new_model,
            sampler=sampler, scheduler=scheduler, batch_size=batch_size,
        )

    def _show_prompt_history_popup(self) -> None:
        """Display the persistent prompt history popup menu under the history button."""
        history = self.controller.load_prompt_history()
        if not history:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Verlauf leer", state="disabled")
            menu.configure(
                bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body, relief="flat", bd=1,
            )
            x = self.history_btn.winfo_rootx()
            y = self.history_btn.winfo_rooty() + self.history_btn.winfo_height()
            menu.post(x, y)
            return

        menu = tk.Menu(self, tearoff=0)
        menu.configure(
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
            font=PHOENIX_THEME.font_body, relief="flat", bd=1,
        )

        for prompt in history:
            display_label = prompt if len(prompt) < 50 else prompt[:47] + "..."
            menu.add_command(
                label=display_label,
                command=lambda p=prompt: self._load_prompt_from_history(p)
            )

        x = self.history_btn.winfo_rootx()
        y = self.history_btn.winfo_rooty() + self.history_btn.winfo_height()
        menu.post(x, y)

    def _load_prompt_from_history(self, prompt: str) -> None:
        """Load a selected prompt into the input field."""
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", prompt)
        if hasattr(self, "_prompt_popup_text") and self._prompt_popup_text.winfo_exists():
            self._prompt_popup_text.delete("1.0", "end")
            self._prompt_popup_text.insert("1.0", prompt)

    def _ensure_progress_style(self) -> None:
        """Sustainably ensure the custom Phoenix progress bar style is active and correctly colored."""
        style = ttk.Style(self)
        style.configure(
            "Phoenix.Horizontal.TProgressbar",
            troughcolor=PHOENIX_THEME.elevated_bg,
            background=PHOENIX_THEME.success,
            lightcolor=PHOENIX_THEME.success,
            darkcolor=PHOENIX_THEME.success,
            bordercolor=PHOENIX_THEME.border,
        )
        elements = set(style.element_names())
        if "Phoenix.Horizontal.Progressbar.trough" not in elements:
            try:
                style.element_create(
                    "Phoenix.Horizontal.Progressbar.trough",
                    "from",
                    "clam",
                    "Horizontal.Progressbar.trough",
                )
            except Exception:
                pass
        if "Phoenix.Horizontal.Progressbar.pbar" not in elements:
            try:
                style.element_create(
                    "Phoenix.Horizontal.Progressbar.pbar",
                    "from",
                    "clam",
                    "Horizontal.Progressbar.pbar",
                )
            except Exception:
                pass

        style.layout(
            "Phoenix.Horizontal.TProgressbar",
            [
                (
                    "Phoenix.Horizontal.Progressbar.trough",
                    {
                        "sticky": "nswe",
                        "children": [
                            (
                                "Phoenix.Horizontal.Progressbar.pbar",
                                {"side": "left", "sticky": "ns"},
                            )
                        ],
                    },
                )
            ],
        )

    def _show_templates_popup(self) -> None:
        """Display a hierarchical popup menu with prompt templates categories and presets."""
        categories = self.controller.load_prompt_templates()
        if not categories:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Keine Vorlagen gefunden", state="disabled")
            menu.configure(
                bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body, relief="flat", bd=1,
            )
            x = self.templates_btn.winfo_rootx()
            y = self.templates_btn.winfo_rooty() + self.templates_btn.winfo_height()
            menu.post(x, y)
            return

        menu = tk.Menu(self, tearoff=0)
        menu.configure(
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
            font=PHOENIX_THEME.font_body, relief="flat", bd=1,
        )

        order = ["Portrait", "Landschaft", "Architektur", "Fantasy", "Sci-Fi", "Produktfoto"]
        available_categories = list(categories.keys())

        sorted_categories = []
        for cat in order:
            if cat in available_categories:
                sorted_categories.append(cat)
                available_categories.remove(cat)
        sorted_categories.extend(available_categories)

        self._submenus = []

        for category_name in sorted_categories:
            presets = categories[category_name]
            if not presets:
                continue

            sub_menu = tk.Menu(menu, tearoff=0)
            sub_menu.configure(
                bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
                activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
                font=PHOENIX_THEME.font_body, relief="flat", bd=1,
            )
            self._submenus.append(sub_menu)

            for preset in presets:
                name = preset.get("name", "Preset")
                prompt = preset.get("prompt", "")
                sub_menu.add_command(
                    label=name,
                    command=lambda p=prompt: self._load_template_prompt(p)
                )

            menu.add_cascade(label=category_name, menu=sub_menu)

        x = self.templates_btn.winfo_rootx()
        y = self.templates_btn.winfo_rooty() + self.templates_btn.winfo_height()
        menu.post(x, y)

    def _load_template_prompt(self, prompt: str) -> None:
        """Load a prompt template into the input field."""
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", prompt)
        if hasattr(self, "_prompt_popup_text") and self._prompt_popup_text.winfo_exists():
            self._prompt_popup_text.delete("1.0", "end")
            self._prompt_popup_text.insert("1.0", prompt)

    def _select_steps_preset(self, preset_name: str) -> None:
        """Select a steps preset and update the steps scale value and UI colors."""
        self.active_steps_preset = preset_name

        # Default maps (both SD1.5 and SD2.1 use: Schnell=10, Standard=20, Beste Qualität=30)
        val = 20
        if preset_name == "Schnell":
            val = 10
        elif preset_name == "Standard":
            val = 20
        elif preset_name == "Beste Qualität":
            val = 30

        self.steps_scale.set(val)
        self._update_steps_preset_colors()

    def _update_steps_preset_colors(self) -> None:
        """Update background and foreground colors of the steps preset buttons based on active selection."""
        presets = {
            "Schnell": self.btn_preset_schnell,
            "Standard": self.btn_preset_standard,
            "Beste Qualität": self.btn_preset_beste,
        }
        for name, btn in presets.items():
            if self.active_steps_preset == name:
                btn.configure(
                    bg=PHOENIX_THEME.accent,
                    fg=PHOENIX_THEME.text_on_accent,
                    activebackground=PHOENIX_THEME.accent,
                    activeforeground=PHOENIX_THEME.text_on_accent,
                )
            else:
                btn.configure(
                    bg=PHOENIX_THEME.elevated_bg,
                    fg=PHOENIX_THEME.text_secondary,
                    activebackground=PHOENIX_THEME.elevated_bg,
                    activeforeground=PHOENIX_THEME.text_primary,
                )

    def _open_advanced_settings_popup(self) -> None:
        """Open a modal/non-modal popup for advanced settings."""
        if hasattr(self, "_advanced_popup") and self._advanced_popup.winfo_exists():
            self._advanced_popup.focus()
            return

        popup = tk.Toplevel(self)
        popup.title("Erweiterte Einstellungen")
        popup.geometry("380x520")
        popup.configure(bg=PHOENIX_THEME.card_bg)
        popup.resizable(False, False)
        self._advanced_popup = popup

        # Center the popup relative to main window
        try:
            x = self.winfo_rootx() + (self.winfo_width() - 380) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 520) // 2
            popup.geometry(f"+{x}+{y}")
        except Exception:
            pass

        # Scrollable container inside popup to ensure everything fits perfectly
        container = tk.Frame(popup, bg=PHOENIX_THEME.card_bg)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Get active model contract
        contract = self.controller.select_model(self.model_var.get())
        if not contract:
            contract = {}

        # ── Group: Image Size ─────────────────────────
        tk.Label(container, text="Image Size", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_card_title, anchor="w").pack(fill="x", pady=(0, 4))

        size_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        size_frame.pack(fill="x", pady=(0, 12))
        size_frame.grid_columnconfigure(0, weight=0)
        size_frame.grid_columnconfigure(1, weight=1)
        size_frame.grid_columnconfigure(2, weight=0)
        size_frame.grid_columnconfigure(3, weight=1)

        popup_width_label = tk.Label(size_frame, text="Breite:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        popup_width_menu = tk.OptionMenu(size_frame, self.width_var, "256", "512", "768", "1024")
        popup_width_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        popup_width_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)

        popup_height_label = tk.Label(size_frame, text="Höhe:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        popup_height_menu = tk.OptionMenu(size_frame, self.height_var, "256", "512", "768", "1024")
        popup_height_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        popup_height_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)

        # Build Locked Resolution View inside popup
        from resources.icons import IconManager
        popup_locked_res_frame = tk.Frame(size_frame, bg=PHOENIX_THEME.card_bg)
        popup_locked_res_frame.grid_columnconfigure(0, weight=1)
        popup_locked_res_frame.grid_columnconfigure(1, weight=1)

        popup_res_512_btn = tk.Button(
            popup_locked_res_frame, text="512 × 512",
            bg=PHOENIX_THEME.accent, fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat", bd=0, font=PHOENIX_THEME.font_button, state="normal", padx=10, pady=8
        )
        popup_res_512_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(4, 4))

        lock_symbol = IconManager.get_symbol("lock")
        popup_res_1024_btn = tk.Button(
            popup_locked_res_frame, text=f"{lock_symbol} 1024 × 1024 (Demnächst)",
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_disabled,
            activebackground=PHOENIX_THEME.elevated_bg, activeforeground=PHOENIX_THEME.text_disabled,
            relief="flat", bd=0, font=PHOENIX_THEME.font_button, state="disabled",
            disabledforeground=PHOENIX_THEME.text_disabled, padx=10, pady=8
        )
        popup_res_1024_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(4, 4))

        popup_locked_hint_lbl = tk.Label(
            popup_locked_res_frame, text="Höhere Auflösungen benötigen ein kompatibles Qualcomm-Modell.",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_caption,
            anchor="w", justify="left", wraplength=340
        )
        popup_locked_hint_lbl.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        # Show either locked resolution or width/height dropdowns
        if contract.get("resolution_locked") is True:
            popup_width_label.grid_remove()
            popup_width_menu.grid_remove()
            popup_height_label.grid_remove()
            popup_height_menu.grid_remove()
            popup_locked_res_frame.grid(row=0, column=0, columnspan=4, sticky="ew")
        else:
            popup_locked_res_frame.grid_remove()
            popup_width_label.grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
            popup_width_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)
            popup_height_label.grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
            popup_height_menu.grid(row=0, column=3, sticky="ew", pady=2)

            # Configure options in width/height dropdowns
            self._configure_option_contract(popup_width_menu, self.width_var, contract.get("width", {}))
            self._configure_option_contract(popup_height_menu, self.height_var, contract.get("height", {}))

        # ── Group: Sampling ───────────────────────────
        tk.Label(container, text="Sampling", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_card_title, anchor="w").pack(fill="x", pady=(10, 4))

        sampling_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        sampling_frame.pack(fill="x", pady=(0, 12))
        sampling_frame.grid_columnconfigure(0, weight=1)

        # CFG Scale Slider
        tk.Label(sampling_frame, text="CFG Scale:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 1))
        popup_cfg_scale = tk.Scale(
            sampling_frame, from_=1.0, to=20.0, resolution=0.5, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            width=12, variable=self.cfg_var
        )
        popup_cfg_scale.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        # Configure CFG from contract
        cfg_spec = contract.get("cfg", {})
        cfg_options = {}
        if "min" in cfg_spec:
            cfg_options["from_"] = cfg_spec["min"]
        if "max" in cfg_spec:
            cfg_options["to"] = cfg_spec["max"]
        if "resolution" in cfg_spec:
            cfg_options["resolution"] = cfg_spec["resolution"]
        if cfg_options:
            popup_cfg_scale.configure(**cfg_options)

        # Sampler & Scheduler
        dropdown_frame = tk.Frame(sampling_frame, bg=PHOENIX_THEME.card_bg)
        dropdown_frame.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        dropdown_frame.grid_columnconfigure(0, weight=0)
        dropdown_frame.grid_columnconfigure(1, weight=1)
        dropdown_frame.grid_columnconfigure(2, weight=0)
        dropdown_frame.grid_columnconfigure(3, weight=1)

        tk.Label(dropdown_frame, text="Sampler:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        popup_sampler_menu = tk.OptionMenu(dropdown_frame, self.sampler_var, "Euler a", "Euler", "DPM++ 2M", "DDIM", "LMS")
        popup_sampler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        popup_sampler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        popup_sampler_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        tk.Label(dropdown_frame, text="Sched.:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        popup_scheduler_menu = tk.OptionMenu(dropdown_frame, self.scheduler_var, "Normal", "Karras", "Exponential", "SGM Uniform")
        popup_scheduler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        popup_scheduler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        popup_scheduler_menu.grid(row=0, column=3, sticky="ew", pady=2)

        # Configure Sampler & Scheduler from contract
        self._configure_option_contract(popup_sampler_menu, self.sampler_var, contract.get("sampler", {}))
        self._configure_option_contract(popup_scheduler_menu, self.scheduler_var, contract.get("scheduler", {}))

        # ── Group: Output ─────────────────────────────
        tk.Label(container, text="Output", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_card_title, anchor="w").pack(fill="x", pady=(10, 4))

        output_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        output_frame.pack(fill="x", pady=(0, 12))
        output_frame.grid_columnconfigure(0, weight=0)
        output_frame.grid_columnconfigure(1, weight=1)
        output_frame.grid_columnconfigure(2, weight=0)
        output_frame.grid_columnconfigure(3, weight=1)

        tk.Label(output_frame, text="Seed:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        popup_seed_entry = tk.Entry(
            output_frame, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body,
            textvariable=self.seed_var
        )
        popup_seed_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        tk.Label(output_frame, text="Batch:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        popup_batch_menu = tk.OptionMenu(output_frame, self.batch_var, "1", "2", "4", "8")
        popup_batch_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        popup_batch_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        popup_batch_menu.grid(row=0, column=3, sticky="ew", pady=2)

        # OK button to close
        close_btn = tk.Button(
            container, text="Schließen", bg=PHOENIX_THEME.accent, fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat", bd=0, font=PHOENIX_THEME.font_button, cursor="hand2", padx=16, pady=8,
            command=popup.destroy
        )
        close_btn.pack(pady=(16, 0))

    def _open_expandable_prompt_popup(self) -> None:
        """Open a large prompt editor popup (ca. 80% of main window size)."""
        if hasattr(self, "_prompt_popup") and self._prompt_popup.winfo_exists():
            self._prompt_popup.focus()
            return

        popup = tk.Toplevel(self)
        popup.title("Großer Prompt-Editor")
        popup.configure(bg=PHOENIX_THEME.card_bg)
        self._prompt_popup = popup

        # Calculate dimensions: 80% of main window
        try:
            main_w = self.winfo_toplevel().winfo_width()
            main_h = self.winfo_toplevel().winfo_height()
            width = int(main_w * 0.8) if main_w > 200 else 1120
            height = int(main_h * 0.8) if main_h > 200 else 720
            x = self.winfo_toplevel().winfo_rootx() + (main_w - width) // 2
            y = self.winfo_toplevel().winfo_rooty() + (main_h - height) // 2
            popup.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            popup.geometry("1120x720")

        # Container
        container = tk.Frame(popup, bg=PHOENIX_THEME.card_bg)
        container.pack(fill="both", expand=True, padx=24, pady=24)

        # Header with title & shortcut reminder
        header_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        header_frame.pack(fill="x", pady=(0, 12))

        tk.Label(
            header_frame, text="Großer Prompt-Editor",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title, anchor="w"
        ).pack(side="left")

        tk.Label(
            header_frame, text="(ESC zum Schließen & Übernehmen)",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption, anchor="e"
        ).pack(side="right")

        # Text widget container with Scrollbar
        text_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        text_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(text_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        popup_text = tk.Text(
            text_frame, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body, wrap="word",
            padx=16, pady=16, yscrollcommand=scrollbar.set
        )
        popup_text.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=popup_text.yview)
        self._prompt_popup_text = popup_text

        # Populate initial content
        initial_text = self.prompt_text.get("1.0", "end-1c")
        popup_text.insert("1.0", initial_text)
        popup_text.focus_set()

        # Live Prompt Counter Label in Popup
        self.popup_counter_lbl = tk.Label(
            container,
            text="Zeichen: 0 | Wörter: 0",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="e"
        )
        self.popup_counter_lbl.pack(fill="x", pady=(4, 0))

        # Real-time synchronization
        popup_text.bind("<KeyRelease>", lambda e: self._sync_popup_prompt_to_main())
        self._update_prompt_counters()

        # OK button to close
        btn_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        btn_frame.pack(fill="x", pady=(16, 0))

        close_btn = tk.Button(
            btn_frame, text="Schließen & Übernehmen", bg=PHOENIX_THEME.accent, fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat", bd=0, font=PHOENIX_THEME.font_button, cursor="hand2", padx=20, pady=10,
            command=popup.destroy
        )
        close_btn.pack(anchor="center")

        # Bind ESC key to close
        popup.bind("<Escape>", lambda e: popup.destroy())

    def _sync_popup_prompt_to_main(self) -> None:
        """Synchronize text from popup editor to main prompt field."""
        if hasattr(self, "_prompt_popup_text") and self._prompt_popup_text.winfo_exists():
            content = self._prompt_popup_text.get("1.0", "end-1c")
            self.prompt_text.delete("1.0", "end")
            self.prompt_text.insert("1.0", content)
            self._update_prompt_counters()

    def _sync_main_prompt_to_popup(self) -> None:
        """Synchronize text from main prompt field to popup editor."""
        if hasattr(self, "_prompt_popup_text") and self._prompt_popup_text.winfo_exists():
            content = self.prompt_text.get("1.0", "end-1c")
            self._prompt_popup_text.delete("1.0", "end")
            self._prompt_popup_text.insert("1.0", content)
            self._update_prompt_counters()

    def _on_main_prompt_key(self) -> None:
        """Key release handler for the main prompt text box."""
        self._sync_main_prompt_to_popup()
        self._update_prompt_counters()

    def _update_prompt_counters(self) -> None:
        """Update character and word counts in both the main view and the popup if open."""
        content = self.prompt_text.get("1.0", "end-1c")
        char_count = len(content)
        word_count = len(content.split())
        counter_text = f"Zeichen: {char_count} | Wörter: {word_count}"

        if hasattr(self, "prompt_counter_lbl"):
            self.prompt_counter_lbl.configure(text=counter_text)

        if hasattr(self, "popup_counter_lbl") and hasattr(self, "_prompt_popup") and self._prompt_popup.winfo_exists():
            self.popup_counter_lbl.configure(text=counter_text)
