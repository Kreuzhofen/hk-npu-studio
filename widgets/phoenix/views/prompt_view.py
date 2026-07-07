from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from controllers.prompt_workspace_controller import PromptWorkspaceController
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME


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
        width_menu = tk.OptionMenu(size_frame, self.width_var, "256", "512", "768", "1024")
        width_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        width_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        width_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        tk.Label(size_frame, text="Höhe:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        self.height_var = tk.StringVar(value="512")
        height_menu = tk.OptionMenu(size_frame, self.height_var, "256", "512", "768", "1024")
        height_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        height_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        height_menu.grid(row=0, column=3, sticky="ew", pady=2)
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
        sampler_menu = tk.OptionMenu(dropdown_frame, self.sampler_var, "Euler a", "Euler", "DPM++ 2M", "DDIM", "LMS")
        sampler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        sampler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        sampler_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        tk.Label(dropdown_frame, text="Sched.:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        self.scheduler_var = tk.StringVar(value="Normal")
        scheduler_menu = tk.OptionMenu(dropdown_frame, self.scheduler_var, "Normal", "Karras", "Exponential", "SGM Uniform")
        scheduler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        scheduler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        scheduler_menu.grid(row=0, column=3, sticky="ew", pady=2)
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

        preview_center = tk.Frame(preview_frame, bg=PHOENIX_THEME.content_bg)
        preview_center.grid(row=0, column=0, sticky="", pady=8)

        from resources.icons import IconManager
        tk.Label(
            preview_center, text=IconManager.get_symbol("image"),
            bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.accent,
            font=(PHOENIX_THEME.font_title[0], 20, "bold"),
        ).pack(anchor="center", pady=(0, 2))

        tk.Label(
            preview_center, text="No image generated",
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

        tk.Button(btn_frame, text="Open in Library", **btn_style).grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        tk.Button(btn_frame, text="Open in Review", **btn_style).grid(row=0, column=1, sticky="ew", padx=1, pady=1)
        tk.Button(btn_frame, text="Save As", **btn_style).grid(row=0, column=2, sticky="ew", padx=1, pady=1)

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

        self.controller.update_parameters(
            prompt=prompt, negative_prompt=neg_prompt,
            seed=seed, steps=steps, cfg=cfg,
            width=width, height=height, selected_model=selected_model,
        )

        self.controller.generate_image()
        self.refresh()

    # ==================================================================
    # REFRESH
    # ==================================================================

    def refresh(self) -> None:
        # Reload repository data from disk so it stays in sync with Model Manager installs/uninstalls
        if hasattr(self.controller, "repository") and self.controller.repository is not None:
            self.controller.repository.load_repository()

        state = self.controller.get_state()
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

    def _on_model_changed(self, *args) -> None:
        """Trace callback when the model variable is updated in the UI."""
        new_model = self.model_var.get()
        self.controller.repository.set_active_model_id(new_model)

        try:
            prompt = self.prompt_text.get("1.0", "end-1c")
            neg_prompt = self.neg_prompt_text.get("1.0", "end-1c")
            seed = int(self.seed_entry.get().strip() or -1)
            steps = int(self.steps_scale.get())
            cfg = float(self.cfg_scale.get())
            width = int(self.width_var.get() or 512)
            height = int(self.height_var.get() or 512)
        except Exception:
            prompt, neg_prompt = "", ""
            seed, steps, cfg, width, height = -1, 20, 7.0, 512, 512

        self.controller.update_parameters(
            prompt=prompt, negative_prompt=neg_prompt,
            seed=seed, steps=steps, cfg=cfg,
            width=width, height=height, selected_model=new_model,
        )
