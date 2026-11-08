from __future__ import annotations

import shutil
import time
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from config import OUTPUT_DIR, TEMP_DIR
from controllers.inpainting_controller import InpaintingController
from controllers.prompt_edit_controller import (
    IntentCategory,
    PromptEditController,
    PromptEditPlan,
    PromptEditResult,
)
from app.i18n import tr
from engine.brand_manager import BrandManager
from engine.material_priming import (
    MATERIAL_PRESETS,
    get_material_preset,
    prime_material_chrominance,
)
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.inpainting_canvas import PhoenixInpaintingCanvas
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixInpaintingView(WorkspaceFrame):
    """Phoenix Image Lab: SD 1.5 NPU generative fill & inpainting on Qualcomm Hexagon HTP."""

    def __init__(
        self,
        master: tk.Misc,
        controller: InpaintingController | None = None,
        on_navigate: Callable[[str], None] | None = None,
        output_dir: Path | str | None = None,
        temp_dir: Path | str | None = None,
    ) -> None:
        super().__init__(
            master,
            title=tr("image_lab_editor_title", "Generatives Füllen & Retusche"),
            subtitle=tr(
                "image_lab_editor_subtitle",
                "Generatives Füllen mit Stable Diffusion 1.5 auf Qualcomm Hexagon NPU",
            ),
        )
        self.controller = controller or InpaintingController(ui_dispatch=lambda callback: self.after(0, callback))
        self.prompt_edit_controller = PromptEditController(
            inpainting_controller=self.controller,
            ui_dispatch=lambda callback: self.after(0, callback),
        )
        self.current_prompt_plan: PromptEditPlan | None = None
        self.prompt_edit_var = tk.StringVar(value="")
        self.on_navigate = on_navigate
        self.output_dir: Path = Path(output_dir) if output_dir is not None else OUTPUT_DIR
        self.temp_dir: Path = Path(temp_dir) if temp_dir is not None else (TEMP_DIR / "image_lab")
        self.input_path: Path | None = None
        self.result_path: Path | None = None
        self.material_preset_var = tk.StringVar(value="none")
        self.material_intensity_var = tk.IntVar(value=100)
        self._material_popup: tk.Toplevel | None = None
        self._build_canvas()
        self._build_inspector()
        self._build_status()

    def _build_canvas(self) -> None:
        toolbar = tk.Frame(self.header.toolbar_slot, bg=PHOENIX_THEME.content_bg)
        self.toolbar = toolbar
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
        self.load_button = PhoenixButton(
            toolbar, text=tr("load_image", "Bild laden"), command=self._load_image, button_type="neutral",
            icon_name="load_image", icon_color=PHOENIX_THEME.warning,
            font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        self.remove_button = PhoenixButton(
            toolbar, text=tr("inpainting_remove_image", "Bild entfernen"), command=self._remove_image, button_type="neutral",
            icon_name="remove_image", font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        self.brush_button = PhoenixButton(
            toolbar, text=tr("inpainting_brush", "Pinsel"), command=lambda: self._select_tool(False), button_type="nav_active",
            icon_name="sparkles",
            font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        self.eraser_button = PhoenixButton(
            toolbar, text=tr("inpainting_eraser", "Radierer"), command=lambda: self._select_tool(True), button_type="neutral",
            icon_name="remove_image",
            font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        self.clear_button = PhoenixButton(
            toolbar, text=tr("clear_mask", "Maske löschen"), command=self._clear_mask, button_type="neutral",
            icon_name="delete", icon_color=PHOENIX_THEME.danger,
            font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        self.undo_button = PhoenixButton(
            toolbar, text=tr("undo", "Rückgängig"), command=lambda: self.canvas.undo(), button_type="neutral",
            icon_name="back", font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        brush_controls = tk.Frame(self.header.toolbar_slot, bg=PHOENIX_THEME.content_bg)
        brush_controls.grid(row=1, column=0, sticky="w", pady=PHOENIX_THEME.space_xs)
        tk.Label(brush_controls, text=tr("inpainting_brush_size", "Pinselgröße"), bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.text_secondary).pack(side="left")
        self.brush_size = tk.IntVar(value=48)
        self.brush_size_scale = tk.Scale(
            brush_controls, from_=8, to=160, orient="horizontal", variable=self.brush_size,
            command=self._on_brush_size_change,
            bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.text_secondary,
            troughcolor=PHOENIX_THEME.card_bg, highlightthickness=0, length=140, showvalue=False,
        )
        self.brush_size_scale.pack(side="left", padx=PHOENIX_THEME.space_sm)
        tk.Label(
            brush_controls, textvariable=self.brush_size, bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, width=3, anchor="w",
        ).pack(side="left")

        # Separator
        tk.Label(
            brush_controls, text="  |  ", bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.border,
        ).pack(side="left", padx=PHOENIX_THEME.space_xs)

        # Brush Hardness 0–100%
        tk.Label(
            brush_controls, text=tr("inpainting_brush_hardness", "Härte"), bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.text_secondary,
        ).pack(side="left")
        self.brush_hardness = tk.IntVar(value=100)
        self.hardness_display_var = tk.StringVar(value="100%")
        self.hardness_scale = tk.Scale(
            brush_controls, from_=0, to=100, orient="horizontal", variable=self.brush_hardness,
            command=self._on_brush_hardness_change,
            bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.text_secondary,
            troughcolor=PHOENIX_THEME.card_bg, highlightthickness=0, length=120, showvalue=False,
        )
        self.hardness_scale.pack(side="left", padx=PHOENIX_THEME.space_sm)
        tk.Label(
            brush_controls, textvariable=self.hardness_display_var, bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, width=5, anchor="w",
        ).pack(side="left")
        self._toolbar_items = (
            self.overview_button,
            self.load_button, self.remove_button, self.brush_button, self.eraser_button,
            self.undo_button, self.clear_button,
        )
        toolbar.bind("<Configure>", lambda event: self._reflow(toolbar, self._toolbar_items, event.width))
        self._reflow(toolbar, self._toolbar_items, 0)

        self.content_slot.grid_rowconfigure(0, weight=0)
        self.content_slot.grid_rowconfigure(1, weight=1)
        self.content_slot.grid_columnconfigure(0, weight=1)

        self._build_prompt_edit_bar(self.content_slot)

        self.canvas = PhoenixInpaintingCanvas(self.content_slot)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.on_point_selected = self._on_point_selected
        self.canvas.on_negative_point_selected = self._on_negative_point_selected
        self.point_prompt: tuple[int, int] | None = None

    def _build_prompt_edit_bar(self, parent: tk.Misc) -> None:
        """Build compact Prompt-Edit bar directly embedded above inpainting canvas."""
        bar_card = tk.Frame(parent, bg=PHOENIX_THEME.card_bg, padx=12, pady=8)
        bar_card.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 6))
        self.prompt_edit_bar = bar_card

        # Top row: Prompt Input & Action Buttons
        top_row = tk.Frame(bar_card, bg=PHOENIX_THEME.card_bg)
        top_row.pack(fill="x")
        top_row.grid_columnconfigure(1, weight=1)

        lbl = tk.Label(
            top_row,
            text="✨ " + tr("prompt_edit_title", "Prompt-Edit:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        lbl.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.prompt_edit_entry = tk.Entry(
            top_row,
            textvariable=self.prompt_edit_var,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            relief="flat",
            font=PHOENIX_THEME.font_body,
        )
        self.prompt_edit_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.prompt_edit_entry.bind("<Return>", lambda _event: self._on_analyze_prompt())

        self.prompt_edit_point_btn = PhoenixButton(
            top_row,
            text=tr("prompt_edit_point_btn", "📍 Klick-Auswahl"),
            command=self._on_toggle_point_select,
            button_type="neutral",
            font=PHOENIX_THEME.font_small,
            height=30,
            radius=6,
        )
        self.prompt_edit_point_btn.grid(row=0, column=2, padx=(0, 4))

        self.prompt_edit_analyze_btn = PhoenixButton(
            top_row,
            text=tr("prompt_edit_analyze", "Analysieren"),
            command=self._on_analyze_prompt,
            button_type="neutral",
            icon_name="sparkles",
            font=PHOENIX_THEME.font_small,
            height=30,
            radius=6,
        )
        self.prompt_edit_analyze_btn.grid(row=0, column=3, padx=(0, 4))

        self.prompt_edit_preview_btn = PhoenixButton(
            top_row,
            text=tr("prompt_edit_preview", "Vorschau"),
            command=self._on_toggle_preview,
            button_type="neutral",
            font=PHOENIX_THEME.font_small,
            height=30,
            radius=6,
        )
        self.prompt_edit_preview_btn.grid(row=0, column=4, padx=2)

        self.prompt_edit_compare_btn = PhoenixButton(
            top_row,
            text=tr("prompt_edit_compare", "Vorher/Nachher"),
            command=self._on_toggle_compare,
            button_type="neutral",
            font=PHOENIX_THEME.font_small,
            height=30,
            radius=6,
        )
        self.prompt_edit_compare_btn.grid(row=0, column=5, padx=2)

        self.prompt_edit_exec_btn = PhoenixButton(
            top_row,
            text=tr("prompt_edit_execute", "Ausführen (HTP)"),
            command=self._on_execute_prompt_edit,
            button_type="primary",
            icon_name="start",
            font=PHOENIX_THEME.font_small,
            height=30,
            radius=6,
        )
        self.prompt_edit_exec_btn.grid(row=0, column=6, padx=(2, 4))

        self.prompt_edit_reset_btn = PhoenixButton(
            top_row,
            text=tr("prompt_edit_reset", "Zurücksetzen"),
            command=self._on_reset_prompt_edit,
            button_type="neutral",
            font=PHOENIX_THEME.font_small,
            height=30,
            radius=6,
        )
        self.prompt_edit_reset_btn.grid(row=0, column=7, padx=(2, 0))

        # Bottom row: Intent Status Badge & Canvas Mode Indicator
        bot_row = tk.Frame(bar_card, bg=PHOENIX_THEME.card_bg)
        bot_row.pack(fill="x", pady=(4, 0))
        bot_row.grid_columnconfigure(0, weight=1)

        self.prompt_edit_badge = tk.Label(
            bot_row,
            text=tr("prompt_edit_idle_badge", "Geben Sie einen Bearbeitungsauftrag ein (z. B. „Verwandle den Apfel in 24k Gold“)"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        self.prompt_edit_badge.grid(row=0, column=0, sticky="w")

        self.prompt_edit_mode_label = tk.Label(
            bot_row,
            text=tr("prompt_edit_mode_original", "Canvas: Original"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="e",
        )
        self.prompt_edit_mode_label.grid(row=0, column=1, sticky="e", padx=(8, 0))

    def _build_inspector(self) -> None:
        host = self.inspector_slot
        host.grid_rowconfigure(0, weight=1)
        host.grid_columnconfigure(0, weight=1)
        scroll = tk.Canvas(host, width=300, bg=PHOENIX_THEME.card_bg, highlightthickness=0)
        bar = ttk.Scrollbar(host, orient="vertical", command=scroll.yview, style="Phoenix.Vertical.TScrollbar")
        scroll.grid(row=0, column=0, sticky="nsew")
        bar.grid(row=0, column=1, sticky="ns")
        scroll.configure(yscrollcommand=bar.set)
        panel = tk.Frame(scroll, bg=PHOENIX_THEME.card_bg)
        window = scroll.create_window((0, 0), window=panel, anchor="nw")
        panel.bind("<Configure>", lambda _event: scroll.configure(scrollregion=scroll.bbox("all")))
        scroll.bind("<Configure>", lambda event: scroll.itemconfigure(window, width=event.width))

        self.model_badge = tk.Label(
            panel,
            text="SD 1.5 NPU",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        )
        self.model_badge.pack(fill="x", padx=16, pady=(16, 4))

        self._label(panel, "Prompt").pack(fill="x", padx=16, pady=(8, 4))
        self.prompt = tk.Text(
            panel, height=7, wrap="word", bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary, insertbackground=PHOENIX_THEME.text_primary,
            relief="flat", font=PHOENIX_THEME.font_body,
        )
        self.prompt.pack(fill="x", padx=16)

        self._label(panel, tr("inpainting_negative_prompt", "Negativer Prompt")).pack(fill="x", padx=16, pady=(10, 4))
        self.negative_prompt = tk.Text(
            panel, height=3, wrap="word", bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary, insertbackground=PHOENIX_THEME.text_primary,
            relief="flat", font=PHOENIX_THEME.font_body,
        )
        self.negative_prompt.pack(fill="x", padx=16)
        steps_header = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        steps_header.pack(fill="x", padx=16, pady=(14, 2))
        self._label(steps_header, "Steps").pack(side="left")
        self.steps = tk.IntVar(value=20)
        self.steps_spin = tk.Spinbox(
            steps_header,
            from_=10,
            to=50,
            textvariable=self.steps,
            width=5,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            buttonbackground=PHOENIX_THEME.card_bg,
            relief="flat",
            font=PHOENIX_THEME.font_small,
        )
        self.steps_spin.pack(side="right")

        self.steps_scale = tk.Scale(
            panel,
            from_=10,
            to=50,
            orient="horizontal",
            variable=self.steps,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            highlightthickness=0,
            font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent,
            troughcolor=PHOENIX_THEME.elevated_bg,
            showvalue=False,
        )
        self.steps_scale.pack(fill="x", padx=16, pady=(0, 4))

        cfg_header = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        cfg_header.pack(fill="x", padx=16, pady=(14, 2))
        self._label(cfg_header, tr("inpainting_cfg_label", "Texttreue (CFG Scale)")).pack(side="left")
        self.cfg_var = tk.DoubleVar(value=7.5)
        self.cfg_spin = tk.Spinbox(
            cfg_header,
            from_=1.0,
            to=15.0,
            increment=0.5,
            format="%.1f",
            textvariable=self.cfg_var,
            width=5,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            buttonbackground=PHOENIX_THEME.card_bg,
            relief="flat",
            font=PHOENIX_THEME.font_small,
            command=self._on_slider_manual_change,
        )
        self.cfg_spin.pack(side="right")

        self.cfg_scale = tk.Scale(
            panel,
            from_=1.0,
            to=15.0,
            resolution=0.5,
            orient="horizontal",
            variable=self.cfg_var,
            command=lambda _val: self._on_slider_manual_change(),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            highlightthickness=0,
            font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent,
            troughcolor=PHOENIX_THEME.elevated_bg,
            showvalue=False,
        )
        self.cfg_scale.pack(fill="x", padx=16, pady=(0, 4))
        self.cfg_scale_slider = self.cfg_scale

        strength_header = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        strength_header.pack(fill="x", padx=16, pady=(14, 2))
        self._label(strength_header, tr("inpainting_strength_label", "Stärke (Denoising)")).pack(side="left")
        self.strength_var = tk.DoubleVar(value=1.0)
        self.strength_spin = tk.Spinbox(
            strength_header,
            from_=0.1,
            to=1.0,
            increment=0.05,
            format="%.2f",
            textvariable=self.strength_var,
            width=5,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            buttonbackground=PHOENIX_THEME.card_bg,
            relief="flat",
            font=PHOENIX_THEME.font_small,
            command=self._on_slider_manual_change,
        )
        self.strength_spin.pack(side="right")

        self.strength_scale = tk.Scale(
            panel,
            from_=0.1,
            to=1.0,
            resolution=0.05,
            orient="horizontal",
            variable=self.strength_var,
            command=lambda _val: self._on_slider_manual_change(),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            highlightthickness=0,
            font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent,
            troughcolor=PHOENIX_THEME.elevated_bg,
            showvalue=False,
        )
        self.strength_scale.pack(fill="x", padx=16, pady=(0, 4))
        self.strength_scale_slider = self.strength_scale
        self._label(panel, "Seed").pack(fill="x", padx=16, pady=(14, 4))
        self.seed = tk.StringVar(value="20260830")
        tk.Entry(panel, textvariable=self.seed, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat").pack(fill="x", padx=16)

        # Modus-Presets: Hinzufügen (5/0), Ersetzen (6/2), Entfernen (8/3)
        self._label(panel, tr("inpainting_presets_title", "Presets")).pack(fill="x", padx=16, pady=(16, 6))
        preset_frame = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        preset_frame.pack(fill="x", padx=16, pady=(0, 4))
        preset_frame.grid_columnconfigure(0, weight=1)
        preset_frame.grid_columnconfigure(1, weight=1)
        preset_frame.grid_columnconfigure(2, weight=1)

        self.preset_add_button = PhoenixButton(
            preset_frame,
            text=tr("preset_add", "Hinzufügen"),
            command=lambda: self._apply_preset("add"),
            button_type="nav_active",
            font=PHOENIX_THEME.font_small,
            height=28,
            radius=6,
        )
        self.preset_add_button.grid(row=0, column=0, sticky="ew", padx=(0, 2))

        self.preset_replace_button = PhoenixButton(
            preset_frame,
            text=tr("preset_replace", "Ersetzen"),
            command=lambda: self._apply_preset("replace"),
            button_type="neutral",
            font=PHOENIX_THEME.font_small,
            height=28,
            radius=6,
        )
        self.preset_replace_button.grid(row=0, column=1, sticky="ew", padx=2)

        self.preset_remove_button = PhoenixButton(
            preset_frame,
            text=tr("preset_remove", "Entfernen"),
            command=lambda: self._apply_preset("remove"),
            button_type="neutral",
            font=PHOENIX_THEME.font_small,
            height=28,
            radius=6,
        )
        self.preset_remove_button.grid(row=0, column=2, sticky="ew", padx=(2, 0))

        self.preset_buttons = {
            "add": self.preset_add_button,
            "replace": self.preset_replace_button,
            "remove": self.preset_remove_button,
        }
        self.active_preset: str | None = "add"
        self._updating_preset = False

        # Feathering (Kantenglättung) 0–15 px, Standard 5
        feather_header = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        feather_header.pack(fill="x", padx=16, pady=(14, 2))
        self._label(feather_header, tr("inpainting_feather_label", "Kantenglättung (px)")).pack(side="left")
        self.feather_radius = tk.IntVar(value=5)
        self.feather_spin = tk.Spinbox(
            feather_header,
            from_=0,
            to=15,
            textvariable=self.feather_radius,
            width=5,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            buttonbackground=PHOENIX_THEME.card_bg,
            relief="flat",
            font=PHOENIX_THEME.font_small,
            command=self._on_slider_manual_change,
        )
        self.feather_spin.pack(side="right")

        self.feather_scale = tk.Scale(
            panel,
            from_=0,
            to=15,
            orient="horizontal",
            variable=self.feather_radius,
            command=lambda _val: self._on_slider_manual_change(),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            highlightthickness=0,
            font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent,
            troughcolor=PHOENIX_THEME.elevated_bg,
            showvalue=False,
        )
        self.feather_scale.pack(fill="x", padx=16, pady=(0, 4))

        # Dilatation (Maskenausdehnung) 0–8 px, Standard 0
        dilate_header = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        dilate_header.pack(fill="x", padx=16, pady=(14, 2))
        self._label(dilate_header, tr("inpainting_dilate_label", "Maskenausdehnung (px)")).pack(side="left")
        self.dilate_pixels = tk.IntVar(value=0)
        self.dilate_spin = tk.Spinbox(
            dilate_header,
            from_=0,
            to=8,
            textvariable=self.dilate_pixels,
            width=5,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            buttonbackground=PHOENIX_THEME.card_bg,
            relief="flat",
            font=PHOENIX_THEME.font_small,
            command=self._on_slider_manual_change,
        )
        self.dilate_spin.pack(side="right")

        self.dilate_scale = tk.Scale(
            panel,
            from_=0,
            to=8,
            orient="horizontal",
            variable=self.dilate_pixels,
            command=lambda _val: self._on_slider_manual_change(),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            highlightthickness=0,
            font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent,
            troughcolor=PHOENIX_THEME.elevated_bg,
            showvalue=False,
        )
        self.dilate_scale.pack(fill="x", padx=16, pady=(0, 8))

        # Phoenix Material Lab Section
        material_header = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        material_header.pack(fill="x", padx=16, pady=(14, 2))
        self._label(material_header, tr("material_lab_section_title", "Phoenix Material Lab")).pack(side="left")

        self.material_status_label = tk.Label(
            material_header,
            text=tr("material_none_status", "Deaktiviert"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
        )
        self.material_status_label.pack(side="right")

        material_btn_frame = tk.Frame(panel, bg=PHOENIX_THEME.card_bg)
        material_btn_frame.pack(fill="x", padx=16, pady=(0, 8))
        material_btn_frame.grid_columnconfigure(0, weight=1)
        material_btn_frame.grid_columnconfigure(1, weight=0)

        self.material_popup_btn = PhoenixButton(
            material_btn_frame,
            text=tr("material_select_button", "Material auswählen..."),
            command=self._open_material_lab_popup,
            button_type="neutral",
            icon_name="sparkles",
            font=PHOENIX_THEME.font_small,
            height=30,
            radius=6,
        )
        self.material_popup_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.material_reset_btn = PhoenixButton(
            material_btn_frame,
            text="✕",
            command=self._reset_material_preset,
            button_type="neutral",
            font=PHOENIX_THEME.font_small,
            height=30,
            width=30,
            radius=6,
        )
        self.material_reset_btn.grid(row=0, column=1, sticky="e")

        buttons = tk.Frame(host, bg=PHOENIX_THEME.card_bg)
        buttons.grid(row=1, column=0, columnspan=2, sticky="ew", pady=PHOENIX_THEME.space_sm)
        self.start_button = PhoenixButton(
            buttons, text=tr("inpainting_start", "Start"), command=self._start, button_type="primary",
            icon_name="start", height=34, radius=8,
        )
        self.cancel_button = PhoenixButton(
            buttons, text=tr("cancel", "Abbrechen"), command=self.controller.cancel, button_type="danger",
            icon_name="stop", height=34, radius=8,
        )
        self.save_button = PhoenixButton(
            buttons, text=tr("inpainting_save", "Speichern"), command=self._save_result, button_type="secondary",
            icon_name="save", height=34, radius=8,
        )
        actions = (self.start_button, self.cancel_button, self.save_button)
        self.action_buttons = actions
        self.action_bar = buttons
        # Reserve the natural three-button width for the normal inspector.
        scroll.configure(width=sum(button.winfo_reqwidth() + 2 * PHOENIX_THEME.space_xs for button in actions))
        buttons.bind("<Configure>", lambda event: self._reflow(buttons, actions, event.width))
        self._reflow(buttons, actions, 0)

    @staticmethod
    def _reflow(host, items, width: int) -> None:
        # Same Configure/grid pattern as the generation toolbar; use font-sized
        # widget requests rather than fixed pixel thresholds at high DPI.
        gap = PHOENIX_THEME.space_xs
        widths = [item.winfo_reqwidth() + 2 * gap for item in items]
        columns = 1
        for candidate in range(len(items), 1, -1):
            required = sum(max(widths[column::candidate]) for column in range(candidate))
            if required <= width:
                columns = candidate
                break
        for column in range(len(items)):
            host.grid_columnconfigure(column, weight=0)
        for index, item in enumerate(items):
            item.grid(row=index // columns, column=index % columns, sticky="w", padx=gap, pady=gap)

    def _build_status(self) -> None:
        self.status_text = tk.StringVar(value="Bereit")
        tk.Label(
            self.status_slot, textvariable=self.status_text, bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_secondary, anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        self.progress = ttk.Progressbar(self.status_slot, maximum=1.0, style="Phoenix.Horizontal.TProgressbar")
        self.progress.grid(row=1, column=0, sticky="ew", pady=(4, 0))

    @staticmethod
    def _label(master: tk.Misc, text: str) -> tk.Label:
        return tk.Label(master, text=text, bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, anchor="w")

    def _load_image(self) -> None:
        selected = filedialog.askopenfilename(filetypes=(("Bilddateien", "*.png *.jpg *.jpeg *.webp *.bmp"),))
        if selected:
            self.input_path = Path(selected)
            self.result_path = None
            self.current_prompt_plan = None
            self.point_prompt = None
            if hasattr(self, "canvas") and self.canvas is not None:
                self.canvas.clear_point_prompt()
            if hasattr(self, "prompt_edit_badge"):
                self.prompt_edit_badge.configure(
                    text=tr("prompt_edit_idle_badge", "Geben Sie einen Bearbeitungsauftrag ein (z. B. „Verwandle den Apfel in 24k Gold“)"),
                    fg=PHOENIX_THEME.text_muted,
                )
            if hasattr(self, "prompt_edit_mode_label"):
                self.prompt_edit_mode_label.configure(
                    text=tr("prompt_edit_mode_original", "Canvas: Original"),
                    fg=PHOENIX_THEME.text_secondary,
                )
            self.canvas.load_image(selected)

    def _clear_mask(self) -> None:
        self.canvas.clear_mask()

    def _remove_image(self) -> None:
        self.input_path = self.result_path = None
        self._on_reset_prompt_edit()
        self.canvas.remove_image()
        self.status_text.set("Bereit")
        self.progress.configure(value=0.0)

    def _apply_preset(self, preset_name: str) -> None:
        """
        Apply preset for Feathering, Dilation and CFG.
        - Hinzufügen (add): 5 / 0 / 7.5
        - Ersetzen (replace): 6 / 2 / 8.5
        - Entfernen (remove): 8 / 3 / 5.0
        Steps, Seed and Prompts remain strictly untouched.
        """
        preset_values = {
            "add": (5, 0, 7.5),
            "replace": (6, 2, 8.5),
            "remove": (8, 3, 5.0),
        }
        if preset_name not in preset_values:
            return
        feather, dilate, cfg = preset_values[preset_name]
        self._updating_preset = True
        try:
            self.feather_radius.set(feather)
            self.dilate_pixels.set(dilate)
            self.cfg_var.set(cfg)
            if hasattr(self, "strength_var"):
                self.strength_var.set(1.0)
        finally:
            self._updating_preset = False

        self.active_preset = preset_name
        self._update_preset_button_states()

    def _on_slider_manual_change(self) -> None:
        """Called when feather, dilate or cfg slider/spinbox is modified manually."""
        if getattr(self, "_updating_preset", False):
            return
        try:
            cur_feather = self.feather_radius.get()
            cur_dilate = self.dilate_pixels.get()
            cur_cfg = round(float(self.cfg_var.get()), 1)
            cur_strength = round(float(self.strength_var.get()), 2) if hasattr(self, "strength_var") else 1.0
        except (tk.TclError, ValueError):
            return

        preset_values = {
            "add": (5, 0, 7.5, 1.0),
            "replace": (6, 2, 8.5, 1.0),
            "remove": (8, 3, 5.0, 1.0),
        }
        matched = None
        for name, vals in preset_values.items():
            if (cur_feather, cur_dilate, cur_cfg, cur_strength) == vals:
                matched = name
                break
        self.active_preset = matched
        self._update_preset_button_states()

    def _update_preset_button_states(self) -> None:
        """Update button_type on preset buttons according to self.active_preset."""
        for name, button in getattr(self, "preset_buttons", {}).items():
            if name == self.active_preset:
                button.configure(button_type="nav_active")
            else:
                button.configure(button_type="neutral")

    def _on_brush_size_change(self, value: str) -> None:
        if hasattr(self, "canvas") and self.canvas is not None:
            self.canvas.set_brush_size(int(float(value)))

    def _on_brush_hardness_change(self, value: str) -> None:
        val = int(float(value))
        if hasattr(self, "canvas") and self.canvas is not None:
            self.canvas.set_brush_hardness(val / 100.0)
        if hasattr(self, "hardness_display_var"):
            self.hardness_display_var.set(f"{val}%")

    def _select_tool(self, erase: bool) -> None:
        self.canvas.set_tool(erase)
        if hasattr(self, "prompt_edit_point_btn"):
            self.prompt_edit_point_btn.configure(button_type="neutral")
        self.brush_button.configure(button_type="neutral" if erase else "nav_active")
        self.eraser_button.configure(button_type="nav_active" if erase else "neutral")

    def _start(self) -> None:
        if self.input_path is None:
            messagebox.showerror("Phoenix Image Lab", "Bitte zuerst ein Bild laden.")
            return
        prompt = self.prompt.get("1.0", "end").strip()
        if not prompt:
            messagebox.showerror("Phoenix Image Lab", "Bitte einen Prompt eingeben.")
            return
        negative_prompt = ""
        if hasattr(self, "negative_prompt"):
            negative_prompt = self.negative_prompt.get("1.0", "end").strip()
        mask_path = self.temp_dir / "inpainting_mask.png"
        output_path = self.output_dir / f"generative_fill_{time.time_ns()}.png"
        mask_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.canvas.save_mask(mask_path)
        mat_preset = self.material_preset_var.get()
        if mat_preset == "none" or not mat_preset:
            mat_preset_arg = None
        else:
            mat_preset_arg = mat_preset

        mat_intensity_arg = float(self.material_intensity_var.get()) / 100.0

        self.controller.start(
            input_image_path=self.input_path,
            mask_image_path=mask_path,
            prompt=prompt,
            output_path=output_path,
            steps=self.steps.get(),
            seed=int(self.seed.get()),
            negative_prompt=negative_prompt,
            cfg_scale=float(self.cfg_var.get()),
            denoising_strength=float(self.strength_var.get()) if hasattr(self, "strength_var") else 1.0,
            feather_radius=self.feather_radius.get(),
            dilate_pixels=self.dilate_pixels.get(),
            material_preset=mat_preset_arg,
            material_priming_intensity=mat_intensity_arg,
            on_progress=self._on_progress,
            on_complete=self._on_complete,
        )

    def _on_progress(self, phase: str, value: float, detail: str | None) -> None:
        self.progress.configure(value=value)
        phase_labels = {
            "prepare": "Vorbereitung",
            "vae_encode": "VAE-Vorbereitung",
            "setup_htp": "NPU-Initialisierung",
            "text_encode": "Text-Enkodierung",
            "denoise": "Denoising",
            "denoising": "Denoising",
            "vae_decode": "VAE-Dekodierung",
            "composite": "Fertigstellung",
        }
        prefix = phase_labels.get(phase, phase.capitalize())
        if detail:
            self.status_text.set(f"{prefix}: {detail}")
        else:
            self.status_text.set(prefix)

    def _on_complete(self, result) -> None:
        if self.input_path is None:
            return
        if result.success and result.output_path:
            self.result_path = Path(result.output_path)
            self.canvas.set_result(self.result_path)
            self.status_text.set("Abgeschlossen")
        else:
            self.status_text.set(f"{result.error_code}: {result.error_message}")

    def _on_back_to_overview(self) -> None:
        if callable(getattr(self, "on_navigate", None)):
            self.on_navigate("overview")
            return
        parent = getattr(self, "master", None)
        while parent is not None:
            if hasattr(parent, "select_subview") and callable(parent.select_subview):
                parent.select_subview("overview")
                return
            parent = getattr(parent, "master", None)

    def _save_result(self) -> None:
        if self.result_path is None:
            return
        selected = filedialog.asksaveasfilename(defaultextension=".png", filetypes=(("PNG", "*.png"),))
        if selected:
            shutil.copy2(self.result_path, selected)

    def _open_material_lab_popup(self) -> None:
        if hasattr(self, "_material_popup") and self._material_popup and self._material_popup.winfo_exists():
            self._material_popup.focus()
            return

        popup = tk.Toplevel(self)
        BrandManager.apply_window_icon(popup)
        popup.title(tr("material_lab_title", "Phoenix Material Lab"))
        popup.geometry("520x560")
        popup.minsize(460, 480)
        popup.configure(bg=PHOENIX_THEME.card_bg)

        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        self._material_popup = popup
        popup.protocol("WM_DELETE_WINDOW", self._close_material_lab_popup)

        try:
            x = self.winfo_rootx() + (self.winfo_width() - 520) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 560) // 2
            popup.geometry(f"+{x}+{y}")
        except Exception:
            pass

        container = tk.Frame(popup, bg=PHOENIX_THEME.card_bg)
        container.pack(fill="both", expand=True, padx=20, pady=16)

        # Header Title & Description
        header_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        header_frame.pack(fill="x", pady=(0, 12))
        tk.Label(
            header_frame,
            text=tr("material_lab_header", "Phoenix Material Lab"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            header_frame,
            text=tr(
                "material_lab_subtitle",
                "Physikalisches Farbraum-Priming vor der Hexagon NPU-Inferenz (Zero-CPU Fallback)",
            ),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
            wraplength=480,
            justify="left",
        ).pack(fill="x", pady=(2, 0))

        # Material Selection Grid
        tk.Label(
            container,
            text=tr("material_selection_title", "Materialauswahl:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).pack(fill="x", pady=(6, 4))

        choices_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        choices_frame.pack(fill="x", pady=(0, 10))
        choices_frame.grid_columnconfigure(0, weight=1)
        choices_frame.grid_columnconfigure(1, weight=1)

        self._popup_temp_preset = self.material_preset_var.get()
        self._popup_material_buttons: dict[str, PhoenixButton] = {}

        btn_none = PhoenixButton(
            choices_frame,
            text=tr("material_none_label", "Kein Material-Priming (Bisheriger Standardpfad)"),
            command=lambda: self._set_popup_temp_preset("none"),
            button_type="nav_active" if self._popup_temp_preset == "none" else "neutral",
            font=PHOENIX_THEME.font_small,
            height=32,
            radius=6,
        )
        btn_none.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self._popup_material_buttons["none"] = btn_none

        presets = [
            ("24k_gold", "24k Gold", "sparkles"),
            ("antique_brass", "Antik-Messing", "palette"),
            ("copper", "Kupfer", "palette"),
            ("chrome", "Chrom", "sparkles"),
        ]

        for idx, (p_id, p_name, icon) in enumerate(presets):
            row = 1 + idx // 2
            col = idx % 2
            pad_x = (0, 3) if col == 0 else (3, 0)
            btn = PhoenixButton(
                choices_frame,
                text=p_name,
                command=lambda pid=p_id: self._set_popup_temp_preset(pid),
                button_type="nav_active" if self._popup_temp_preset == p_id else "neutral",
                icon_name=icon,
                font=PHOENIX_THEME.font_small,
                height=32,
                radius=6,
            )
            btn.grid(row=row, column=col, sticky="ew", padx=pad_x, pady=3)
            self._popup_material_buttons[p_id] = btn

        # Material-Intensität
        intensity_header = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        intensity_header.pack(fill="x", pady=(8, 2))
        tk.Label(
            intensity_header,
            text=tr("material_intensity_label", "Material-Intensität"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
        ).pack(side="left")
        self._popup_intensity_disp = tk.Label(
            intensity_header,
            text=f"{self.material_intensity_var.get()}%",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_small,
        )
        self._popup_intensity_disp.pack(side="right")

        self._popup_intensity_scale = tk.Scale(
            container,
            from_=10,
            to=100,
            orient="horizontal",
            variable=self.material_intensity_var,
            command=lambda val: self._popup_intensity_disp.configure(text=f"{int(float(val))}%"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            highlightthickness=0,
            font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent,
            troughcolor=PHOENIX_THEME.elevated_bg,
            showvalue=False,
        )
        self._popup_intensity_scale.pack(fill="x", pady=(0, 8))

        # Helper Actions: Prompt suggestion & Canvas Preview
        helper_frame = tk.Frame(container, bg=PHOENIX_THEME.elevated_bg, padx=10, pady=8)
        helper_frame.pack(fill="x", pady=(4, 10))
        helper_frame.grid_columnconfigure(0, weight=1)
        helper_frame.grid_columnconfigure(1, weight=1)

        self._btn_prompt_suggest = PhoenixButton(
            helper_frame,
            text=tr("material_prompt_suggest", "Prompt-Empfehlung"),
            command=self._apply_material_prompt_suggestion,
            button_type="neutral",
            font=PHOENIX_THEME.font_small,
            height=28,
            radius=6,
        )
        self._btn_prompt_suggest.grid(row=0, column=0, sticky="ew", padx=(0, 3))

        self._btn_preview_priming = PhoenixButton(
            helper_frame,
            text=tr("material_preview_priming", "Sofort-Vorschau (Canvas)"),
            command=self._preview_priming_on_canvas,
            button_type="neutral",
            font=PHOENIX_THEME.font_small,
            height=28,
            radius=6,
        )
        self._btn_preview_priming.grid(row=0, column=1, sticky="ew", padx=(3, 0))

        # Action Buttons at Bottom
        actions_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        actions_frame.pack(side="bottom", fill="x", pady=(8, 0))
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)

        apply_btn = PhoenixButton(
            actions_frame,
            text=tr("apply", "Übernehmen"),
            command=self._apply_material_lab_popup,
            button_type="primary",
            height=34,
            radius=6,
        )
        apply_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        close_btn = PhoenixButton(
            actions_frame,
            text=tr("close", "Schließen"),
            command=self._close_material_lab_popup,
            button_type="neutral",
            height=34,
            radius=6,
        )
        close_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _set_popup_temp_preset(self, preset_id: str) -> None:
        self._popup_temp_preset = preset_id
        for pid, btn in getattr(self, "_popup_material_buttons", {}).items():
            if pid == preset_id:
                btn.configure(button_type="nav_active")
            else:
                btn.configure(button_type="neutral")

    def _apply_material_prompt_suggestion(self) -> None:
        if not hasattr(self, "_popup_temp_preset") or self._popup_temp_preset == "none":
            messagebox.showinfo("Phoenix Material Lab", "Bitte zuerst ein Material (z.B. 24k Gold) auswählen.")
            return
        try:
            preset = get_material_preset(self._popup_temp_preset)
        except KeyError:
            return

        self.prompt.delete("1.0", "end")
        self.prompt.insert("1.0", preset.recommended_prompt)
        if hasattr(self, "negative_prompt"):
            self.negative_prompt.delete("1.0", "end")
            self.negative_prompt.insert("1.0", preset.negative_prompt)
        if hasattr(self, "strength_var"):
            self.strength_var.set(0.40)
        if hasattr(self, "steps"):
            self.steps.set(10)
        if hasattr(self, "cfg_var"):
            self.cfg_var.set(8.0)
        self.status_text.set(f"Prompt-Empfehlung für {preset.display_name} übernommen (D=0.40, Steps=10, CFG=8.0)")

    def _preview_priming_on_canvas(self) -> None:
        if self.input_path is None or not hasattr(self, "canvas") or getattr(self.canvas, "image", None) is None:
            messagebox.showinfo("Phoenix Material Lab", "Bitte zuerst ein Bild laden.")
            return
        if self.canvas.mask is None or self.canvas.mask.getbbox() is None:
            messagebox.showinfo("Phoenix Material Lab", "Bitte zuerst einen Bereich mit dem Pinsel maskieren.")
            return
        if not hasattr(self, "_popup_temp_preset") or self._popup_temp_preset == "none":
            messagebox.showinfo("Phoenix Material Lab", "Bitte zuerst ein Material auswählen.")
            return

        intensity = float(self.material_intensity_var.get()) / 100.0
        try:
            primed = prime_material_chrominance(
                self.canvas.image,
                self.canvas.mask,
                preset_name=self._popup_temp_preset,
                intensity=intensity,
            )
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            preview_path = self.temp_dir / f"priming_preview_{time.time_ns()}.png"
            primed.save(preview_path, format="PNG")
            self.canvas.set_result(preview_path)
            preset_obj = get_material_preset(self._popup_temp_preset)
            self.status_text.set(f"Fotometrische Vorschau: {preset_obj.display_name} ({int(intensity * 100)}%)")
        except Exception as exc:
            messagebox.showerror("Phoenix Material Lab", f"Fehler bei der Vorschau: {exc}")

    def _apply_material_lab_popup(self) -> None:
        chosen = getattr(self, "_popup_temp_preset", "none")
        self.material_preset_var.set(chosen)
        self._update_material_ui_indicators()
        self._close_material_lab_popup()

    def _reset_material_preset(self) -> None:
        self.material_preset_var.set("none")
        self.material_intensity_var.set(100)
        self._update_material_ui_indicators()

    def _update_material_ui_indicators(self) -> None:
        chosen = self.material_preset_var.get()
        if chosen == "none" or not chosen:
            if hasattr(self, "material_status_label"):
                self.material_status_label.configure(text=tr("material_none_status", "Deaktiviert"), fg=PHOENIX_THEME.text_muted)
            if hasattr(self, "material_popup_btn"):
                self.material_popup_btn.configure(text=tr("material_select_button", "Material auswählen..."), button_type="neutral")
        else:
            try:
                preset = get_material_preset(chosen)
                display_title = preset.display_name
            except Exception:
                display_title = chosen
            intensity_pct = self.material_intensity_var.get()
            label_text = f"{display_title} ({intensity_pct}%)"
            if hasattr(self, "material_status_label"):
                self.material_status_label.configure(text=label_text, fg=PHOENIX_THEME.accent)
            if hasattr(self, "material_popup_btn"):
                self.material_popup_btn.configure(text=label_text, button_type="nav_active")

    def _close_material_lab_popup(self) -> None:
        if hasattr(self, "_material_popup") and self._material_popup:
            try:
                self._material_popup.destroy()
            except Exception:
                pass
        self._material_popup = None

    def _on_toggle_point_select(self) -> None:
        """Toggle canvas interactive point-prompting mode."""
        if not hasattr(self, "canvas") or getattr(self.canvas, "image", None) is None:
            self.status_text.set("Bitte zuerst ein Bild laden.")
            if hasattr(self, "prompt_edit_badge"):
                self.prompt_edit_badge.configure(
                    text="⚠ Bitte zuerst ein Bild laden.",
                    fg=PHOENIX_THEME.warning,
                )
            return

        is_point_mode = getattr(self.canvas, "tool_mode", "brush") == "point_select"
        if is_point_mode:
            self.canvas.set_tool_mode("brush")
            if hasattr(self, "prompt_edit_point_btn"):
                self.prompt_edit_point_btn.configure(button_type="neutral")
            if hasattr(self, "brush_button"):
                self.brush_button.configure(button_type="nav_active")
        else:
            self.canvas.set_tool_mode("point_select")
            if hasattr(self, "prompt_edit_point_btn"):
                self.prompt_edit_point_btn.configure(button_type="nav_active")
            if hasattr(self, "brush_button"):
                self.brush_button.configure(button_type="neutral")
            if hasattr(self, "eraser_button"):
                self.eraser_button.configure(button_type="neutral")
            self.prompt_edit_badge.configure(
                text="📍 Klick-Modus aktiv: Klicken Sie auf ein Objekt im Bild, um es auszuwählen.",
                fg=PHOENIX_THEME.accent,
            )

    def _on_point_selected(self, point: tuple[int, int]) -> None:
        """Called when an interactive point prompt is selected on the canvas."""
        self.point_prompt = point
        px, py = point
        prompt_text = self.prompt_edit_var.get().strip()
        if prompt_text:
            self.prompt_edit_badge.configure(
                text=f"📍 Punkt ausgewählt: ({px}, {py}) • Analysiere Intent und Quellfarbe...",
                fg=PHOENIX_THEME.accent,
            )
            self._on_analyze_prompt()
        else:
            self.prompt_edit_badge.configure(
                text=f"📍 Punkt ({px}, {py}) ausgewählt. Geben Sie jetzt Ihren Bearbeitungsauftrag ein (z. B. „Mache die Jacke zu schwarzem Leder“).",
                fg=PHOENIX_THEME.accent,
            )
            self.status_text.set(f"Punkt ({px}, {py}) gesetzt. Quellfarbe wird automatisch erkannt.")

    def _on_negative_point_selected(self, point: tuple[int, int]) -> None:
        """Called when a negative exclusion point prompt is selected on the canvas."""
        px, py = point
        neg_count = len(getattr(self.canvas, "negative_points", []))
        prompt_text = self.prompt_edit_var.get().strip()
        if prompt_text:
            self.prompt_edit_badge.configure(
                text=f"❌ Negativer Ausschluss-Punkt ({px}, {py}) gesetzt ({neg_count} aktiv) • Aktualisiere Maske...",
                fg=PHOENIX_THEME.accent,
            )
            self._on_analyze_prompt()
        else:
            self.prompt_edit_badge.configure(
                text=f"❌ Negativer Ausschluss-Punkt ({px}, {py}) gesetzt ({neg_count} aktiv).",
                fg=PHOENIX_THEME.accent,
            )
            self.status_text.set(f"Ausschluss-Punkt ({px}, {py}) gesetzt ({neg_count} aktiv).")

    def _on_analyze_prompt(self) -> None:
        """Analyze natural-language edit intent, extract mask, and prepare photometric priming."""
        if not hasattr(self, "canvas") or getattr(self.canvas, "image", None) is None:
            self.status_text.set("Bitte zuerst ein Bild laden.")
            if hasattr(self, "prompt_edit_badge"):
                self.prompt_edit_badge.configure(
                    text="⚠ Bitte zuerst ein Bild laden.",
                    fg=PHOENIX_THEME.warning,
                )
            return

        prompt_text = self.prompt_edit_var.get().strip()
        if not prompt_text:
            if hasattr(self, "prompt_edit_badge"):
                self.prompt_edit_badge.configure(
                    text="⚠ Bitte einen Bearbeitungsauftrag eingeben (z. B. „Verwandle den Apfel in 24k Gold“).",
                    fg=PHOENIX_THEME.warning,
                )
            return

        source_img = self.canvas.original_image or self.canvas.image
        self.prompt_edit_badge.configure(
            text="⏳ Analysiere Intent und Segmentierungsmaske...",
            fg=PHOENIX_THEME.accent,
        )

        neg_points = getattr(self.canvas, "negative_points", None)
        plan = self.prompt_edit_controller.analyze(
            image=source_img,
            prompt=prompt_text,
            point_prompt=self.point_prompt,
            negative_points=neg_points,
        )
        self.current_prompt_plan = plan

        if not plan.can_execute:
            reason = plan.rejection_reason or "Intent oder Konfidenz unzureichend."
            self.prompt_edit_badge.configure(
                text=f"⚠ {tr('prompt_edit_rejected', 'Zurückgewiesen')}: {reason}",
                fg=PHOENIX_THEME.danger,
            )
            self.status_text.set(f"Safety Gate: {reason}")
            return

        # Success: Safety Gate passed
        obj_name = plan.target_object or "Objekt"
        cat_name = plan.intent.value
        mat_info = f" • Material: {plan.material_preset}" if plan.material_preset else ""
        color_detected = plan.segment_result.detected_color_name if plan.segment_result else None
        color_info = f" • Farbe: {color_detected or plan.target_color}" if (color_detected or plan.target_color) else ""
        pt_info = f" • 📍 ({self.point_prompt[0]}, {self.point_prompt[1]})" if self.point_prompt else ""
        self.prompt_edit_badge.configure(
            text=f"✓ [{cat_name}] Ziel: {obj_name}{mat_info}{color_info}{pt_info} • Route: {plan.controller_route}",
            fg=PHOENIX_THEME.accent,
        )

        # Apply segmented mask to canvas overlay
        if plan.segment_result and plan.segment_result.mask is not None:
            self.canvas.set_mask(plan.segment_result.mask)

        # Sync inspector fields
        if plan.refined_prompt and hasattr(self, "prompt"):
            self.prompt.delete("1.0", "end")
            self.prompt.insert("1.0", plan.refined_prompt)
        if plan.negative_prompt and hasattr(self, "negative_prompt"):
            self.negative_prompt.delete("1.0", "end")
            self.negative_prompt.insert("1.0", plan.negative_prompt)
        if plan.denoising_strength and hasattr(self, "strength_var"):
            self.strength_var.set(plan.denoising_strength)
        if plan.material_preset:
            self.material_preset_var.set(plan.material_preset)
            self._update_material_ui_indicators()

        # Prepare photometric priming preview
        if plan.segment_result and plan.segment_result.mask is not None:
            if plan.material_preset:
                try:
                    intensity = float(self.material_intensity_var.get()) / 100.0
                    primed = prime_material_chrominance(
                        source_img,
                        plan.segment_result.mask,
                        preset_name=plan.material_preset,
                        intensity=intensity,
                    )
                    self.canvas.set_preview_image(primed)
                    self.prompt_edit_mode_label.configure(
                        text=tr("prompt_edit_mode_preview", "Canvas: Vorschau (Priming)"),
                        fg=PHOENIX_THEME.accent,
                    )
                except Exception as exc:
                    self.prompt_edit_mode_label.configure(
                        text="Canvas: Maske erkannt",
                        fg=PHOENIX_THEME.text_secondary,
                    )
            else:
                self.prompt_edit_mode_label.configure(
                    text="Canvas: Maske erkannt",
                    fg=PHOENIX_THEME.text_secondary,
                )

        self.status_text.set(f"Analyse bereit: {plan.controller_route} (CFG={self.cfg_var.get()}, Denoising={plan.denoising_strength})")

    def _on_toggle_preview(self) -> None:
        """Toggle canvas preview between original image and photometric priming / result."""
        if not hasattr(self, "canvas"):
            return
        is_preview = self.canvas.toggle_compare()
        if is_preview:
            self.prompt_edit_mode_label.configure(
                text=tr("prompt_edit_mode_preview", "Canvas: Vorschau (Priming)"),
                fg=PHOENIX_THEME.accent,
            )
        else:
            self.prompt_edit_mode_label.configure(
                text=tr("prompt_edit_mode_original", "Canvas: Original"),
                fg=PHOENIX_THEME.text_secondary,
            )

    def _on_toggle_compare(self) -> None:
        """Toggle before/after comparison between original and preview/result."""
        self._on_toggle_preview()

    def _on_execute_prompt_edit(self, asynchronous: bool = True) -> None:
        """Execute prompt-driven image editing on Qualcomm Hexagon HTP via PromptEditController."""
        if self.input_path is None:
            messagebox.showerror("Phoenix Image Lab", "Bitte zuerst ein Bild laden.")
            return

        prompt_text = self.prompt_edit_var.get().strip()
        if not prompt_text:
            messagebox.showerror("Phoenix Image Lab", "Bitte einen Bearbeitungsauftrag eingeben.")
            return

        if self.current_prompt_plan is None or not self.current_prompt_plan.can_execute:
            self._on_analyze_prompt()
            if self.current_prompt_plan is None or not self.current_prompt_plan.can_execute:
                return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"prompt_edit_{time.time_ns()}.png"

        # Non-destructive enforcement: Ensure output_path != input_path
        if output_path.resolve() == self.input_path.resolve():
            output_path = self.output_dir / f"prompt_edit_{time.time_ns()}_safe.png"

        self.prompt_edit_badge.configure(
            text="⚙ HTP-Inferenz aktiv auf Qualcomm Hexagon NPU (Zero-CPU Fallback)...",
            fg=PHOENIX_THEME.accent,
        )
        self.status_text.set("HTP-Inferenz wird vorbereitet...")
        self.progress.configure(value=0.05)

        neg_points = getattr(self.canvas, "negative_points", None)
        self.prompt_edit_controller.start(
            input_image_path=self.input_path,
            prompt=prompt_text,
            output_path=output_path,
            steps=self.steps.get(),
            seed=int(self.seed.get()),
            cfg_scale=float(self.cfg_var.get()),
            point_prompt=self.point_prompt,
            negative_points=neg_points,
            on_progress=self._on_progress,
            on_complete=self._on_prompt_edit_complete,
            asynchronous=asynchronous,
        )

    def _on_prompt_edit_complete(self, result: PromptEditResult) -> None:
        """Handle completion of prompt edit inference with background verification."""
        if result.success and result.output_path:
            self.result_path = Path(result.output_path)
            self.canvas.set_result(self.result_path)
            self.prompt_edit_badge.configure(
                text=f"✓ Erfolgreich generiert ({result.execution_time_ms:.0f} ms) • Bit-exakter Hintergrund erhalten",
                fg=PHOENIX_THEME.accent,
            )
            self.prompt_edit_mode_label.configure(
                text="Canvas: HTP-Ergebnis",
                fg=PHOENIX_THEME.accent,
            )
            self.status_text.set(f"Abgeschlossen: {self.result_path.name}")
        else:
            err = result.error_message or "Inferenz fehlgeschlagen"
            self.prompt_edit_badge.configure(
                text=f"❌ Fehler: {err}",
                fg=PHOENIX_THEME.danger,
            )
            self.status_text.set(f"Fehler: {err}")

    def _on_reset_prompt_edit(self) -> None:
        """Reset Prompt-Edit state, restore original image, clear point marker and mask."""
        self.point_prompt = None
        if hasattr(self, "canvas") and self.canvas is not None:
            self.canvas.restore_original_image()
            self.canvas.clear_mask()
            self.canvas.clear_point_prompt()
            self.canvas.set_tool_mode("brush")
        if hasattr(self, "prompt_edit_point_btn"):
            self.prompt_edit_point_btn.configure(button_type="neutral")
        if hasattr(self, "brush_button"):
            self.brush_button.configure(button_type="nav_active")
        if hasattr(self, "eraser_button"):
            self.eraser_button.configure(button_type="neutral")
        self.prompt_edit_var.set("")
        self.current_prompt_plan = None
        if hasattr(self, "prompt_edit_badge"):
            self.prompt_edit_badge.configure(
                text=tr("prompt_edit_idle_badge", "Geben Sie einen Bearbeitungsauftrag ein (z. B. „Verwandle den Apfel in 24k Gold“)"),
                fg=PHOENIX_THEME.text_muted,
            )
        if hasattr(self, "prompt_edit_mode_label"):
            self.prompt_edit_mode_label.configure(
                text=tr("prompt_edit_mode_original", "Canvas: Original"),
                fg=PHOENIX_THEME.text_secondary,
            )
        self.status_text.set("Bereit")
