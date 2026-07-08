from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from controllers.model_manager_controller import ModelManagerController
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixModelManagerView(tk.Frame):
    """
    Phoenix Workspace View for the AI Model Manager.
    Presents models in a professional grid list and exposes detailed properties
    along with system diagnostics in a single, dedicated right-hand Inspector.
    """

    def __init__(self, master: tk.Misc, controller: ModelManagerController | None = None) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.controller = controller or ModelManagerController()
        
        self._build()
        self.refresh()

    def _build(self) -> None:
        # Configure layout rows and columns grid weights
        self.rowconfigure(0, weight=0)  # Header
        self.rowconfigure(1, weight=1)  # Content Panels
        self.rowconfigure(2, weight=0)  # Status Bar
        self.columnconfigure(0, weight=7)  # Main left column (Tabelle)
        self.columnconfigure(1, weight=3)  # Inspector right column (Details)

        # ==========================================
        # HEADER BLOCK
        # ==========================================
        header_frame = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(24, 8))

        tk.Label(
            header_frame,
            text="Model Repository Manager",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            header_frame,
            text="Lokale Modelldatenbank (Datenbasiert über resources/models/*.json)",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # ==========================================
        # MAIN LEFT COLUMN (Table only)
        # ==========================================
        main_column = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        main_column.grid(row=1, column=0, sticky="nsew", padx=(24, 12), pady=(8, 16))
        main_column.rowconfigure(0, weight=1)  # Table fills all vertical space
        main_column.columnconfigure(0, weight=1)

        # Style TTK Treeview to match HSL Dark/Light themes
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Phoenix.Treeview",
            background=PHOENIX_THEME.card_bg,
            foreground=PHOENIX_THEME.text_primary,
            fieldbackground=PHOENIX_THEME.card_bg,
            bordercolor=PHOENIX_THEME.border,
            lightcolor=PHOENIX_THEME.border,
            darkcolor=PHOENIX_THEME.border,
            rowheight=30,
            font=PHOENIX_THEME.font_body,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "Phoenix.Treeview.Heading",
            background=PHOENIX_THEME.elevated_bg,
            foreground=PHOENIX_THEME.text_primary,
            bordercolor=PHOENIX_THEME.border,
            lightcolor=PHOENIX_THEME.border,
            darkcolor=PHOENIX_THEME.border,
            font=PHOENIX_THEME.font_button,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Phoenix.Treeview",
            background=[("selected", PHOENIX_THEME.accent)],
            foreground=[("selected", PHOENIX_THEME.text_on_accent)],
        )
        style.map(
            "Phoenix.Treeview.Heading",
            background=[("active", PHOENIX_THEME.accent), ("!active", PHOENIX_THEME.elevated_bg)],
            foreground=[("active", PHOENIX_THEME.text_on_accent), ("!active", PHOENIX_THEME.text_primary)],
        )

        # Table container card
        table_frame = tk.Frame(
            main_column,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        table_frame.grid(row=0, column=0, sticky="nsew")

        columns = ("active", "name", "category", "backend", "status")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Phoenix.Treeview",
            selectmode="browse",
        )
        self.tree.heading("active", text="Aktiv")
        self.tree.heading("name", text="Modellname")
        self.tree.heading("category", text="Kategorie")
        self.tree.heading("backend", text="Ziel-Backend")
        self.tree.heading("status", text="Status")

        self.tree.column("active", width=45, anchor="center", stretch=False)
        self.tree.column("name", width=240, anchor="w", stretch=True)
        self.tree.column("category", width=160, anchor="w", stretch=True)
        self.tree.column("backend", width=130, anchor="w", stretch=True)
        self.tree.column("status", width=180, anchor="center", stretch=True)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        # Bindings for selection display and double-click
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_details())
        self.tree.bind("<Double-1>", self._on_double_click)

        # ==========================================
        # RIGHT COLUMN (Inspector Card - Scrollable)
        # ==========================================
        self.inspector_panel = tk.Frame(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.inspector_panel.grid(row=1, column=1, sticky="nsew", padx=(12, 24), pady=(8, 16))

        # Canvas & Scrollbar for vertical scrolling
        self.inspector_canvas = tk.Canvas(
            self.inspector_panel,
            bg=PHOENIX_THEME.card_bg,
            bd=0,
            highlightthickness=0,
        )
        self.inspector_scrollbar = ttk.Scrollbar(
            self.inspector_panel,
            orient="vertical",
            command=self.inspector_canvas.yview
        )
        self.inspector_canvas.configure(yscrollcommand=self.inspector_scrollbar.set)

        self.inspector_scrollbar.pack(side="right", fill="y")
        self.inspector_canvas.pack(side="left", fill="both", expand=True)

        # Scroll content frame inside Canvas
        self.inspector_scroll_content = tk.Frame(
            self.inspector_canvas,
            bg=PHOENIX_THEME.card_bg,
        )
        self.canvas_window_id = self.inspector_canvas.create_window(
            (0, 0),
            window=self.inspector_scroll_content,
            anchor="nw"
        )

        # Configure columns inside scroll content
        self.inspector_scroll_content.columnconfigure(0, weight=1)
        self.inspector_scroll_content.columnconfigure(1, weight=1)

        # Update scrollregion on configure
        self.inspector_scroll_content.bind(
            "<Configure>",
            lambda e: self.inspector_canvas.configure(
                scrollregion=self.inspector_canvas.bbox("all")
            )
        )
        # Keep width of inner frame matched to canvas width
        self.inspector_canvas.bind(
            "<Configure>",
            lambda e: self.inspector_canvas.itemconfig(
                self.canvas_window_id,
                width=e.width
            )
        )

        # Bind MouseWheel locally when mouse enters the inspector panel
        def _on_mousewheel(event: tk.Event) -> None:
            self.inspector_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(event: tk.Event) -> None:
            self.inspector_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(event: tk.Event) -> None:
            self.inspector_canvas.unbind_all("<MouseWheel>")

        self.inspector_panel.bind("<Enter>", _bind_mousewheel)
        self.inspector_panel.bind("<Leave>", _unbind_mousewheel)

        # Title: Model Information
        tk.Label(
            self.inspector_scroll_content,
            text="Model Information",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(12, 8))

        # Model properties sheet
        selected_props = [
            ("Name:", 1), ("Beschreibung:", 2), ("Kategorie:", 3),
            ("Version:", 4), ("Autor:", 5), ("Lizenz:", 6),
            ("Backend:", 7), ("Min. RAM:", 8), ("Empf. RAM:", 9),
            ("Installiert:", 10), ("Downloadstatus:", 11), ("Status:", 12),
            ("Pfad:", 13)
        ]
        for name, r in selected_props:
            tk.Label(
                self.inspector_scroll_content,
                text=name,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body,
                anchor="w"
            ).grid(row=r, column=0, sticky="w", padx=(16, 4), pady=4)

        # Create labels (description wrapping enabled)
        self.inspect_name = self._create_value_label(self.inspector_scroll_content, 1, 1)
        self.inspect_desc = self._create_value_label(self.inspector_scroll_content, 2, 1, wrap=True)
        self.inspect_category = self._create_value_label(self.inspector_scroll_content, 3, 1)
        self.inspect_version = self._create_value_label(self.inspector_scroll_content, 4, 1)
        self.inspect_author = self._create_value_label(self.inspector_scroll_content, 5, 1)
        self.inspect_license = self._create_value_label(self.inspector_scroll_content, 6, 1)
        self.inspect_backend = self._create_value_label(self.inspector_scroll_content, 7, 1)
        self.inspect_min_ram = self._create_value_label(self.inspector_scroll_content, 8, 1)
        self.inspect_rec_ram = self._create_value_label(self.inspector_scroll_content, 9, 1)
        self.inspect_installed = self._create_value_label(self.inspector_scroll_content, 10, 1)
        self.inspect_download = self._create_value_label(self.inspector_scroll_content, 11, 1)
        self.inspect_status = self._create_value_label(self.inspector_scroll_content, 12, 1)
        self.inspect_path = self._create_value_label(self.inspector_scroll_content, 13, 1, wrap=True)

        # Package catalog details
        tk.Label(
            self.inspector_scroll_content,
            text="Package Details",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(row=14, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))

        package_props = [
            ("Package Status:", 15), ("Package-Typ:", 16), ("Package-Version:", 17),
            ("Installierte Version:", 18), ("Update-Hinweis:", 19),
            ("Erforderliche Runtime:", 20), ("Installierte Runtime:", 21),
            ("Runtime-Verfügbarkeit:", 22), ("Package-Größe:", 23),
            ("Download-URL:", 24), ("Checksum:", 25), ("Capabilities:", 26)
        ]
        for name, r in package_props:
            tk.Label(
                self.inspector_scroll_content,
                text=name,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body,
                anchor="w"
            ).grid(row=r, column=0, sticky="w", padx=(16, 4), pady=4)

        self.inspect_package_status = self._create_value_label(self.inspector_scroll_content, 15, 1)
        self.inspect_package_status.configure(font=PHOENIX_THEME.font_button, fg=PHOENIX_THEME.accent)
        self.inspect_package_type = self._create_value_label(self.inspector_scroll_content, 16, 1)
        self.inspect_package_version = self._create_value_label(self.inspector_scroll_content, 17, 1)
        self.inspect_installed_version = self._create_value_label(self.inspector_scroll_content, 18, 1)
        self.inspect_update_hint = self._create_value_label(self.inspector_scroll_content, 19, 1, wrap=True)
        self.inspect_required_runtime = self._create_value_label(self.inspector_scroll_content, 20, 1)
        self.inspect_installed_runtime = self._create_value_label(self.inspector_scroll_content, 21, 1)
        self.inspect_runtime_available = self._create_value_label(self.inspector_scroll_content, 22, 1, wrap=True)
        self.inspect_package_size = self._create_value_label(self.inspector_scroll_content, 23, 1)
        self.inspect_download_url = self._create_value_label(self.inspector_scroll_content, 24, 1, wrap=True)
        self.inspect_checksum = self._create_value_label(self.inspector_scroll_content, 25, 1, wrap=True)
        self.inspect_capabilities = self._create_value_label(self.inspector_scroll_content, 26, 1, wrap=True)

        # ==========================================
        # FUTURE ACTION BUTTONS (PLACEHOLDERS)
        # ==========================================
        self.buttons_frame = tk.Frame(self.inspector_scroll_content, bg=PHOENIX_THEME.card_bg)
        self.buttons_frame.grid(row=27, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 12))
        self.buttons_frame.columnconfigure((0, 1), weight=1)

        button_style = {
            "bg": PHOENIX_THEME.elevated_bg,
            "fg": PHOENIX_THEME.text_muted,
            "activebackground": PHOENIX_THEME.elevated_bg,
            "activeforeground": PHOENIX_THEME.text_muted,
            "bd": 1,
            "relief": "flat",
            "font": PHOENIX_THEME.font_button,
            "state": "disabled",
            "height": 1,
        }

        self.btn_install = tk.Button(self.buttons_frame, text="Installieren", **button_style)
        self.btn_uninstall = tk.Button(self.buttons_frame, text="Deinstallieren", **button_style)
        self.btn_update = tk.Button(self.buttons_frame, text="Aktualisieren", **button_style)
        self.btn_benchmark = tk.Button(self.buttons_frame, text="Benchmark", **button_style)
        self.btn_open_folder = tk.Button(self.buttons_frame, text="Ordner öffnen", **button_style)

        self.btn_install.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        self.btn_uninstall.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        self.btn_update.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        self.btn_benchmark.grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        self.btn_open_folder.grid(row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        # ==========================================
        # SYSTEM ENVIRONMENT CARD
        # ==========================================
        tk.Label(
            self.inspector_scroll_content,
            text="System-Umgebung",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(row=28, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))

        env_props = [
            ("Betriebssystem:", 29), ("Architektur:", 30), ("Python:", 31),
            ("CPU:", 32), ("ONNX Runtime:", 33), ("QNN SDK:", 34), ("QNN Tools:", 35)
        ]
        for name, r in env_props:
            tk.Label(
                self.inspector_scroll_content,
                text=name,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body,
                anchor="w"
            ).grid(row=r, column=0, sticky="w", padx=(16, 4), pady=4)

        self.env_os = self._create_value_label(self.inspector_scroll_content, 29, 1)
        self.env_arch = self._create_value_label(self.inspector_scroll_content, 30, 1)
        self.env_python = self._create_value_label(self.inspector_scroll_content, 31, 1)
        self.env_cpu = self._create_value_label(self.inspector_scroll_content, 32, 1)
        self.env_onnx = self._create_value_label(self.inspector_scroll_content, 33, 1)
        self.env_qnn_sdk = self._create_value_label(self.inspector_scroll_content, 34, 1)
        self.env_qnn_tools = self._create_value_label(self.inspector_scroll_content, 35, 1)

        # ==========================================
        # BOTTOM STATUS BAR
        # ==========================================
        self.status_bar = tk.Frame(
            self,
            bg=PHOENIX_THEME.elevated_bg,
            height=26,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(24, 24), pady=(0, 16))
        
        self.status_lbl = tk.Label(
            self.status_bar,
            text="Bereit",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w"
        )
        self.status_lbl.pack(side="left", padx=12, pady=4)

    def _create_value_label(self, parent: tk.Frame, r: int, c: int, wrap: bool = False) -> tk.Label:
        lbl = tk.Label(
            parent,
            text="—",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            justify="left",
        )
        if wrap:
            lbl.configure(wraplength=180)
        lbl.grid(row=r, column=c, sticky="w", padx=(4, 16), pady=4)
        return lbl

    @staticmethod
    def _safe_text(value: object, fallback: str = "—") -> str:
        if value is None:
            return fallback
        text = str(value).strip()
        return text if text else fallback

    @staticmethod
    def _format_bool(value: object) -> str:
        return "Ja" if bool(value) else "Nein"

    @staticmethod
    def _format_ram(value: object) -> str:
        if value is None or value == "":
            return "—"
        return f"{value} GB"

    @staticmethod
    def _format_size(package: dict[str, object] | None) -> str:
        if not package:
            return "Nicht verfügbar"
        raw_bytes = package.get("estimated_size_bytes")
        raw_gb = package.get("estimated_size_gb")
        size_bytes = 0.0
        try:
            if raw_bytes not in (None, ""):
                size_bytes = float(raw_bytes)
            elif raw_gb not in (None, ""):
                size_bytes = float(raw_gb) * 1024 * 1024 * 1024
        except (TypeError, ValueError):
            return "Nicht verfügbar"
        if size_bytes <= 0:
            return "Nicht verfügbar"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        if size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    @staticmethod
    def _format_status(status: object) -> str:
        mapping = {
            "Installed": "INSTALLED",
            "Not Installed": "NOT_INSTALLED",
            "Update Available": "UPDATE_AVAILABLE",
            "Invalid": "INVALID",
            "Ready": "READY",
        }
        status_text = str(status or "").strip()
        return mapping.get(status_text, status_text.upper().replace(" ", "_") if status_text else "NOT_INSTALLED")

    @staticmethod
    def _format_status_badge(status: object) -> str:
        normalized = PhoenixModelManagerView._format_status(status)
        labels = {
            "INSTALLED": "[INSTALLED]",
            "NOT_INSTALLED": "[NOT INSTALLED]",
            "UPDATE_AVAILABLE": "[UPDATE AVAILABLE]",
            "INVALID": "[INVALID]",
            "READY": "[READY]",
        }
        return labels.get(normalized, f"[{normalized.replace('_', ' ')}]")

    @staticmethod
    def _runtime_family(runtime: object) -> str:
        runtime_text = PhoenixModelManagerView._safe_text(runtime, "").lower()
        if "qnn" in runtime_text:
            return "QNN"
        if "onnx" in runtime_text:
            return "ONNX"
        if "cpu" in runtime_text:
            return "CPU"
        return ""

    @staticmethod
    def _format_runtime_badge(runtime: object, fallback: str = "Nicht verfügbar") -> str:
        runtime_text = PhoenixModelManagerView._safe_text(runtime, fallback)
        family = PhoenixModelManagerView._runtime_family(runtime_text)
        if family:
            return f"[{family}] {runtime_text}"
        return runtime_text

    @staticmethod
    def _format_runtime_availability_badge(required_runtime: object, availability: str) -> str:
        family = PhoenixModelManagerView._runtime_family(required_runtime)
        if family:
            return f"[{family}] {availability}"
        return availability

    def _status_foreground(self, status: object) -> str:
        normalized = self._format_status(status)
        if normalized == "UPDATE_AVAILABLE":
            return PHOENIX_THEME.text_primary
        if normalized == "INVALID":
            return PHOENIX_THEME.text_disabled
        if normalized == "NOT_INSTALLED":
            return PHOENIX_THEME.text_muted
        return PHOENIX_THEME.accent

    def _configure_status_badge(self, label: tk.Label, status: object) -> None:
        label.configure(
            text=self._format_status_badge(status),
            bg=PHOENIX_THEME.elevated_bg,
            fg=self._status_foreground(status),
            font=PHOENIX_THEME.font_button,
            padx=6,
            pady=2,
        )

    @staticmethod
    def _format_capabilities(capabilities: object) -> str:
        if not isinstance(capabilities, dict) or not capabilities:
            return "Nicht verfügbar"
        enabled = sorted(str(name) for name, active in capabilities.items() if bool(active))
        if not enabled:
            return "Keine Capabilities angegeben"
        return "  ".join(f"[{name}]" for name in enabled)

    def _get_catalog_package(self, model_id: str) -> dict[str, object] | None:
        try:
            for package in self.controller.list_available_packages():
                if package.get("model_id") == model_id:
                    return package
        except Exception:
            return None
        return None

    def _resolved_package_status(self, model_id: str) -> str:
        package = self._get_catalog_package(model_id)
        if package:
            return self._format_status(package.get("status"))
        try:
            return self._format_status(self.controller.get_package_status(model_id))
        except Exception:
            return "NOT_INSTALLED"

    def _runtime_availability(self, required_runtime: str) -> str:
        if not required_runtime or required_runtime == "—":
            return "Nicht verfügbar"
        result = self.controller.get_discovery_result()
        runtime = required_runtime.lower()
        if "qnn" in runtime:
            if result and result.qnn_sdk_found and result.qnn_tools_found:
                return "Verfügbar"
            return "Fehlt: QNN Runtime nicht gefunden"
        if "onnx" in runtime:
            if result and result.onnx_available:
                return "Verfügbar"
            return "Fehlt: ONNX Runtime nicht installiert"
        if "cpu" in runtime:
            if result and result.cpu_available:
                return "Verfügbar"
            return "Fehlt: CPU Runtime nicht verfügbar"
        return "Nicht verfügbar"

    def _set_package_detail_values(self, model: dict[str, object]) -> None:
        model_id = self._safe_text(model.get("id"))
        package = self._get_catalog_package(model_id)
        status = self._resolved_package_status(model_id)
        package_version = self._safe_text(package.get("version") if package else model.get("version"))
        installed_version = self._safe_text(model.get("version"), "Nicht verfügbar") if model.get("installed") else "Nicht verfügbar"
        required_runtime = self._safe_text(
            package.get("recommended_runtime") if package else model.get("recommended_backend") or model.get("backend")
        )
        installed_runtime = self._safe_text(model.get("backend"), "Nicht verfügbar") if model.get("installed") else "Nicht verfügbar"
        capabilities = package.get("capabilities") if package else model.get("capabilities")

        update_hint = "Keine neuere Version verfügbar"
        if status == "UPDATE_AVAILABLE":
            update_hint = f"Neuere Version verfügbar: {package_version}"

        self._configure_status_badge(self.inspect_package_status, status)
        self.inspect_package_type.configure(text=self._safe_text(package.get("package_type") if package else "SMP"))
        self.inspect_package_version.configure(text=package_version)
        self.inspect_installed_version.configure(text=installed_version)
        self.inspect_update_hint.configure(text=update_hint)
        self.inspect_required_runtime.configure(text=self._format_runtime_badge(required_runtime))
        self.inspect_installed_runtime.configure(text=self._format_runtime_badge(installed_runtime))
        self.inspect_runtime_available.configure(
            text=self._format_runtime_availability_badge(required_runtime, self._runtime_availability(required_runtime))
        )
        self.inspect_package_size.configure(text=self._format_size(package))
        self.inspect_download_url.configure(text=self._safe_text(package.get("download_url") if package else None, "Nicht verfügbar"))
        self.inspect_checksum.configure(text=self._safe_text(package.get("checksum") if package else None, "Nicht verfügbar"))
        self.inspect_capabilities.configure(text=self._format_capabilities(capabilities))

    def refresh(self) -> None:
        """Reload models from repository and populate treeview while keeping active selection."""
        # 1. Get the currently selected model ID (if any) before refresh to preserve state
        selected_id = None
        selected = self.tree.selection()
        if selected:
            selected_id = selected[0]  # iid is the model ID!

        # 2. Reload repository data
        self.controller.refresh_repository()
        models = self.controller.get_all_models()
        active_model_id = self.controller.get_active_model_id()

        # 3. Rebuild Treeview items
        for item in self.tree.get_children():
            self.tree.delete(item)

        for model in models:
            is_active = "✓" if model.get("id") == active_model_id else ""
            model_id = self._safe_text(model.get("id"))
            self.tree.insert(
                "",
                "end",
                iid=model_id,
                values=(
                    is_active,
                    self._safe_text(model.get("display_name")),
                    self._safe_text(model.get("category")),
                    self._safe_text(model.get("backend")),
                    self._format_status_badge(self._resolved_package_status(model_id)),
                ),
            )

        # 4. Restore selection state or fallback to first item
        children = self.tree.get_children()
        if children:
            target_item = children[0]  # Default to first item
            if selected_id is not None and selected_id in children:
                target_item = selected_id
            
            # Apply selection
            self.tree.selection_set(target_item)
            self.tree.focus(target_item)
            
            # Populate details of the active selection (prevents overwrite/wipe)
            self.show_details()
        else:
            # Fallback values if list is completely empty
            for lbl in (self.inspect_name, self.inspect_desc, self.inspect_category,
                        self.inspect_version, self.inspect_author, self.inspect_license,
                        self.inspect_backend, self.inspect_min_ram, self.inspect_rec_ram,
                        self.inspect_installed, self.inspect_download, self.inspect_status,
                        self.inspect_path, self.inspect_package_status,
                        self.inspect_package_type, self.inspect_package_version,
                        self.inspect_installed_version, self.inspect_update_hint,
                        self.inspect_required_runtime, self.inspect_installed_runtime,
                        self.inspect_runtime_available, self.inspect_package_size,
                        self.inspect_download_url, self.inspect_checksum,
                        self.inspect_capabilities):
                lbl.configure(text="—")

        # 5. Update System Environment discovery details
        res = self.controller.get_discovery_result()
        if res:
            self.env_os.configure(text=self._safe_text(res.os_name))
            self.env_arch.configure(text=self._safe_text(res.architecture))
            self.env_python.configure(text=self._safe_text(res.python_version))
            self.env_cpu.configure(text="Verfügbar" if res.cpu_available else "Nicht verfügbar")
            
            onnx_txt = f"Verfügbar ({res.onnx_version})" if res.onnx_available else "Nicht installiert"
            self.env_onnx.configure(text=onnx_txt)
            
            qnn_sdk_txt = "Gefunden" if res.qnn_sdk_found else "Nicht gefunden"
            self.env_qnn_sdk.configure(text=qnn_sdk_txt)
            
            qnn_tools_txt = "Gefunden" if res.qnn_tools_found else "Nicht gefunden"
            self.env_qnn_tools.configure(text=qnn_tools_txt)

    def show_details(self) -> None:
        """Display comprehensive metadata properties for the selected model."""
        selected = self.tree.selection()
        if not selected:
            return

        model_id = selected[0]
        model = self.controller.get_model_details(model_id)
        if not model:
            return

        # Update Grid value labels cleanly
        self.inspect_name.configure(text=self._safe_text(model.get("display_name")))
        self.inspect_desc.configure(text=self._safe_text(model.get("description")))
        self.inspect_category.configure(text=self._safe_text(model.get("category")))
        self.inspect_version.configure(text=self._safe_text(model.get("version")))
        self.inspect_author.configure(text=self._safe_text(model.get("author")))
        self.inspect_license.configure(text=self._safe_text(model.get("license")))
        self.inspect_backend.configure(text=self._safe_text(model.get("backend")))
        self.inspect_min_ram.configure(text=self._format_ram(model.get("minimum_ram_gb")))
        self.inspect_rec_ram.configure(text=self._format_ram(model.get("recommended_ram_gb")))
        self.inspect_installed.configure(text=self._format_bool(model.get("installed")))
        self.inspect_download.configure(text="Heruntergeladen" if model.get("downloaded") else "Ausstehend")
        self._configure_status_badge(self.inspect_status, self._resolved_package_status(model_id))
        self.inspect_path.configure(text=self._safe_text(model.get("path"), "Nicht verfügbar"))
        self._set_package_detail_values(model)

        # Update status bar feedback: "Modell ausgewählt: <Modellname>"
        self.status_lbl.configure(text=f"Modell ausgewählt: {self._safe_text(model.get('display_name'))}")

        # Update button states based on installation status
        is_installed = model.get("installed", False)
        if is_installed:
            self.btn_install.configure(state="disabled", fg=PHOENIX_THEME.text_disabled)
            self.btn_uninstall.configure(state="normal", fg=PHOENIX_THEME.text_primary, command=lambda m_id=model["id"]: self._on_uninstall(m_id))
            
            model_path_str = model.get("path")
            if model_path_str and os.path.exists(model_path_str):
                self.btn_open_folder.configure(state="normal", fg=PHOENIX_THEME.text_primary, command=lambda path=model_path_str: self._on_open_folder(path))
            else:
                self.btn_open_folder.configure(state="disabled", fg=PHOENIX_THEME.text_disabled)
        else:
            self.btn_install.configure(state="normal", fg=PHOENIX_THEME.text_primary, command=lambda m_id=model["id"]: self._on_install(m_id))
            self.btn_uninstall.configure(state="disabled", fg=PHOENIX_THEME.text_disabled)
            self.btn_open_folder.configure(state="disabled", fg=PHOENIX_THEME.text_disabled)

    def _on_double_click(self, event: tk.Event) -> None:
        """
        Handler for double-click event on a model row.
        Sets the clicked model as the active model, updates checkmarks and inspector.
        Does NOT switch the workspace automatically to remain user-friendly.
        """
        selected = self.tree.selection()
        if not selected:
            return

        model_id = selected[0]
        model = self.controller.get_model_details(model_id)
        if not model:
            return

        display_name = model["display_name"]

        # Set as active model in ModelRepository
        self.controller.set_active_model_id(model_id)

        # Refresh visually to apply the checkmark marker and update inspector
        self.refresh()

        # Update status bar feedback: "Aktives Modell geändert: <Modellname>"
        self.status_lbl.configure(text=f"Aktives Modell geändert: {display_name}")

        # TODO (UX-003): Add context menu item "Mit diesem Modell generieren" 
        # which will explicitly trigger open_generate() on the WorkflowController.

    def _on_install(self, model_id: str) -> None:
        """Prompt user for a local model file/folder and trigger installation."""
        source_path = filedialog.askopenfilename(
            title="Lokale Modelldatei auswählen",
            filetypes=[
                ("Modelldateien", "*.bin *.safetensors *.onnx *.json *.pth"),
                ("Alle Dateien", "*.*")
            ]
        )
        if not source_path:
            return  # User cancelled

        # Inform user we are installing
        self.status_lbl.configure(text=f"Installiere Modell '{model_id}'...")
        self.update_idletasks()

        success = self.controller.install_model(model_id, source_path)
        if success:
            messagebox.showinfo(
                "Erfolg",
                f"Modell '{model_id}' wurde erfolgreich installiert."
            )
        else:
            messagebox.showerror(
                "Fehler",
                f"Installation des Modells '{model_id}' fehlgeschlagen. Überprüfen Sie den Speicherplatz und die Gültigkeit der Datei."
            )
        self.refresh()

    def _on_uninstall(self, model_id: str) -> None:
        """Confirm and uninstall the selected model."""
        confirm = messagebox.askyesno(
            "Modell deinstallieren",
            f"Möchten Sie das Modell '{model_id}' wirklich deinstallieren und alle zugehörigen lokalen Dateien löschen?"
        )
        if not confirm:
            return

        self.status_lbl.configure(text=f"Deinstalliere Modell '{model_id}'...")
        self.update_idletasks()

        success = self.controller.uninstall_model(model_id)
        if success:
            messagebox.showinfo(
                "Erfolg",
                f"Modell '{model_id}' wurde erfolgreich deinstalliert."
            )
        else:
            messagebox.showerror(
                "Fehler",
                f"Deinstallation des Modells '{model_id}' fehlgeschlagen."
            )
        self.refresh()

    def _on_open_folder(self, path: str) -> None:
        """Open the containing folder of the installed model in Windows Explorer."""
        if os.path.isfile(path):
            folder_path = os.path.dirname(path)
        else:
            folder_path = path

        if os.path.exists(folder_path):
            try:
                os.startfile(folder_path)
            except Exception as e:
                messagebox.showerror("Fehler", f"Ordner konnte nicht geöffnet werden: {e}")
        else:
            messagebox.showerror("Fehler", f"Der Pfad '{folder_path}' existiert nicht.")
