from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from controllers.model_manager_controller import ModelManagerController
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixModelManagerView(tk.Frame):
    """
    Phoenix Workspace View for the AI Model Manager.
    Presents models in a professional grid list, exposes detailed properties on selection,
    and shows the currently active model parameters in a dedicated right-hand Inspector.
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
        self.columnconfigure(0, weight=7)  # Main left column
        self.columnconfigure(1, weight=3)  # Inspector right column

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
        # MAIN LEFT COLUMN (Table & Selected Property Card)
        # ==========================================
        main_column = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        main_column.grid(row=1, column=0, sticky="nsew", padx=(24, 12), pady=(8, 16))
        main_column.rowconfigure(0, weight=6)  # Table gets more weight
        main_column.rowconfigure(1, weight=4)  # Selected model details card
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
        )
        style.configure(
            "Phoenix.Treeview.Heading",
            background=PHOENIX_THEME.elevated_bg,
            foreground=PHOENIX_THEME.text_primary,
            bordercolor=PHOENIX_THEME.border,
            lightcolor=PHOENIX_THEME.border,
            darkcolor=PHOENIX_THEME.border,
            font=PHOENIX_THEME.font_button,
        )
        style.map(
            "Phoenix.Treeview",
            background=[("selected", PHOENIX_THEME.accent)],
            foreground=[("selected", PHOENIX_THEME.text_on_accent)],
        )

        # Table container card
        table_frame = tk.Frame(
            main_column,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        table_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 16))

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

        self.tree.column("active", width=50, anchor="center")
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("category", width=120, anchor="w")
        self.tree.column("backend", width=160, anchor="w")
        self.tree.column("status", width=180, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        # Selected Model Property Details Card
        self.details_card = tk.Frame(
            main_column,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.details_card.grid(row=1, column=0, sticky="nsew")
        self.details_card.columnconfigure((0, 2), weight=1)
        self.details_card.columnconfigure((1, 3), weight=2)

        # Title for selection details
        tk.Label(
            self.details_card,
            text="Ausgewähltes Modell (Properties)",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, sticky="ew", padx=16, pady=(12, 8))

        # Create structured labels for 2x4 Property grid
        properties = [
            ("Name:", 1, 0), ("Version:", 2, 0), ("Autor:", 3, 0), ("Lizenz:", 4, 0),
            ("Kategorie:", 1, 2), ("Backend:", 2, 2), ("RAM (Empfohlen):", 3, 2), ("Status:", 4, 2)
        ]
        for name, r, c in properties:
            tk.Label(
                self.details_card,
                text=name,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body,
                anchor="w"
            ).grid(row=r, column=c, sticky="w", padx=(16, 4), pady=4)

        # Property Value Labels
        self.prop_name = self._create_value_label(self.details_card, 1, 1)
        self.prop_version = self._create_value_label(self.details_card, 2, 1)
        self.prop_author = self._create_value_label(self.details_card, 3, 1)
        self.prop_license = self._create_value_label(self.details_card, 4, 1)

        self.prop_category = self._create_value_label(self.details_card, 1, 3)
        self.prop_backend = self._create_value_label(self.details_card, 2, 3)
        self.prop_ram = self._create_value_label(self.details_card, 3, 3)
        self.prop_status = self._create_value_label(self.details_card, 4, 3)

        # Bindings for automatic details display and double-click
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

        # Title
        tk.Label(
            self.inspector_scroll_content,
            text="Model Inspector (Aktives Modell)",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(12, 8))

        # Vertical Property Sheet for active model
        active_props = [
            ("Aktives Modell:", 1), ("Version:", 2), ("Backend:", 3),
            ("Kategorie:", 4), ("Min. RAM:", 5), ("Status:", 6),
            ("Installiert:", 7), ("Downloadstatus:", 8)
        ]
        for name, r in active_props:
            tk.Label(
                self.inspector_scroll_content,
                text=name,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body,
                anchor="w"
            ).grid(row=r, column=0, sticky="w", padx=(16, 4), pady=4)

        # Active Value Labels
        self.active_name = self._create_value_label(self.inspector_scroll_content, 1, 1)
        self.active_version = self._create_value_label(self.inspector_scroll_content, 2, 1)
        self.active_backend = self._create_value_label(self.inspector_scroll_content, 3, 1)
        self.active_category = self._create_value_label(self.inspector_scroll_content, 4, 1)
        self.active_ram = self._create_value_label(self.inspector_scroll_content, 5, 1)
        self.active_status = self._create_value_label(self.inspector_scroll_content, 6, 1)
        self.active_installed = self._create_value_label(self.inspector_scroll_content, 7, 1)
        self.active_download = self._create_value_label(self.inspector_scroll_content, 8, 1)

        # Environment Section Header
        tk.Label(
            self.inspector_scroll_content,
            text="System-Umgebung",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(row=9, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))

        # Environment Properties Grid
        env_props = [
            ("Betriebssystem:", 10), ("Architektur:", 11), ("Python:", 12),
            ("CPU:", 13), ("ONNX Runtime:", 14), ("QNN SDK:", 15), ("QNN Tools:", 16)
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

        # Environment Value Labels
        self.env_os = self._create_value_label(self.inspector_scroll_content, 10, 1)
        self.env_arch = self._create_value_label(self.inspector_scroll_content, 11, 1)
        self.env_python = self._create_value_label(self.inspector_scroll_content, 12, 1)
        self.env_cpu = self._create_value_label(self.inspector_scroll_content, 13, 1)
        self.env_onnx = self._create_value_label(self.inspector_scroll_content, 14, 1)
        self.env_qnn_sdk = self._create_value_label(self.inspector_scroll_content, 15, 1)
        self.env_qnn_tools = self._create_value_label(self.inspector_scroll_content, 16, 1)

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
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        self.status_lbl = tk.Label(
            self.status_bar,
            text="Bereit",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w"
        )
        self.status_lbl.pack(side="left", padx=12, pady=4)

    def _create_value_label(self, parent: tk.Frame, r: int, c: int) -> tk.Label:
        lbl = tk.Label(
            parent,
            text="-",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="w"
        )
        lbl.grid(row=r, column=c, sticky="w", padx=(4, 16), pady=4)
        return lbl

    def refresh(self) -> None:
        """
        Reload models from repository and populate treeview while keeping active selection.

        Future Extension Hooks (P-055.3+):
        - Implement automatic file-system monitoring (e.g. using watchdog or native OS event polling)
          to automatically trigger reload when JSON files are modified, created or deleted.
          Once the auto-refresh monitoring is active, the manual "Aktualisieren" button can be removed.
        """
        # 1. Get the currently selected model ID (if any) before refresh to preserve state
        selected_id = None
        selected = self.tree.selection()
        if selected:
            try:
                idx = self.tree.index(selected[0])
                models = self.controller.get_all_models()
                if idx < len(models):
                    selected_id = models[idx]["id"]
            except Exception:
                pass

        # 2. Reload repository data
        self.controller.refresh_repository()
        models = self.controller.get_all_models()
        active_model_id = self.controller.get_active_model_id()

        # 3. Rebuild Treeview items
        for item in self.tree.get_children():
            self.tree.delete(item)

        for model in models:
            is_active = "✓" if model.get("id") == active_model_id else ""
            self.tree.insert(
                "",
                "end",
                values=(
                    is_active,
                    model.get("display_name", ""),
                    model.get("category", ""),
                    model.get("backend", ""),
                    model.get("status", ""),
                ),
            )

        # 4. Update the Active Model Inspector panel
        active_model = None
        for m in models:
            if m.get("id") == active_model_id:
                active_model = m
                break

        if active_model:
            self.active_name.configure(text=active_model.get("display_name", "-"))
            self.active_version.configure(text=active_model.get("version", "-"))
            self.active_backend.configure(text=active_model.get("backend", "-"))
            self.active_category.configure(text=active_model.get("category", "-"))
            self.active_ram.configure(text=f"{active_model.get('minimum_ram_gb', '-')} GB")
            self.active_status.configure(text=active_model.get("status", "-"))
            self.active_installed.configure(text="Ja" if active_model.get("installed") else "Nein")
            self.active_download.configure(text="Heruntergeladen" if active_model.get("downloaded") else "Ausstehend")
        else:
            self.active_name.configure(text="Kein aktives Modell")
            for lbl in (self.active_version, self.active_backend, self.active_category,
                        self.active_ram, self.active_status, self.active_installed, self.active_download):
                lbl.configure(text="-")

        # 5. Restore selection state or fallback to first item
        children = self.tree.get_children()
        if children:
            select_idx = 0  # Default to first item
            if selected_id is not None:
                # Find matching model index in refreshed data
                for i, m in enumerate(models):
                    if m["id"] == selected_id:
                        select_idx = i
                        break
            
            # Apply selection
            target_item = children[select_idx]
            self.tree.selection_set(target_item)
            self.tree.focus(target_item)
            
            # Populate details of the active selection (prevents overwrite/wipe)
            self.show_details()
        else:
            # Fallback values if list is completely empty
            for lbl in (self.prop_name, self.prop_version, self.prop_author, self.prop_license,
                        self.prop_category, self.prop_backend, self.prop_ram, self.prop_status):
                lbl.configure(text="-")

        # 6. Update System Environment discovery details
        res = self.controller.get_discovery_result()
        if res:
            self.env_os.configure(text=res.os_name)
            self.env_arch.configure(text=res.architecture)
            self.env_python.configure(text=res.python_version)
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

        try:
            # Query index dynamically from Tkinter tree hierarchy (100% robust fallback)
            idx = self.tree.index(selected[0])
        except Exception:
            return

        models = self.controller.get_all_models()
        if idx >= len(models):
            return

        model = models[idx]
        active_model_id = self.controller.get_active_model_id()
        is_active = model.get("id") == active_model_id

        # Update Grid value labels cleanly (no debug-string dumps)
        self.prop_name.configure(text=model.get("display_name", "-"))
        self.prop_version.configure(text=model.get("version", "-"))
        self.prop_author.configure(text=model.get("author", "-"))
        self.prop_license.configure(text=model.get("license", "-"))
        
        self.prop_category.configure(text=model.get("category", "-"))
        self.prop_backend.configure(text=model.get("backend", "-"))
        self.prop_ram.configure(text=f"{model.get('recommended_ram_gb', '-')} GB")
        self.prop_status.configure(text=model.get("status", "-"))

    def _on_double_click(self, event: tk.Event) -> None:
        """
        Handler for double-click event on a model row.
        Sets the clicked model as the active model, updates checkmarks and inspector.
        Does NOT switch the workspace automatically to remain user-friendly.
        """
        selected = self.tree.selection()
        if not selected:
            return

        try:
            idx = self.tree.index(selected[0])
        except Exception:
            return

        models = self.controller.get_all_models()
        if idx >= len(models):
            return

        model = models[idx]
        model_id = model["id"]
        display_name = model["display_name"]

        # Set as active model in ModelRepository
        self.controller.set_active_model_id(model_id)

        # Refresh visually to apply the checkmark marker and update inspector
        self.refresh()

        # Update status bar feedback
        self.status_lbl.configure(text=f"Aktives Modell geändert: {display_name}")

        # TODO (UX-003): Add context menu item "Mit diesem Modell generieren" 
        # which will explicitly trigger open_generate() on the WorkflowController.
