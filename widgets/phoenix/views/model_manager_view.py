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
            ("Installiert:", 10), ("Downloadstatus:", 11), ("Status:", 12)
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

        # ==========================================
        # FUTURE ACTION BUTTONS (PLACEHOLDERS)
        # ==========================================
        self.buttons_frame = tk.Frame(self.inspector_scroll_content, bg=PHOENIX_THEME.card_bg)
        self.buttons_frame.grid(row=13, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 12))
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
        ).grid(row=14, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))

        env_props = [
            ("Betriebssystem:", 15), ("Architektur:", 16), ("Python:", 17),
            ("CPU:", 18), ("ONNX Runtime:", 19), ("QNN SDK:", 20), ("QNN Tools:", 21)
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

        self.env_os = self._create_value_label(self.inspector_scroll_content, 15, 1)
        self.env_arch = self._create_value_label(self.inspector_scroll_content, 16, 1)
        self.env_python = self._create_value_label(self.inspector_scroll_content, 17, 1)
        self.env_cpu = self._create_value_label(self.inspector_scroll_content, 18, 1)
        self.env_onnx = self._create_value_label(self.inspector_scroll_content, 19, 1)
        self.env_qnn_sdk = self._create_value_label(self.inspector_scroll_content, 20, 1)
        self.env_qnn_tools = self._create_value_label(self.inspector_scroll_content, 21, 1)

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
            text="-",
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

    def refresh(self) -> None:
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

        # 4. Restore selection state or fallback to first item
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
            for lbl in (self.inspect_name, self.inspect_desc, self.inspect_category,
                        self.inspect_version, self.inspect_author, self.inspect_license,
                        self.inspect_backend, self.inspect_min_ram, self.inspect_rec_ram,
                        self.inspect_installed, self.inspect_download, self.inspect_status):
                lbl.configure(text="-")

        # 5. Update System Environment discovery details
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
            # Query index dynamically from Tkinter tree hierarchy
            idx = self.tree.index(selected[0])
        except Exception:
            return

        models = self.controller.get_all_models()
        if idx >= len(models):
            return

        model = models[idx]

        # Update Grid value labels cleanly
        self.inspect_name.configure(text=model.get("display_name", "-"))
        self.inspect_desc.configure(text=model.get("description", "-"))
        self.inspect_category.configure(text=model.get("category", "-"))
        self.inspect_version.configure(text=model.get("version", "-"))
        self.inspect_author.configure(text=model.get("author", "-"))
        self.inspect_license.configure(text=model.get("license", "-"))
        self.inspect_backend.configure(text=model.get("backend", "-"))
        self.inspect_min_ram.configure(text=f"{model.get('minimum_ram_gb', '-')} GB")
        self.inspect_rec_ram.configure(text=f"{model.get('recommended_ram_gb', '-')} GB")
        self.inspect_installed.configure(text="Ja" if model.get("installed") else "Nein")
        self.inspect_download.configure(text="Heruntergeladen" if model.get("downloaded") else "Ausstehend")
        self.inspect_status.configure(text=model.get("status", "-"))

        # Update status bar feedback: "Modell ausgewählt: <Modellname>"
        self.status_lbl.configure(text=f"Modell ausgewählt: {model.get('display_name', '-')}")

        # Update button states based on installation status
        is_installed = model.get("installed", False)
        if is_installed:
            self.btn_install.configure(state="disabled", fg=PHOENIX_THEME.text_disabled)
            self.btn_uninstall.configure(state="normal", fg=PHOENIX_THEME.text_primary, command=lambda: self._on_uninstall(model["id"]))
            
            model_path_str = model.get("path")
            if model_path_str and os.path.exists(model_path_str):
                self.btn_open_folder.configure(state="normal", fg=PHOENIX_THEME.text_primary, command=lambda: self._on_open_folder(model_path_str))
            else:
                self.btn_open_folder.configure(state="disabled", fg=PHOENIX_THEME.text_disabled)
        else:
            self.btn_install.configure(state="normal", fg=PHOENIX_THEME.text_primary, command=lambda: self._on_install(model["id"]))
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
