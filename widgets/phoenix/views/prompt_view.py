from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk_real
from widgets.phoenix.controls.button import PhoenixButton

def make_phoenix_button(*args, **kwargs):
    bg = kwargs.get("bg")
    button_type = "primary"
    if bg == PHOENIX_THEME.accent:
        button_type = "primary"
    elif bg in (PHOENIX_THEME.elevated_bg, PHOENIX_THEME.card_bg, PHOENIX_THEME.panel_bg, PHOENIX_THEME.accent_soft):
        button_type = "neutral"
    elif bg == PHOENIX_THEME.danger or (isinstance(bg, str) and ("#ef" in bg.lower() or "#dc" in bg.lower() or "danger" in bg.lower() or "red" in bg.lower() or "#cf" in bg.lower() or "#b0" in bg.lower())):
        button_type = "danger"
    else:
        text = kwargs.get("text", "").lower()
        if "abbrechen" in text or "cancel" in text or "loeschen" in text or "löschen" in text or "remove" in text or "delete" in text:
            if "abbrechen" in text or "cancel" in text:
                button_type = "neutral"
            else:
                button_type = "danger"
        else:
            button_type = "neutral" if bg else "primary"

    for k in ["bg", "fg", "activebackground", "activeforeground", "relief", "bd", "padx", "pady", "anchor", "disabledforeground", "highlightbackground", "highlightthickness", "highlightcolor", "overrelief"]:
        kwargs.pop(k, None)

    text_val = kwargs.get("text", "")
    icon_name = None
    if "→" in text_val:
        kwargs["text"] = text_val.replace("→", "").strip()
        icon_name = "start"
    elif "←" in text_val:
        kwargs["text"] = text_val.replace("←", "").strip()
        icon_name = "back"
    elif "✕" in text_val:
        kwargs["text"] = text_val.replace("✕", "").strip()
        icon_name = "close"
    elif "✓" in text_val:
        kwargs["text"] = text_val.replace("✓", "").strip()
        icon_name = "success"
    elif "⚡" in text_val:
        kwargs["text"] = text_val.replace("⚡", "").strip()
        icon_name = "start"

    if icon_name and "icon_name" not in kwargs:
        kwargs["icon_name"] = icon_name

    return PhoenixButton(*args, button_type=button_type, **kwargs)

def make_phoenix_frame(*args, **kwargs):
    highlightthickness = kwargs.get("highlightthickness", 0)

    if highlightthickness and int(highlightthickness) > 0:
        from widgets.phoenix.controls.card import PhoenixCard
        bg = kwargs.pop("bg", PHOENIX_THEME.card_bg)
        border_color = kwargs.pop("highlightbackground", PHOENIX_THEME.border)
        for k in ["highlightthickness", "highlightcolor", "padx", "pady", "ipadx", "ipady"]:
            kwargs.pop(k, None)
        return PhoenixCard(*args, bg=bg, border_color=border_color, radius=10, **kwargs)

    return tk_real.Frame(*args, **kwargs)

def make_phoenix_option_menu(*args, **kwargs):
    if len(args) < 3:
        return tk_real.OptionMenu(*args, **kwargs)

    master = args[0]
    variable = args[1]
    default_val = args[2]
    values = list(args[3:])

    # Standard cleanup of styling parameters
    for k in ["command", "bg", "fg", "activebackground", "activeforeground", "relief", "bd", "padx", "pady", "anchor", "disabledforeground", "highlightbackground", "highlightthickness", "highlightcolor", "overrelief"]:
        kwargs.pop(k, None)

    # Resolve a context-appropriate icon
    icon_name = None
    var_name = str(variable).lower()
    if "preset" in var_name:
        icon_name = "preset"
    elif "model" in var_name:
        icon_name = "models"
    elif "width" in var_name or "height" in var_name or "size" in var_name:
        icon_name = "zoom"
    elif "sampler" in var_name or "scheduler" in var_name:
        icon_name = "settings"
    elif "batch" in var_name:
        icon_name = "grid"

    from widgets.phoenix.controls.dropdown import PhoenixDropdown
    return PhoenixDropdown(
        master,
        variable=variable,
        values=values,
        icon_name=icon_name,
        radius=6,
        **kwargs
    )

class _TkProxy:
    def __getattr__(self, name):
        if name == "Button":
            return make_phoenix_button
        if name == "Frame":
            return make_phoenix_frame
        if name == "OptionMenu":
            return make_phoenix_option_menu
        return getattr(tk_real, name)

tk = _TkProxy()
import datetime
import time
import os
import shutil
import subprocess
from dataclasses import replace
from tkinter import messagebox, ttk
from pathlib import Path

from controllers.prompt_workspace_controller import PromptWorkspaceController
from engine.brand_manager import BrandManager
from engine.boost_ai_service import BoostAIService
from engine.boost_engine import BoostSuggestion, PhoenixBoostEngine, PromptAnalysis
from engine.ollama_status import OllamaStatus, OllamaStatusService
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr
from app.runtime_localization import localize_runtime_text

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_FILES = None
    DND_AVAILABLE = False


logger = logging.getLogger("PhoenixPromptView")


class _Tooltip:
    """Small Tk tooltip helper for reference image name label."""

    def __init__(self, widget: tk.Widget, text_func) -> None:
        self.widget = widget
        self.text_func = text_func if callable(text_func) else lambda: text_func
        self.window: tk.Toplevel | None = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event: tk.Event | None = None) -> None:
        if self.window:
            return
        text = self.text_func()
        if not text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.window = tk.Toplevel(self.widget)
        BrandManager.apply_window_icon(self.window)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.window,
            text=text,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_caption,
            bd=1,
            relief="solid",
            padx=8,
            pady=4,
        ).pack()

    def hide(self, event: tk.Event | None = None) -> None:
        if self.window:
            self.window.destroy()
            self.window = None


