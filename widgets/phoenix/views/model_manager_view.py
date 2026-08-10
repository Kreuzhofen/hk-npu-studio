from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Any

from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr
from widgets.phoenix.controls.button import PhoenixButton

logger = logging.getLogger("PhoenixModelManagerView")


class PhoenixModelManagerView(WorkspaceFrame):
    """
    Phoenix Workspace View for Model Management & Qualcomm NPU Package Qualification.
    Displays available Snapdragon AI models, package statuses, and installation options.
    """

    def __init__(self, master: tk.Misc, controller: Any | None = None) -> None:
        super().__init__(
            master,
            tr("model_manager_title", "Modell-Manager"),
            tr("model_manager_subtitle", "Verwalte KI-Modelle und Snapdragon NPU-Pakete für die Phoenix Engine"),
            has_inspector=True
        )
        
        if controller is None:
            try:
                from controllers.model_manager_controller import ModelManagerController
                self.controller = ModelManagerController()
            except Exception:
                self.controller = None
        else:
            self.controller = controller

        self.selected_model_id: str | None = None
        self._last_rendered_signature: tuple | None = None
        
        # Proportional weights for Model List (60%) and Model Inspector (40%)
        self.grid_columnconfigure(0, weight=6, uniform="model_cols")
        self.grid_columnconfigure(1, weight=4, uniform="model_cols")

        self._build_model_list_area()
        self._build_model_inspector()
        self.refresh()

    # ==================================================================
    # LEFT COLUMN – Scrollable List of Model Cards
    # ==================================================================

    def _build_model_list_area(self) -> None:
        self.content_slot.grid_rowconfigure(0, weight=1)
        self.content_slot.grid_columnconfigure(0, weight=1)

        self.list_card = tk.Frame(
            self.content_slot,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1
        )
        self.list_card.grid(row=0, column=0, sticky="nsew", padx=PHOENIX_THEME.space_xs, pady=PHOENIX_THEME.space_xs)
        self.list_card.grid_rowconfigure(1, weight=1)
        self.list_card.grid_columnconfigure(0, weight=1)

        header_frame = tk.Frame(self.list_card, bg=PHOENIX_THEME.card_bg)
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        header_frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            header_frame,
            text=tr("available_models_header", "VERFÜGBARE QUALCOMM SNAPDRAGON MODELLE"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_card_title,
            anchor="w"
        ).grid(row=0, column=0, sticky="w")

        self.canvas = tk.Canvas(
            self.list_card,
            bg=PHOENIX_THEME.card_bg,
            bd=0,
            highlightthickness=0
        )
        self.canvas.grid(row=1, column=0, sticky="nsew")

        self.cards_container = tk.Frame(self.canvas, bg=PHOENIX_THEME.card_bg)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_container, anchor="nw")

        self.cards_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        def _on_mousewheel(event: tk.Event) -> None:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.list_card.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.list_card.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    # ==================================================================
    # RIGHT COLUMN – Selected Model Details & Operations Inspector
    # ==================================================================

    def _build_model_inspector(self) -> None:
        if self.inspector_slot is None:
            return

        self.inspector_slot.grid_rowconfigure(0, weight=1)
        self.inspector_slot.grid_columnconfigure(0, weight=1)

        self.insp_panel = tk.Frame(
            self.inspector_slot,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.insp_panel.grid(row=0, column=0, sticky="nsew", padx=PHOENIX_THEME.space_xs, pady=PHOENIX_THEME.space_xs)
        self.insp_panel.grid_rowconfigure(0, weight=1)
        self.insp_panel.grid_rowconfigure(1, weight=0)
        self.insp_panel.grid_columnconfigure(0, weight=1)

        self.insp_content = tk.Frame(self.insp_panel, bg=PHOENIX_THEME.card_bg)
        self.insp_content.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)
        self.insp_content.columnconfigure(0, weight=0)
        self.insp_content.columnconfigure(1, weight=1)

        r = 0
        tk.Label(
            self.insp_content,
            text=tr("model_details_header", "Modell-Details"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w"
        ).grid(row=r, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        r += 1

        def _add_detail_row(label_text: str) -> tk.Label:
            nonlocal r
            tk.Label(
                self.insp_content,
                text=label_text,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_small,
                anchor="w"
            ).grid(row=r, column=0, sticky="w", pady=3, padx=(0, 8))

            val_lbl = tk.Label(
                self.insp_content,
                text="-",
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_primary,
                font=PHOENIX_THEME.font_small,
                anchor="w",
                justify="left",
                wraplength=220
            )
            val_lbl.grid(row=r, column=1, sticky="w", pady=3)
            r += 1
            return val_lbl

        self.det_name = _add_detail_row(tr("name_colon", "Name:"))
        self.det_id = _add_detail_row(tr("model_id_colon", "Modell-ID:"))
        self.det_backend = _add_detail_row(tr("npu_backend_colon", "NPU-Backend:"))
        self.det_arch = _add_detail_row(tr("architecture_colon", "Architektur:"))
        self.det_format = _add_detail_row(tr("package_format_colon", "Paketformat:"))
        self.det_controlnet = _add_detail_row(tr("controlnet_colon", "ControlNet:"))
        self.det_status = _add_detail_row(tr("status_label_colon", "Status:"))

        tk.Label(
            self.insp_content,
            text=tr("description_label", "Beschreibung:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w"
        ).grid(row=r, column=0, columnspan=2, sticky="w", pady=(12, 4))
        r += 1

        desc_box = tk.Frame(
            self.insp_content,
            bg=PHOENIX_THEME.elevated_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            padx=8,
            pady=8
        )
        desc_box.grid(row=r, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        desc_box.columnconfigure(0, weight=1)

        self.det_desc = tk.Label(
            desc_box,
            text="-",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            justify="left",
            wraplength=300
        )
        self.det_desc.grid(row=0, column=0, sticky="ew")
        r += 1

        self.action_frame = tk.Frame(
            self.insp_panel,
            bg=PHOENIX_THEME.surface,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            padx=16,
            pady=12
        )
        self.action_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.action_frame.columnconfigure(0, weight=1)

        self.btn_activate = PhoenixButton(
            self.action_frame,
            text=tr("btn_activate_model", "Als aktives Modell setzen"),
            command=self._on_activate_selected,
            button_type="primary",
            icon_name="start",
            height=34,
        )
        self.btn_activate.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.btn_install = PhoenixButton(
            self.action_frame,
            text=tr("install", "Installieren"),
            command=self._on_install_selected,
            button_type="secondary",
            icon_name="download",
            height=34,
        )
        self.btn_install.grid(row=1, column=0, sticky="ew")

    # ==================================================================
    # DATA REFRESH & UI RENDERING (Anti-Flicker Caching)
    # ==================================================================

    def refresh(self) -> None:
        if not hasattr(self, "cards_container"):
            return

        controller_model = getattr(self.controller, "model", None) if self.controller else None
        repository = getattr(controller_model, "repository", None)
        if repository is not None:
            try:
                repository.load_repository()
            except Exception as e:
                logger.error("Failed to reload model repository: %s", e)

        models = []
        if repository is not None:
            for method_name in ("list_models", "get_all_models", "get_models", "available_models"):
                fn = getattr(repository, method_name, None)
                if callable(fn):
                    try:
                        res = fn()
                        if isinstance(res, (list, dict)):
                            models = list(res.values()) if isinstance(res, dict) else res
                            break
                    except Exception:
                        pass

        active_id = repository.get_active_model_id() if repository and hasattr(repository, "get_active_model_id") else None

        if not models:
            models = [
                {
                    "id": "stable_diffusion_v1_5_qnn",
                    "name": "Stable Diffusion 1.5 (Qualcomm NPU)",
                    "description": tr("model_description_stable_diffusion_v1_5_qnn", "Qualcomm-vorkompiliertes Stable-Diffusion-1.5-W8A16-Modell für die Hexagon NPU (HTP V73)."),
                    "backend": "Qualcomm SD 1.5 (HTP V73)",
                    "installed": True,
                    "capabilities": {"controlnet": True}
                },
                {
                    "id": "stable_diffusion_v2_1_qnn",
                    "name": "Stable Diffusion 2.1 (Qualcomm NPU)",
                    "description": tr("model_description_stable_diffusion_v2_1_qnn", "Optimiertes SD-2.1-Modell für höhere Auflösungen auf Snapdragon X Elite."),
                    "backend": "Qualcomm SD 2.1 (HTP V73)",
                    "installed": True,
                    "capabilities": {"controlnet": False}
                },
                {
                    "id": "sdxl_base",
                    "name": "SDXL Base 1.0 (NPU Package)",
                    "description": tr("model_description_sdxl_base", "Snapdragon-NPU-Paket für die SDXL-Base-Generierung."),
                    "backend": "Qualcomm QNN HTP",
                    "installed": False,
                    "capabilities": {"controlnet": False}
                }
            ]
            if not active_id:
                active_id = "stable_diffusion_v1_5_qnn"

        if not self.selected_model_id and models:
            first_item = models[0]
            if isinstance(first_item, dict):
                self.selected_model_id = first_item.get("id")
            else:
                self.selected_model_id = str(first_item)

        current_signature = (
            tuple(m.get("id") if isinstance(m, dict) else str(m) for m in models),
            tuple(m.get("installed") if isinstance(m, dict) else True for m in models),
            active_id,
            self.selected_model_id
        )

        if self._last_rendered_signature == current_signature and len(self.cards_container.winfo_children()) > 0:
            return

        self._last_rendered_signature = current_signature

        for child in self.cards_container.winfo_children():
            child.destroy()

        for idx, model in enumerate(models):
            if isinstance(model, str):
                model_dict = {
                    "id": model,
                    "name": model,
                    "description": tr("model_package_description", "Modellpaket"),
                    "installed": True,
                }
            else:
                model_dict = model
            self._render_model_card(idx, model_dict, active_id)

        self._update_inspector(models, active_id)

    def _render_model_card(self, index: int, model: dict, active_id: str | None) -> None:
        model_id = model.get("id", f"model_{index}")
        is_active = (model_id == active_id)
        is_selected = (model_id == self.selected_model_id)

        border_color = PHOENIX_THEME.accent if is_selected else PHOENIX_THEME.border
        card_bg = PHOENIX_THEME.surface if is_selected else PHOENIX_THEME.card_bg

        card = tk.Frame(
            self.cards_container,
            bg=card_bg,
            highlightbackground=border_color,
            highlightthickness=1,
            padx=12,
            pady=10
        )
        card.pack(fill="x", padx=16, pady=4)
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=0)

        title_lbl = tk.Label(
            card,
            text=model.get("name", model_id),
            bg=card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w"
        )
        title_lbl.grid(row=0, column=0, sticky="w")

        if is_active:
            badge_text = f"  {tr('status_active', 'AKTIV')}  "
            badge_bg = PHOENIX_THEME.accent
            badge_fg = PHOENIX_THEME.text_on_accent
        elif model.get("installed", True):
            badge_text = f"  {tr('status_installed', 'INSTALLIERT')}  "
            badge_bg = PHOENIX_THEME.elevated_bg
            badge_fg = PHOENIX_THEME.success
        else:
            badge_text = f"  {tr('status_download_ready', 'DOWNLOAD BEREIT')}  "
            badge_bg = PHOENIX_THEME.elevated_bg
            badge_fg = PHOENIX_THEME.text_muted

        badge = tk.Label(
            card,
            text=badge_text,
            bg=badge_bg,
            fg=badge_fg,
            font=PHOENIX_THEME.font_caption,
            bd=0,
            padx=6,
            pady=2
        )
        badge.grid(row=0, column=1, sticky="e")

        desc_text = self._localized_description(model)
        if len(desc_text) > 110:
            desc_text = desc_text[:107] + "..."

        desc_lbl = tk.Label(
            card,
            text=desc_text,
            bg=card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left"
        )
        desc_lbl.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        def _on_click(e=None, m_id=model_id):
            if self.selected_model_id != m_id:
                self.selected_model_id = m_id
                self._last_rendered_signature = None
                self.refresh()

        for w in (card, title_lbl, badge, desc_lbl):
            w.bind("<Button-1>", _on_click)

    def _update_inspector(self, models: list[Any], active_id: str | None) -> None:
        selected_model = None
        for miss in models:
            if isinstance(miss, dict) and miss.get("id") == self.selected_model_id:
                selected_model = miss
                break
            elif isinstance(miss, str) and miss == self.selected_model_id:
                selected_model = {"id": miss, "name": miss, "description": "", "installed": True}

        if not selected_model:
            return

        is_active = (self.selected_model_id == active_id)

        model_name = selected_model.get("name") or selected_model.get("id", "-")
        self.det_name.configure(text=model_name)
        self.det_id.configure(text=selected_model.get("id", "-"))
        self.det_backend.configure(text=selected_model.get("backend", "Qualcomm QNN HTP"))
        self.det_arch.configure(text=selected_model.get("architecture", "ARM64 / Hexagon NPU"))
        self.det_format.configure(text=selected_model.get("format", "Snapdragon Model Package"))
        
        has_controlnet = selected_model.get("capabilities", {}).get("controlnet", False)
        self.det_controlnet.configure(text=tr("controlnet_supported_canny", "Unterstützt (Canny)") if has_controlnet else tr("controlnet_not_supported", "Nicht unterstützt"))
        
        status_str = (
            tr("status_active_title", "Aktiv")
            if is_active
            else (
                tr("status_installed_title", "Installiert")
                if selected_model.get("installed", True)
                else tr("not_installed", "Nicht installiert")
            )
        )
        self.det_status.configure(text=status_str)
        description = self._localized_description(selected_model)
        if not selected_model.get("installed", True):
            availability_message = str(selected_model.get("availability_message") or "").strip()
            if availability_message:
                availability_message = tr(
                    f"model_availability_{selected_model.get('id', '')}",
                    availability_message,
                )
                description = f"{description}\n\n{availability_message}"
        self.det_desc.configure(text=description)

        is_installed = bool(selected_model.get("installed", True))
        self.btn_install.configure(state="disabled" if is_installed else "normal")

        if is_active or not is_installed:
            self.btn_activate.configure(
                state="disabled",
                text=(
                    tr("active_model", "Aktives Modell")
                    if is_active
                    else tr("install_before_activation", "Vor Aktivierung lokal installieren")
                ),
                icon_name="success" if is_active else "info"
            )
        else:
            self.btn_activate.configure(
                state="normal",
                text=tr("btn_activate_model", "Als aktives Modell setzen"),
                button_type="primary",
                icon_name="start"
            )

    @staticmethod
    def _localized_description(model: dict[str, Any]) -> str:
        model_id = str(model.get("id", "")).replace("-", "_")
        fallback = model.get("description") or tr(
            "no_description_available", "Keine Beschreibung verfügbar."
        )
        return tr(f"model_description_{model_id}", fallback)

    def _on_activate_selected(self) -> None:
        if not self.selected_model_id or not self.controller:
            return

        controller_model = getattr(self.controller, "model", None)
        repository = getattr(controller_model, "repository", None)
        if repository and hasattr(repository, "set_active_model_id"):
            repository.set_active_model_id(self.selected_model_id)
            self._last_rendered_signature = None
            messagebox.showinfo(
                tr("model_manager_title", "Modell-Manager"),
                tr("model_activated_msg", "Modell '{id}' erfolgreich als aktives NPU-Modell gesetzt.", id=self.selected_model_id)
            )
            self.refresh()

    def _on_install_selected(self) -> None:
        if not self.selected_model_id or not self.controller:
            return

        controller_model = getattr(self.controller, "model", None) if self.controller else None
        repository = getattr(controller_model, "repository", None)
        selected_model = None
        if repository is not None:
            selected_model = repository.get_model(self.selected_model_id)

        source_url = selected_model.get("source_url") if selected_model else None
        if source_url:
            from dialogs.model_source_dialog import ModelSourceDialog
            brand = getattr(self.winfo_toplevel(), "brand", None)
            dialog = ModelSourceDialog(
                self.winfo_toplevel(),
                model_name=selected_model.get("name") or self.selected_model_id,
                source_url=source_url,
                brand=brand,
            )
            if dialog.choice != "install":
                return

        source_path = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            title=tr("select_local_package", "Lokales Modellpaket auswählen"),
            filetypes=[
                (tr("model_package_files", "Modellpakete"), "*.smp *.zip"),
                (tr("all_files", "Alle Dateien"), "*.*"),
            ],
        )
        if not source_path:
            return

        install_package = getattr(self.controller, "install_package", None)
        if not callable(install_package):
            messagebox.showerror(
                tr("model_manager_title", "Modell-Manager"),
                tr("local_package_install_unavailable", "Der lokale Paketimport ist nicht verfügbar."),
                parent=self.winfo_toplevel(),
            )
            return

        if install_package(self.selected_model_id, source_path):
            self._last_rendered_signature = None
            self.refresh()
            messagebox.showinfo(
                tr("model_manager_title", "Modell-Manager"),
                tr("local_package_install_success", "Das lokale Modellpaket wurde erfolgreich installiert."),
                parent=self.winfo_toplevel(),
            )
        else:
            messagebox.showerror(
                tr("model_manager_title", "Modell-Manager"),
                tr("local_package_install_failed", "Das Modellpaket konnte nicht installiert werden. Prüfen Sie Paket-ID, Manifest und Dateien."),
                parent=self.winfo_toplevel(),
            )

    def _add_button_hover(self, button: tk.Button) -> None:
        orig_bg = button.cget("bg")
        orig_fg = button.cget("fg")

        def on_enter(e):
            if str(button.cget("state")) != "disabled":
                button.configure(bg=PHOENIX_THEME.accent_dark, fg=PHOENIX_THEME.text_on_accent)

        def on_leave(e):
            if str(button.cget("state")) != "disabled":
                button.configure(bg=orig_bg, fg=orig_fg)

        button.bind("<Enter>", on_enter, add="+")
        button.bind("<Leave>", on_leave, add="+")
