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

        # ── Fixed Generate Button (always visible) ────
        self.gen_btn = tk.Button(
            self.input_card,
            text="BILD GENERIEREN",
            command=self._on_generate,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat", bd=0,
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=16, pady=6
        )
        self.gen_btn.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 6))

    def _build_parameters(self) -> None:
        """Build all parameter groups inside the scrollable param_content frame."""
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
        r = self._section_header(p, "Prompt", r)

        tk.Label(
            p, text="Prompt (Bildbeschreibung):", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(2, 1))
        r += 1

        self.prompt_text = tk.Text(
            p, height=3, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body, wrap="word"
        )
        self.prompt_text.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        self.prompt_text.insert("1.0", "A futuristic cyberpunk cityscape, neon lights, high resolution, highly detailed")
        r += 1

        tk.Label(
            p, text="Negativer Prompt (Ausschließen):", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(2, 1))
        r += 1

        self.neg_prompt_text = tk.Text(
            p, height=1, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body, wrap="word"
        )
        self.neg_prompt_text.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        self.neg_prompt_text.insert("1.0", "blurry, low quality, distorted, extra limbs, bad anatomy")
        r += 1

        # ── Group: Image Size ─────────────────────────
        r = self._section_header(p, "Image Size", r)

        size_frame = tk.Frame(p, bg=PHOENIX_THEME.card_bg)
        size_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        size_frame.grid_columnconfigure(0, weight=0)
        size_frame.grid_columnconfigure(1, weight=1)
        size_frame.grid_columnconfigure(2, weight=0)
        size_frame.grid_columnconfigure(3, weight=1)

        tk.Label(size_frame, text="Breite:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        self.width_var = tk.StringVar(value="512")
        self.width_menu = tk.OptionMenu(size_frame, self.width_var, "256", "512", "768", "1024")
        self.width_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.width_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.width_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        tk.Label(size_frame, text="Höhe:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        self.height_var = tk.StringVar(value="512")
        self.height_menu = tk.OptionMenu(size_frame, self.height_var, "256", "512", "768", "1024")
        self.height_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.height_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.height_menu.grid(row=0, column=3, sticky="ew", pady=2)
        r += 1

        # ── Group: Sampling ───────────────────────────
        r = self._section_header(p, "Sampling", r)

        sampling_frame = tk.Frame(p, bg=PHOENIX_THEME.card_bg)
        sampling_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        sampling_frame.grid_columnconfigure(0, weight=1)
        sampling_frame.grid_columnconfigure(1, weight=1)

        tk.Label(sampling_frame, text="CFG Scale:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 1))
        self.cfg_scale = tk.Scale(
            sampling_frame, from_=1.0, to=20.0, resolution=0.5, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            width=12
        )
        self.cfg_scale.set(7.0)
        self.cfg_scale.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 2))

        tk.Label(sampling_frame, text="Steps:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=1, sticky="w", pady=(0, 1))
        self.steps_scale = tk.Scale(
            sampling_frame, from_=1, to=100, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            width=12
        )
        self.steps_scale.set(20)
        self.steps_scale.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 2))

        dropdown_frame = tk.Frame(sampling_frame, bg=PHOENIX_THEME.card_bg)
        dropdown_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        dropdown_frame.grid_columnconfigure(0, weight=0)
        dropdown_frame.grid_columnconfigure(1, weight=1)
        dropdown_frame.grid_columnconfigure(2, weight=0)
        dropdown_frame.grid_columnconfigure(3, weight=1)

        tk.Label(dropdown_frame, text="Sampler:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        self.sampler_var = tk.StringVar(value="Euler a")
        self.sampler_menu = tk.OptionMenu(dropdown_frame, self.sampler_var, "Euler a", "Euler", "DPM++ 2M", "DDIM", "LMS")
        self.sampler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.sampler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.sampler_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        tk.Label(dropdown_frame, text="Sched.:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        self.scheduler_var = tk.StringVar(value="Normal")
        self.scheduler_menu = tk.OptionMenu(dropdown_frame, self.scheduler_var, "Normal", "Karras", "Exponential", "SGM Uniform")
        self.scheduler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.scheduler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.scheduler_menu.grid(row=0, column=3, sticky="ew", pady=2)
        r += 1

        # ── Group: Output ─────────────────────────────
        r = self._section_header(p, "Output", r)

        output_frame = tk.Frame(p, bg=PHOENIX_THEME.card_bg)
        output_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        output_frame.grid_columnconfigure(0, weight=0)
        output_frame.grid_columnconfigure(1, weight=1)
        output_frame.grid_columnconfigure(2, weight=0)
        output_frame.grid_columnconfigure(3, weight=1)

        tk.Label(output_frame, text="Seed:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        self.seed_entry = tk.Entry(
            output_frame, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body
        )
        self.seed_entry.insert(0, "-1")
        self.seed_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        tk.Label(output_frame, text="Batch:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        self.batch_var = tk.StringVar(value="1")
        batch_menu = tk.OptionMenu(output_frame, self.batch_var, "1", "2", "4", "8")
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
        contract = self.controller.get_generation_parameters(model_id)
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

        seed_spec = contract.get("seed")
        if isinstance(seed_spec, dict) and "default" in seed_spec:
            self.seed_entry.delete(0, "end")
            self.seed_entry.insert(0, str(seed_spec["default"]))

    def _section_header(self, parent: tk.Frame, title: str, row: int) -> int:
        """Create a subtle section divider label and return the next row index."""
        tk.Label(
            parent, text=title, bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title, anchor="w"
        ).grid(row=row, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 1))
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
        self.progress_bar = ttk.Progressbar(
            self.insp_content, variable=self.progress_var, maximum=100, mode="determinate"
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
        self._set_progress(100, "Fertig" if result.success else "Fehler", self._step_text())
        self._set_generation_busy(False)

        if result.success:
            self._append_generation_diagnostic(result, "before_finish_callback")
            self._notify_generation_finished(result)
            self._append_generation_diagnostic(result, "after_finish_callback")
            self._append_generation_diagnostic(result, "before_gallery_open_callback")
            self._show_generated_output_in_library(result.image_path)
            self._append_generation_diagnostic(result, "after_gallery_open_callback")
        else:
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
        state = "disabled" if busy else "normal"
        self.gen_btn.configure(state=state)
        status_text = "Generierung läuft" if busy else self.controller.get_state().status
        self._configure_if_alive(self.status_label, text=f"Status: {status_text}")
        self._configure_if_alive(self.insp_gen_status, text=status_text)

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
        self.controller.repository.set_active_model_id(new_model)

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
            seed, steps, cfg, width, height = -1, 20, 7.0, 512, 512
            sampler, scheduler, batch_size = "Euler a", "Normal", 1

        self.controller.update_parameters(
            prompt=prompt, negative_prompt=neg_prompt,
            seed=seed, steps=steps, cfg=cfg,
            width=width, height=height, selected_model=new_model,
            sampler=sampler, scheduler=scheduler, batch_size=batch_size,
        )