class PhoenixPromptView(WorkspaceFrame):
    """
    Phoenix Workspace View for AI Image Generation.
    Professional two-column layout with grouped parameters on the left
    and a unified AI Generation Inspector on the right.
    """
    COMPACT_PREVIEW_MODE = False

    def __init__(self, master: tk.Misc, controller: PromptWorkspaceController | None = None) -> None:
        super().__init__(
            master,
            tr("ai_generate_title", "AI Image Generation"),
            tr("ai_generate_subtitle", "Bilder mittels Text-Prompts lokal auf der Snapdragon NPU generieren"),
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

        # Canny edge preview state
        self._canny_debounce_id = None
        self._latest_canny_req_id = None
        self._dnd_canny_photo_ref = None
        self._canny_rendered_path = None
        self._canny_rendered_low = None
        self._canny_rendered_high = None
        self._canny_queue = queue.Queue()
        self._canny_poll_id = None

        # Preset manager initialization
        from app.preset_manager import PresetManager
        self.preset_manager = PresetManager()
        self.selected_preset_var = tk.StringVar()
        self.available_presets = []

        # Configure 60/40 proportional column weights for compact zero-scroll layout
        self.grid_columnconfigure(0, weight=6, uniform="generate_cols")
        self.grid_columnconfigure(1, weight=4, uniform="generate_cols")

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
        self.input_card.grid(row=0, column=0, sticky="nsew", padx=PHOENIX_THEME.space_xs, pady=PHOENIX_THEME.space_xs)
        self.input_card.grid_rowconfigure(0, weight=1)
        self.input_card.grid_columnconfigure(0, weight=1)

        # ── Scrollable parameter area (Canvas) ────────
        self.param_canvas = tk.Canvas(
            self.input_card, bg=PHOENIX_THEME.card_bg,
            bd=0, highlightthickness=0,
        )
        self.param_canvas.grid(row=0, column=0, sticky="nsew")

        self.param_content = tk.Frame(self.param_canvas, bg=PHOENIX_THEME.card_bg)
        self.param_content.grid_propagate(True)
        self.param_canvas_wid = self.param_canvas.create_window(
            (0, 0), window=self.param_content, anchor="nw"
        )
        self.param_content.columnconfigure(0, weight=1)
        self.param_content.columnconfigure(1, weight=1)

        def _update_scroll(event=None):
            if self.param_canvas.winfo_exists() and self.param_content.winfo_exists():
                try:
                    self.param_content.update_idletasks()
                    self.param_canvas.configure(scrollregion=self.param_canvas.bbox("all"))
                except Exception:
                    pass

        self.param_content.bind(
            "<Configure>",
            lambda e: self.param_canvas.after(10, _update_scroll)
        )
        self.param_canvas.bind(
            "<Configure>",
            lambda e: self.param_canvas.itemconfig(self.param_canvas_wid, width=e.width)
        )

        def _on_param_mousewheel(event: tk.Event) -> None:
            self.param_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.input_card.bind("<Enter>", lambda e: self.param_canvas.bind_all("<MouseWheel>", _on_param_mousewheel))
        self.input_card.bind("<Leave>", lambda e: self.param_canvas.unbind_all("<MouseWheel>"))

        self._build_parameters()

    def _build_parameters(self) -> None:
        """Build all parameter groups inside the scrollable param_content frame."""
        self.width_var = tk.StringVar(value="512")
        self.height_var = tk.StringVar(value="512")
        self.sampler_var = tk.StringVar(value="Euler")
        self.scheduler_var = tk.StringVar(value="Normal")
        self.batch_var = tk.StringVar(value="1")
        self.cfg_var = tk.DoubleVar(value=7.5)
        self.steps_var = tk.IntVar(value=20)
        self.seed_var = tk.StringVar(value="-1")
        self.canny_low_var = tk.IntVar(value=50)
        self.canny_high_var = tk.IntVar(value=150)
        self.conditioning_strength_var = tk.DoubleVar(value=1.0)
        self.controlnet_canny_var = tk.BooleanVar(value=False)
        self.upscale_2x_var = tk.BooleanVar(value=False)
        self._upscale_requested_for_job = False

        self.canny_low_var.trace_add("write", self._on_canny_param_changed)
        self.canny_high_var.trace_add("write", self._on_canny_param_changed)
        self.controlnet_canny_var.trace_add("write", self._on_controlnet_enable_changed)

        p = self.param_content
        r = 0

        # ── Group: Presets ─────────────────────────────
        preset_section_title = tr("presets_section_header", "Presets & Vorlagen")
        r = self._section_header(p, preset_section_title, r)
        self.preset_section_label = self._section_labels[preset_section_title]

        preset_frame = tk.Frame(p, bg=PHOENIX_THEME.card_bg)
        self.preset_frame = preset_frame
        preset_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        preset_frame.grid_columnconfigure(0, weight=0)
        preset_frame.grid_columnconfigure(1, weight=1)
        preset_frame.grid_columnconfigure(2, weight=0)
        preset_frame.grid_columnconfigure(3, weight=0)
        preset_frame.grid_columnconfigure(4, weight=0)

        tk.Label(
            preset_frame, text=tr("preset_load_label", "Preset wählen:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=2)

        self.preset_dropdown = tk.OptionMenu(preset_frame, self.selected_preset_var, "-")
        self.preset_dropdown.configure(
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_button,
        )
        self.preset_dropdown.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        apply_btn = tk.Button(
            preset_frame,
            text=tr("apply_preset_btn", "Anwenden"),
            command=self._on_apply_preset,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=10,
            pady=4,
        )
        apply_btn.grid(row=0, column=2, sticky="ew", padx=(0, 4), pady=2)
        self._add_button_hover(apply_btn)

        save_preset_btn = tk.Button(
            preset_frame,
            text=tr("save_preset_btn", "Speichern"),
            command=self._on_save_preset,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=10,
            pady=4,
        )
        save_preset_btn.grid(row=0, column=3, sticky="ew", padx=(0, 4), pady=2)
        self._add_button_hover(save_preset_btn)

        delete_preset_btn = tk.Button(
            preset_frame,
            text=tr("delete_preset_btn", "Löschen"),
            command=self._on_delete_preset,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=10,
            pady=4,
        )
        delete_preset_btn.grid(row=0, column=4, sticky="ew", pady=2)
        self._add_button_hover(delete_preset_btn)

        self._refresh_presets_dropdown()
        r += 1

        # ── Group: Model ──────────────────────────────
        r = self._section_header(p, tr("section_model", "Model"), r)

        model_frame = tk.Frame(p, bg=PHOENIX_THEME.card_bg)
        model_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        model_frame.grid_columnconfigure(0, weight=0)
        model_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            model_frame, text=tr("ai_model_label", "KI-Modell:"), bg=PHOENIX_THEME.card_bg,
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

        self.model_desc_frame = tk.Frame(
            model_frame,
            bg=PHOENIX_THEME.elevated_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            padx=6,
            pady=4
        )
        self.model_desc_frame.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(2, 0),
        )
        self.model_desc_frame.grid_columnconfigure(0, weight=1)

        self.model_description_var = tk.StringVar()
        self.model_description_label = tk.Label(
            self.model_desc_frame,
            textvariable=self.model_description_var,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            justify="left",
            wraplength=1,
        )
        self.model_description_label.grid(row=0, column=0, sticky="ew")

        model_frame.bind(
            "<Configure>",
            lambda event: self.model_description_label.configure(
                wraplength=max(1, event.width - 24)
            ),
        )
        self._update_model_description(default_model)

        self.parameter_description_var = tk.StringVar()
        self.parameter_description_label = tk.Label(
            model_frame,
            textvariable=self.parameter_description_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        self.parameter_description_label.grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0)
        )
        for variable in (
            self.width_var, self.height_var, self.steps_var, self.cfg_var,
            self.seed_var, self.sampler_var, self.scheduler_var,
        ):
            variable.trace_add("write", self._update_parameter_description)
        self._update_parameter_description()
        r += 1

        # ── Group: Prompt ─────────────────────────────
        prompt_card = tk.Frame(
            p,
            bg=PHOENIX_THEME.surface,
            highlightbackground=PHOENIX_THEME.accent,
            highlightthickness=1,
            padx=2,
            pady=2,
        )
        prompt_card.grid_propagate(True)
        prompt_card.grid(
            row=r,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=16,
            pady=(0, 4),
        )
        r += 1
        prompt_card.grid_columnconfigure(0, weight=1)

        prompt_header_frame = tk.Frame(prompt_card, bg=PHOENIX_THEME.surface)
        prompt_header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(4, 0),
        )
        prompt_header_frame.grid_columnconfigure(0, weight=1)
        prompt_header_frame.grid_columnconfigure(1, weight=0)

        self.prompt_title_label = tk.Label(
            prompt_header_frame,
            text=tr("your_prompt_title", "DEIN PROMPT"),
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        )
        self.prompt_title_label.grid(row=0, column=0, sticky="ew")

        self.prompt_toolbar = tk.Frame(
            prompt_card,
            bg=PHOENIX_THEME.border,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.prompt_toolbar.grid_propagate(True)
        self.prompt_toolbar.grid(
            row=1, column=0, sticky="ew",
            padx=PHOENIX_THEME.space_md, pady=(6, 6),
        )
        for column in range(4):
            self.prompt_toolbar.grid_columnconfigure(column, weight=1)

        # Zeile 1 Buttons
        self.presets_popup_btn = PhoenixButton(
            self.prompt_toolbar, text=tr("presets_section_header", "Presets & Vorlagen"),
            icon_name="folder", icon_color=PHOENIX_THEME.warning,
            command=self._open_presets_popup, button_type="neutral",
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_small, height=32, radius=6,
            width=10,
        )
        self.presets_popup_btn.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        self.boost_btn = PhoenixButton(
            self.prompt_toolbar, text=tr("boost_button", "Phoenix Boost"),
            icon_name="sparkles", icon_color=PHOENIX_THEME.success,
            command=self._open_boost_preview, button_type="neutral",
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_small, height=32, radius=6,
            width=10,
        )
        self.boost_btn.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        _Tooltip(
            self.boost_btn,
            lambda: tr("boost_tooltip", "Prompt lokal optimieren und Einstellungen empfehlen."),
        )

        self.parameters_popup_btn = PhoenixButton(
            self.prompt_toolbar, text=tr("generator_settings_toolbar", "Generierungsparameter"),
            icon_name="settings", icon_color=PHOENIX_THEME.danger,
            command=self._open_advanced_settings_popup, button_type="neutral",
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_small, height=32, radius=6,
            width=10,
        )
        self.parameters_popup_btn.grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

        self.controlnet_popup_btn = PhoenixButton(
            self.prompt_toolbar, text=tr("tab_controlnet", "ControlNet"),
            icon_name="image", icon_color=PHOENIX_THEME.accent,
            command=self._open_controlnet_popup, button_type="neutral",
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_small, height=32, radius=6,
            width=10,
        )
        self.controlnet_popup_btn.grid(row=0, column=3, sticky="nsew", padx=2, pady=2)

        # Zeile 2 Buttons
        self.history_btn = PhoenixButton(
            self.prompt_toolbar, text=tr("history_tab", "Verlauf"),
            icon_name="back", icon_color=PHOENIX_THEME.accent,
            command=self._show_prompt_history_popup, button_type="neutral",
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_small, height=32, radius=6,
            width=10,
        )
        self.history_btn.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=2, pady=2)

        self.maximize_btn = PhoenixButton(
            self.prompt_toolbar,
            text=f"⛶ {tr('maximize_btn', 'Maximieren')}",
            button_type="neutral", bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small,
            height=32, radius=6,
            command=self._open_expandable_prompt_popup,
            width=10,
        )
        self.maximize_btn.grid(row=1, column=2, columnspan=2, sticky="nsew", padx=2, pady=2)

        tk.Label(
            prompt_card,
            text=tr("prompt_placeholder", "Beschreibe Motiv, Licht, Perspektive und Stil möglichst konkret."),
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).grid(
            row=2,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(0, 3),
        )

        self.prompt_text = tk.Text(
            prompt_card, height=3, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body, wrap="word",
            padx=6, pady=4,
        )
        self.prompt_text.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(0, 2),
        )
        self.prompt_text.insert("1.0", "A futuristic cyberpunk cityscape, neon lights, high resolution, highly detailed")
        self.prompt_text.bind("<KeyRelease>", lambda e: self._on_main_prompt_key())

        self.prompt_counter_lbl = tk.Label(
            prompt_card,
            text=tr("chars_words_label", "Zeichen: {chars} | Wörter: {words}", chars=0, words=0),
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="e"
        )
        self.prompt_counter_lbl.grid(
            row=4,
            column=0,
            sticky="e",
            padx=PHOENIX_THEME.space_md,
            pady=(0, 2)
        )

        self.negative_prompt_title_label = tk.Label(
            prompt_card,
            text=tr("exclude_negative_prompt_title", "AUSSCHLIESSEN"),
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        )
        self.negative_prompt_title_label.grid(
            row=5,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(0, 2),
        )

        self.neg_prompt_text = tk.Text(
            prompt_card, height=2, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body, wrap="word",
            padx=6, pady=4,
        )
        self.neg_prompt_text.grid(
            row=6,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(0, 4),
        )
        self.neg_prompt_text.insert("1.0", "blurry, low quality, distorted, extra limbs, bad anatomy")
        self._update_prompt_counters()
        r += 1

        # ── Group: Generation Parameters ──────────────
        generation_section_title = tr("section_generation_parameters", "Generation Parameters")
        r = self._section_header(p, generation_section_title, r)
        self.generation_section_label = self._section_labels[generation_section_title]

        self.active_tab = "basic"
        self.canny_supported = False

        self.tab_bar = tk.Frame(p, bg=PHOENIX_THEME.elevated_bg, padx=2, pady=2, bd=0, highlightthickness=0)
        self.tab_bar.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(8, 6))
        r += 1

        for col_idx in range(3):
            self.tab_bar.columnconfigure(col_idx, weight=1)

        self.btn_tab_basic = tk.Button(
            self.tab_bar,
            text=tr("tab_basic", "Basic"),
            font=PHOENIX_THEME.font_small,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=12,
            pady=4,
            command=lambda: self._switch_tab("basic")
        )
        self.btn_tab_basic.grid(row=0, column=0, sticky="ew", padx=1)
        self._add_button_hover(self.btn_tab_basic)
 
        self.btn_tab_canny = tk.Button(
            self.tab_bar,
            text=tr("tab_controlnet", "ControlNet/Canny"),
            font=PHOENIX_THEME.font_small,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=12,
            pady=4,
            command=lambda: self._switch_tab("canny")
        )
        self.btn_tab_canny.grid(row=0, column=1, sticky="ew", padx=1)
        self._add_button_hover(self.btn_tab_canny)
 
        self.btn_tab_advanced = tk.Button(
            self.tab_bar,
            text=tr("tab_advanced", "Advanced"),
            font=PHOENIX_THEME.font_small,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=12,
            pady=4,
            command=lambda: self._switch_tab("advanced")
        )
        self.btn_tab_advanced.grid(row=0, column=2, sticky="ew", padx=1)
        self._add_button_hover(self.btn_tab_advanced)

        self.tab_container = tk.Frame(
            p,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
        )
        self.tab_container.grid(row=r, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        self.tab_container.columnconfigure(0, weight=1)
        self.tab_container.columnconfigure(1, weight=1)
        r += 1

        self.tab_basic_content = tk.Frame(self.tab_container, bg=PHOENIX_THEME.card_bg, bd=0, highlightthickness=0)
        self.tab_basic_content.columnconfigure(0, weight=1)
        self.tab_basic_content.columnconfigure(1, weight=1)

        self.tab_canny_content = tk.Frame(self.tab_container, bg=PHOENIX_THEME.card_bg, bd=0, highlightthickness=0)
        self.tab_canny_content.columnconfigure(0, weight=1)
        self.tab_canny_content.columnconfigure(1, weight=1)

        self.tab_advanced_content = tk.Frame(self.tab_container, bg=PHOENIX_THEME.card_bg, bd=0, highlightthickness=0)
        self.tab_advanced_content.columnconfigure(0, weight=1)
        self.tab_advanced_content.columnconfigure(1, weight=1)

        self.tab_basic_content.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=8)

        # ── Group: ControlNet Canny popup widgets container ──
        self._dummy_hidden_frame = tk.Frame(self)
        self._ensure_controlnet_widgets(self._dummy_hidden_frame)
        
        # ── Group: Image Size (inside tab_basic_content) ──
        self.size_frame = tk.Frame(self.tab_basic_content, bg=PHOENIX_THEME.card_bg)
        self.size_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
        self.size_frame.row_idx = 0
        self.size_frame.grid_columnconfigure(0, weight=0)
        self.size_frame.grid_columnconfigure(1, weight=1)
        self.size_frame.grid_columnconfigure(2, weight=0)
        self.size_frame.grid_columnconfigure(3, weight=1)

        self.width_label = tk.Label(self.size_frame, text=tr("width_label_colon", "Breite:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.width_label.grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        self.width_menu = tk.OptionMenu(self.size_frame, self.width_var, "256", "512", "768", "1024")
        self.width_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, disabledforeground=PHOENIX_THEME.text_disabled, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.width_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.width_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)
 
        self.height_label = tk.Label(self.size_frame, text=tr("height_label_colon", "Höhe:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.height_label.grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        self.height_menu = tk.OptionMenu(self.size_frame, self.height_var, "256", "512", "768", "1024")
        self.height_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, disabledforeground=PHOENIX_THEME.text_disabled, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.height_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.height_menu.grid(row=0, column=3, sticky="ew", pady=2)

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
            pady=4
        )
        self.res_512_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(2, 2))
        self.res_512_btn.is_active = True
        self.res_512_btn.normal_bg = PHOENIX_THEME.accent
        self.res_512_btn.normal_fg = PHOENIX_THEME.text_on_accent
        self._add_button_hover(self.res_512_btn)

        lock_symbol = IconManager.get_symbol("lock")
        self.res_1024_btn = tk.Button(
            self.locked_res_frame,
            text=f"{lock_symbol} {tr('res_1024_btn_text', '1024 × 1024 (Demnächst)')}",
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
            pady=4
        )
        self.res_1024_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(2, 2))
        self.res_1024_btn.is_active = False
        self.res_1024_btn.normal_bg = PHOENIX_THEME.elevated_bg
        self.res_1024_btn.normal_fg = PHOENIX_THEME.text_disabled
        self._add_button_hover(self.res_1024_btn)
 
        self.locked_hint_lbl = tk.Label(
            self.locked_res_frame,
            text=tr("resolution_lock_tooltip", "Höhere Auflösungen benötigen ein kompatibles Qualcomm-Modell."),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left",
            wraplength=280
        )
        self.locked_hint_lbl.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))

        # ── Group: Sampling Frame (inside tab_basic_content) ──
        self.sampling_frame = tk.Frame(self.tab_basic_content, bg=PHOENIX_THEME.card_bg)
        self.sampling_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 2))
        self.sampling_frame.grid_columnconfigure(0, weight=1)
        self.sampling_frame.grid_columnconfigure(1, weight=1)

        self.cfg_label = tk.Label(self.sampling_frame, text=tr("cfg_scale_label_colon", "CFG Scale:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.cfg_label.grid(row=0, column=0, sticky="w", pady=(0, 1))
        self.cfg_scale = tk.Scale(
            self.sampling_frame, from_=1.0, to=20.0, resolution=0.5, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            width=12, variable=self.cfg_var
        )
        self.cfg_scale.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 2))
 
        self.adv_label = tk.Label(self.sampling_frame, text=tr("settings_label_colon", "Einstellungen:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.adv_settings_btn = tk.Button(
            self.sampling_frame, text=tr("advanced_settings_trigger", "Erweiterte Einstellungen ⚙️"),
            font=PHOENIX_THEME.font_caption, cursor="hand2", relief="flat", bd=0, padx=8, pady=3,
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_secondary,
            activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
            command=self._open_advanced_settings_popup
        )
        self._add_button_hover(self.adv_settings_btn)

        self.steps_label = tk.Label(self.sampling_frame, text=tr("steps_label_colon", "Steps:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.steps_label.grid(row=0, column=1, sticky="w", pady=(0, 1))
        self.steps_scale = tk.Scale(
            self.sampling_frame, from_=1, to=100, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            width=12, variable=self.steps_var
        )
        self.steps_scale.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 2))

        self.active_steps_preset = "Standard"
        self.steps_preset_frame = tk.Frame(self.sampling_frame, bg=PHOENIX_THEME.card_bg)
        self.steps_preset_frame.grid_columnconfigure(0, weight=1)

        self.btn_preset_schnell = tk.Button(
            self.steps_preset_frame, text=tr("steps_fast", "⚡ Schnell"),
            font=PHOENIX_THEME.font_caption, cursor="hand2", relief="flat", bd=0, padx=8, pady=2,
            command=lambda: self._select_steps_preset("Schnell")
        )
        self.btn_preset_schnell.grid(row=0, column=0, sticky="ew", pady=1)
        self._add_button_hover(self.btn_preset_schnell)
 
        self.btn_preset_standard = tk.Button(
            self.steps_preset_frame, text=tr("steps_standard", "⭐ Standard"),
            font=PHOENIX_THEME.font_caption, cursor="hand2", relief="flat", bd=0, padx=8, pady=2,
            command=lambda: self._select_steps_preset("Standard")
        )
        self.btn_preset_standard.grid(row=1, column=0, sticky="ew", pady=1)
        self._add_button_hover(self.btn_preset_standard)
 
        self.btn_preset_beste = tk.Button(
            self.steps_preset_frame, text=tr("steps_best", "💎 Beste Qualität"),
            font=PHOENIX_THEME.font_caption, cursor="hand2", relief="flat", bd=0, padx=8, pady=2,
            command=lambda: self._select_steps_preset("Beste Qualität")
        )
        self.btn_preset_beste.grid(row=2, column=0, sticky="ew", pady=1)
        self._add_button_hover(self.btn_preset_beste)

        self._update_steps_preset_colors()

        # ── Group: Advanced Dropdown Frame (inside tab_advanced_content) ──
        self.dropdown_frame = tk.Frame(self.tab_advanced_content, bg=PHOENIX_THEME.card_bg)
        self.dropdown_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        self.dropdown_frame.grid_columnconfigure(0, weight=0)
        self.dropdown_frame.grid_columnconfigure(1, weight=1)
        self.dropdown_frame.grid_columnconfigure(2, weight=0)
        self.dropdown_frame.grid_columnconfigure(3, weight=1)

        self.sampler_lbl = tk.Label(self.dropdown_frame, text=tr("sampler_label_colon", "Sampler:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.sampler_lbl.grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        self.sampler_menu = tk.OptionMenu(self.dropdown_frame, self.sampler_var, "Euler a", "Euler", "DPM++ 2M", "DDIM", "LMS")
        self.sampler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, disabledforeground=PHOENIX_THEME.text_disabled, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.sampler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.sampler_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)
 
        self.scheduler_lbl = tk.Label(self.dropdown_frame, text=tr("scheduler_label_colon", "Sched.:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.scheduler_lbl.grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        self.scheduler_menu = tk.OptionMenu(self.dropdown_frame, self.scheduler_var, "Normal", "Karras", "Exponential", "SGM Uniform")
        self.scheduler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, disabledforeground=PHOENIX_THEME.text_disabled, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.scheduler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.scheduler_menu.grid(row=0, column=3, sticky="ew", pady=2)

        # ── Group: Output (inside tab_advanced_content) ──
        self.output_frame = tk.Frame(self.tab_advanced_content, bg=PHOENIX_THEME.card_bg)
        self.output_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 2))
        self.output_frame.row_idx = 1
        self.output_frame.grid_columnconfigure(0, weight=0)
        self.output_frame.grid_columnconfigure(1, weight=1)
        self.output_frame.grid_columnconfigure(2, weight=0)
        self.output_frame.grid_columnconfigure(3, weight=1)

        self.seed_label = tk.Label(self.output_frame, text=tr("seed_label_colon", "Seed:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.seed_label.grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        self.seed_entry = tk.Entry(
            self.output_frame, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body,
            textvariable=self.seed_var
        )
        self.seed_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)
 
        self.batch_label = tk.Label(self.output_frame, text=tr("batch_label_colon", "Batch:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        self.batch_label.grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        self.batch_menu = tk.OptionMenu(self.output_frame, self.batch_var, "1", "2", "4", "8")
        self.batch_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, disabledforeground=PHOENIX_THEME.text_disabled, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        self.batch_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        self.batch_menu.grid(row=0, column=3, sticky="ew", pady=2)

        self._attach_parameter_help((self.seed_label, self.seed_entry), "seed_help", "Reproduzierbarer Startwert; -1 bedeutet zufälliger Seed.")
        self._attach_parameter_help((self.batch_label, self.batch_menu), "batch_help", "Anzahl der zu erzeugenden Bilder; erhöht Zeit- und Speicherbedarf.")
        self._attach_parameter_help((self.steps_label, self.steps_scale), "steps_help", "Mehr Entrauschungsschritte können Details verbessern, benötigen aber mehr Zeit.")
        self._attach_parameter_help((self.cfg_label, self.cfg_scale), "cfg_scale_help", "Stärke der Prompt-Befolgung; typische Empfehlung 6–8.")
        self._attach_parameter_help((self.sampler_lbl, self.sampler_menu), "sampler_help", "Verwendetes Berechnungsverfahren für die Bildentstehung.", self.sampler_menu)
        self._attach_parameter_help((self.scheduler_lbl, self.scheduler_menu), "scheduler_help", "Zeitliche Verteilung der Entrauschungsschritte.", self.scheduler_menu)

        self._update_tab_bar_visuals()
        self._apply_generation_contract(self.model_var.get())
        self.preset_section_label.grid_remove()
        self.preset_frame.grid_remove()
        self.generation_section_label.grid_remove()
        self.tab_bar.grid_remove()
        self.tab_container.grid_remove()

    @staticmethod
    def _configure_option_contract(widget: tk.OptionMenu, variable: tk.StringVar, spec: dict, label_widget: tk.Label | None = None, label_base_text: str = "") -> None:
        values = [str(value) for value in spec.get("values", [])]
        default = str(spec.get("default", values[0] if values else variable.get()))
        if default not in values:
            values.insert(0, default)
        menu = widget["menu"]
        menu.delete(0, "end")
        for value in values:
            menu.add_command(label=value, command=tk._setit(variable, value))
        variable.set(default)
        is_editable = spec.get("editable", True) and len(values) > 1
        widget.configure(state="normal" if is_editable else "disabled")
        if label_widget:
            if not is_editable:
                label_widget.configure(text=f"{label_base_text} 🔒")
            else:
                label_widget.configure(text=label_base_text)

    @staticmethod
    def _attach_parameter_help(
        widgets: tuple[tk.Widget, ...],
        translation_key: str,
        fallback: str,
        constrained_widget: tk.Widget | None = None,
    ) -> None:
        def help_text() -> str:
            text = tr(translation_key, fallback)
            if constrained_widget is not None and str(constrained_widget.cget("state")) == "disabled":
                fixed_hint = tr(
                    "parameter_fixed_by_model_backend",
                    "Für dieses Modell/Backend fest vorgegeben.",
                )
                return f"{text}\n{fixed_hint}"
            return text

        for widget in widgets:
            _Tooltip(widget, help_text)

    def _apply_generation_contract(self, model_id: str) -> None:
        contract = self.controller.select_model(model_id)
        if not contract:
            return

        for name in ["width", "height"]:
            spec = contract.get(name)
            if isinstance(spec, dict):
                widget, variable = (self.width_menu, self.width_var) if name == "width" else (self.height_menu, self.height_var)
                self._configure_option_contract(widget, variable, spec)

        if isinstance(contract.get("sampler"), dict):
            self._configure_option_contract(
                self.sampler_menu, self.sampler_var, contract["sampler"],
                self.sampler_lbl, tr("sampler_label_colon", "Sampler:"),
            )
        if isinstance(contract.get("scheduler"), dict):
            self._configure_option_contract(
                self.scheduler_menu, self.scheduler_var, contract["scheduler"],
                self.scheduler_lbl, tr("scheduler_label_colon", "Sched.:"),
            )

        self.sampling_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))

        if self.COMPACT_PREVIEW_MODE:
            self.size_frame.grid_remove()
            self.dropdown_frame.grid_remove()
            self.output_frame.grid_remove()
            if hasattr(self, "_section_labels"):
                if "Image Size" in self._section_labels:
                    self._section_labels["Image Size"].grid_remove()
                if "Output" in self._section_labels:
                    self._section_labels["Output"].grid_remove()

            self.cfg_label.grid_remove()
            self.cfg_scale.grid_remove()
            self.adv_label.grid(row=0, column=0, sticky="w", pady=(0, 1))
            self.adv_settings_btn.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 2))
        else:
            self.adv_label.grid_remove()
            self.adv_settings_btn.grid_remove()
            self.cfg_label.grid(row=0, column=0, sticky="w", pady=(0, 1))
            self.cfg_scale.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 2))

            if hasattr(self, "_section_labels"):
                if "Image Size" in self._section_labels:
                    lbl = self._section_labels["Image Size"]
                    lbl.grid_remove()
                if "Output" in self._section_labels:
                    lbl = self._section_labels["Output"]
                    lbl.grid_remove()

            self.size_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))
            self.dropdown_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(2, 0))
            self.output_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4))

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

        self.steps_preset_frame.grid_remove()
        self.steps_scale.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 2))

        seed_spec = contract.get("seed")
        if isinstance(seed_spec, dict) and "default" in seed_spec:
            self.seed_var.set(str(seed_spec["default"]))

        model_meta = self.controller.repository.get_model(model_id)
        supports_controlnet = False
        if model_meta:
            supports_controlnet = model_meta.get("capabilities", {}).get("controlnet", False)

        self.canny_supported = supports_controlnet

        if supports_controlnet:
            if hasattr(self, "controlnet_popup_btn") and self.controlnet_popup_btn:
                self.controlnet_popup_btn.configure(state="normal", bg=PHOENIX_THEME.elevated_bg)
            self.controlnet_canny_var.set(True)
        else:
            if hasattr(self, "controlnet_popup_btn") and self.controlnet_popup_btn:
                self.controlnet_popup_btn.configure(state="disabled", bg=PHOENIX_THEME.elevated_bg)
            if hasattr(self, "_controlnet_popup") and self._controlnet_popup and self._controlnet_popup.winfo_exists():
                self._controlnet_popup.destroy()
            self._controlnet_popup = None
            self._ensure_controlnet_widgets(self._dummy_hidden_frame)
            self.controlnet_canny_var.set(False)

    def _section_header(self, parent: tk.Frame, title: str, row: int) -> int:
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

        self.inspector_panel = tk.Frame(
            self.inspector_slot, bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border, highlightthickness=1,
        )
        self.inspector_panel.grid(row=0, column=0, sticky="nsew", padx=PHOENIX_THEME.space_xs, pady=PHOENIX_THEME.space_xs)
        self.inspector_panel.grid_rowconfigure(0, weight=1)
        self.inspector_panel.grid_rowconfigure(1, weight=0)
        self.inspector_panel.grid_columnconfigure(0, weight=1)

        self.insp_content = tk.Frame(self.inspector_panel, bg=PHOENIX_THEME.card_bg)
        self.insp_content.grid(row=0, column=0, sticky="nsew")
        self.insp_content.columnconfigure(0, weight=0)
        self.insp_content.columnconfigure(1, weight=1)
        self.insp_content.columnconfigure(2, weight=0)
        self.insp_content.columnconfigure(3, weight=1)

        row = 0

        # ── Section: Generation Status ────────────────
        row = self._inspector_section_header(tr("insp_sec_status", "Generation Status"), row)

        tk.Label(
            self.insp_content, text=tr("ai_model_label", "KI-Modell:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_model = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_model.grid(row=row, column=1, columnspan=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        tk.Label(
            self.insp_content, text=tr("backend_label_colon", "Backend:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_backend = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_backend.grid(row=row, column=1, sticky="w", padx=(4, 16), pady=1)

        tk.Label(
            self.insp_content, text=tr("queue_label_colon", "Queue:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=2, sticky="w", padx=(16, 4), pady=1)
        self.insp_queue = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_queue.grid(row=row, column=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        tk.Label(
            self.insp_content, text=tr("status_label_colon", "Status:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_gen_status = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_gen_status.grid(row=row, column=1, columnspan=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        tk.Label(
            self.insp_content, text=tr("progress_label_colon", "Fortschritt:"), bg=PHOENIX_THEME.card_bg,
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
            self.insp_content, text=tr("phase_label_colon", "Phase:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.progress_stage_label = tk.Label(
            self.insp_content, text=tr("ready", "Bereit"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.progress_stage_label.grid(row=row, column=1, sticky="w", padx=(4, 16), pady=1)

        tk.Label(
            self.insp_content, text=tr("steps_label_colon", "Steps:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=2, sticky="w", padx=(16, 4), pady=1)
        self.progress_step_label = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.progress_step_label.grid(row=row, column=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        # ── Section: Generation Information ───────────
        row = self._inspector_section_header(tr("insp_sec_info", "Generation Information"), row)

        tk.Label(
            self.insp_content, text=tr("size_label_colon", "Size:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_size = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_size.grid(row=row, column=1, sticky="w", padx=(4, 16), pady=1)

        tk.Label(
            self.insp_content, text=tr("steps_label_colon", "Steps:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=2, sticky="w", padx=(16, 4), pady=1)
        self.insp_steps = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_steps.grid(row=row, column=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        tk.Label(
            self.insp_content, text=tr("cfg_label_colon", "CFG:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_cfg = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_cfg.grid(row=row, column=1, sticky="w", padx=(4, 16), pady=1)

        tk.Label(
            self.insp_content, text=tr("seed_label_colon", "Seed:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=2, sticky="w", padx=(16, 4), pady=1)
        self.insp_seed = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_seed.grid(row=row, column=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        tk.Label(
            self.insp_content, text=tr("sampler_label_colon", "Sampler:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=1)
        self.insp_sampler = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_sampler.grid(row=row, column=1, sticky="w", padx=(4, 16), pady=1)

        tk.Label(
            self.insp_content, text=tr("scheduler_label_colon", "Sched.:"), bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w"
        ).grid(row=row, column=2, sticky="w", padx=(16, 4), pady=1)
        self.insp_scheduler = tk.Label(
            self.insp_content, text="-", bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_small, anchor="w"
        )
        self.insp_scheduler.grid(row=row, column=3, sticky="w", padx=(4, 16), pady=1)
        row += 1

        # ── Section: Preview ──────────────────────────
        row = self._inspector_section_header(tr("insp_sec_preview", "Preview"), row)

        preview_frame = tk.Frame(
            self.insp_content, bg=PHOENIX_THEME.content_bg,
            highlightbackground=PHOENIX_THEME.border, highlightthickness=1
        )
        preview_frame.grid(row=row, column=0, columnspan=4, sticky="nsew", padx=16, pady=(0, 4))
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        self.insp_content.grid_rowconfigure(row, weight=1)

        self.preview_center = tk.Frame(preview_frame, bg=PHOENIX_THEME.content_bg)
        self.preview_center.grid(row=0, column=0, sticky="nsew", pady=8)
        self.preview_center.grid_columnconfigure(0, weight=0)
        self.preview_center.grid_rowconfigure(0, weight=1)
        self.preview_center.bind("<Configure>", self._on_preview_resize)

        self.placeholder_container = tk.Frame(self.preview_center, bg=PHOENIX_THEME.content_bg)
        self.placeholder_container.place(relx=0.5, rely=0.5, anchor="center")

        from resources.icons import IconManager
        tk.Label(
            self.placeholder_container, text=IconManager.get_symbol("image"),
            bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.accent,
            font=(PHOENIX_THEME.font_title[0], 20, "bold"),
        ).pack(anchor="center", pady=(0, 2))

        tk.Label(
            self.placeholder_container, text=tr("home_no_images_generated", "No image generated"),
            bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small, justify="center"
        ).pack(anchor="center")
        row += 1

        # ── Clean Native Action Grid (No flickering, uniform text layout) ──
        btn_frame = tk.Frame(self.insp_content, bg=PHOENIX_THEME.card_bg)
        btn_frame.grid(row=row, column=0, columnspan=4, sticky="ew", padx=16, pady=(4, 8))
        btn_frame.columnconfigure(0, weight=1, uniform="insp_btns")
        btn_frame.columnconfigure(1, weight=1, uniform="insp_btns")

        btn_kwargs = {
            "bg": PHOENIX_THEME.elevated_bg,
            "fg": PHOENIX_THEME.text_primary,
            "activebackground": PHOENIX_THEME.accent,
            "activeforeground": PHOENIX_THEME.text_on_accent,
            "bd": 0,
            "relief": "flat",
            "font": PHOENIX_THEME.font_button,
            "cursor": "hand2",
            "padx": 10,
            "pady": 6,
            "anchor": "w",
            "compound": "left",
        }

        self.btn_open_library = tk.Button(
            btn_frame,
            text=tr("btn_open_in_library", "In Galerie öffnen"),
            command=self._on_open_library,
            **btn_kwargs
        )
        self.btn_open_library.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self._add_button_hover(self.btn_open_library)

        self.btn_open_review = tk.Button(
            btn_frame,
            text=tr("btn_open_in_review", "Im Vergleich öffnen"),
            command=self._on_open_review,
            **btn_kwargs
        )
        self.btn_open_review.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        self._add_button_hover(self.btn_open_review)

        self.btn_save_as = tk.Button(
            btn_frame,
            text=tr("btn_save_as", "Speichern unter..."),
            command=self._on_save_as,
            **btn_kwargs
        )
        self.btn_save_as.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self._add_button_hover(self.btn_save_as)

        self.btn_open_explorer = tk.Button(
            btn_frame,
            text=tr("btn_open_in_explorer", "Im Explorer anzeigen"),
            command=self._on_open_explorer,
            **btn_kwargs
        )
        self.btn_open_explorer.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)
        self._add_button_hover(self.btn_open_explorer)

        # ── Fixed primary action (always visible) ─────
        self.action_bar = tk.Frame(
            self.inspector_panel,
            bg=PHOENIX_THEME.surface,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.action_bar.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=16,
            pady=(0, 16),
        )
        self.action_bar.grid_columnconfigure(0, weight=1, uniform="generation_actions")
        self.action_bar.grid_columnconfigure(1, weight=1, uniform="generation_actions")

        tk.Label(
            self.action_bar,
            text=tr("title_actions", "Actions"),
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=12,
            pady=(4, 0),
        )
        tk.Label(
            self.action_bar,
            text=tr("action_bar_hint", "Bereit für deine nächste Idee – Ausführung erfolgt lokal auf der NPU."),
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=12,
            pady=(0, 4),
        )

        self.gen_btn = tk.Button(
            self.action_bar,
            text=tr("btn_generate_image", "BILD GENERIEREN  →"),
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
            padx=(12, 4),
            pady=(0, 12),
        )
        self.cancel_btn = tk.Button(
            self.action_bar,
            text=tr("btn_cancel_generation", "ABBRECHEN"),
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
            padx=(4, 12),
            pady=(0, 12),
        )
        self._layout_generation_actions(False)

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
        self.status_bar_frame.grid(row=0, column=0, sticky="ew", padx=PHOENIX_THEME.space_sm)

        self.status_label = tk.Label(
            self.status_bar_frame, text=tr("status_prefix", "Status: {status}", status=tr("ready", "Bereit")),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption, anchor="w", padx=16, pady=6
        )
        self.status_label.pack(side="left")

        self.model_status_label = tk.Label(
            self.status_bar_frame, text=tr("model_prefix", "Modell: {model}", model="-"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption, anchor="w", padx=16, pady=6
        )
        self.model_status_label.pack(side="left")

        self.backend_status_label = tk.Label(
            self.status_bar_frame, text=tr("backend_prefix", "Backend: {backend}", backend="-"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption, anchor="w", padx=16, pady=6
        )
        self.backend_status_label.pack(side="left")

        self.env_status_label = tk.Label(
            self.status_bar_frame, text=tr("env_status_placeholder", "Environment: -"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption, anchor="w", padx=16, pady=6
        )
        self.env_status_label.pack(side="left")

        self.qnn_status_label = tk.Label(
            self.status_bar_frame, text=tr("qnn_status_placeholder", "QNN: -"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption, anchor="w", padx=16, pady=6
        )
        self.qnn_status_label.pack(side="left")

        self.queue_status_label = tk.Label(
            self.status_bar_frame, text=tr("queue_status_placeholder", "Queue: 0 Job(s)"),
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
        canny_low, canny_high, cond_scale = self._get_controlnet_params()
        self._upscale_requested_for_job = bool(self.upscale_2x_var.get())

        self.controller.update_parameters(
            prompt=prompt, negative_prompt=neg_prompt,
            seed=seed, steps=steps, cfg=cfg,
            width=width, height=height, selected_model=selected_model,
            sampler=sampler, scheduler=scheduler, batch_size=batch_size,
            input_image_path=self.controller.model.state.input_image_path,
            controlnet_enabled=bool(self.canny_supported and self.active_tab == "canny"),
            canny_low_threshold=canny_low,
            canny_high_threshold=canny_high,
            controlnet_conditioning_scale=cond_scale,
        )

        is_valid, msg = self.controller.generation_controller.validate_session()
        if not is_valid:
            self.controller.model.update_state(status=f"error: {msg}")
            self.refresh()
            messagebox.showerror(tr("validation_error", "Validierungsfehler"), msg)
            return

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
            def progress_cb(percent: float, stage: str) -> None:
                self._generation_events.put(("progress", (percent, stage)))

            result = self.controller.generate_image(notify_workflow=False, progress_callback=progress_cb)
            if (
                self._upscale_requested_for_job
                and result.success
                and result.status != "CANCELLED"
                and result.image_path
            ):
                try:
                    result.metadata["upscaled_2x_image_path"] = (
                        self.controller.upscale_generated_image_2x(result.image_path)
                    )
                except Exception as error:
                    logger.exception("Optional RealESRGAN 2x upscale failed")
                    result.metadata["upscale_2x_error"] = str(error)
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
        self._set_progress(self._progress_percent, tr("status_cancelled", "CANCELLED"), self._step_text())
        self._configure_if_alive(self.status_label, text=tr("status_prefix", "Status: {status}", status=tr("status_cancelled", "CANCELLED")))
        self._configure_if_alive(self.insp_gen_status, text=tr("status_cancelled", "CANCELLED"))

    def _schedule_result_poll(self) -> None:
        if not self._is_view_alive():
            return
        self._result_after_id = self.after(250, self._poll_generation_events)

    def _poll_generation_events(self) -> None:
        if not self._is_view_alive():
            return

        has_more = True
        while has_more:
            try:
                event, payload = self._generation_events.get_nowait()
                if event == "result":
                    self._handle_generation_result(payload)
                elif event == "error":
                    self._handle_generation_error(payload)
                elif event == "progress":
                    percent, stage = payload
                    self._handle_generation_progress(percent, stage)
            except queue.Empty:
                has_more = False

        if self._generation_running:
            self._schedule_result_poll()

    def _handle_generation_result(self, result) -> None:
        if not self._is_view_alive():
            return

        self._generation_running = False
        self._cancel_progress_tick()
        cancelled = result.status == "CANCELLED"
        output_path = Path(result.image_path) if result.image_path else None
        presentable_success = bool(
            result.success
            and not cancelled
            and output_path is not None
            and output_path.is_file()
        )
        if result.success and not cancelled and not presentable_success:
            result.success = False
            result.message = tr(
                "generation_output_missing",
                "Die Generierung wurde beendet, aber die Bilddatei fehlt.",
            )
            self.controller.model.update_state(status=f"error: {result.message}")
        
        if presentable_success:
            self._progress_current_step = self._progress_total_steps

        if cancelled:
            self._set_progress(self._progress_percent, tr("status_cancelled", "CANCELLED"), self._step_text())
        else:
            self._set_progress(100, tr("status_completed", "Fertig") if presentable_success else tr("status_failed", "Fehler"), self._step_text())
        self._set_generation_busy(False)

        if presentable_success:
            self._append_generation_diagnostic(result, "before_finish_callback")
            self._notify_generation_finished(result)
            self._append_generation_diagnostic(result, "after_finish_callback")
            upscale_error = result.metadata.get("upscale_2x_error")
            if upscale_error:
                messagebox.showwarning(
                    tr("upscale_2x_title", "2× Upscaling"),
                    tr(
                        "upscale_2x_failed",
                        "Das Originalbild wurde gespeichert, aber das optionale 2×-Upscaling ist fehlgeschlagen: {error}",
                        error=upscale_error,
                    ),
                )
        elif not cancelled:
            self._append_generation_diagnostic(result, "generation_failed", result.message)
            messagebox.showerror(tr("nav_ai_generate", "KI-Generierung"), result.message)

        self.refresh()

    def _handle_generation_error(self, error: object) -> None:
        if not self._is_view_alive():
            return

        self._generation_running = False
        self._cancel_progress_tick()
        self.controller.model.update_state(status=f"error: {error}")
        self._set_progress(100, "Fehler", self._step_text())
        self._set_generation_busy(False)
        messagebox.showerror(tr("nav_ai_generate", "KI-Generierung"), str(error))
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
        status_text = localize_runtime_text(
            "generating" if busy else self.controller.get_state().status
        )
        status_text_lower = status_text.lower()
        if status_text_lower == "idle":
            status_text = tr("ready", "Bereit")
        elif status_text_lower in ("running", "generating", "generierung läuft"):
            status_text = tr("status_generating", "Generierung läuft")
        elif status_text_lower in ("cancelled", "canceled"):
            status_text = tr("status_cancelled", "CANCELLED")
        elif status_text_lower in ("completed", "finished", "success"):
            status_text = tr("status_completed", "Fertig")
        elif status_text_lower in ("error", "failed"):
            status_text = tr("status_failed", "Fehler")

        self._configure_if_alive(self.status_label, text=tr("status_prefix", "Status: {status}", status=status_text))
        self._configure_if_alive(self.insp_gen_status, text=status_text)

    def _layout_generation_actions(self, busy: bool) -> None:
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
        pass

    def _handle_generation_progress(self, percent: float, stage: str) -> None:
        if not self._is_view_alive() or not self._generation_running:
            return

        step_text = "-"
        if "Schritt " in stage:
            try:
                parts = stage.split("Schritt ")[1].split(")...")[0]
                step_text = f"{tr('step', 'Schritt')} {parts}"
            except Exception:
                step_text = "-"

        self._set_progress(percent, stage, step_text)
        self.controller.model.update_state(status=stage)
        self._configure_if_alive(self.status_label, text=tr("status_prefix", "Status: {status}", status=stage))
        self._configure_if_alive(self.insp_gen_status, text=stage)

    def _cancel_progress_tick(self) -> None:
        if self._progress_after_id and self._is_view_alive():
            try:
                self.after_cancel(self._progress_after_id)
            except Exception:
                pass
        self._progress_after_id = None

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
            from engine.asset_files import copy_asset_with_sidecar
            initial_name = Path(response.image_path).name
            dest = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png")],
                initialfile=initial_name
            )
            if dest:
                try:
                    copy_asset_with_sidecar(response.image_path, dest)
                except Exception as e:
                    logger.error(f"Failed to save image copy: {e}")

    def _on_open_explorer(self) -> None:
        """Opens Windows Explorer with the generated image file selected."""
        response = getattr(self.controller, "last_response", None)
        if response and response.image_path:
            path = Path(response.image_path).resolve()
            if path.exists():
                subprocess.run(f'explorer /select,"{path}"')

    def _enable_action_buttons(self, enable: bool) -> None:
        state = "normal" if enable else "disabled"
        fg_color = PHOENIX_THEME.text_primary if enable else PHOENIX_THEME.text_disabled

        for btn in (self.btn_open_library, self.btn_open_review, self.btn_save_as, self.btn_open_explorer):
            btn.configure(state=state, fg=fg_color)

    # ==================================================================
    # REFRESH
    # ==================================================================

    def refresh(self) -> None:
        if hasattr(self.controller, "repository") and self.controller.repository is not None:
            self.controller.repository.load_repository()

        state = self.controller.get_state()
        if not self._generation_running:
            localized_status = localize_runtime_text(state.status)
            self.status_label.configure(text=tr("status_prefix", "Status: {status}", status=localized_status))

        active_backend_name = "None"
        queued_count = 0

        gen_ctrl = getattr(self.controller, "generation_controller", None)
        if gen_ctrl is not None:
            queued_count = gen_ctrl.queue.get_queued_count()
            active_backend_name = (
                gen_ctrl.backend_manager.get_active_execution_provider_label()
            )

        active_model_id = self.controller.repository.get_active_model_id()
        if (
            active_model_id
            and self.model_var.get() != active_model_id
            and not getattr(self, "_in_model_change", False)
        ):
            self.model_var.set(active_model_id)
            state = self.controller.get_state()

        self.insp_model.configure(text=state.selected_model if state.selected_model else "-")
        self.insp_backend.configure(text=active_backend_name)
        if not self._generation_running:
            self.insp_gen_status.configure(text=localize_runtime_text(state.status))
        self.insp_queue.configure(
            text=tr("job_count", "{count} Job(s)", count=queued_count)
        )

        self.insp_size.configure(text=f"{state.width} × {state.height}")
        self.insp_steps.configure(text=str(state.steps))
        self.insp_cfg.configure(text=str(state.cfg))
        self.insp_seed.configure(text=str(state.seed))
        self.insp_sampler.configure(text=self.sampler_var.get())
        self.insp_scheduler.configure(text=self.scheduler_var.get())

        self.model_status_label.configure(text=tr("model_prefix", "Modell: {model}", model=state.selected_model if state.selected_model else "-"))
        self.backend_status_label.configure(text=tr("backend_prefix", "Backend: {backend}", backend=active_backend_name))
        self.queue_status_label.configure(text=tr("queue_prefix", "Queue: {jobs} Job(s)", jobs=queued_count))

        env_text = tr("env_status_placeholder", "Environment: -")
        qnn_text = tr("qnn_status_placeholder", "QNN: -")
        if gen_ctrl is not None and getattr(gen_ctrl, "backend_manager", None) is not None:
            res = gen_ctrl.backend_manager.get_discovery_result()
            if res:
                env_text = tr("env_status_prefix", "Environment: {env}", env=f"{res.os_name} {res.architecture}")
                qnn_status_str = tr("home_found", "Gefunden") if res.qnn_sdk_found else tr("home_not_found", "Nicht gefunden")
                qnn_text = tr("qnn_status_prefix", "QNN: {status}", status=qnn_status_str)

        self.env_status_label.configure(text=env_text)
        self.qnn_status_label.configure(text=qnn_text)

        for widget in self.preview_center.winfo_children():
            widget.destroy()

        last_resp = getattr(self.controller, "last_response", None)
        has_preview = False
        if last_resp and last_resp.success and last_resp.image_path:
            img_path = Path(last_resp.image_path)
            self._current_preview_image_path = img_path
            if img_path.exists():
                try:
                    from PIL import Image, ImageTk
                    w = self.preview_center.winfo_width()
                    h = self.preview_center.winfo_height()
                    if w < 50 or h < 50:
                        w, h = 250, 250
                    with Image.open(img_path) as pil_img:
                        img_w, img_h = pil_img.size
                        scale = min(w / img_w, h / img_h)
                        new_w = max(10, int(img_w * scale))
                        new_h = max(10, int(img_h * scale))
                        resized_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        self._preview_photo = ImageTk.PhotoImage(resized_img)

                    img_label = tk.Label(
                        self.preview_center,
                        image=self._preview_photo,
                        bg=PHOENIX_THEME.content_bg,
                        cursor="hand2"
                    )
                    img_label.is_image_label = True
                    img_label.place(relx=0.5, rely=0.5, anchor="center")
                    img_label.bind("<Button-1>", lambda e: self._open_lightbox_preview(img_path))

                    def _on_img_enter(e):
                        img_label.configure(bg=PHOENIX_THEME.accent)
                    def _on_img_leave(e):
                        img_label.configure(bg=PHOENIX_THEME.content_bg)

                    img_label.bind("<Enter>", _on_img_enter)
                    img_label.bind("<Leave>", _on_img_leave)

                    has_preview = True
                except Exception as e:
                    logger.error(f"Failed to load preview image: {e}")

        if not has_preview:
            self._current_preview_image_path = None
            from resources.icons import IconManager
            placeholder_container = tk.Frame(self.preview_center, bg=PHOENIX_THEME.content_bg)
            placeholder_container.place(relx=0.5, rely=0.5, anchor="center")

            tk.Label(
                placeholder_container, text=IconManager.get_symbol("image"),
                bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.accent,
                font=(PHOENIX_THEME.font_title[0], 20, "bold"),
            ).pack(anchor="center", pady=(0, 2))

            tk.Label(
                placeholder_container, text=tr("home_no_images_generated", "No image generated"),
                bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_small, justify="center"
            ).pack(anchor="center")

        self._enable_action_buttons(has_preview)
        self._update_dnd_preview()

    def _open_lightbox_preview(self, img_path: Path) -> None:
        """Opens a large popup window showing the generated image in full size."""
        if not img_path.exists():
            return

        popup = tk.Toplevel(self)
        BrandManager.apply_window_icon(popup)
        popup.title("Vorschau – " + img_path.name)
        popup.configure(bg=PHOENIX_THEME.card_bg)

        try:
            from PIL import Image, ImageTk
            with Image.open(img_path) as pil_img:
                w, h = pil_img.size

            main_w = self.winfo_toplevel().winfo_width()
            main_h = self.winfo_toplevel().winfo_height()
            max_w = int(main_w * 0.85) if main_w > 300 else 800
            max_h = int(main_h * 0.85) if main_h > 300 else 800

            scale = min(max_w / w, max_h / h, 1.0)
            disp_w = int(w * scale)
            disp_h = int(h * scale)

            x = self.winfo_toplevel().winfo_rootx() + (main_w - disp_w) // 2
            y = self.winfo_toplevel().winfo_rooty() + (main_h - disp_h) // 2
            popup.geometry(f"{disp_w}x{disp_h}+{x}+{y}")

            with Image.open(img_path) as pil_img:
                resized = pil_img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
                lightbox_photo = ImageTk.PhotoImage(resized)

            lbl = tk.Label(popup, image=lightbox_photo, bg=PHOENIX_THEME.card_bg)
            lbl.image = lightbox_photo
            lbl.pack(fill="both", expand=True)

        except Exception as e:
            logger.error("Failed to render lightbox: %s", e)
            popup.destroy()

        popup.bind("<Escape>", lambda e: popup.destroy())

    def _on_preview_resize(self, event: tk.Event = None) -> None:
        w = self.preview_center.winfo_width()
        h = self.preview_center.winfo_height()
        if w < 50 or h < 50:
            return

        img_path = getattr(self, "_current_preview_image_path", None)
        if not img_path or not img_path.exists():
            return

        try:
            from PIL import Image, ImageTk
            with Image.open(img_path) as pil_img:
                img_w, img_h = pil_img.size
                scale = min(w / img_w, h / img_h)
                new_w = max(10, int(img_w * scale))
                new_h = max(10, int(img_h * scale))
                resized_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                self._preview_photo = ImageTk.PhotoImage(resized_img)

            for widget in self.preview_center.winfo_children():
                if isinstance(widget, tk.Label) and getattr(widget, "is_image_label", False):
                    widget.configure(image=self._preview_photo)
                    break
        except Exception:
            pass

    def _on_model_changed(self, *args) -> None:
        if getattr(self, "_in_model_change", False):
            return
        new_model = self.model_var.get()
        self._change_active_model(new_model)

    def _change_active_model(self, new_model: str) -> None:
        if getattr(self, "_in_model_change", False):
            return

        self._in_model_change = True
        try:
            self._update_model_description(new_model)
            if hasattr(self, "seed_entry"):
                self._apply_generation_contract(new_model)

            self._ref_image_path = None
            self._dnd_photo_ref = None
            self._dnd_error_message = None

            if getattr(self, "_canny_debounce_id", None) is not None:
                try:
                    self.after_cancel(self._canny_debounce_id)
                except Exception:
                    pass
                self._canny_debounce_id = None

            if getattr(self, "_canny_poll_id", None) is not None:
                try:
                    self.after_cancel(self._canny_poll_id)
                except Exception:
                    pass
                self._canny_poll_id = None

            while not self._canny_queue.empty():
                try:
                    self._canny_queue.get_nowait()
                except queue.Empty:
                    break

            self._clear_canny_preview()

            self.canny_low_var.set(50)
            self.canny_high_var.set(150)
            self.conditioning_strength_var.set(1.0)

            try:
                prompt = self.prompt_text.get("1.0", "end-1c").strip()
                neg_prompt = self.neg_prompt_text.get("1.0", "end-1c").strip()
                try:
                    seed = int(self.seed_entry.get().strip() or -1)
                except ValueError:
                    seed = -1
                steps = int(self.steps_scale.get())
                cfg = float(self.cfg_scale.get())
                try:
                    width = int(self.width_var.get() or 512)
                except ValueError:
                    width = 512
                try:
                    height = int(self.height_var.get() or 512)
                except ValueError:
                    height = 512
                sampler = self.sampler_var.get()
                scheduler = self.scheduler_var.get()
                try:
                    batch_size = int(self.batch_var.get() or 1)
                except ValueError:
                    batch_size = 1
            except Exception:
                prompt, neg_prompt = "", ""
                seed, steps, cfg, width, height = -1, 20, 7.5, 512, 512
                sampler, scheduler, batch_size = "Euler", "Euler", 1

            canny_low, canny_high, cond_scale = self._get_controlnet_params()

            self.controller.update_parameters(
                prompt=prompt, negative_prompt=neg_prompt,
                seed=seed, steps=steps, cfg=cfg,
                width=width, height=height, selected_model=new_model,
                sampler=sampler, scheduler=scheduler, batch_size=batch_size,
                input_image_path=None,
                canny_low_threshold=canny_low,
                canny_high_threshold=canny_high,
                controlnet_conditioning_scale=cond_scale,
            )

            current_status = self.controller.model.state.status
            if current_status and ("Fehler" in current_status or "Validierung" in current_status):
                self.controller.model.update_state(status="ready")

            self.refresh()
        finally:
            self._in_model_change = False

    def _update_model_description(self, model_id: str) -> None:
        model = self.controller.repository.get_model(model_id)
        description = model.get("description", "") if model else ""
        description_key = f"model_description_{model_id.replace('-', '_')}"
        self.model_description_var.set(tr(description_key, str(description)))

    def _update_parameter_description(self, *_args) -> None:
        """Keep the compact generation-parameter description in sync."""
        self.parameter_description_var.set(
            f"{self.width_var.get()} × {self.height_var.get()}  •  "
            f"{tr('steps_label_colon', 'Schritte:').rstrip(':')} {self.steps_var.get()}  •  "
            f"CFG {self.cfg_var.get():g}  •  "
            f"{tr('seed_label_colon', 'Seed:').rstrip(':')} {self.seed_var.get()}  •  "
            f"{self.sampler_var.get()} / {self.scheduler_var.get()}"
        )

    def _on_image_drop(self, event) -> None:
        if not event.data:
            return
        dropped_paths = self.tk.splitlist(event.data)
        if dropped_paths:
            path_str = str(dropped_paths[0])
            path_str = path_str.strip('{}""\'\'')
            path_str = str(Path(path_str).resolve())
            self._load_reference_image(path_str)

    def _on_dnd_click(self, event=None) -> None:
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title=tr("reference_image_dialog_title", "Referenzbild auswählen"),
            filetypes=[
                ("Bilddateien", "*.png *.jpg *.jpeg *.webp"),
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg *.jpeg"),
                ("WebP Image", "*.webp"),
                ("Alle Dateien", "*.*")
            ]
        )
        if file_path:
            self._load_reference_image(file_path)

    def _load_reference_image(self, file_path: str) -> None:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            self._clear_reference_image_state(
                error_message=tr(
                    "reference_file_invalid",
                    "Datei existiert nicht oder ist kein Bild.",
                )
            )
            return

        ext = path.suffix.lower()
        if ext not in (".png", ".jpg", ".jpeg", ".webp"):
            self._clear_reference_image_state(
                error_message=tr(
                    "reference_format_unsupported",
                    "Format nicht unterstützt (nur PNG, JPG, JPEG, WebP).",
                )
            )
            messagebox.showerror(
                tr("invalid_format_title", "Ungültiges Format"),
                tr(
                    "supported_image_formats_only",
                    "Es werden nur Bilddateien in den Formaten PNG, JPG, JPEG und WebP unterstützt.",
                ),
            )
            return

        try:
            from PIL import Image
            with Image.open(path) as img:
                img.verify()
            with Image.open(path) as img:
                img.convert('L')

            self._ref_image_path = str(path)
            self._dnd_error_message = None

            prompt = self.prompt_text.get("1.0", "end-1c").strip()
            neg_prompt = self.neg_prompt_text.get("1.0", "end-1c").strip()
            try:
                seed = int(self.seed_entry.get().strip() or -1)
            except ValueError:
                seed = -1
            steps = int(self.steps_scale.get())
            cfg = float(self.cfg_scale.get())
            try:
                width = int(self.width_var.get() or 512)
            except ValueError:
                width = 512
            try:
                height = int(self.height_var.get() or 512)
            except ValueError:
                height = 512
            selected_model = self.model_var.get()
            sampler = self.sampler_var.get()
            scheduler = self.scheduler_var.get()
            try:
                batch_size = int(self.batch_var.get() or 1)
            except ValueError:
                batch_size = 1

            canny_low, canny_high, cond_scale = self._get_controlnet_params()

            self.controller.update_parameters(
                prompt=prompt, negative_prompt=neg_prompt,
                seed=seed, steps=steps, cfg=cfg,
                width=width, height=height, selected_model=selected_model,
                sampler=sampler, scheduler=scheduler, batch_size=batch_size,
                input_image_path=self._ref_image_path,
                canny_low_threshold=canny_low,
                canny_high_threshold=canny_high,
                controlnet_conditioning_scale=cond_scale,
            )
            self.refresh()
        except Exception as e:
            logger.exception("Failed to load reference image: %s", file_path)
            self._clear_reference_image_state(error_message=f"Fehler: {str(e)}")
            messagebox.showerror(
                tr("image_load_failed_title", "Fehler beim Laden"),
                tr("image_load_failed_message", "Das Bild konnte nicht geladen werden:\n{error}", error=e),
            )

    def _get_controlnet_params(self) -> tuple[int, int, float]:
        try:
            canny_low = int(self.canny_low_var.get())
        except (ValueError, AttributeError):
            canny_low = 50
        try:
            canny_high = int(self.canny_high_var.get())
        except (ValueError, AttributeError):
            canny_high = 150
        try:
            cond_scale = float(self.conditioning_strength_var.get())
        except (ValueError, AttributeError):
            cond_scale = 1.0
        return canny_low, canny_high, cond_scale

    def _remove_reference_image(self) -> None:
        self._clear_reference_image_state()

    def _clear_reference_image_state(self, error_message: str | None = None) -> None:
        self._ref_image_path = None
        self._dnd_photo_ref = None
        self._dnd_error_message = error_message

        if getattr(self, "_canny_debounce_id", None) is not None:
            try:
                self.after_cancel(self._canny_debounce_id)
            except Exception:
                pass
            self._canny_debounce_id = None

        if getattr(self, "_canny_poll_id", None) is not None:
            try:
                self.after_cancel(self._canny_poll_id)
            except Exception:
                pass
            self._canny_poll_id = None

        while not self._canny_queue.empty():
            try:
                self._canny_queue.get_nowait()
            except queue.Empty:
                break

        self._clear_canny_preview()

        try:
            prompt = self.prompt_text.get("1.0", "end-1c").strip()
            neg_prompt = self.neg_prompt_text.get("1.0", "end-1c").strip()
            try:
                seed = int(self.seed_entry.get().strip() or -1)
            except ValueError:
                seed = -1
            steps = int(self.steps_scale.get())
            cfg = float(self.cfg_scale.get())
            try:
                width = int(self.width_var.get() or 512)
            except ValueError:
                width = 512
            try:
                height = int(self.height_var.get() or 512)
            except ValueError:
                height = 512
            selected_model = self.model_var.get()
            sampler = self.sampler_var.get()
            scheduler = self.scheduler_var.get()
            try:
                batch_size = int(self.batch_var.get() or 1)
            except ValueError:
                batch_size = 1
        except Exception:
            prompt, neg_prompt = "", ""
            seed, steps, cfg, width, height = -1, 20, 7.5, 512, 512
            sampler, scheduler, batch_size = "Euler", "Euler", 1

        canny_low, canny_high, cond_scale = self._get_controlnet_params()

        self.controller.update_parameters(
            prompt=prompt, negative_prompt=neg_prompt,
            seed=seed, steps=steps, cfg=cfg,
            width=width, height=height, selected_model=selected_model,
            sampler=sampler, scheduler=scheduler, batch_size=batch_size,
            input_image_path=None,
            canny_low_threshold=canny_low,
            canny_high_threshold=canny_high,
            controlnet_conditioning_scale=cond_scale,
        )

        current_status = self.controller.model.state.status
        if current_status and ("Fehler" in current_status or "Validierung" in current_status):
            self.controller.model.update_state(status="ready")

        self.refresh()

    def _update_dnd_preview(self) -> None:
        if not hasattr(self, "_dnd_preview_label") or not self._dnd_preview_label or not self._dnd_preview_label.winfo_exists():
            return

        input_path = self.controller.model.state.input_image_path
        error_msg = getattr(self, "_dnd_error_message", None)

        if error_msg:
            new_state = "error"
        elif input_path:
            new_state = "loaded"
        else:
            new_state = "empty"

        supports_controlnet = False
        model_id = self.model_var.get()
        model_meta = self.controller.repository.get_model(model_id)
        if model_meta:
            supports_controlnet = model_meta.get("capabilities", {}).get("controlnet", False)

        # Update labels name and resolution
        if new_state == "error":
            from engine.theme_manager import ThemeManager
            error_color = ThemeManager.palette().error
            self._dnd_preview_label.configure(image="", text=tr("error_loading_dnd", "Fehler beim Laden"), fg=error_color)
            self._dnd_name_label.configure(text=tr("error_loading_dnd", "Fehler beim Laden"), fg=error_color)
            
            display_err = error_msg or ""
            if len(display_err) > 35:
                display_err = display_err[:32] + "..."
            self._dnd_resolution_label.configure(text=display_err, fg=PHOENIX_THEME.text_muted)
            self.btn_remove_image.configure(state="disabled")
            self._clear_canny_preview()
            
        elif new_state == "loaded":
            filename = tr("unknown", "Unbekannt")
            resolution = "-"
            photo_image = None
            try:
                from PIL import Image, ImageTk
                from pathlib import Path
                path = Path(input_path)
                if path.exists() and path.is_file():
                    filename = path.name
                    with Image.open(path) as img:
                        width, height = img.size
                        resolution = f"{width} × {height}"
                        img.thumbnail((140, 140))
                        photo_image = ImageTk.PhotoImage(img)
                else:
                    filename = "Datei nicht gefunden"
            except Exception as e:
                logger.error("Failed to render DND preview thumbnail: %s", e)
                filename = "Fehler beim Laden"

            self._dnd_photo_ref = photo_image
            if photo_image is not None:
                self._dnd_preview_label.configure(image=photo_image, text="")
            else:
                from engine.theme_manager import ThemeManager
                self._dnd_preview_label.configure(image="", text=tr("error", "Fehler"), fg=ThemeManager.palette().error)

            def shorten_filename(name: str, max_len: int = 24) -> str:
                if len(name) <= max_len:
                    return name
                from pathlib import Path
                p = Path(name)
                stem = p.stem
                suffix = p.suffix
                stem_len = max_len - len(suffix) - 3
                if stem_len > 0:
                    return f"{stem[:stem_len]}...{suffix}"
                return name[:max_len-3] + "..."

            display_filename = shorten_filename(filename)
            self._dnd_name_label.configure(text=display_filename, fg=PHOENIX_THEME.text_primary)
            self._dnd_resolution_label.configure(text=resolution, fg=PHOENIX_THEME.text_muted)
            self.btn_remove_image.configure(state="normal")

            if supports_controlnet:
                self._trigger_canny_preview_update()
        else:
            # empty
            self._dnd_photo_ref = None
            self._dnd_preview_label.configure(image="", text=tr("no_image_selected", "Kein Bild ausgewählt"))
            self._dnd_name_label.configure(text="")
            self._dnd_resolution_label.configure(text="")
            self.btn_remove_image.configure(state="disabled")
            self._clear_canny_preview()

        self._dnd_visible_state = new_state
        self._dnd_rendered_input_path = input_path
        self._dnd_rendered_supports_controlnet = supports_controlnet

    def _on_controlnet_enable_changed(self, *args) -> None:
        enabled = bool(self.canny_supported and self.controlnet_canny_var.get())
        self.controller.model.update_state(controlnet_enabled=enabled)
        self.controller.generation_controller.update_session(
            controlnet_enabled=enabled
        )
        if enabled:
            if hasattr(self, "controlnet_layout_frame") and self.controlnet_layout_frame and self.controlnet_layout_frame.winfo_exists():
                self.controlnet_layout_frame.pack(fill="both", expand=True, padx=20, pady=5)
                self.dnd_subtitle.pack(fill="x", pady=(0, 5))
                self.dnd_card.pack(fill="x", pady=(0, 10))
                self.controlnet_frame.pack(fill="x", pady=5)
                self._update_dnd_preview()
        else:
            if hasattr(self, "controlnet_layout_frame") and self.controlnet_layout_frame and self.controlnet_layout_frame.winfo_exists():
                self.controlnet_layout_frame.pack_forget()
                self.dnd_subtitle.pack_forget()
                self.dnd_card.pack_forget()
                self.controlnet_frame.pack_forget()


    def _on_canny_param_changed(self, *args) -> None:
        if getattr(self, "_in_model_change", False):
            return
        if not self.controller.model.state.input_image_path:
            return

        if getattr(self, "_canny_debounce_id", None) is not None:
            try:
                self.after_cancel(self._canny_debounce_id)
            except Exception:
                pass
            self._canny_debounce_id = None

        self._canny_debounce_id = self.after(150, self._trigger_canny_preview_update)

    def _trigger_canny_preview_update(self) -> None:
        self._canny_debounce_id = None
        input_path = self.controller.model.state.input_image_path
        if not input_path:
            self._clear_canny_preview()
            return

        try:
            low = int(self.canny_low_var.get())
            high = int(self.canny_high_var.get())
        except (ValueError, AttributeError):
            low, high = 50, 150

        if (
            getattr(self, "_canny_rendered_path", None) == input_path
            and getattr(self, "_canny_rendered_low", None) == low
            and getattr(self, "_canny_rendered_high", None) == high
            and getattr(self, "_dnd_canny_photo_ref", None) is not None
        ):
            return

        if low >= high:
            self._show_canny_error("Low Threshold >= High Threshold")
            return

        self._clear_canny_error()
        self._set_canny_preview_stale()

        req_id = time.time()
        self._latest_canny_req_id = req_id

        def worker():
            try:
                from engine.controlnet_canny_backend import canny_edge_detector
                edges = canny_edge_detector(input_path, low_threshold=low, high_threshold=high)
                from PIL import Image
                edges_img = Image.fromarray(edges)
                self._canny_queue.put(("ready", (req_id, input_path, low, high, edges_img)))
            except Exception as e:
                logger.exception("Error in Canny background worker thread")
                self._canny_queue.put(("error", (req_id, str(e))))

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        self._poll_canny_queue()

    def _poll_canny_queue(self) -> None:
        if getattr(self, "_canny_poll_id", None) is not None:
            try:
                self.after_cancel(self._canny_poll_id)
            except Exception:
                pass
            self._canny_poll_id = None

        has_more = True
        while has_more:
            try:
                event_type, payload = self._canny_queue.get_nowait()
                if event_type == "ready":
                    req_id, path, low, high, edges_img = payload
                    self._on_canny_preview_ready(req_id, path, low, high, edges_img)
                elif event_type == "error":
                    req_id, err_str = payload
                    self._on_canny_preview_error(req_id, err_str)
            except queue.Empty:
                has_more = False

        latest_id = getattr(self, "_latest_canny_req_id", None)
        rendered_path = getattr(self, "_canny_rendered_path", None)
        rendered_low = getattr(self, "_canny_rendered_low", None)
        rendered_high = getattr(self, "_canny_rendered_high", None)
        input_path = self.controller.model.state.input_image_path

        if not input_path:
            return

        if latest_id is not None:
            try:
                low = int(self.canny_low_var.get())
                high = int(self.canny_high_var.get())
            except (ValueError, AttributeError):
                low, high = 50, 150

            if (
                rendered_path != input_path
                or rendered_low != low
                or rendered_high != high
            ):
                self._canny_poll_id = self.after(50, self._poll_canny_queue)

    def _on_canny_preview_ready(self, req_id: float, path: str, low: int, high: int, edges_img) -> None:
        if getattr(self, "_latest_canny_req_id", None) != req_id:
            return
        if self.controller.model.state.input_image_path != path:
            return

        try:
            from PIL import ImageTk
            edges_img.thumbnail((140, 140))
            photo = ImageTk.PhotoImage(edges_img)

            self._dnd_canny_photo_ref = photo
            self._canny_rendered_path = path
            self._canny_rendered_low = low
            self._canny_rendered_high = high

            if hasattr(self, "_dnd_canny_preview_label") and self._dnd_canny_preview_label.winfo_exists():
                self._dnd_canny_preview_label.configure(image=photo, text="")

            if hasattr(self, "_dnd_canny_status_label") and self._dnd_canny_status_label.winfo_exists():
                self._dnd_canny_status_label.configure(text=tr("preview_current", "Vorschau aktuell"), fg=PHOENIX_THEME.text_muted)
        except Exception as e:
            logger.error("Failed to render Canny preview thumbnail: %s", e)
            self._on_canny_preview_error(req_id, str(e))

    def _on_canny_preview_error(self, req_id: float, error_msg: str) -> None:
        if getattr(self, "_latest_canny_req_id", None) != req_id:
            return
        self._show_canny_error(error_msg)

    def _show_canny_error(self, error_msg: str) -> None:
        self._dnd_canny_photo_ref = None
        self._canny_rendered_path = None
        self._canny_rendered_low = None
        self._canny_rendered_high = None

        from engine.theme_manager import ThemeManager
        error_color = ThemeManager.palette().error

        if hasattr(self, "_dnd_canny_preview_label") and self._dnd_canny_preview_label.winfo_exists():
            self._dnd_canny_preview_label.configure(image="", text=tr("error", "Fehler"), fg=error_color)

        if hasattr(self, "_dnd_canny_status_label") and self._dnd_canny_status_label.winfo_exists():
            display_err = error_msg
            if len(display_err) > 35:
                display_err = display_err[:32] + "..."
            self._dnd_canny_status_label.configure(text=f"⚠️ {display_err}", fg=error_color)

    def _clear_canny_error(self) -> None:
        if hasattr(self, "_dnd_canny_status_label") and self._dnd_canny_status_label.winfo_exists():
            self._dnd_canny_status_label.configure(text="", fg=PHOENIX_THEME.text_muted)

    def _set_canny_preview_stale(self) -> None:
        if hasattr(self, "_dnd_canny_preview_label") and self._dnd_canny_preview_label.winfo_exists():
            self._dnd_canny_preview_label.configure(image="", text="⏳", fg=PHOENIX_THEME.text_secondary)
        if hasattr(self, "_dnd_canny_status_label") and self._dnd_canny_status_label.winfo_exists():
            self._dnd_canny_status_label.configure(text=tr("calculating", "Berechne..."), fg=PHOENIX_THEME.text_secondary)

    def _clear_canny_preview(self) -> None:
        self._dnd_canny_photo_ref = None
        self._canny_rendered_path = None
        self._canny_rendered_low = None
        self._canny_rendered_high = None
        if hasattr(self, "_dnd_canny_preview_label") and self._dnd_canny_preview_label.winfo_exists():
            self._dnd_canny_preview_label.configure(image="", text="-")
        if hasattr(self, "_dnd_canny_status_label") and self._dnd_canny_status_label.winfo_exists():
            self._dnd_canny_status_label.configure(text="")

    def _show_prompt_history_popup(self) -> None:
        history = self.controller.load_prompt_history(return_dicts=True)
        if not history:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label=tr("history_empty", "Verlauf leer"), state="disabled")
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

        for entry in history:
            prompt = entry.get("prompt", "") if isinstance(entry, dict) else str(entry)
            display_label = prompt if len(prompt) < 50 else prompt[:47] + "..."
            menu.add_command(
                label=display_label,
                command=lambda e=entry: self._load_prompt_from_history(e)
            )

        x = self.history_btn.winfo_rootx()
        y = self.history_btn.winfo_rooty() + self.history_btn.winfo_height()
        menu.post(x, y)

    def _load_prompt_from_history(self, entry: str | dict) -> None:
        if isinstance(entry, dict):
            prompt = entry.get("prompt", "")
            neg_prompt = entry.get("negative_prompt", "")
            model_name = entry.get("model_name") or entry.get("model")
            width = entry.get("width")
            height = entry.get("height")
            steps = entry.get("steps")
            cfg = entry.get("cfg_scale") or entry.get("cfg")
            seed = entry.get("seed")
            batch = entry.get("batch", entry.get("batch_size"))
            sampler = entry.get("sampler")
            scheduler = entry.get("scheduler")

            self.prompt_text.delete("1.0", "end")
            self.prompt_text.insert("1.0", prompt)
            if hasattr(self, "_prompt_popup_text") and self._prompt_popup_text.winfo_exists():
                self._prompt_popup_text.delete("1.0", "end")
                self._prompt_popup_text.insert("1.0", prompt)

            if neg_prompt is not None:
                self.neg_prompt_text.delete("1.0", "end")
                self.neg_prompt_text.insert("1.0", neg_prompt)
                if (
                    hasattr(self, "_negative_prompt_popup_text")
                    and self._negative_prompt_popup_text.winfo_exists()
                ):
                    self._negative_prompt_popup_text.delete("1.0", "end")
                    self._negative_prompt_popup_text.insert("1.0", neg_prompt)

            if model_name:
                self.model_var.set(model_name)
                self._apply_generation_contract(model_name)

            controlnet_enabled = entry.get("controlnet_enabled", False)
            if controlnet_enabled:
                self.canny_low_var.set(entry.get("canny_low_threshold", 50))
                self.canny_high_var.set(entry.get("canny_high_threshold", 150))
                self.conditioning_strength_var.set(entry.get("controlnet_conditioning_scale", 1.0))
                ref_path = entry.get("reference_image_path")
                if ref_path:
                    self._load_reference_image(ref_path)
                else:
                    self._clear_reference_image_state()
                if self.canny_supported:
                    self._switch_tab("canny")
            else:
                self._clear_reference_image_state()
                if self.active_tab == "canny":
                    self._switch_tab("basic")

            if width is not None:
                self.width_var.set(str(width))
            if height is not None:
                self.height_var.set(str(height))
            if steps is not None:
                self.steps_var.set(int(steps))
            if cfg is not None:
                self.cfg_var.set(float(cfg))
            if seed is not None:
                self.seed_var.set(str(seed))
            if batch is not None:
                self.batch_var.set(str(batch))
            if sampler is not None:
                self.sampler_var.set(sampler)
            if scheduler is not None:
                self.scheduler_var.set(scheduler)
        else:
            self.prompt_text.delete("1.0", "end")
            self.prompt_text.insert("1.0", entry)
            if hasattr(self, "_prompt_popup_text") and self._prompt_popup_text.winfo_exists():
                self._prompt_popup_text.delete("1.0", "end")
                self._prompt_popup_text.insert("1.0", entry)

    def apply_generation_settings(self, settings: dict) -> None:
        self._load_prompt_from_history(self._normalize_preset_settings(settings))

    def _normalize_preset_settings(self, settings: dict) -> dict:
        """Fill fields omitted by older presets with the existing model defaults."""
        model_name = settings.get("model_name") or settings.get("model") or self.model_var.get()
        contract = self.controller.get_generation_parameters(model_name) or {}

        def contract_default(name: str, fallback):
            spec = contract.get(name)
            return spec.get("default", fallback) if isinstance(spec, dict) else fallback

        model_metadata = self.controller.repository.get_model(model_name) or {}
        defaults = {
            "prompt": "",
            "negative_prompt": "",
            "model_name": model_name,
            "backend": model_metadata.get("backend", ""),
            "seed": contract_default("seed", -1),
            "width": contract_default("width", 512),
            "height": contract_default("height", 512),
            "steps": contract_default("steps", 20),
            "cfg_scale": contract_default("cfg", 7.5),
            "sampler": contract_default("sampler", "Euler"),
            "scheduler": contract_default("scheduler", "Normal"),
            "batch": 1,
            "controlnet_enabled": False,
            "canny_low_threshold": 50,
            "canny_high_threshold": 150,
            "controlnet_conditioning_scale": 1.0,
            "reference_image_path": "",
        }
        normalized = dict(defaults)
        normalized.update(settings)
        if "batch" not in settings and "batch_size" in settings:
            normalized["batch"] = settings["batch_size"]
        return normalized

    def _ensure_progress_style(self) -> None:
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

    def _switch_tab(self, tab_name: str) -> None:
        if tab_name == "canny" and not self.canny_supported:
            return
        self.active_tab = tab_name
        controlnet_enabled = bool(self.canny_supported and tab_name == "canny")
        self.controller.model.update_state(controlnet_enabled=controlnet_enabled)
        self.controller.generation_controller.update_session(
            controlnet_enabled=controlnet_enabled
        )

        self.tab_basic_content.grid_remove()
        self.tab_canny_content.grid_remove()
        self.tab_advanced_content.grid_remove()

        if tab_name == "basic":
            self.tab_basic_content.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=8)
        elif tab_name == "canny":
            self.tab_canny_content.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=8)
        elif tab_name == "advanced":
            self.tab_advanced_content.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=8)

        self._update_tab_bar_visuals()

    def _update_tab_bar_visuals(self) -> None:
        buttons = [
            ("basic", self.btn_tab_basic),
            ("canny", self.btn_tab_canny),
            ("advanced", self.btn_tab_advanced),
        ]
        for name, btn in buttons:
            if name == self.active_tab:
                btn.is_active = True
                btn.normal_bg = PHOENIX_THEME.accent
                btn.normal_fg = PHOENIX_THEME.text_on_accent
                btn.configure(
                    bg=PHOENIX_THEME.accent,
                    fg=PHOENIX_THEME.text_on_accent,
                    activebackground=PHOENIX_THEME.accent,
                    activeforeground=PHOENIX_THEME.text_on_accent,
                    state="normal"
                )
            else:
                btn.is_active = False
                if name == "canny" and not self.canny_supported:
                    btn.configure(
                        bg=PHOENIX_THEME.elevated_bg,
                        fg=PHOENIX_THEME.text_disabled,
                        activebackground=PHOENIX_THEME.elevated_bg,
                        activeforeground=PHOENIX_THEME.text_disabled,
                        state="disabled"
                    )
                else:
                    btn.normal_bg = PHOENIX_THEME.elevated_bg
                    btn.normal_fg = PHOENIX_THEME.text_secondary
                    btn.configure(
                        bg=PHOENIX_THEME.elevated_bg,
                        fg=PHOENIX_THEME.text_secondary,
                        activebackground=PHOENIX_THEME.accent,
                        activeforeground=PHOENIX_THEME.text_on_accent,
                        state="normal"
                    )

    def _show_templates_popup(self) -> None:
        categories = self.controller.load_prompt_templates()
        if not categories:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label=tr("templates_empty", "Keine Vorlagen gefunden"), state="disabled")
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
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", prompt)
        if hasattr(self, "_prompt_popup_text") and self._prompt_popup_text.winfo_exists():
            self._prompt_popup_text.delete("1.0", "end")
            self._prompt_popup_text.insert("1.0", prompt)

    def _select_steps_preset(self, preset_name: str) -> None:
        self.active_steps_preset = preset_name

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
        presets = {
            "Schnell": self.btn_preset_schnell,
            "Standard": self.btn_preset_standard,
            "Beste Qualität": self.btn_preset_beste,
        }
        for name, btn in presets.items():
            if self.active_steps_preset == name:
                btn.is_active = True
                btn.normal_bg = PHOENIX_THEME.accent
                btn.normal_fg = PHOENIX_THEME.text_on_accent
                btn.configure(
                    bg=PHOENIX_THEME.accent,
                    fg=PHOENIX_THEME.text_on_accent,
                    activebackground=PHOENIX_THEME.accent,
                    activeforeground=PHOENIX_THEME.text_on_accent,
                )
            else:
                btn.is_active = False
                btn.normal_bg = PHOENIX_THEME.elevated_bg
                btn.normal_fg = PHOENIX_THEME.text_secondary
                btn.configure(
                    bg=PHOENIX_THEME.elevated_bg,
                    fg=PHOENIX_THEME.text_secondary,
                    activebackground=PHOENIX_THEME.elevated_bg,
                    activeforeground=PHOENIX_THEME.text_primary,
                )

    def _build_standard_dialog_header(
        self, popup: tk.Toplevel, parent: tk.Misc, title: str
    ) -> tk.Frame:
        """Create the shared title area used by standard work dialogs."""
        header = tk.Frame(parent, bg=PHOENIX_THEME.card_bg)
        header.pack(fill="x", pady=(0, 16))
        popup._standard_dialog_title = tk.Label(
            header, text=title, bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_card_title, anchor="w",
        )
        popup._standard_dialog_title.pack(fill="x")
        return header

    def _open_presets_popup(self) -> None:
        if hasattr(self, "_presets_popup") and self._presets_popup.winfo_exists():
            self._presets_popup.focus()
            return

        popup = tk.Toplevel(self)
        BrandManager.apply_window_icon(popup)
        popup.title(tr("presets_section_header", "Presets & Vorlagen"))
        popup.geometry("620x310")
        popup.minsize(540, 280)
        popup.configure(bg=PHOENIX_THEME.card_bg)
        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        self._presets_popup = popup

        container = tk.Frame(popup, bg=PHOENIX_THEME.card_bg)
        container.pack(fill="both", expand=True, padx=24, pady=20)
        self._build_standard_dialog_header(
            popup, container, tr("presets_section_header", "Presets & Vorlagen"),
        )

        preset_row = tk.Frame(container, bg=PHOENIX_THEME.surface)
        preset_row.pack(fill="x", pady=(0, 14), ipady=4)
        preset_row.grid_columnconfigure(0, weight=1)
        tk.Label(
            preset_row, text=tr("preset_load_label", "Preset wählen:"),
            bg=PHOENIX_THEME.surface, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small, anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
        self._preset_popup_dropdown = tk.OptionMenu(
            preset_row, self.selected_preset_var, *self.available_presets
        )
        self._preset_popup_dropdown.configure(
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat", bd=0, highlightthickness=0,
            font=PHOENIX_THEME.font_button,
        )
        self._preset_popup_dropdown.grid(
            row=1, column=0, sticky="ew", padx=14, pady=(0, 10)
        )

        preset_actions = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        preset_actions.pack(fill="x")
        preset_actions.grid_columnconfigure(0, weight=1)
        preset_actions.grid_columnconfigure(1, weight=1)
        preset_actions.grid_columnconfigure(2, weight=1)

        apply_btn = PhoenixButton(
            preset_actions, text=tr("apply_preset_btn", "Anwenden"),
            command=self._on_apply_preset, button_type="primary",
        )
        self._preset_apply_btn = apply_btn
        apply_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        rename_btn = PhoenixButton(
            preset_actions, text=tr("rename_preset_btn", "Umbenennen"),
            command=self._on_rename_preset, button_type="neutral",
        )
        self._preset_rename_btn = rename_btn
        rename_btn.grid(row=0, column=1, sticky="ew", padx=5)
        delete_btn = PhoenixButton(
            preset_actions, text=tr("delete_preset_btn", "Löschen"),
            command=self._on_delete_preset, button_type="danger",
        )
        self._preset_delete_btn = delete_btn
        delete_btn.grid(row=0, column=2, sticky="ew", padx=(5, 0))

        close_btn = PhoenixButton(
            container, text=tr("cancel", "Abbrechen"), command=popup.destroy,
            button_type="neutral", width=110,
        )
        close_btn.pack(side="right", pady=(14, 0))
        self._refresh_presets_dropdown()
        popup.bind("<Escape>", lambda _event: popup.destroy())

    def _open_advanced_settings_popup(self) -> None:
        if hasattr(self, "_advanced_popup") and self._advanced_popup.winfo_exists():
            self._advanced_popup.focus()
            return

        popup = tk.Toplevel(self)
        BrandManager.apply_window_icon(popup)
        popup.title(tr("section_generation_parameters", "Generierungsparameter"))
        popup.geometry("560x760")
        popup.configure(bg=PHOENIX_THEME.card_bg)
        popup.minsize(460, 580)
        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        self._advanced_popup = popup

        try:
            x = self.winfo_rootx() + (self.winfo_width() - 560) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 760) // 2
            popup.geometry(f"+{x}+{y}")
        except Exception:
            pass

        popup_shell = tk.Frame(popup, bg=PHOENIX_THEME.card_bg)
        popup_shell.pack(fill="both", expand=True)
        popup_actions = tk.Frame(popup_shell, bg=PHOENIX_THEME.card_bg)
        popup_actions.pack(side="bottom", fill="x", padx=24, pady=(8, 16))
        popup_scroll = tk.Canvas(
            popup_shell, bg=PHOENIX_THEME.card_bg, highlightthickness=0, bd=0
        )
        popup_scrollbar = ttk.Scrollbar(
            popup_shell, orient="vertical", command=popup_scroll.yview,
            style="Phoenix.Vertical.TScrollbar",
        )
        popup_scroll.configure(yscrollcommand=popup_scrollbar.set)
        popup_scrollbar.pack(side="right", fill="y")
        popup_scroll.pack(side="left", fill="both", expand=True)
        container = tk.Frame(popup_scroll, bg=PHOENIX_THEME.card_bg)
        popup_content_window = popup_scroll.create_window(
            (24, 20), window=container, anchor="nw"
        )
        container.bind(
            "<Configure>",
            lambda _event: popup_scroll.configure(scrollregion=popup_scroll.bbox("all")),
        )
        popup_scroll.bind(
            "<Configure>",
            lambda event: popup_scroll.itemconfigure(
                popup_content_window, width=max(1, event.width - 48)
            ),
        )
        popup.bind(
            "<MouseWheel>",
            lambda event: popup_scroll.yview_scroll(int(-event.delta / 120), "units"),
        )

        self._build_standard_dialog_header(
            popup, container,
            tr("section_generation_parameters", "Generierungsparameter"),
        )

        tk.Label(
            container, text=tr("section_model", "Modell"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title, anchor="w",
        ).pack(fill="x", pady=(0, 4))
        popup_model_menu = tk.OptionMenu(
            container, self.model_var, *self.controller.AVAILABLE_MODELS
        )
        popup_model_menu.configure(
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat", bd=0, highlightthickness=0,
            font=PHOENIX_THEME.font_button,
        )
        popup_model_menu["menu"].configure(
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            font=PHOENIX_THEME.font_body, relief="flat", bd=0,
        )
        popup_model_menu.pack(fill="x", pady=(0, 3))
        tk.Label(
            container, text=tr("model_parameter_help", "Das Modell bestimmt Stil, Fähigkeiten und unterstützte Einstellungen."),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption, anchor="w", justify="left",
            wraplength=460,
        ).pack(fill="x", pady=(0, 12))

        contract = self.controller.select_model(self.model_var.get())
        if not contract:
            contract = {}

        tk.Label(container, text=tr("image_size_title", "Image Size"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_card_title, anchor="w").pack(fill="x", pady=(0, 4))

        size_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        size_frame.pack(fill="x", pady=(0, 12))
        size_frame.grid_columnconfigure(0, weight=0)
        size_frame.grid_columnconfigure(1, weight=1)
        size_frame.grid_columnconfigure(2, weight=0)
        size_frame.grid_columnconfigure(3, weight=1)

        popup_width_label = tk.Label(size_frame, text=tr("width_label_colon", "Breite:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        popup_width_menu = tk.OptionMenu(size_frame, self.width_var, "256", "512", "768", "1024")
        popup_width_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        popup_width_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)

        popup_height_label = tk.Label(size_frame, text=tr("height_label_colon", "Höhe:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        popup_height_menu = tk.OptionMenu(size_frame, self.height_var, "256", "512", "768", "1024")
        popup_height_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        popup_height_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)

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
            popup_locked_res_frame, text=f"{lock_symbol} {tr('res_1024_btn_text', '1024 × 1024 (Demnächst)')}",
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_disabled,
            activebackground=PHOENIX_THEME.elevated_bg, activeforeground=PHOENIX_THEME.text_disabled,
            relief="flat", bd=0, font=PHOENIX_THEME.font_button, state="disabled",
            disabledforeground=PHOENIX_THEME.text_disabled, padx=10, pady=8
        )
        popup_res_1024_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(4, 4))

        popup_locked_hint_lbl = tk.Label(
            popup_locked_res_frame, text=tr("resolution_lock_tooltip", "Höhere Auflösungen benötigen ein kompatibles Qualcomm-Modell."),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_caption,
            anchor="w", justify="left", wraplength=340
        )
        popup_locked_hint_lbl.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))

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

            self._configure_option_contract(popup_width_menu, self.width_var, contract.get("width", {}))
            self._configure_option_contract(popup_height_menu, self.height_var, contract.get("height", {}))

        tk.Label(
            container,
            text=tr(
                "resolution_lock_tooltip",
                "Die Auflösung bestimmt Bildbreite und Bildhöhe; höhere Werte benötigen mehr Speicher.",
            ),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption, anchor="w", justify="left",
            wraplength=460,
        ).pack(fill="x", pady=(0, 8))

        tk.Label(container, text=tr("sampling_title", "Sampling"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_card_title, anchor="w").pack(fill="x", pady=(10, 4))

        sampling_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        sampling_frame.pack(fill="x", pady=(0, 12))
        sampling_frame.grid_columnconfigure(0, weight=1)

        tk.Label(sampling_frame, text=tr("cfg_scale_label_colon", "CFG Scale:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 1))
        popup_cfg_scale = tk.Scale(
            sampling_frame, from_=1.0, to=20.0, resolution=0.5, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            width=12, variable=self.cfg_var
        )
        popup_cfg_scale.grid(row=1, column=0, sticky="ew", pady=(0, 8))

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

        tk.Label(
            sampling_frame, text=tr("cfg_scale_help", "Stärke der Prompt-Befolgung; typische Empfehlung 6–8."),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption, anchor="w", justify="left",
        ).grid(row=2, column=0, sticky="ew", pady=(0, 6))

        tk.Label(
            sampling_frame, text=tr("steps_label_colon", "Schritte:"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small, anchor="w",
        ).grid(row=3, column=0, sticky="w", pady=(2, 1))
        popup_steps_scale = tk.Scale(
            sampling_frame, from_=1, to=100, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent,
            troughcolor=PHOENIX_THEME.elevated_bg,
            width=12, variable=self.steps_var,
        )
        popup_steps_scale.grid(row=4, column=0, sticky="ew", pady=(0, 2))
        steps_spec = contract.get("steps", {})
        popup_steps_scale.configure(
            from_=steps_spec.get("min", 1), to=steps_spec.get("max", 100)
        )
        tk.Label(
            sampling_frame, text=tr("steps_help", "Mehr Entrauschungsschritte können Details verbessern, benötigen aber mehr Zeit."),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption, anchor="w", justify="left",
        ).grid(row=5, column=0, sticky="ew", pady=(0, 6))

        dropdown_frame = tk.Frame(sampling_frame, bg=PHOENIX_THEME.card_bg)
        dropdown_frame.grid(row=6, column=0, sticky="ew", pady=(4, 0))
        dropdown_frame.grid_columnconfigure(0, weight=0)
        dropdown_frame.grid_columnconfigure(1, weight=1)
        dropdown_frame.grid_columnconfigure(2, weight=0)
        dropdown_frame.grid_columnconfigure(3, weight=1)

        tk.Label(dropdown_frame, text=tr("sampler_label_colon", "Sampler:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        popup_sampler_menu = tk.OptionMenu(dropdown_frame, self.sampler_var, "Euler a", "Euler", "DPM++ 2M", "DDIM", "LMS")
        popup_sampler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        popup_sampler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        popup_sampler_menu.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        tk.Label(dropdown_frame, text=tr("scheduler_label_colon", "Sched.:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        popup_scheduler_menu = tk.OptionMenu(dropdown_frame, self.scheduler_var, "Normal", "Karras", "Exponential", "SGM Uniform")
        popup_scheduler_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        popup_scheduler_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        popup_scheduler_menu.grid(row=0, column=3, sticky="ew", pady=2)

        tk.Label(
            dropdown_frame, text=tr("sampler_help", "Verwendetes Berechnungsverfahren für die Bildentstehung."),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption, anchor="w", justify="left",
            wraplength=205,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 8), pady=(2, 0))
        tk.Label(
            dropdown_frame, text=tr("scheduler_help", "Zeitliche Verteilung der Entrauschungsschritte."),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption, anchor="w", justify="left",
            wraplength=205,
        ).grid(row=1, column=2, columnspan=2, sticky="ew", padx=(8, 0), pady=(2, 0))

        self._configure_option_contract(popup_sampler_menu, self.sampler_var, contract.get("sampler", {}))
        self._configure_option_contract(popup_scheduler_menu, self.scheduler_var, contract.get("scheduler", {}))

        tk.Label(container, text=tr("output_title", "Output"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, font=PHOENIX_THEME.font_card_title, anchor="w").pack(fill="x", pady=(10, 4))

        output_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        output_frame.pack(fill="x", pady=(0, 12))
        output_frame.grid_columnconfigure(0, weight=0)
        output_frame.grid_columnconfigure(1, weight=1)
        output_frame.grid_columnconfigure(2, weight=0)
        output_frame.grid_columnconfigure(3, weight=1)

        tk.Label(output_frame, text=tr("seed_label_colon", "Seed:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        popup_seed_entry = tk.Entry(
            output_frame, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body,
            textvariable=self.seed_var
        )
        popup_seed_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2)

        tk.Label(output_frame, text=tr("batch_label_colon", "Batch:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=2)
        popup_batch_menu = tk.OptionMenu(output_frame, self.batch_var, "1", "2", "4", "8")
        popup_batch_menu.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat", bd=0, highlightthickness=0, font=PHOENIX_THEME.font_caption)
        popup_batch_menu["menu"].configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary, activebackground=PHOENIX_THEME.accent, font=PHOENIX_THEME.font_caption, relief="flat", bd=0)
        popup_batch_menu.grid(row=0, column=3, sticky="ew", pady=2)
        tk.Label(
            output_frame, text=tr("seed_help", "Reproduzierbarer Startwert; -1 bedeutet zufälliger Seed."),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption, anchor="w", justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))

        popup_upscale_check = tk.Checkbutton(
            output_frame,
            text=tr("upscale_2x_option", "Nach Generierung mit RealESRGAN 2× hochskalieren"),
            variable=self.upscale_2x_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.elevated_bg,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        popup_upscale_check.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(12, 2))
        tk.Label(
            output_frame,
            text=tr(
                "upscale_2x_help",
                "Optional; erhält das Original und speichert zusätzlich ein separates Bild mit doppelter Auflösung.",
            ),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left",
            wraplength=460,
        ).grid(row=3, column=0, columnspan=4, sticky="ew", pady=(0, 4))



        close_btn = tk.Button(
            popup_actions, text=tr("apply", "Übernehmen"), bg=PHOENIX_THEME.accent, fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat", bd=0, font=PHOENIX_THEME.font_button, cursor="hand2", padx=16, pady=8,
            command=popup.destroy
        )
        close_btn.pack(side="right")

    def _open_boost_preview(self) -> None:
        prompt = self.prompt_text.get("1.0", "end-1c").strip()
        if not prompt:
            messagebox.showinfo(
                tr("boost_title", "Phoenix Boost"),
                tr("boost_empty_prompt", "Bitte zuerst einen Prompt eingeben."),
            )
            return

        try:
            suggestion = PhoenixBoostEngine.suggest(
                prompt=prompt,
                negative_prompt=self.neg_prompt_text.get("1.0", "end-1c"),
                model_id=self.model_var.get(),
                steps=int(self.steps_var.get()),
                cfg=float(self.cfg_var.get()),
                width=int(self.width_var.get()),
                height=int(self.height_var.get()),
            )
        except (TypeError, ValueError):
            messagebox.showinfo(
                tr("boost_title", "Phoenix Boost"),
                tr("boost_empty_prompt", "Bitte zuerst einen Prompt eingeben."),
            )
            return

        popup = tk.Toplevel(self)
        BrandManager.apply_window_icon(popup)
        popup.title(tr("boost_preview_title", "Phoenix Boost – Vorschau"))
        popup.configure(bg=PHOENIX_THEME.card_bg)
        popup.geometry("760x760")
        popup.minsize(680, 620)
        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        self._boost_popup = popup
        self._boost_suggestion = suggestion
        self._boost_mode = "Boost"
        self._ollama_status = OllamaStatus(False, False)

        dialog_shell = tk.Frame(popup, bg=PHOENIX_THEME.card_bg)
        dialog_shell.pack(fill="both", expand=True)

        actions = tk.Frame(dialog_shell, bg=PHOENIX_THEME.card_bg)
        actions.pack(side="bottom", fill="x", padx=24, pady=(8, 16))
        self._boost_actions = actions

        scroll_area = tk.Frame(dialog_shell, bg=PHOENIX_THEME.card_bg)
        scroll_area.pack(side="top", fill="both", expand=True)
        scroll_canvas = tk.Canvas(
            scroll_area, bg=PHOENIX_THEME.card_bg,
            highlightthickness=0, bd=0,
        )
        scrollbar = ttk.Scrollbar(
            scroll_area, orient="vertical", command=scroll_canvas.yview,
            style="Phoenix.Vertical.TScrollbar",
        )
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)
        self._boost_scroll_canvas = scroll_canvas

        container = tk.Frame(scroll_canvas, bg=PHOENIX_THEME.card_bg)
        content_window = scroll_canvas.create_window((24, 20), window=container, anchor="nw")
        container.bind(
            "<Configure>",
            lambda _event: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")),
        )
        scroll_canvas.bind(
            "<Configure>",
            lambda event: scroll_canvas.itemconfigure(
                content_window, width=max(1, event.width - 48)
            ),
        )
        popup.bind(
            "<MouseWheel>",
            lambda event: scroll_canvas.yview_scroll(int(-event.delta / 120), "units"),
        )
        self._build_standard_dialog_header(
            popup, container, tr("boost_preview_title", "Phoenix Boost – Vorschau"),
        )

        if self._ollama_status.available:
            tk.Label(
                container, text=tr("boost_ai_available", "Phoenix Boost AI verfügbar"),
                bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.success,
                font=PHOENIX_THEME.font_small, anchor="w",
            ).pack(fill="x", pady=(0, 8))
        else:
            ai_info = tk.Frame(container, bg=PHOENIX_THEME.surface)
            ai_info.pack(fill="x", pady=(0, 10))
            ai_copy = tk.Frame(ai_info, bg=PHOENIX_THEME.surface)
            ai_copy.pack(side="left", fill="x", expand=True, padx=10, pady=7)
            self._boost_ai_title_lbl = tk.Label(
                ai_copy, text=tr("boost_ai_title", "Phoenix Boost AI"),
                bg=PHOENIX_THEME.surface, fg=PHOENIX_THEME.text_primary,
                font=PHOENIX_THEME.font_card_title, anchor="w",
            )
            self._boost_ai_title_lbl.pack(fill="x")
            self._boost_ollama_status_lbl = tk.Label(
                ai_copy, text=tr("boost_ollama_status_missing", "Ollama: nicht installiert"),
                bg=PHOENIX_THEME.surface, fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_small, anchor="w",
            )
            self._boost_ollama_status_lbl.pack(fill="x", pady=(2, 0))
            self._boost_model_status_lbl = tk.Label(
                ai_copy, text=tr("boost_model_status_unavailable", "Qwen2.5 3B: nicht verfügbar"),
                bg=PHOENIX_THEME.surface, fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_small, anchor="w",
            )
            self._boost_model_status_lbl.pack(fill="x", pady=(2, 0))
            self._boost_ai_status_lbl = tk.Label(
                ai_copy, text=tr("boost_ai_status_not_ready", "Phoenix Boost AI: nicht bereit"),
                bg=PHOENIX_THEME.surface, fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_small, anchor="w",
            )
            self._boost_ai_status_lbl.pack(fill="x", pady=(2, 0))
            self._boost_ai_info_lbl = tk.Label(
                ai_copy,
                text=tr("boost_ai_info", "Erweitert die Prompt-Optimierung optional mit lokaler KI."),
                bg=PHOENIX_THEME.surface, fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_caption, anchor="w",
            )
            self._boost_ai_info_lbl.pack(fill="x", pady=(2, 0))
            self._boost_install_btn = PhoenixButton(
                ai_info, text=tr("boost_install_ollama", "Ollama installieren"),
                command=self._open_ollama_download,
                button_type="primary", font=PHOENIX_THEME.font_small,
            )
            self._boost_install_btn.pack(side="right", padx=8, pady=5)

        self._boost_preview_field(container, tr("boost_original_prompt", "Originalprompt"), suggestion.original_prompt)
        self._boost_optimized_value = self._boost_preview_field(
            container, tr("boost_optimized_prompt", "Optimierter Prompt"), suggestion.optimized_prompt
        )
        self._boost_preview_field(
            container,
            tr("boost_existing_negative", "Vorhandener Negative Prompt"),
            suggestion.existing_negative_prompt or tr("boost_none", "Nicht vorhanden"),
        )
        self._boost_negative_value = self._boost_preview_field(
            container, tr("boost_negative_addition", "Empfohlene Ergänzung"), suggestion.negative_addition,
        )

        values = tk.Frame(container, bg=PHOENIX_THEME.surface)
        values.pack(fill="x", pady=(4, 10))
        rows = (
            (tr("boost_steps", "Schritte"), str(suggestion.current_steps), str(suggestion.recommended_steps)),
            (tr("boost_cfg", "CFG Scale"), f"{suggestion.current_cfg:g}", f"{suggestion.recommended_cfg:g}"),
            (tr("boost_resolution", "Auflösung"), f"{suggestion.current_resolution[0]} × {suggestion.current_resolution[1]}", f"{suggestion.recommended_resolution[0]} × {suggestion.recommended_resolution[1]}"),
        )
        for column, text_value in enumerate(("", tr("boost_current", "Aktuell"), tr("boost_recommended", "Empfohlen"))):
            tk.Label(values, text=text_value, bg=PHOENIX_THEME.surface, fg=PHOENIX_THEME.text_secondary,
                     font=PHOENIX_THEME.font_small, anchor="w").grid(row=0, column=column, sticky="ew", padx=10, pady=(8, 4))
        for row, (label, current, recommended) in enumerate(rows, start=1):
            for column, text_value in enumerate((label, current, recommended)):
                tk.Label(values, text=text_value, bg=PHOENIX_THEME.surface, fg=PHOENIX_THEME.text_primary,
                         font=PHOENIX_THEME.font_small, anchor="w").grid(row=row, column=column, sticky="ew", padx=10, pady=3)
        for column in range(3):
            values.grid_columnconfigure(column, weight=1)

        if suggestion.model_hint:
            tk.Label(
                container,
                text=tr("boost_model_hint", "Modellhinweis: Für dieses Motiv kann SDXL bessere Details liefern."),
                bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_small, anchor="w", justify="left",
            ).pack(fill="x", pady=(0, 8))

        self._boost_apply_negative_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            container, variable=self._boost_apply_negative_var,
            text=tr("boost_apply_negative", "Empfohlene Ergänzung zum Negative Prompt übernehmen"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.card_bg, activeforeground=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.elevated_bg, font=PHOENIX_THEME.font_small, anchor="w",
        ).pack(fill="x", pady=2)

        resolution_allowed = self._boost_resolution_allowed(suggestion)
        self._boost_apply_resolution_var = tk.BooleanVar(value=False)
        resolution_check = tk.Checkbutton(
            container, variable=self._boost_apply_resolution_var,
            text=tr("boost_apply_resolution", "Empfohlene Auflösung ausdrücklich übernehmen"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.card_bg, activeforeground=PHOENIX_THEME.text_primary,
            disabledforeground=PHOENIX_THEME.text_muted, selectcolor=PHOENIX_THEME.elevated_bg,
            font=PHOENIX_THEME.font_small, anchor="w",
            state="normal" if resolution_allowed else "disabled",
        )
        resolution_check.pack(fill="x", pady=2)
        if not resolution_allowed:
            reason_key = "boost_resolution_controlnet_locked" if self._controlnet_active() else "boost_resolution_model_locked"
            fallback = "Bei aktivem ControlNet bleibt die Auflösung unverändert." if self._controlnet_active() else "Die Auflösung ist für dieses Modell/Backend fest vorgegeben."
            tk.Label(container, text=tr(reason_key, fallback), bg=PHOENIX_THEME.card_bg,
                     fg=PHOENIX_THEME.text_muted, font=PHOENIX_THEME.font_small, anchor="w").pack(fill="x", padx=(22, 0))

        self._boost_save_template_btn = PhoenixButton(
            actions, text=tr("boost_save_template", "Als Vorlage speichern"),
            icon_name="preset", icon_color=PHOENIX_THEME.warning,
            command=self._save_boost_as_template, button_type="neutral",
            font=PHOENIX_THEME.font_small,
        )
        self._boost_save_template_btn.pack(side="left")

        cancel_btn = tk.Button(
            actions, text=tr("cancel", "Abbrechen"), command=popup.destroy,
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.border, activeforeground=PHOENIX_THEME.text_primary,
            relief="flat", bd=0, font=PHOENIX_THEME.font_button, cursor="hand2", padx=18, pady=8,
        )
        self._boost_cancel_btn = cancel_btn
        cancel_btn.pack(side="right", padx=(8, 0))
        self._add_button_hover(cancel_btn, PHOENIX_THEME.border, PHOENIX_THEME.text_primary)
        apply_btn = tk.Button(
            actions, text=tr("apply", "Übernehmen"), command=self._apply_boost_suggestion,
            bg=PHOENIX_THEME.accent, fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.button_hover, activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat", bd=0, font=PHOENIX_THEME.font_button, cursor="hand2", padx=18, pady=8,
        )
        self._boost_apply_btn = apply_btn
        apply_btn.pack(side="right")
        self._add_button_hover(apply_btn, PHOENIX_THEME.button_hover, PHOENIX_THEME.text_on_accent)
        popup.bind("<Escape>", lambda _event: popup.destroy())
        self._boost_ai_queue = queue.Queue(maxsize=1)
        threading.Thread(
            target=self._load_boost_ai_suggestion, args=(suggestion,), daemon=True,
        ).start()
        popup.after(100, self._poll_boost_ai_suggestion)

    def _save_boost_as_template(self) -> None:
        suggestion = self._boost_suggestion
        data = self._collect_preset_data(
            prompt=suggestion.optimized_prompt,
            negative_prompt=suggestion.recommended_negative_prompt,
        )
        self._prompt_and_save_preset(data)

    @staticmethod
    def _boost_preview_field(parent: tk.Widget, label: str, value: str) -> tk.Label:
        tk.Label(parent, text=label, bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
                 font=PHOENIX_THEME.font_small, anchor="w").pack(fill="x")
        value_label = tk.Label(
            parent, text=value, bg=PHOENIX_THEME.surface, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_small, anchor="w", justify="left", wraplength=690,
            padx=10, pady=7,
        )
        value_label.pack(fill="x", pady=(2, 8))
        return value_label

    def _load_boost_ai_suggestion(self, local_suggestion: BoostSuggestion) -> None:
        status = OllamaStatusService.detect()
        result = BoostAIService.optimize(local_suggestion.original_prompt) if status.available else None
        if result is None:
            self._boost_ai_queue.put((status, None))
            return
        existing = local_suggestion.existing_negative_prompt
        combined = f"{existing}, {result.negative_prompt}" if existing else result.negative_prompt
        analysis = PromptAnalysis(
            result.main_object, result.count,
            (result.action,) if result.action else (), result.relationships,
            result.environment or None, local_suggestion.analysis.colors,
            result.style or local_suggestion.analysis.style,
        )
        ai_suggestion = replace(
            local_suggestion, optimized_prompt=result.optimized_prompt,
            negative_addition=result.negative_prompt,
            recommended_negative_prompt=combined, analysis=analysis,
        )
        self._boost_ai_queue.put((status, ai_suggestion))

    def _poll_boost_ai_suggestion(self) -> None:
        if not hasattr(self, "_boost_popup") or not self._boost_popup.winfo_exists():
            return
        try:
            status, suggestion = self._boost_ai_queue.get_nowait()
        except queue.Empty:
            self._boost_popup.after(100, self._poll_boost_ai_suggestion)
            return
        self._update_ollama_install_button(status)
        if suggestion is not None:
            self._apply_boost_ai_preview(suggestion)

    def _update_ollama_install_button(self, status: OllamaStatus) -> None:
        self._ollama_status = status
        if not hasattr(self, "_boost_install_btn"):
            return
        self._boost_ollama_status_lbl.configure(text=tr(
            "boost_ollama_status_ready" if status.available else "boost_ollama_status_missing",
            "Ollama: bereit" if status.available else "Ollama: nicht installiert",
        ))
        self._boost_model_status_lbl.configure(text=tr(
            "boost_model_status_ready" if status.model_available else "boost_model_status_missing",
            "Qwen2.5 3B: installiert" if status.model_available else "Qwen2.5 3B: nicht installiert",
        ) if status.available else tr("boost_model_status_unavailable", "Qwen2.5 3B: nicht verfügbar"))
        self._boost_ai_status_lbl.configure(text=tr(
            "boost_ai_status_ready" if status.ai_ready else "boost_ai_status_not_ready",
            "Phoenix Boost AI: bereit" if status.ai_ready else "Phoenix Boost AI: nicht bereit",
        ))
        if status.ai_ready:
            self._boost_install_btn.configure(
                text=tr("boost_ai_ready_button", "Phoenix Boost AI bereit ✓"),
                state="disabled",
            )
        elif status.available:
            self._boost_install_btn.configure(
                text=tr("boost_install_qwen", "Qwen2.5 3B installieren"),
                command=self._confirm_qwen_install,
                button_type="primary", state="normal",
            )
        else:
            self._boost_install_btn.configure(
                text=tr("boost_install_ollama", "Ollama installieren"),
                command=self._open_ollama_download,
                button_type="primary", state="normal",
            )

    def _confirm_qwen_install(self) -> None:
        confirmed = messagebox.askokcancel(
            tr("boost_install_qwen_title", "Qwen2.5 3B installieren"),
            tr(
                "boost_install_qwen_storage_hint",
                "Das lokale Modell benötigt zusätzlichen Speicherplatz. Download jetzt starten?",
            ),
            parent=self._boost_popup,
        )
        if not confirmed:
            return
        executable = shutil.which("ollama")
        if not executable:
            OllamaStatusService.invalidate_cache()
            return
        try:
            subprocess.Popen(
                [executable, "pull", OllamaStatusService.MODEL],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            OllamaStatusService.invalidate_cache()
            self._boost_install_btn.configure(
                text=tr("boost_qwen_install_started", "Download gestartet …"),
                state="disabled",
            )
        except OSError:
            OllamaStatusService.invalidate_cache()

    def _apply_boost_ai_preview(self, suggestion: BoostSuggestion) -> None:
        if not hasattr(self, "_boost_popup") or not self._boost_popup.winfo_exists():
            return
        self._boost_suggestion = suggestion
        self._boost_mode = "Boost AI"
        self._boost_optimized_value.configure(text=suggestion.optimized_prompt)
        self._boost_negative_value.configure(text=suggestion.negative_addition)
        if hasattr(self, "_boost_ai_title_lbl"):
            self._boost_ai_title_lbl.configure(text=tr("boost_ai_available", "Phoenix Boost AI verfügbar"), fg=PHOENIX_THEME.success)
            self._boost_ai_info_lbl.pack_forget()

    @staticmethod
    def _open_ollama_download() -> None:
        import webbrowser

        webbrowser.open(OllamaStatusService.DOWNLOAD_URL)

    def _controlnet_active(self) -> bool:
        return bool(self.canny_supported and self.active_tab == "canny")

    def _boost_resolution_allowed(self, suggestion: BoostSuggestion) -> bool:
        if self._controlnet_active():
            return False
        contract = self.controller.get_generation_parameters(self.model_var.get()) or {}
        for name, recommended in zip(("width", "height"), suggestion.recommended_resolution):
            spec = contract.get(name, {})
            values = spec.get("values", []) if isinstance(spec, dict) else []
            if not spec.get("editable", True) or (values and recommended not in values):
                return False
        return True

    def _apply_boost_suggestion(self) -> None:
        suggestion = self._boost_suggestion
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", suggestion.optimized_prompt)
        if self._boost_apply_negative_var.get():
            self.neg_prompt_text.delete("1.0", "end")
            self.neg_prompt_text.insert("1.0", suggestion.recommended_negative_prompt)
        self.steps_var.set(suggestion.recommended_steps)
        self.cfg_var.set(suggestion.recommended_cfg)
        if self._boost_apply_resolution_var.get() and self._boost_resolution_allowed(suggestion):
            self.width_var.set(str(suggestion.recommended_resolution[0]))
            self.height_var.set(str(suggestion.recommended_resolution[1]))
        self._update_prompt_counters()
        canny_low, canny_high, conditioning = self._get_controlnet_params()
        try:
            seed = int(self.seed_var.get())
        except ValueError:
            seed = -1
        self.controller.update_parameters(
            prompt=self.prompt_text.get("1.0", "end-1c").strip(),
            negative_prompt=self.neg_prompt_text.get("1.0", "end-1c").strip(),
            seed=seed, steps=int(self.steps_var.get()), cfg=float(self.cfg_var.get()),
            width=int(self.width_var.get()), height=int(self.height_var.get()),
            selected_model=self.model_var.get(), sampler=self.sampler_var.get(),
            scheduler=self.scheduler_var.get(), batch_size=int(self.batch_var.get()),
            input_image_path=self.controller.model.state.input_image_path,
            controlnet_enabled=self._controlnet_active(), canny_low_threshold=canny_low,
            canny_high_threshold=canny_high, controlnet_conditioning_scale=conditioning,
        )
        self._boost_popup.destroy()

    def _open_expandable_prompt_popup(self) -> None:
        if hasattr(self, "_prompt_popup") and self._prompt_popup.winfo_exists():
            self._prompt_popup.focus()
            return

        popup = tk.Toplevel(self)
        BrandManager.apply_window_icon(popup)
        popup.title(tr("large_prompt_editor_title", "Großer Prompt-Editor"))
        popup.configure(bg=PHOENIX_THEME.card_bg)
        self._prompt_popup = popup

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

        container = tk.Frame(popup, bg=PHOENIX_THEME.card_bg)
        container.pack(fill="both", expand=True, padx=24, pady=24)

        header_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        header_frame.pack(fill="x", pady=(0, 12))

        tk.Label(
            header_frame, text=tr("large_prompt_editor_title", "Großer Prompt-Editor"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title, anchor="w"
        ).pack(side="left")

        tk.Label(
            header_frame, text=tr("large_prompt_editor_shortcut_hint", "(ESC zum Schließen & Übernehmen)"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption, anchor="e"
        ).pack(side="right")

        tk.Label(
            container, text=tr("large_prompt_editor_prompt_label", "Prompt"),
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small, anchor="w",
        ).pack(fill="x", pady=(0, 4))

        text_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        text_frame.pack(fill="both", expand=True)
        from tkinter import ttk
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", style="Phoenix.Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")

        popup_text = tk.Text(
            text_frame, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border, highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1, relief="flat", font=PHOENIX_THEME.font_body, wrap="word",
            padx=16, pady=16, height=8, yscrollcommand=scrollbar.set
        )
        popup_text.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=popup_text.yview)
        self._prompt_popup_text = popup_text

        initial_text = self.prompt_text.get("1.0", "end-1c")
        popup_text.insert("1.0", initial_text)
        popup_text.focus_set()

        self.popup_counter_lbl = tk.Label(
            container,
            text=tr("chars_words_label", "Zeichen: {chars} | Wörter: {words}", chars=0, words=0),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="e"
        )
        self.popup_counter_lbl.pack(fill="x", pady=(4, 0))

        tk.Label(
            container,
            text=tr("large_prompt_editor_negative_label", "Negative Prompt"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).pack(fill="x", pady=(12, 4))

        negative_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        negative_frame.pack(fill="both", expand=True)
        negative_scrollbar = ttk.Scrollbar(
            negative_frame, orient="vertical", style="Phoenix.Vertical.TScrollbar"
        )
        negative_scrollbar.pack(side="right", fill="y")
        negative_popup_text = tk.Text(
            negative_frame,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border,
            highlightcolor=PHOENIX_THEME.accent,
            highlightthickness=1,
            relief="flat",
            font=PHOENIX_THEME.font_body,
            wrap="word",
            padx=16,
            pady=16,
            height=8,
            yscrollcommand=negative_scrollbar.set,
        )
        negative_popup_text.pack(side="left", fill="both", expand=True)
        negative_scrollbar.configure(command=negative_popup_text.yview)
        self._negative_prompt_popup_text = negative_popup_text
        negative_popup_text.insert(
            "1.0", self.neg_prompt_text.get("1.0", "end-1c")
        )

        popup_text.bind("<KeyRelease>", lambda e: self._sync_popup_prompt_to_main())
        negative_popup_text.bind(
            "<KeyRelease>", lambda e: self._sync_popup_prompt_to_main()
        )
        self._update_prompt_counters()

        btn_frame = tk.Frame(container, bg=PHOENIX_THEME.card_bg)
        btn_frame.pack(fill="x", pady=(16, 0))

        close_btn = tk.Button(
            btn_frame, text=tr("btn_close_apply", "Schließen & Übernehmen"), bg=PHOENIX_THEME.accent, fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent, activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat", bd=0, font=PHOENIX_THEME.font_button, cursor="hand2", padx=20, pady=10,
            command=self._apply_expandable_prompt
        )
        close_btn.pack(anchor="center")

        popup.bind("<Escape>", lambda e: self._apply_expandable_prompt())

    def _apply_expandable_prompt(self) -> None:
        self._sync_popup_prompt_to_main()
        if hasattr(self, "_prompt_popup") and self._prompt_popup.winfo_exists():
            self._prompt_popup.destroy()

    def _sync_popup_prompt_to_main(self) -> None:
        if hasattr(self, "_prompt_popup_text") and self._prompt_popup_text.winfo_exists():
            content = self._prompt_popup_text.get("1.0", "end-1c")
            self.prompt_text.delete("1.0", "end")
            self.prompt_text.insert("1.0", content)
        if (
            hasattr(self, "_negative_prompt_popup_text")
            and self._negative_prompt_popup_text.winfo_exists()
        ):
            negative_content = self._negative_prompt_popup_text.get("1.0", "end-1c")
            self.neg_prompt_text.delete("1.0", "end")
            self.neg_prompt_text.insert("1.0", negative_content)
        self._update_prompt_counters()

    def _sync_main_prompt_to_popup(self) -> None:
        if hasattr(self, "_prompt_popup_text") and self._prompt_popup_text.winfo_exists():
            content = self.prompt_text.get("1.0", "end-1c")
            self._prompt_popup_text.delete("1.0", "end")
            self._prompt_popup_text.insert("1.0", content)
        if (
            hasattr(self, "_negative_prompt_popup_text")
            and self._negative_prompt_popup_text.winfo_exists()
        ):
            negative_content = self.neg_prompt_text.get("1.0", "end-1c")
            self._negative_prompt_popup_text.delete("1.0", "end")
            self._negative_prompt_popup_text.insert("1.0", negative_content)
        self._update_prompt_counters()

    def _on_main_prompt_key(self) -> None:
        self._sync_main_prompt_to_popup()
        self._update_prompt_counters()

    def _update_prompt_counters(self) -> None:
        content = self.prompt_text.get("1.0", "end-1c")
        char_count = len(content)
        word_count = len(content.split())
        counter_text = tr("chars_words_label", "Zeichen: {chars} | Wörter: {words}", chars=char_count, words=word_count)

        if hasattr(self, "prompt_counter_lbl"):
            self.prompt_counter_lbl.configure(text=counter_text)

        if hasattr(self, "popup_counter_lbl") and hasattr(self, "_prompt_popup") and self._prompt_popup.winfo_exists():
            self.popup_counter_lbl.configure(text=counter_text)

    def _add_button_hover(self, button: tk.Button, hover_bg: str | None = None, hover_fg: str | None = None) -> None:
        original_bg = button.cget("bg")
        original_fg = button.cget("fg")
        h_bg = hover_bg or PHOENIX_THEME.accent
        h_fg = hover_fg or PHOENIX_THEME.text_on_accent

        def on_enter(event):
            if str(button.cget("state")) != "disabled":
                if hasattr(button, "is_active") and button.is_active:
                    return
                button.configure(bg=h_bg, fg=h_fg)

        def on_leave(event):
            if str(button.cget("state")) != "disabled":
                if hasattr(button, "is_active") and button.is_active:
                    button.configure(bg=PHOENIX_THEME.accent, fg=PHOENIX_THEME.text_on_accent)
                    return
                current_normal_bg = getattr(button, "normal_bg", original_bg)
                current_normal_fg = getattr(button, "normal_fg", original_fg)
                button.configure(bg=current_normal_bg, fg=current_normal_fg)

        button.bind("<Enter>", on_enter, add="+")
        button.bind("<Leave>", on_leave, add="+")

    def _on_apply_preset(self) -> None:
        name = self.selected_preset_var.get()
        if not name or name == "-":
            return
        preset = self.preset_manager.get_preset(name)
        if preset:
            self.apply_generation_settings(preset)
            if hasattr(self, "_presets_popup") and self._presets_popup and self._presets_popup.winfo_exists():
                try:
                    self._presets_popup.destroy()
                except Exception:
                    pass
                self._presets_popup = None
            if hasattr(self, "prompt_text") and self.prompt_text and self.prompt_text.winfo_exists():
                try:
                    self.prompt_text.focus_set()
                except Exception:
                    pass

    def _on_save_preset(self) -> None:
        self._prompt_and_save_preset(self._collect_preset_data())

    def _collect_preset_data(
        self, *, prompt: str | None = None, negative_prompt: str | None = None
    ) -> dict:
        generation_controller = getattr(self.controller, "generation_controller", None)
        backend_manager = getattr(generation_controller, "backend_manager", None)
        backend = (
            backend_manager.get_active_execution_provider_label()
            if backend_manager is not None else ""
        )

        def numeric(variable, converter, fallback):
            try:
                return converter(variable.get())
            except (TypeError, ValueError, tk.TclError):
                return fallback

        controlnet_enabled = bool(self.canny_supported and self.active_tab == "canny")
        return {
            "prompt": prompt if prompt is not None else self.prompt_text.get("1.0", "end-1c").strip(),
            "negative_prompt": negative_prompt if negative_prompt is not None else self.neg_prompt_text.get("1.0", "end-1c").strip(),
            "model_name": self.model_var.get(),
            "backend": backend,
            "seed": numeric(self.seed_var, int, -1),
            "width": numeric(self.width_var, int, 512),
            "height": numeric(self.height_var, int, 512),
            "steps": numeric(self.steps_var, int, 20),
            "cfg_scale": numeric(self.cfg_var, float, 7.5),
            "sampler": self.sampler_var.get(),
            "scheduler": self.scheduler_var.get(),
            "batch": numeric(self.batch_var, int, 1),
            "controlnet_enabled": controlnet_enabled,
            "canny_low_threshold": numeric(self.canny_low_var, int, 50),
            "canny_high_threshold": numeric(self.canny_high_var, int, 150),
            "controlnet_conditioning_scale": numeric(self.conditioning_strength_var, float, 1.0),
            "reference_image_path": getattr(self, "_ref_image_path", None) or "",
        }

    def _prompt_and_save_preset(self, data: dict) -> bool:
        from tkinter import messagebox, simpledialog

        parent = self
        if hasattr(self, "_boost_popup") and self._boost_popup.winfo_exists():
            parent = self._boost_popup
        name = simpledialog.askstring(
            tr("template_save_title", "Als Vorlage speichern"),
            tr("template_save_prompt", "Name der Vorlage:"),
            parent=parent,
        )
        if not name:
            return False

        if self.preset_manager.preset_exists(name):
            overwrite = messagebox.askyesno(
                tr("preset_overwrite_title", "Preset überschreiben"),
                tr(
                    "preset_overwrite_confirm",
                    "Das Preset '{name}' existiert bereits. Möchten Sie es überschreiben?",
                    name=name,
                ),
            )
            if not overwrite:
                return False

        success = self.preset_manager.save_preset(name, data)
        if success:
            success_message = tr(
                "preset_save_success", "Preset '{name}' erfolgreich gespeichert.", name=name
            )
            self.controller.model.update_state(status=success_message)
            self._configure_if_alive(
                self.status_label,
                text=tr("status_prefix", "Status: {status}", status=success_message),
            )
            self._refresh_presets_dropdown()
            self.selected_preset_var.set(self.preset_manager.preset_key(name))
            return True
        else:
            messagebox.showerror(
                tr("template_save_title", "Als Vorlage speichern"),
                tr("preset_save_error", "Fehler beim Speichern des Presets.")
            )
        return False

    def _on_delete_preset(self) -> None:
        from tkinter import messagebox
        name = self.selected_preset_var.get()
        if not name or name == "-":
            return

        confirm = messagebox.askyesno(
            tr("delete_preset_btn", "Löschen"),
            tr("preset_delete_confirm", "Möchtest du das Preset '{name}' wirklich löschen?", name=name)
        )
        if not confirm:
            return

        success = self.preset_manager.delete_preset(name)
        if success:
            messagebox.showinfo(
                tr("delete_preset_btn", "Löschen"),
                tr("preset_delete_success", "Preset '{name}' gelöscht.", name=name)
            )
            self._refresh_presets_dropdown()

    def _on_rename_preset(self) -> None:
        from tkinter import messagebox, simpledialog

        current_name = self.selected_preset_var.get()
        if not current_name or current_name == "-":
            return
        data = self.preset_manager.get_preset(current_name)
        if not data:
            return
        new_name = simpledialog.askstring(
            tr("rename_preset_title", "Vorlage umbenennen"),
            tr("rename_preset_prompt", "Neuer Name für die Vorlage:"),
            initialvalue=data.get("name", current_name),
            parent=getattr(self, "_presets_popup", self),
        )
        if not new_name or self.preset_manager.preset_key(new_name) == current_name:
            return
        if self.preset_manager.preset_exists(new_name):
            messagebox.showerror(
                tr("rename_preset_title", "Vorlage umbenennen"),
                tr("rename_preset_exists", "Eine Vorlage mit diesem Namen existiert bereits."),
                parent=getattr(self, "_presets_popup", self),
            )
            return
        if not self.preset_manager.save_preset(new_name, data):
            return
        if not self.preset_manager.delete_preset(current_name):
            self.preset_manager.delete_preset(self.preset_manager.preset_key(new_name))
            return
        self._refresh_presets_dropdown()
        self.selected_preset_var.set(self.preset_manager.preset_key(new_name))

    def _refresh_presets_dropdown(self) -> None:
        self.available_presets = self.preset_manager.list_presets()
        if not self.available_presets:
            self.available_presets = ["-"]

        dropdowns = [self.preset_dropdown]
        if hasattr(self, "_preset_popup_dropdown") and self._preset_popup_dropdown.winfo_exists():
            dropdowns.append(self._preset_popup_dropdown)
        for dropdown in dropdowns:
            menu = dropdown["menu"]
            menu.delete(0, "end")
            for p in self.available_presets:
                menu.add_command(
                    label=p,
                    command=lambda value=p: self.selected_preset_var.set(value)
                )

        curr = self.selected_preset_var.get()
        if curr not in self.available_presets:
            self.selected_preset_var.set(self.available_presets[0])


    def _open_controlnet_popup(self) -> None:
        if hasattr(self, "_controlnet_popup") and self._controlnet_popup and self._controlnet_popup.winfo_exists():
            self._controlnet_popup.focus()
            return

        popup = tk.Toplevel(self)
        from engine.brand_manager import BrandManager
        BrandManager.apply_window_icon(popup)
        popup.title(tr("tab_controlnet", "ControlNet Canny"))
        popup.geometry("380x540")
        popup.configure(bg=PHOENIX_THEME.card_bg)
        popup.resizable(False, False)
        popup.transient(self.winfo_toplevel())
        popup.protocol("WM_DELETE_WINDOW", self._close_controlnet_popup)
        
        try:
            main_w = self.winfo_toplevel().winfo_width()
            main_h = self.winfo_toplevel().winfo_height()
            x = self.winfo_toplevel().winfo_rootx() + (main_w - 380) // 2
            y = self.winfo_toplevel().winfo_rooty() + (main_h - 540) // 2
            popup.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._controlnet_popup = popup
        self._ensure_controlnet_widgets(popup)

    def _close_controlnet_popup(self) -> None:
        if hasattr(self, "_controlnet_popup") and self._controlnet_popup:
            try:
                self._controlnet_popup.destroy()
            except Exception:
                pass
        self._controlnet_popup = None
        self._ensure_controlnet_widgets(self._dummy_hidden_frame)

    def _ensure_controlnet_widgets(self, master: tk.Misc) -> None:
        if hasattr(self, "dnd_card") and self.dnd_card and self.dnd_card.winfo_exists():
            if self.dnd_card.master is master:
                return
            self._destroy_controlnet_widgets()
        self._build_controlnet_widgets(master)

    def _destroy_controlnet_widgets(self) -> None:
        widgets = [
            "controlnet_enable_checkbox",
            "controlnet_layout_frame",
            "dnd_subtitle",
            "dnd_card",
            "_dnd_previews_container",
            "_dnd_ref_container",
            "_dnd_ref_title",
            "_ref_box",
            "_dnd_preview_label",
            "_arrow_label",
            "_dnd_canny_container",
            "_dnd_canny_title",
            "_canny_box",
            "_dnd_canny_preview_label",
            "_dnd_meta_frame",
            "_dnd_name_label",
            "_dnd_resolution_label",
            "_dnd_canny_status_label",
            "buttons_frame",
            "btn_select_image",
            "btn_remove_image",
            "controlnet_frame",
            "low_scale",
            "high_scale",
            "strength_scale"
        ]
        for w_name in widgets:
            if hasattr(self, w_name):
                w = getattr(self, w_name)
                if w and hasattr(w, "winfo_exists") and w.winfo_exists():
                    try:
                        w.destroy()
                    except Exception:
                        pass
                setattr(self, w_name, None)

    def _build_controlnet_widgets(self, master: tk.Misc) -> None:
        self.controlnet_enable_checkbox = tk.Checkbutton(
            master,
            text=tr("enable_controlnet_canny", "ControlNet Canny"),
            variable=self.controlnet_canny_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.card_bg,
            font=PHOENIX_THEME.font_body,
            bd=0,
            highlightthickness=0,
        )
        self.controlnet_enable_checkbox.pack(anchor="w", padx=20, pady=(15, 10))

        self.controlnet_layout_frame = tk.Frame(master, bg=PHOENIX_THEME.card_bg)
        self.controlnet_layout_frame.pack(fill="both", expand=True, padx=20, pady=5)

        self.dnd_subtitle = tk.Label(
            self.controlnet_layout_frame,
            text=tr("ref_image_canny_hint", "Referenzbild für ControlNet Canny:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        self.dnd_subtitle.pack(fill="x", pady=(0, 5))

        self.dnd_card = tk.Frame(
            self.controlnet_layout_frame,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.dnd_card.pack(fill="x", pady=(0, 10))
        self.dnd_card.columnconfigure(0, weight=1)

        self._dnd_previews_container = tk.Frame(self.dnd_card, bg=PHOENIX_THEME.card_bg)
        self._dnd_previews_container.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="n")

        self._dnd_ref_container = tk.Frame(self._dnd_previews_container, bg=PHOENIX_THEME.card_bg)
        self._dnd_ref_container.grid(row=0, column=0, padx=(0, 12), sticky="nw")
        
        self._dnd_ref_title = tk.Label(
            self._dnd_ref_container,
            text=tr("original_image_label", "Originalbild"),
            font=PHOENIX_THEME.font_caption,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
        )
        self._dnd_ref_title.pack(anchor="w")
        
        self._ref_box = tk.Frame(self._dnd_ref_container, width=140, height=140, bg=PHOENIX_THEME.elevated_bg, highlightbackground=PHOENIX_THEME.border, highlightthickness=1)
        self._ref_box.pack_propagate(False)
        self._ref_box.pack(anchor="w", pady=(4, 0))

        self._dnd_preview_label = tk.Label(
            self._ref_box,
            text=tr("no_image_selected", "Kein Bild ausgewählt"),
            font=PHOENIX_THEME.font_caption,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            wraplength=120,
            justify="center",
            cursor="hand2"
        )
        self._dnd_preview_label.pack(fill="both", expand=True)
        self._dnd_preview_label.bind("<Button-1>", lambda e: self._on_dnd_click())

        self._arrow_label = tk.Label(
            self._dnd_previews_container,
            text="→",
            font=("Segoe UI", 16),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
        )
        self._arrow_label.grid(row=0, column=1, padx=4, )

        self._dnd_canny_container = tk.Frame(self._dnd_previews_container, bg=PHOENIX_THEME.card_bg)
        self._dnd_canny_container.grid(row=0, column=2, padx=(12, 0), sticky="nw")
        
        self._dnd_canny_title = tk.Label(
            self._dnd_canny_container,
            text=tr("canny_preview_label", "Canny-Vorschau"),
            font=PHOENIX_THEME.font_caption,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
        )
        self._dnd_canny_title.pack(anchor="w")
        
        self._canny_box = tk.Frame(self._dnd_canny_container, width=140, height=140, bg=PHOENIX_THEME.elevated_bg, highlightbackground=PHOENIX_THEME.border, highlightthickness=1)
        self._canny_box.pack_propagate(False)
        self._canny_box.pack(anchor="w", pady=(4, 0))

        self._dnd_canny_preview_label = tk.Label(
            self._canny_box,
            text="-",
            font=("Segoe UI", 16),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
        )
        self._dnd_canny_preview_label.pack(fill="both", expand=True)

        self._dnd_meta_frame = tk.Frame(self.dnd_card, bg=PHOENIX_THEME.card_bg)
        self._dnd_meta_frame.grid(row=1, column=0, padx=12, pady=(0, 2), sticky="ew")
        self._dnd_meta_frame.columnconfigure(0, weight=1)
        
        self._dnd_name_label = tk.Label(
            self._dnd_meta_frame,
            text="",
            font=PHOENIX_THEME.font_caption,
            fg=PHOENIX_THEME.text_primary,
            bg=PHOENIX_THEME.card_bg,
            anchor="center",
        )
        self._dnd_name_label.grid(row=0, column=0, sticky="ew")
        
        self._dnd_resolution_label = tk.Label(
            self._dnd_meta_frame,
            text="",
            font=PHOENIX_THEME.font_caption,
            fg=PHOENIX_THEME.text_muted,
            bg=PHOENIX_THEME.card_bg,
            anchor="center",
        )
        self._dnd_resolution_label.grid(row=1, column=0, sticky="ew")
        
        self._dnd_canny_status_label = tk.Label(
            self._dnd_meta_frame,
            text="",
            font=PHOENIX_THEME.font_caption,
            fg=PHOENIX_THEME.text_muted,
            bg=PHOENIX_THEME.card_bg,
            anchor="center",
        )
        self._dnd_canny_status_label.grid(row=2, column=0, sticky="ew")

        self.buttons_frame = tk.Frame(self.dnd_card, bg=PHOENIX_THEME.card_bg)
        self.buttons_frame.grid(row=2, column=0, padx=12, pady=(4, 12), sticky="n")

        self.btn_select_image = tk.Button(
            self.buttons_frame,
            text=tr("select_image", "Bild auswählen"),
            command=self._on_dnd_click,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_caption,
            cursor="hand2",
            padx=12,
            pady=4,
        )
        self.btn_select_image.grid(row=0, column=0, padx=(0, 6), sticky="w")
        self._add_button_hover(self.btn_select_image)

        self.btn_remove_image = tk.Button(
            self.buttons_frame,
            text=tr("remove_image", "Bild entfernen"),
            command=self._remove_reference_image,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_caption,
            cursor="hand2",
            padx=12,
            pady=4,
            state="disabled",
        )
        self.btn_remove_image.grid(row=0, column=1, padx=(6, 0), sticky="w")
        self._add_button_hover(self.btn_remove_image)
        self._dnd_remove_button = self.btn_remove_image

        self.controlnet_frame = tk.Frame(self.controlnet_layout_frame, bg=PHOENIX_THEME.card_bg)
        self.controlnet_frame.pack(fill="x", pady=5)
        self.controlnet_frame.grid_columnconfigure(0, weight=1)
        self.controlnet_frame.grid_columnconfigure(1, weight=1)

        low_label = tk.Label(self.controlnet_frame, text=tr("canny_low_threshold_label", "Canny Low Threshold:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        low_label.grid(row=0, column=0, sticky="w", pady=(0, 1))
        self.low_scale = tk.Scale(
            self.controlnet_frame, from_=0, to=255, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            width=12, variable=self.canny_low_var
        )
        self.low_scale.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 2))
        self.low_scale.bind("<ButtonRelease-1>", lambda e: self._trigger_canny_preview_update())

        high_label = tk.Label(self.controlnet_frame, text=tr("canny_high_threshold_label", "Canny High Threshold:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        high_label.grid(row=0, column=1, sticky="w", pady=(0, 1))
        self.high_scale = tk.Scale(
            self.controlnet_frame, from_=0, to=255, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            width=12, variable=self.canny_high_var
        )
        self.high_scale.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 2))
        self.high_scale.bind("<ButtonRelease-1>", lambda e: self._trigger_canny_preview_update())

        strength_label = tk.Label(self.controlnet_frame, text=tr("conditioning_strength_label", "Conditioning Strength:"), bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small, anchor="w")
        strength_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 1))
        self.strength_scale = tk.Scale(
            self.controlnet_frame, from_=0.0, to=2.0, resolution=0.05, orient="horizontal",
            bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_primary,
            highlightthickness=0, font=PHOENIX_THEME.font_caption,
            activebackground=PHOENIX_THEME.accent, troughcolor=PHOENIX_THEME.elevated_bg,
            width=12, variable=self.conditioning_strength_var
        )
        self.strength_scale.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        _Tooltip(low_label, lambda: tr("tooltip_canny_low", "Unterer Canny-Schwellenwert für die Kantenerkennung (0 - 255)."))
        _Tooltip(high_label, lambda: tr("tooltip_canny_high", "Oberer Canny-Schwellenwert für die Kantenerkennung (0 - 255)."))
        _Tooltip(strength_label, lambda: tr("tooltip_canny_strength", "Einflussstärke von ControlNet auf das generierte Bild (0.0 - 2.0)."))

        # Setup drag & drop if available
        if DND_AVAILABLE:
            for widget in (self.dnd_card, self._dnd_preview_label):
                try:
                    widget.drop_target_register(DND_FILES)
                    widget.dnd_bind("<<Drop>>", self._on_image_drop)
                except Exception as e:
                    logger.warning("TkDND not available: %s", e)

        # Trigger visibility update immediately based on current checkbox state
        self._on_controlnet_enable_changed()
