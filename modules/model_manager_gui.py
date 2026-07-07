import tkinter as tk
from tkinter import ttk
from controllers.model_manager_controller import ModelManagerController

BG = "#101418"
PANEL = "#171d23"
PANEL_2 = "#1f2730"
TEXT = "#e8edf2"
MUTED = "#9aa7b2"
ACCENT = "#3b82f6"


class ModelManagerWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Model Repository Manager")
        self.geometry("1020x660")
        self.configure(bg=BG)
        
        # Instantiate MVC Controller
        self.controller = ModelManagerController()
        
        self._build()
        self.refresh()

    def _label(self, parent, text, size=10, bold=False, color=TEXT, bg=None):
        return tk.Label(parent, text=text, font=("Segoe UI", size, "bold" if bold else "normal"),
                        fg=color, bg=bg if bg else parent["bg"])

    def _build(self):
        # Configure Grid Layout rows and columns weights
        self.rowconfigure(0, weight=0)  # Title block
        self.rowconfigure(1, weight=1)  # Main panel
        self.rowconfigure(2, weight=0)  # Status Bar
        self.columnconfigure(0, weight=7)
        self.columnconfigure(1, weight=3)

        # Header Block
        header = tk.Frame(self, bg=BG)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(18, 4))
        self._label(header, "AI Model Repository Manager", 20, True, TEXT, BG).pack(anchor="w")
        self._label(header, "Lokale Modelldatenbank (Datenbasiert über resources/models/*.json)", 10, False, MUTED, BG).pack(anchor="w")
        
        # Main Column Left (Table & Property Grid)
        main_column = tk.Frame(self, bg=BG)
        main_column.grid(row=1, column=0, sticky="nsew", padx=(24, 12), pady=12)
        main_column.rowconfigure(0, weight=6)
        main_column.rowconfigure(1, weight=4)
        main_column.columnconfigure(0, weight=1)

        # Table container panel
        table_frame = tk.Frame(main_column, bg=PANEL)
        table_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 16))
        
        columns = ("active", "name", "category", "backend", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14, selectmode="browse")
        self.tree.heading("active", text="Aktiv")
        self.tree.heading("name", text="Modellname")
        self.tree.heading("category", text="Kategorie")
        self.tree.heading("backend", text="Ziel-Backend")
        self.tree.heading("status", text="Status")
        
        self.tree.column("active", width=60, anchor="center")
        self.tree.column("name", width=230)
        self.tree.column("category", width=150)
        self.tree.column("backend", width=200)
        self.tree.column("status", width=100)
        self.tree.pack(fill="both", expand=True, padx=12, pady=12)

        # Selection Details Card (Left bottom)
        self.details_card = tk.Frame(main_column, bg=PANEL)
        self.details_card.grid(row=1, column=0, sticky="nsew")
        self.details_card.columnconfigure((0, 2), weight=1)
        self.details_card.columnconfigure((1, 3), weight=2)

        self._label(self.details_card, "Ausgewähltes Modell (Properties)", 10, True, TEXT).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(12, 6)
        )

        # Properties Grid
        properties = [
            ("Name:", 1, 0), ("Version:", 2, 0), ("Autor:", 3, 0), ("Lizenz:", 4, 0),
            ("Kategorie:", 1, 2), ("Backend:", 2, 2), ("RAM (Empfohlen):", 3, 2), ("Status:", 4, 2)
        ]
        for name, r, c in properties:
            self._label(self.details_card, name, 9, False, MUTED).grid(row=r, column=c, sticky="w", padx=(16, 4), pady=4)

        # Property Value Labels
        self.prop_name = self._create_value_label(self.details_card, 1, 1)
        self.prop_version = self._create_value_label(self.details_card, 2, 1)
        self.prop_author = self._create_value_label(self.details_card, 3, 1)
        self.prop_license = self._create_value_label(self.details_card, 4, 1)

        self.prop_category = self._create_value_label(self.details_card, 1, 3)
        self.prop_backend = self._create_value_label(self.details_card, 2, 3)
        self.prop_ram = self._create_value_label(self.details_card, 3, 3)
        self.prop_status = self._create_value_label(self.details_card, 4, 3)

        # Bindings
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_details())
        self.tree.bind("<Double-1>", self._on_double_click)

        # Right Column (Inspector Card)
        self.inspector_panel = tk.Frame(self, bg=PANEL)
        self.inspector_panel.grid(row=1, column=1, sticky="nsew", padx=(12, 24), pady=12)
        self.inspector_panel.columnconfigure(0, weight=1)
        self.inspector_panel.columnconfigure(1, weight=1)

        self._label(self.inspector_panel, "Model Inspector (Aktives Modell)", 10, True, TEXT).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 12)
        )

        active_props = [
            ("Aktives Modell:", 1), ("Version:", 2), ("Backend:", 3),
            ("Kategorie:", 4), ("Min. RAM:", 5), ("Status:", 6),
            ("Installiert:", 7), ("Downloadstatus:", 8)
        ]
        for name, r in active_props:
            self._label(self.inspector_panel, name, 9, False, MUTED).grid(row=r, column=0, sticky="w", padx=(16, 4), pady=8)

        self.active_name = self._create_value_label(self.inspector_panel, 1, 1)
        self.active_version = self._create_value_label(self.inspector_panel, 2, 1)
        self.active_backend = self._create_value_label(self.inspector_panel, 3, 1)
        self.active_category = self._create_value_label(self.inspector_panel, 4, 1)
        self.active_ram = self._create_value_label(self.inspector_panel, 5, 1)
        self.active_status = self._create_value_label(self.inspector_panel, 6, 1)
        self.active_installed = self._create_value_label(self.inspector_panel, 7, 1)
        self.active_download = self._create_value_label(self.inspector_panel, 8, 1)

        # Environment Section Header
        self._label(self.inspector_panel, "System-Umgebung", 10, True, TEXT).grid(
            row=9, column=0, columnspan=2, sticky="w", padx=16, pady=(20, 6)
        )

        # Environment Properties Grid
        env_props = [
            ("Betriebssystem:", 10), ("Architektur:", 11), ("Python:", 12),
            ("CPU:", 13), ("ONNX Runtime:", 14), ("QNN SDK:", 15), ("QNN Tools:", 16)
        ]
        for name, r in env_props:
            self._label(self.inspector_panel, name, 9, False, MUTED).grid(row=r, column=0, sticky="w", padx=(16, 4), pady=4)

        # Environment Value Labels
        self.env_os = self._create_value_label(self.inspector_panel, 10, 1)
        self.env_arch = self._create_value_label(self.inspector_panel, 11, 1)
        self.env_python = self._create_value_label(self.inspector_panel, 12, 1)
        self.env_cpu = self._create_value_label(self.inspector_panel, 13, 1)
        self.env_onnx = self._create_value_label(self.inspector_panel, 14, 1)
        self.env_qnn_sdk = self._create_value_label(self.inspector_panel, 15, 1)
        self.env_qnn_tools = self._create_value_label(self.inspector_panel, 16, 1)

        # Bottom Status Bar
        self.status_bar = tk.Frame(self, bg=PANEL_2, height=24)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        self.status_lbl = tk.Label(self.status_bar, text="Bereit", bg=PANEL_2, fg=MUTED, font=("Segoe UI", 8), anchor="w")
        self.status_lbl.pack(side="left", padx=12, pady=3)

    def _create_value_label(self, parent: tk.Frame, r: int, c: int) -> tk.Label:
        lbl = tk.Label(parent, text="-", bg=parent["bg"], fg=TEXT, font=("Segoe UI", 9), anchor="w")
        lbl.grid(row=r, column=c, sticky="w", padx=(4, 16), pady=4)
        return lbl

    def refresh(self):
        """Reload models from repository and populate treeview while keeping active selection."""
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
        
        # 3. Clear existing entries
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 4. Insert refreshed models
        for model in models:
            is_active = "✓" if model.get("id") == active_model_id else ""
            self.tree.insert("", "end", values=(
                is_active,
                model.get("display_name", ""),
                model.get("category", ""),
                model.get("backend", ""),
                model.get("status", ""),
            ))

        # 5. Update the Active Model Inspector panel
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
            
        # 6. Restore selection state or fallback to first item
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

        # 7. Update System Environment discovery details
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

    def show_details(self):
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
        
        # Update labels in the Property grid
        self.prop_name.configure(text=model.get("display_name", "-"))
        self.prop_version.configure(text=model.get("version", "-"))
        self.prop_author.configure(text=model.get("author", "-"))
        self.prop_license.configure(text=model.get("license", "-"))
        
        self.prop_category.configure(text=model.get("category", "-"))
        self.prop_backend.configure(text=model.get("backend", "-"))
        self.prop_ram.configure(text=f"{model.get('recommended_ram_gb', '-')} GB")
        self.prop_status.configure(text="Aktiv ausgewählt" if is_active else model.get("status", "-"))

    def _on_double_click(self, event):
        """
        Handler for double-click event on a model row.
        Sets the clicked model as active, updates the checkmarks and inspector.
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
