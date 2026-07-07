from __future__ import annotations

import tkinter as tk

from controllers.prompt_workspace_controller import PromptWorkspaceController
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixPromptView(WorkspaceFrame):
    """UI view for the Prompt / AI Image Generation Workspace."""

    def __init__(self, master: tk.Misc, controller: PromptWorkspaceController | None = None) -> None:
        super().__init__(
            master,
            "AI Image Generation",
            "Bilder mittels Text-Prompts lokal auf der Snapdragon NPU generieren",
            has_inspector=True
        )
        self.controller = controller or PromptWorkspaceController()

        self._build_input_area()
        self._build_preview_area()
        self._build_details_area()
        self._build_status_bar()
        self.refresh()

    def _build_input_area(self) -> None:
        # Outer Card Frame
        self.input_card = tk.Frame(
            self.content_slot,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1
        )
        self.input_card.grid(row=0, column=0, sticky="nsew", padx=PHOENIX_THEME.space_sm, pady=PHOENIX_THEME.space_sm)
        self.input_card.grid_columnconfigure(0, weight=1)
        self.input_card.grid_columnconfigure(1, weight=1)

        r = 0

        # 1. Model Dropdown
        tk.Label(
            self.input_card,
            text="KI-Modell:",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w"
        ).grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 4))
        r += 1

        active_model_id = self.controller.repository.get_active_model_id()
        default_model = active_model_id if active_model_id in self.controller.AVAILABLE_MODELS else self.controller.AVAILABLE_MODELS[0]
        self.model_var = tk.StringVar(value=default_model)
        self.model_var.trace_add("write", self._on_model_changed)
        model_dropdown = tk.OptionMenu(
            self.input_card,
            self.model_var,
            *self.controller.AVAILABLE_MODELS
        )
        model_dropdown.configure(
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=PHOENIX_THEME.font_button,
        )
        model_dropdown["menu"].configure(
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            font=PHOENIX_THEME.font_body,
            relief="flat",
            bd=0,
        )
        model_dropdown.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))
        r += 1

        # 2. Prompt Text Field
        tk.Label(
            self.input_card,
            text="Prompt (Bildbeschreibung):",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w"
        ).grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 4))
        r += 1

        self.prompt_text = tk.Text(
            self.input_card,
            height=4,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border,
            highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1,
            relief="flat",
            font=PHOENIX_THEME.font_body,
            wrap="word"
        )
        self.prompt_text.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))
        self.prompt_text.insert("1.0", "A futuristic cyberpunk cityscape, neon lights, high resolution, highly detailed")
        r += 1

        # 3. Negative Prompt Text Field
        tk.Label(
            self.input_card,
            text="Negativer Prompt (Ausschließen):",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w"
        ).grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 4))
        r += 1

        self.neg_prompt_text = tk.Text(
            self.input_card,
            height=2,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border,
            highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1,
            relief="flat",
            font=PHOENIX_THEME.font_body,
            wrap="word"
        )
        self.neg_prompt_text.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 16))
        self.neg_prompt_text.insert("1.0", "blurry, low quality, distorted, extra limbs, bad anatomy")
        r += 1

        # 4. Grid for Seed, Steps, CFG, Size parameters
        params_frame = tk.Frame(self.input_card, bg=PHOENIX_THEME.card_bg)
        params_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 16))
        params_frame.grid_columnconfigure(0, weight=1)
        params_frame.grid_columnconfigure(1, weight=1)

        # CFG Scale
        tk.Label(params_frame, text="CFG Scale:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.cfg_scale = tk.Scale(
            params_frame,
            from_=1.0,
            to=20.0,
            resolution=0.5,
            orient="horizontal",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            highlightthickness=0,
            font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent,
            troughcolor=PHOENIX_THEME.elevated_bg
        )
        self.cfg_scale.set(7.0)
        self.cfg_scale.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 8))

        # Steps
        tk.Label(params_frame, text="Steps (Schritte):", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=1, sticky="w", pady=(0, 2))
        self.steps_scale = tk.Scale(
            params_frame,
            from_=1,
            to=100,
            orient="horizontal",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            highlightthickness=0,
            font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent,
            troughcolor=PHOENIX_THEME.elevated_bg
        )
        self.steps_scale.set(20)
        self.steps_scale.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 8))

        # Width
        tk.Label(params_frame, text="Breite:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=2, column=0, sticky="w", pady=(4, 2))
        self.width_var = tk.StringVar(value="512")
        width_menu = tk.OptionMenu(params_frame, self.width_var, "256", "512", "768", "1024")
        width_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        width_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        width_menu.grid(row=3, column=0, sticky="ew", padx=(0, 8), pady=(0, 8))

        # Height
        tk.Label(params_frame, text="Höhe:", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=2, column=1, sticky="w", pady=(4, 2))
        self.height_var = tk.StringVar(value="512")
        height_menu = tk.OptionMenu(params_frame, self.height_var, "256", "512", "768", "1024")
        height_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        height_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        height_menu.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(0, 8))

        # Seed
        tk.Label(params_frame, text="Seed (-1 für Zufall):", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=4, column=0, sticky="w", pady=(4, 2))
        self.seed_entry = tk.Entry(
            params_frame,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border,
            highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1,
            relief="flat",
            font=PHOENIX_THEME.font_body
        )
        self.seed_entry.insert(0, "-1")
        self.seed_entry.grid(row=5, column=0, sticky="ew", padx=(0, 8), pady=(0, 8))
        r += 1

        # 5. Generate Button
        self.gen_btn = tk.Button(
            self.input_card,
            text="BILD GENERIEREN",
            command=self._on_generate,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=16,
            pady=10
        )
        self.gen_btn.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 16))

    def _build_preview_area(self) -> None:
        if self.inspector_slot is None:
            return

        # Outer Preview Card
        self.preview_card = tk.Frame(
            self.inspector_slot,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1
        )
        self.preview_card.grid(row=0, column=0, sticky="nsew", padx=PHOENIX_THEME.space_sm, pady=PHOENIX_THEME.space_sm)
        self.preview_card.grid_columnconfigure(0, weight=1)
        self.preview_card.grid_rowconfigure(1, weight=1)
        self.preview_card.grid_rowconfigure(2, weight=0)

        # Title
        tk.Label(
            self.preview_card,
            text="Generierungsvorschau",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        # Inner Preview Frame
        preview_inner = tk.Frame(
            self.preview_card,
            bg=PHOENIX_THEME.content_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1
        )
        preview_inner.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        preview_inner.grid_columnconfigure(0, weight=1)
        preview_inner.grid_rowconfigure(0, weight=1)

        # Center contents
        center_container = tk.Frame(preview_inner, bg=PHOENIX_THEME.content_bg)
        center_container.grid(row=0, column=0, sticky="")

        from resources.icons import IconManager
        tk.Label(
            center_container,
            text=IconManager.get_symbol("image"),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.accent,
            font=(PHOENIX_THEME.font_title[0], 48, "bold"),
        ).pack(anchor="center", pady=(0, 12))

        tk.Label(
            center_container,
            text="AI-Vorschau ausstehend",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
        ).pack(anchor="center", pady=(0, 4))

        tk.Label(
            center_container,
            text="Stelle die Parameter links ein und klicke auf „Bild generieren“.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            wraplength=280,
            justify="center"
        ).pack(anchor="center")

        # Queue Info Label
        self.queue_info_label = tk.Label(
            self.preview_card,
            text="Queue: 0 Jobs",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="e"
        )
        self.queue_info_label.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 16))

    def _build_details_area(self) -> None:
        if self.inspector_slot is None:
            return

        self.inspector_slot.grid_rowconfigure(0, weight=1)
        self.inspector_slot.grid_rowconfigure(1, weight=0)

        # Details Card
        self.details_card = tk.Frame(
            self.inspector_slot,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1
        )
        self.details_card.grid(row=1, column=0, sticky="ew", padx=PHOENIX_THEME.space_sm, pady=(0, PHOENIX_THEME.space_sm))
        self.details_card.grid_columnconfigure(0, weight=0)
        self.details_card.grid_columnconfigure(1, weight=1)

        # Title
        tk.Label(
            self.details_card,
            text="Generierungsinformationen",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w"
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))

        labels = [
            ("Generation Engine:", 1),
            ("Backend:", 2),
            ("Version:", 3),
            ("Status:", 4),
            ("Model:", 5)
        ]

        for text, r_idx in labels:
            tk.Label(
                self.details_card,
                text=text,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_small,
                anchor="w"
            ).grid(row=r_idx, column=0, sticky="w", padx=(16, 8), pady=4)

        self.engine_val = tk.Label(self.details_card, text="Stub Backend", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_body, anchor="w")
        self.engine_val.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=4)

        self.backend_val = tk.Label(self.details_card, text="CPU (Stub)", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_body, anchor="w")
        self.backend_val.grid(row=2, column=1, sticky="w", padx=(0, 16), pady=4)

        self.version_val = tk.Label(self.details_card, text="0.1", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_body, anchor="w")
        self.version_val.grid(row=3, column=1, sticky="w", padx=(0, 16), pady=4)

        self.status_val = tk.Label(self.details_card, text="Ready", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_body, anchor="w")
        self.status_val.grid(row=4, column=1, sticky="w", padx=(0, 16), pady=4)

        self.model_val_lbl = tk.Label(self.details_card, text="None", bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_body, anchor="w")
        self.model_val_lbl.grid(row=5, column=1, sticky="w", padx=(0, 16), pady=(4, 16))

    def _build_status_bar(self) -> None:
        self.status_bar_frame = tk.Frame(
            self.status_slot,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1
        )
        self.status_bar_frame.grid(row=0, column=0, sticky="ew")

        self.status_label = tk.Label(
            self.status_bar_frame,
            text="Status: Bereit",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            padx=16,
            pady=8
        )
        self.status_label.pack(side="left")

        self.model_status_label = tk.Label(
            self.status_bar_frame,
            text="Modell: -",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            padx=16,
            pady=8
        )
        self.model_status_label.pack(side="left")

        self.backend_status_label = tk.Label(
            self.status_bar_frame,
            text="Backend: -",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            padx=16,
            pady=8
        )
        self.backend_status_label.pack(side="left")

        self.env_status_label = tk.Label(
            self.status_bar_frame,
            text="Environment: -",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            padx=16,
            pady=8
        )
        self.env_status_label.pack(side="left")

        self.qnn_status_label = tk.Label(
            self.status_bar_frame,
            text="QNN: -",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            padx=16,
            pady=8
        )
        self.qnn_status_label.pack(side="left")

        self.queue_status_label = tk.Label(
            self.status_bar_frame,
            text="Queue: 0 Job(s)",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            padx=16,
            pady=8
        )
        self.queue_status_label.pack(side="right")

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
            prompt=prompt,
            negative_prompt=neg_prompt,
            seed=seed,
            steps=steps,
            cfg=cfg,
            width=width,
            height=height,
            selected_model=selected_model,
        )

        self.controller.generate_image()
        self.refresh()

    def refresh(self) -> None:
        state = self.controller.get_state()
        self.status_label.configure(text=f"Status: {state.status}")

        active_backend_name = "None"
        queued_count = 0

        gen_ctrl = getattr(self.controller, "generation_controller", None)
        if gen_ctrl is not None:
            queued_count = gen_ctrl.queue.get_queued_count()
            if queued_count == 1:
                self.queue_info_label.configure(text="Queue: 1 Job")
            else:
                self.queue_info_label.configure(text=f"Queue: {queued_count} Jobs")

            active_backend = gen_ctrl.backend_manager.get_active_backend()
            if active_backend is not None:
                active_backend_name = active_backend.get_backend_name()
                self.engine_val.configure(text="Stub Backend")
                self.backend_val.configure(text=active_backend_name)
                self.version_val.configure(text=active_backend.get_backend_version())
            else:
                self.engine_val.configure(text="Keine Engine")
                self.backend_val.configure(text="None")
                self.version_val.configure(text="-")
        else:
            self.queue_info_label.configure(text="Queue: 0 Jobs")
            self.engine_val.configure(text="Keine Engine")
            self.backend_val.configure(text="None")
            self.version_val.configure(text="-")

        # Check if the active model in the single source of truth changed
        active_model_id = self.controller.repository.get_active_model_id()
        if active_model_id and self.model_var.get() != active_model_id:
            self.model_var.set(active_model_id)
            state = self.controller.get_state()

        self.status_val.configure(text=state.status)
        self.model_val_lbl.configure(text=state.selected_model if state.selected_model else "None")

        # Update the extended status bar labels (Sprint UX-002)
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
        
        # Pull parameters from UI to update controller/session state
        try:
            prompt = self.prompt_text.get("1.0", "end-1c")
            neg_prompt = self.neg_prompt_text.get("1.0", "end-1c")
            seed = int(self.seed_var.get() or 0)
            steps = int(self.steps_var.get() or 20)
            cfg = float(self.cfg_var.get() or 7.0)
            width = int(self.width_var.get() or 512)
            height = int(self.height_var.get() or 512)
        except Exception:
            prompt, neg_prompt = "", ""
            seed, steps, cfg, width, height = 0, 20, 7.0, 512, 512

        self.controller.update_parameters(
            prompt=prompt,
            negative_prompt=neg_prompt,
            seed=seed,
            steps=steps,
            cfg=cfg,
            width=width,
            height=height,
            selected_model=new_model,
        )
