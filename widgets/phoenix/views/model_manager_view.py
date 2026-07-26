from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from controllers.model_manager_controller import ModelManagerController
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr



class _Tooltip:
    """Small Tk tooltip helper for existing package action buttons."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.window: tk.Toplevel | None = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event: tk.Event | None = None) -> None:
        if self.window or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.window,
            text=self.text,
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


class PhoenixModelManagerView(tk.Frame):
    """
    Phoenix Workspace View for the AI Model Manager.
    Presents models in a professional grid list and exposes detailed properties
    along with system diagnostics in a single, dedicated right-hand Inspector.
    """

    def __init__(self, master: tk.Misc, controller: ModelManagerController | None = None) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.controller = controller or ModelManagerController()
        self._advanced_popup: tk.Toplevel | None = None
        self._advanced_return_focus: tk.Misc | None = None

        from app.model_downloader import ModelDownloader
        self.downloader = ModelDownloader()

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
            text=tr("model_repository_manager", "Model Repository Manager"),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            header_frame,
            text=tr("local_model_db_subtitle", "Lokale Modelldatenbank (Datenbasiert über resources/models/*.json)"),
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
        style.configure(
            "Phoenix.Horizontal.TProgressbar",
            thickness=10,
            troughcolor=PHOENIX_THEME.elevated_bg,
            background=PHOENIX_THEME.accent,
            bordercolor=PHOENIX_THEME.border,
            lightcolor=PHOENIX_THEME.border,
            darkcolor=PHOENIX_THEME.border,
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
        self.tree.heading("active", text=tr("active", "Aktiv"))
        self.tree.heading("name", text=tr("model_name", "Modellname"))
        self.tree.heading("category", text=tr("category", "Kategorie"))
        self.tree.heading("backend", text=tr("target_backend", "Ziel-Backend"))
        self.tree.heading("status", text=tr("status", "Status"))

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

        # Create and pack the download frame at the bottom of the inspector panel,
        # so it is always visible without scrolling.
        self.download_frame = tk.Frame(self.inspector_panel, bg=PHOENIX_THEME.card_bg)
        self.download_frame.pack(side="bottom", fill="x", padx=16, pady=(10, 16))
        self.download_frame.columnconfigure(0, weight=1)

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
            command=self.inspector_canvas.yview,
            style="Phoenix.Vertical.TScrollbar"
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

        # Compact model information. Operational and diagnostic controls live in
        # the modal Advanced Settings popup below.
        tk.Label(
            self.inspector_scroll_content,
            text=tr("model_info_title", "Modellinformationen"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(12, 8))

        base_props = [
            (tr("model_name_label", "Modellname:"), 1),
            (tr("version_label", "Version:"), 2),
            (tr("backend_label_colon", "Backend:"), 3),
            (tr("status_label_colon", "Status:"), 4),
            (tr("description_label_colon", "Beschreibung:"), 5),
            (tr("capabilities_label_colon", "Fähigkeiten:"), 6),
        ]
        for name, row in base_props:
            tk.Label(
                self.inspector_scroll_content,
                text=name,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body,
                anchor="w"
            ).grid(row=row, column=0, sticky="nw", padx=(16, 4), pady=4)

        self.inspect_name = self._create_value_label(self.inspector_scroll_content, 1, 1)
        self.inspect_version = self._create_value_label(self.inspector_scroll_content, 2, 1)
        self.inspect_backend = self._create_value_label(self.inspector_scroll_content, 3, 1)
        self.inspect_status = self._create_value_label(self.inspector_scroll_content, 4, 1)
        self.inspect_desc = self._create_value_label(self.inspector_scroll_content, 5, 1, wrap=True)
        self.inspect_capabilities = self._create_value_label(self.inspector_scroll_content, 6, 1, wrap=True)

        tk.Label(
            self.inspector_scroll_content,
            text=tr("install_info_title", "Installationsinformationen"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(row=7, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))

        install_props = [
            (tr("installed_label", "Installiert:"), 8),
            (tr("download_status_label", "Downloadstatus:"), 9),
            (tr("path_label_colon", "Pfad:"), 10),
        ]
        for name, row in install_props:
            tk.Label(
                self.inspector_scroll_content,
                text=name,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body,
                anchor="w"
            ).grid(row=row, column=0, sticky="nw", padx=(16, 4), pady=4)

        self.inspect_installed = self._create_value_label(self.inspector_scroll_content, 8, 1)
        self.inspect_download = self._create_value_label(self.inspector_scroll_content, 9, 1)
        self.inspect_path = self._create_value_label(self.inspector_scroll_content, 10, 1, wrap=True)

        # Folder size & Samplers details
        tk.Label(
            self.inspector_scroll_content,
            text=tr("folder_size_label", "Dateigröße:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w"
        ).grid(row=11, column=0, sticky="nw", padx=(16, 4), pady=4)
        
        self.inspect_size = self._create_value_label(self.inspector_scroll_content, 11, 1)

        tk.Label(
            self.inspector_scroll_content,
            text=tr("supported_samplers_label", "Unterstützte Sampler:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w"
        ).grid(row=12, column=0, sticky="nw", padx=(16, 4), pady=4)

        self.inspect_samplers = self._create_value_label(self.inspector_scroll_content, 12, 1, wrap=True)

        self.advanced_settings_button = tk.Button(
            self.inspector_scroll_content,
            text=tr("advanced_settings_btn", "⚙️ Erweiterte Einstellungen..."),
            command=self._open_advanced_settings,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground=PHOENIX_THEME.text_on_accent,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=12,
            pady=9,
        )
        self.advanced_settings_button.grid(
            row=13,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=16,
            pady=(18, 16),
        )

        # self.download_frame is already created and packed at the bottom of inspector_panel

        self.download_button = tk.Button(
            self.download_frame,
            text=tr("download_model_btn", "Modell herunterladen"),
            command=self._start_model_download,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground=PHOENIX_THEME.text_on_accent,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=12,
            pady=9,
        )
        self.download_button.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        self.download_progress = ttk.Progressbar(
            self.download_frame,
            orient="horizontal",
            mode="determinate",
            style="Phoenix.Horizontal.TProgressbar"
        )

        self.download_status_lbl = tk.Label(
            self.download_frame,
            text="",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left"
        )

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
            text=tr("ready", "Bereit"),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w"
        )
        self.status_lbl.pack(side="left", padx=12, pady=4)

    def _advanced_popup_is_open(self) -> bool:
        try:
            return self._advanced_popup is not None and bool(self._advanced_popup.winfo_exists())
        except tk.TclError:
            return False

    def _open_advanced_settings(self) -> None:
        if self._advanced_popup_is_open():
            self._advanced_popup.lift()
            self._advanced_popup.focus_force()
            return

        if not self.tree.selection():
            messagebox.showinfo(tr("advanced_settings_title", "Erweiterte Einstellungen"), tr("no_model_selected", "Kein Modell ausgewählt."))
            return

        self._advanced_return_focus = self.focus_get()
        popup = tk.Toplevel(self.winfo_toplevel(), bg=PHOENIX_THEME.app_bg)
        self._advanced_popup = popup
        popup.withdraw()
        popup.title(tr("advanced_settings_popup_title", "AI Model Manager – Erweiterte Einstellungen"))
        popup.transient(self.winfo_toplevel())
        popup.protocol("WM_DELETE_WINDOW", self._close_advanced_settings)
        popup.bind("<Escape>", lambda _event: self._close_advanced_settings())

        heading = tk.Frame(popup, bg=PHOENIX_THEME.app_bg)
        heading.pack(
            fill="x",
            padx=PHOENIX_THEME.space_xl,
            pady=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_md),
        )
        tk.Label(
            heading,
            text=tr("advanced_settings_title", "Erweiterte Einstellungen"),
            bg=PHOENIX_THEME.app_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            heading,
            text=tr("advanced_settings_popup_subtitle", "Modell-, Package-, Validierungs- und Diagnoseoptionen des ausgewählten Modells"),
            bg=PHOENIX_THEME.app_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).pack(fill="x", pady=(PHOENIX_THEME.space_xs, 0))

        tabs_shell = tk.Frame(popup, bg=PHOENIX_THEME.app_bg)
        tabs_shell.pack(
            fill="both",
            expand=True,
            padx=PHOENIX_THEME.space_xl,
            pady=(0, PHOENIX_THEME.space_md),
        )

        segment_bar = tk.Frame(tabs_shell, bg=PHOENIX_THEME.app_bg)
        segment_bar.pack(fill="x")
        tab_host = tk.Frame(
            tabs_shell,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        tab_host.pack(fill="both", expand=True)
        tab_host.rowconfigure(0, weight=1)
        tab_host.columnconfigure(0, weight=1)

        model_tab = tk.Frame(tab_host, bg=PHOENIX_THEME.card_bg)
        package_tab = tk.Frame(tab_host, bg=PHOENIX_THEME.card_bg)
        system_tab = tk.Frame(tab_host, bg=PHOENIX_THEME.card_bg)
        tab_frames = (model_tab, package_tab, system_tab)
        tab_titles = (tr("tab_model", "Modell"), tr("tab_package", "Package & Validierung"), tr("tab_system", "System & Diagnose"))
        for tab_frame in tab_frames:
            tab_frame.grid(row=0, column=0, sticky="nsew")

        tab_buttons: list[tk.Label] = []
        self._advanced_active_tab = 0

        def render_tabs() -> None:
            for index, button in enumerate(tab_buttons):
                active = index == self._advanced_active_tab
                button.configure(
                    bg=PHOENIX_THEME.accent if active else PHOENIX_THEME.elevated_bg,
                    fg=PHOENIX_THEME.text_on_accent if active else PHOENIX_THEME.text_secondary,
                )

        def select_tab(index: int, *, keyboard: bool = False) -> str:
            self._advanced_active_tab = index
            tab_frames[index].tkraise()
            render_tabs()
            if keyboard:
                tab_buttons[index].focus_set()
            else:
                popup.focus_set()
            return "break"

        def move_tab(index: int, delta: int) -> str:
            return select_tab((index + delta) % len(tab_frames), keyboard=True)

        def on_tab_enter(index: int) -> None:
            if index != self._advanced_active_tab:
                tab_buttons[index].configure(
                    bg=PHOENIX_THEME.accent_soft,
                    fg=PHOENIX_THEME.text_primary,
                )

        def on_tab_leave(index: int) -> None:
            render_tabs()

        def on_tab_focus(index: int, focused: bool) -> None:
            tab_buttons[index].configure(
                highlightbackground=PHOENIX_THEME.accent if focused else PHOENIX_THEME.border,
                highlightcolor=PHOENIX_THEME.accent if focused else PHOENIX_THEME.border,
            )

        for index, title in enumerate(tab_titles):
            button = tk.Label(
                segment_bar,
                text=title,
                bg=PHOENIX_THEME.elevated_bg,
                fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_button,
                cursor="hand2",
                takefocus=True,
                padx=PHOENIX_THEME.button_pad_x,
                pady=PHOENIX_THEME.button_pad_y,
                highlightbackground=PHOENIX_THEME.border,
                highlightcolor=PHOENIX_THEME.border,
                highlightthickness=1,
            )
            button.pack(side="left")
            tab_buttons.append(button)

            button.bind("<Button-1>", lambda _event, tab_index=index: select_tab(tab_index))
            button.bind("<Return>", lambda _event, tab_index=index: select_tab(tab_index, keyboard=True))
            button.bind("<space>", lambda _event, tab_index=index: select_tab(tab_index, keyboard=True))
            button.bind("<Left>", lambda _event, tab_index=index: move_tab(tab_index, -1))
            button.bind("<Right>", lambda _event, tab_index=index: move_tab(tab_index, 1))
            button.bind("<Home>", lambda _event: select_tab(0, keyboard=True))
            button.bind("<End>", lambda _event: select_tab(len(tab_frames) - 1, keyboard=True))
            button.bind("<Enter>", lambda _event, tab_index=index: on_tab_enter(tab_index))
            button.bind("<Leave>", lambda _event, tab_index=index: on_tab_leave(tab_index))
            button.bind("<FocusIn>", lambda _event, tab_index=index: on_tab_focus(tab_index, True))
            button.bind("<FocusOut>", lambda _event, tab_index=index: on_tab_focus(tab_index, False))

        self._advanced_tab_buttons = tab_buttons
        self._advanced_tab_frames = tab_frames
        self._advanced_select_tab = select_tab
        select_tab(0)

        self._build_advanced_model_tab(model_tab)
        self._build_advanced_package_tab(package_tab)
        self._build_advanced_system_tab(system_tab)

        footer = tk.Frame(popup, bg=PHOENIX_THEME.app_bg)
        footer.pack(
            fill="x",
            padx=PHOENIX_THEME.space_xl,
            pady=(0, PHOENIX_THEME.space_lg),
        )
        close_button = tk.Button(
            footer,
            text=tr("close", "Schließen"),
            command=self._close_advanced_settings,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground=PHOENIX_THEME.text_on_accent,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=PHOENIX_THEME.button_pad_x,
            pady=PHOENIX_THEME.button_pad_y,
        )
        close_button.pack(
            side="right",
            padx=PHOENIX_THEME.space_sm,
            pady=PHOENIX_THEME.space_sm,
        )

        self.show_details()
        self._update_environment_details()

        popup.update_idletasks()
        owner = self.winfo_toplevel()
        width = max(820, popup.winfo_reqwidth())
        height = max(620, popup.winfo_reqheight())
        x = owner.winfo_rootx() + max(0, (owner.winfo_width() - width) // 2)
        y = owner.winfo_rooty() + max(0, (owner.winfo_height() - height) // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.minsize(760, 560)
        popup.deiconify()
        popup.lift()
        popup.grab_set()
        close_button.focus_set()

    def _advanced_section(self, parent: tk.Frame, title: str, row: int) -> None:
        section = tk.Frame(parent, bg=PHOENIX_THEME.card_bg)
        section.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.space_lg,
            pady=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_sm),
        )
        tk.Label(
            section,
            text=title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).pack(side="left")
        tk.Frame(section, bg=PHOENIX_THEME.border, height=1).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(PHOENIX_THEME.space_sm, 0),
        )

    def _advanced_value_label(
        self,
        parent: tk.Frame,
        row: int,
        *,
        wrap: bool = False,
    ) -> tk.Label:
        value = tk.Label(
            parent,
            text="—",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            justify="left",
        )
        if wrap:
            value.configure(wraplength=420)
        value.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_lg),
            pady=PHOENIX_THEME.space_xs,
        )
        return value

    def _build_advanced_model_tab(self, parent: tk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        self._advanced_section(parent, tr("model_parameters_section", "Modellparameter"), 0)

        properties = [
            (tr("category_label_colon", "Kategorie:"), 1),
            (tr("author_label_colon", "Autor:"), 2),
            (tr("license_label_colon", "Lizenz:"), 3),
            (tr("min_ram_label", "Min. RAM:"), 4),
            (tr("rec_ram_label", "Empf. RAM:"), 5),
        ]
        for name, row in properties:
            tk.Label(
                parent,
                text=name,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body,
                anchor="w",
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_sm),
                pady=PHOENIX_THEME.space_xs,
            )

        self.inspect_category = self._advanced_value_label(parent, 1)
        self.inspect_author = self._advanced_value_label(parent, 2)
        self.inspect_license = self._advanced_value_label(parent, 3, wrap=True)
        self.inspect_min_ram = self._advanced_value_label(parent, 4)
        self.inspect_rec_ram = self._advanced_value_label(parent, 5)

    def _build_advanced_package_tab(self, parent: tk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        self._advanced_section(parent, tr("package_details_section", "Package Details & Validierung"), 0)

        properties = [
            (tr("package_status_label", "Package Status:"), 1),
            (tr("package_type_label", "Package-Typ:"), 2),
            (tr("package_version_label", "Package-Version:"), 3),
            (tr("installed_version_label", "Installierte Version:"), 4),
            (tr("update_hint_label", "Update-Hinweis:"), 5),
            (tr("required_runtime_label", "Erforderliche Runtime:"), 6),
            (tr("installed_runtime_label", "Installierte Runtime:"), 7),
            (tr("runtime_avail_label", "Runtime-Verfügbarkeit:"), 8),
            (tr("package_size_label", "Package-Größe:"), 9),
            (tr("download_url_label", "Download-URL:"), 10),
            (tr("checksum_label_colon", "Checksum:"), 11),
        ]
        for name, row in properties:
            tk.Label(
                parent,
                text=name,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body,
                anchor="w",
            ).grid(
                row=row,
                column=0,
                sticky="nw",
                padx=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_sm),
                pady=PHOENIX_THEME.space_xs,
            )

        self.inspect_package_status = self._advanced_value_label(parent, 1)
        self.inspect_package_status.configure(font=PHOENIX_THEME.font_button, fg=PHOENIX_THEME.accent)
        self.inspect_package_type = self._advanced_value_label(parent, 2)
        self.inspect_package_version = self._advanced_value_label(parent, 3)
        self.inspect_installed_version = self._advanced_value_label(parent, 4)
        self.inspect_update_hint = self._advanced_value_label(parent, 5, wrap=True)
        self.inspect_required_runtime = self._advanced_value_label(parent, 6)
        self.inspect_installed_runtime = self._advanced_value_label(parent, 7)
        self.inspect_runtime_available = self._advanced_value_label(parent, 8, wrap=True)
        self.inspect_package_size = self._advanced_value_label(parent, 9)
        self.inspect_download_url = self._advanced_value_label(parent, 10, wrap=True)
        self.inspect_checksum = self._advanced_value_label(parent, 11, wrap=True)

        self.buttons_frame = tk.Frame(parent, bg=PHOENIX_THEME.card_bg)
        self.buttons_frame.grid(
            row=12,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.space_lg,
            pady=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_lg),
        )
        self.buttons_frame.columnconfigure((0, 1), weight=1)

        button_style = {
            "bg": PHOENIX_THEME.elevated_bg,
            "fg": PHOENIX_THEME.text_muted,
            "activebackground": PHOENIX_THEME.elevated_bg,
            "activeforeground": PHOENIX_THEME.text_muted,
            "highlightbackground": PHOENIX_THEME.border,
            "highlightthickness": 1,
            "bd": 0,
            "relief": "flat",
            "font": PHOENIX_THEME.font_button,
            "state": "disabled",
            "padx": PHOENIX_THEME.button_pad_x,
            "pady": PHOENIX_THEME.button_pad_y,
            "cursor": "hand2",
        }
        self.btn_install = tk.Button(
            self.buttons_frame,
            text=tr("install", "Install"),
            command=lambda: self._on_package_action("install"),
            **button_style,
        )
        self.btn_validate = tk.Button(
            self.buttons_frame,
            text=tr("validate", "Validate"),
            command=lambda: self._on_package_action("validate"),
            **button_style,
        )
        self.btn_update = tk.Button(
            self.buttons_frame,
            text=tr("update", "Update"),
            command=lambda: self._on_package_action("update"),
            **button_style,
        )
        self.btn_remove = tk.Button(
            self.buttons_frame,
            text=tr("remove", "Remove"),
            command=lambda: self._on_package_action("remove"),
            **button_style,
        )
        self.btn_install.grid(row=0, column=0, sticky="ew", padx=(0, PHOENIX_THEME.space_xs), pady=PHOENIX_THEME.space_xs)
        self.btn_validate.grid(row=0, column=1, sticky="ew", padx=(PHOENIX_THEME.space_xs, 0), pady=PHOENIX_THEME.space_xs)
        self.btn_update.grid(row=1, column=0, sticky="ew", padx=(0, PHOENIX_THEME.space_xs), pady=PHOENIX_THEME.space_xs)
        self.btn_remove.grid(row=1, column=1, sticky="ew", padx=(PHOENIX_THEME.space_xs, 0), pady=PHOENIX_THEME.space_xs)
        _Tooltip(self.btn_install, tr("install_tooltip", "Install local SMP package."))
        _Tooltip(self.btn_validate, tr("validate_tooltip", "Validate installed package locally."))
        _Tooltip(self.btn_update, tr("update_tooltip", "Update from local SMP package."))
        _Tooltip(self.btn_remove, tr("remove_tooltip", "Remove local package files safely."))

    def _build_advanced_system_tab(self, parent: tk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        self._advanced_section(parent, tr("system_environment_section", "System-Umgebung"), 0)

        environment_properties = [
            (tr("os_label", "Betriebssystem:"), 1),
            (tr("arch_label", "Architektur:"), 2),
            (tr("python_label", "Python:"), 3),
            (tr("cpu_label_colon", "CPU:"), 4),
            (tr("onnx_runtime_label", "ONNX Runtime:"), 5),
            (tr("qnn_sdk_label", "QNN SDK:"), 6),
            (tr("qnn_tools_label", "QNN Tools:"), 7),
        ]
        for name, row in environment_properties:
            tk.Label(
                parent,
                text=name,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body,
                anchor="w",
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_sm),
                pady=PHOENIX_THEME.space_xs,
            )

        self.env_os = self._advanced_value_label(parent, 1)
        self.env_arch = self._advanced_value_label(parent, 2)
        self.env_python = self._advanced_value_label(parent, 3)
        self.env_cpu = self._advanced_value_label(parent, 4)
        self.env_onnx = self._advanced_value_label(parent, 5)
        self.env_qnn_sdk = self._advanced_value_label(parent, 6)
        self.env_qnn_tools = self._advanced_value_label(parent, 7)

        self.npu_diag_button = tk.Button(
            parent,
            text=tr("run_npu_diag_btn", "Run NPU Diagnostic"),
            command=self._run_npu_diagnostic,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent_soft,
            activeforeground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            padx=PHOENIX_THEME.button_pad_x,
            pady=PHOENIX_THEME.button_pad_y,
            cursor="hand2",
        )
        self.npu_diag_button.grid(
            row=8,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.space_lg,
            pady=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_md),
        )
        _Tooltip(self.npu_diag_button, tr("run_npu_diag_tooltip", "Run local MobileNetV2 DLC smoke test through qnn-net-run."))

        self._advanced_section(parent, tr("diagnostic_result_section", "Diagnoseergebnis"), 9)
        diagnostic_properties = [
            (tr("qnn_avail_label", "QNN verfügbar:"), 10),
            (tr("dlc_test_label", "DLC-Test:"), 11),
            (tr("exit_code_label", "Exit Code:"), 12),
            (tr("output_file_label", "Output-Datei:"), 13),
            (tr("profiling_label", "Profiling:"), 14),
            (tr("report_label", "Bericht:"), 15),
            (tr("warnings_label", "Warnungen:"), 16),
        ]
        for name, row in diagnostic_properties:
            tk.Label(
                parent,
                text=name,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_body,
                anchor="w",
            ).grid(
                row=row,
                column=0,
                sticky="nw",
                padx=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_sm),
                pady=PHOENIX_THEME.space_xs,
            )

        self.npu_qnn_available = self._advanced_value_label(parent, 10)
        self.npu_test_status = self._advanced_value_label(parent, 11)
        self.npu_exit_code = self._advanced_value_label(parent, 12)
        self.npu_output_file = self._advanced_value_label(parent, 13, wrap=True)
        self.npu_profiling_files = self._advanced_value_label(parent, 14, wrap=True)
        self.npu_report_path = self._advanced_value_label(parent, 15, wrap=True)
        self.npu_warnings = self._advanced_value_label(parent, 16, wrap=True)

    def _close_advanced_settings(self) -> None:
        popup = self._advanced_popup
        return_focus = self._advanced_return_focus
        self._advanced_popup = None
        self._advanced_return_focus = None
        if popup is not None:
            try:
                if popup.grab_current() == popup:
                    popup.grab_release()
                popup.destroy()
            except tk.TclError:
                pass

        if return_focus is not None:
            try:
                if return_focus.winfo_exists():
                    self.after_idle(return_focus.focus_set)
                    return
            except tk.TclError:
                pass
        self.after_idle(self.advanced_settings_button.focus_set)

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
        return tr("yes", "Ja") if bool(value) else tr("no", "Nein")

    @staticmethod
    def _format_ram(value: object) -> str:
        if value is None or value == "":
            return "—"
        return f"{value} GB"

    @staticmethod
    def _format_size(package: dict[str, object] | None) -> str:
        if not package:
            return tr("not_available", "Nicht verfügbar")
        raw_bytes = package.get("estimated_size_bytes")
        raw_gb = package.get("estimated_size_gb")
        size_bytes = 0.0
        try:
            if raw_bytes not in (None, ""):
                size_bytes = float(raw_bytes)
            elif raw_gb not in (None, ""):
                size_bytes = float(raw_gb) * 1024 * 1024 * 1024
        except (TypeError, ValueError):
            return tr("not_available", "Nicht verfügbar")
        if size_bytes <= 0:
            return tr("not_available", "Nicht verfügbar")
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
            "INSTALLABLE": "[INSTALLABLE]",
            "COMING_SOON": "[COMING SOON]",
            "NO_QUALCOMM_PACKAGE": "[NO QUALCOMM PACKAGE]",
            "RESEARCH": "[RESEARCH]",
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
    def _format_runtime_badge(runtime: object, fallback: str | None = None) -> str:
        if fallback is None:
            fallback = tr("not_available", "Nicht verfügbar")
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
        if normalized in {"NOT_INSTALLED", "COMING_SOON", "NO_QUALCOMM_PACKAGE", "RESEARCH"}:
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

    def _set_action_button_state(self, button: tk.Button, enabled: bool) -> None:
        button.configure(
            state="normal" if enabled else "disabled",
            fg=PHOENIX_THEME.text_primary if enabled else PHOENIX_THEME.text_disabled,
            bg=PHOENIX_THEME.elevated_bg,
            activebackground=PHOENIX_THEME.elevated_bg,
            activeforeground=PHOENIX_THEME.text_primary if enabled else PHOENIX_THEME.text_disabled,
        )

    def _set_package_action_states(self, status: object | None) -> None:
        if not self._advanced_popup_is_open():
            return
        normalized = self._format_status(status) if status else ""
        states = {
            "NOT_INSTALLED": {"install"},
            "READY": {"validate", "remove"},
            "INSTALLED": {"validate", "remove"},
            "UPDATE_AVAILABLE": {"validate", "update", "remove"},
            "INVALID": {"validate", "remove"},
        }.get(normalized, set())
        self._set_action_button_state(self.btn_install, "install" in states)
        self._set_action_button_state(self.btn_validate, "validate" in states)
        self._set_action_button_state(self.btn_update, "update" in states)
        self._set_action_button_state(self.btn_remove, "remove" in states)

    def _format_npu_diagnostic_summary(self, report: dict[str, object]) -> str:
        output_files = report.get("output_files") if isinstance(report, dict) else []
        profiling_files = report.get("profiling_files") if isinstance(report, dict) else []

        lines = [
            f"Status: {self._safe_text(report.get('status'))}",
            f"Exit Code: {self._safe_text(report.get('exit_code'))}",
            f"QNN verfügbar: {self._format_bool(report.get('qnn_available'))}",
            f"Report: {self._safe_text(report.get('report_path'))}",
        ]
        if output_files:
            lines.append("")
            lines.append("Output-Dateien:")
            lines.extend(f"- {self._safe_text(item.get('path'))}" for item in output_files[:4] if isinstance(item, dict))
        if profiling_files:
            lines.append("")
            lines.append("Profiling-Dateien:")
            lines.extend(f"- {self._safe_text(item.get('path'))}" for item in profiling_files[:4] if isinstance(item, dict))
        warning_text = self._extract_npu_warning_text(report)
        if warning_text:
            lines.append("")
            lines.append("Bekannte Warnungen:")
            lines.append(warning_text)
        return "\n".join(lines)

    def _extract_npu_warning_text(self, report: dict[str, object]) -> str:
        text = "\n".join([
            self._safe_text(report.get("stdout"), ""),
            self._safe_text(report.get("stderr"), ""),
        ])
        warnings = []
        for line in text.splitlines():
            if "ERROR" in line or "failed" in line.lower():
                clean = line.strip()
                if clean and clean not in warnings:
                    warnings.append(clean)
        return " | ".join(warnings[:3]) if warnings else "Keine"

    def _apply_npu_diagnostic_result(self, report: dict[str, object]) -> None:
        output_files = report.get("output_files") if isinstance(report, dict) else []
        profiling_files = report.get("profiling_files") if isinstance(report, dict) else []
        output_path = "Nicht erzeugt"
        if isinstance(output_files, list):
            for item in output_files:
                if isinstance(item, dict) and str(item.get("path", "")).endswith("class_logits.raw"):
                    output_path = self._safe_text(item.get("path"))
                    break
        profiling_text = "Nicht erzeugt"
        if isinstance(profiling_files, list) and profiling_files:
            profiling_text = f"{len(profiling_files)} Datei(en)"

        self.npu_qnn_available.configure(text=self._format_bool(report.get("qnn_available")))
        self.npu_test_status.configure(text=self._safe_text(report.get("status")))
        self.npu_exit_code.configure(text=self._safe_text(report.get("exit_code")))
        self.npu_output_file.configure(text=output_path)
        self.npu_profiling_files.configure(text=profiling_text)
        self.npu_report_path.configure(text=self._safe_text(report.get("report_path")))
        self.npu_warnings.configure(text=self._extract_npu_warning_text(report))

    def _run_npu_diagnostic(self) -> None:
        self.npu_diag_button.configure(state="disabled", fg=PHOENIX_THEME.text_disabled)
        self.status_lbl.configure(text=tr("npu_diag_running", "NPU-Diagnose läuft..."))
        self.update_idletasks()
        try:
            report = self.controller.run_npu_diagnostic()
        except Exception as exc:
            report = {
                "status": "failed",
                "exit_code": "—",
                "report_path": "",
                "stdout": "",
                "stderr": str(exc),
                "output_files": [],
                "profiling_files": [],
                "htp_indicators": [],
            }
        finally:
            self.npu_diag_button.configure(state="normal", fg=PHOENIX_THEME.text_primary)

        self._apply_npu_diagnostic_result(report)
        success = report.get("status") == "success"
        label = tr("npu_diag_success", "QNN DLC-Diagnose: Erfolgreich") if success else tr("npu_diag_failed", "QNN DLC-Diagnose: Fehlgeschlagen")
        self.status_lbl.configure(text=f"{label} - {self._safe_text(report.get('report_path'))}")
        summary = self._format_npu_diagnostic_summary(report)
        title = tr("run_npu_diag_btn", "NPU-Diagnose ausführen")
        if success:
            messagebox.showinfo(title, summary)
        else:
            messagebox.showwarning(title, summary)

    @staticmethod
    def _format_capabilities(capabilities: object) -> str:
        if not isinstance(capabilities, dict) or not capabilities:
            return tr("not_available", "Nicht verfügbar")
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
        model = self.controller.get_model_details(model_id)
        if model and model.get("catalog_status"):
            return self._format_status(model.get("catalog_status"))
        package = self._get_catalog_package(model_id)
        if package and package.get("catalog_status"):
            return self._format_status(package.get("catalog_status"))
        if package:
            return self._format_status(package.get("status"))
        try:
            return self._format_status(self.controller.get_package_status(model_id))
        except Exception:
            return "NOT_INSTALLED"

    def _runtime_availability(self, required_runtime: str) -> str:
        if not required_runtime or required_runtime == "—":
            return tr("not_available", "Nicht verfügbar")
        result = self.controller.get_discovery_result()
        runtime = required_runtime.lower()
        if "qnn" in runtime:
            if result and result.qnn_sdk_found and result.qnn_tools_found:
                return tr("available", "Verfügbar")
            return tr("missing_qnn", "Fehlt: QNN Runtime nicht gefunden")
        if "onnx" in runtime:
            if result and result.onnx_available:
                return tr("available", "Verfügbar")
            return tr("missing_onnx", "Fehlt: ONNX Runtime nicht installiert")
        if "cpu" in runtime:
            if result and result.cpu_available:
                return tr("available", "Verfügbar")
            return tr("missing_cpu", "Fehlt: CPU Runtime nicht verfügbar")
        return tr("not_available", "Nicht verfügbar")

    def _set_package_detail_values(self, model: dict[str, object]) -> None:
        model_id = self._safe_text(model.get("id"))
        package = self._get_catalog_package(model_id)
        capabilities = package.get("capabilities") if package else model.get("capabilities")
        self.inspect_capabilities.configure(text=self._format_capabilities(capabilities))

        if not self._advanced_popup_is_open():
            return

        status = self._resolved_package_status(model_id)
        package_version = self._safe_text(package.get("version") if package else model.get("version"))
        installed_version = self._safe_text(model.get("version"), tr("not_available", "Nicht verfügbar")) if model.get("installed") else tr("not_available", "Nicht verfügbar")
        required_runtime = self._safe_text(
            package.get("recommended_runtime") if package else model.get("recommended_backend") or model.get("backend")
        )
        installed_runtime = self._safe_text(model.get("backend"), tr("not_available", "Nicht verfügbar")) if model.get("installed") else tr("not_available", "Nicht verfügbar")
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
        availability_message = self._safe_text(
            (package.get("availability_message") if package else None) or model.get("availability_message"),
            tr("not_available", "Nicht verfügbar"),
        )
        download_url = package.get("download_url") if package else None
        self.inspect_download_url.configure(text=self._safe_text(download_url, availability_message))
        self.inspect_checksum.configure(text=self._safe_text(package.get("checksum") if package else None, "Nicht verfügbar"))

    def _update_advanced_model_details(self, model: dict[str, object]) -> None:
        if not self._advanced_popup_is_open():
            return
        self.inspect_category.configure(text=self._safe_text(model.get("category")))
        self.inspect_author.configure(text=self._safe_text(model.get("author")))
        self.inspect_license.configure(text=self._safe_text(model.get("license")))
        self.inspect_min_ram.configure(text=self._format_ram(model.get("minimum_ram_gb")))
        self.inspect_rec_ram.configure(text=self._format_ram(model.get("recommended_ram_gb")))

    def _update_environment_details(self) -> None:
        if not self._advanced_popup_is_open():
            return
        result = self.controller.get_discovery_result()
        if not result:
            return
        self.env_os.configure(text=self._safe_text(result.os_name))
        self.env_arch.configure(text=self._safe_text(result.architecture))
        self.env_python.configure(text=self._safe_text(result.python_version))
        self.env_cpu.configure(text=tr("available", "Verfügbar") if result.cpu_available else tr("not_available", "Nicht verfügbar"))
        self.env_onnx.configure(
            text=f"{tr('available', 'Verfügbar')} ({result.onnx_version})" if result.onnx_available else tr("not_installed", "Nicht installiert")
        )
        self.env_qnn_sdk.configure(text=tr("found", "Gefunden") if result.qnn_sdk_found else tr("not_found", "Nicht gefunden"))
        self.env_qnn_tools.configure(text=tr("found", "Gefunden") if result.qnn_tools_found else tr("not_found", "Nicht gefunden"))

    def refresh(self) -> None:
        """Reload models from repository and populate treeview while keeping active selection."""
        # 1. Get the currently selected model ID (if any) before refresh to preserve state
        selected_id = None
        selected = self.tree.selection()
        if selected:
            selected_id = selected[0]  # iid is the model ID!

        # 2. Reload repository data
        self.controller.refresh_repository()
        active_model_id = self.controller.get_active_model_id()

        # Run model scanner
        try:
            self.scanned_results = {m["id"]: m for m in self.controller.scan_npu_models()}
        except Exception:
            self.scanned_results = {}

        # 3. Rebuild Treeview items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Iterate over only the scanned NPU models
        for model_id, scanned in self.scanned_results.items():
            model = self.controller.get_model_details(model_id)
            display_name = model.get("display_name") if model else scanned.get("display_name")
            category = model.get("category") if model else "Text-to-Image"
            backend = model.get("backend") if model else scanned.get("backend_status")
            
            is_active = "✓" if model_id == active_model_id else ""
            
            is_complete = scanned.get("is_complete", False)
            status_text = tr("einsatzbereit_auf_npu", "Einsatzbereit auf NPU") if is_complete else tr("fehlt_unvollstaendig", "Fehlt / Unvollständig")
            
            self.tree.insert(
                "",
                "end",
                iid=model_id,
                values=(
                    is_active,
                    display_name,
                    category,
                    backend,
                    status_text,
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
            for lbl in (
                self.inspect_name,
                self.inspect_version,
                self.inspect_backend,
                self.inspect_status,
                self.inspect_desc,
                self.inspect_capabilities,
                self.inspect_installed,
                self.inspect_download,
                self.inspect_path,
                self.inspect_size,
                self.inspect_samplers,
            ):
                lbl.configure(text="—")
            if self._advanced_popup_is_open():
                for lbl in (
                    self.inspect_category,
                    self.inspect_author,
                    self.inspect_license,
                    self.inspect_min_ram,
                    self.inspect_rec_ram,
                    self.inspect_package_status,
                    self.inspect_package_type,
                    self.inspect_package_version,
                    self.inspect_installed_version,
                    self.inspect_update_hint,
                    self.inspect_required_runtime,
                    self.inspect_installed_runtime,
                    self.inspect_runtime_available,
                    self.inspect_package_size,
                    self.inspect_download_url,
                    self.inspect_checksum,
                ):
                    lbl.configure(text="—")
            self._set_package_action_states(None)

        self._update_environment_details()

    def show_details(self) -> None:
        """Display comprehensive metadata properties for the selected model."""
        selected = self.tree.selection()
        if not selected:
            self._set_package_action_states(None)
            return

        model_id = selected[0]
        model = self.controller.get_model_details(model_id)
        if not model:
            self._set_package_action_states(None)
            return
        
        scanned = self.scanned_results.get(model_id) if hasattr(self, "scanned_results") else None
        
        # Check complete status
        is_complete = scanned.get("is_complete", False) if scanned else False
        status_text = tr("einsatzbereit_auf_npu", "Einsatzbereit auf NPU") if is_complete else tr("fehlt_unvollstaendig", "Fehlt / Unvollständig")
        
        # Compact inspector values
        self.inspect_name.configure(text=self._safe_text(model.get("display_name")))
        self.inspect_version.configure(text=self._safe_text(model.get("version")))
        self.inspect_backend.configure(text=self._safe_text(model.get("backend")))
        
        # Status badge
        self.inspect_status.configure(
            text=status_text,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.accent if is_complete else PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_button,
            padx=6,
            pady=2,
        )
        
        self.inspect_desc.configure(text=self._safe_text(model.get("description")))
        self.inspect_installed.configure(text=self._format_bool(is_complete))
        self.inspect_download.configure(text=tr("found", "Gefunden") if is_complete else tr("not_found", "Nicht gefunden"))
        
        path_str = scanned.get("path") if scanned else model.get("path")
        self.inspect_path.configure(text=self._safe_text(path_str, tr("not_available", "Nicht verfügbar")))
        
        # Folder size
        size_str = scanned.get("size_str", "—") if scanned else "—"
        self.inspect_size.configure(text=size_str)
        
        # Supported Samplers
        samplers = "—"
        gen_params = model.get("generation_parameters")
        if isinstance(gen_params, dict):
            sampler_spec = gen_params.get("sampler")
            if isinstance(sampler_spec, dict):
                sampler_vals = sampler_spec.get("values")
                if isinstance(sampler_vals, list):
                    samplers = ", ".join(str(s) for s in sampler_vals)
                elif sampler_spec.get("default"):
                    samplers = str(sampler_spec.get("default"))
        if samplers == "—" and scanned:
            samplers = scanned.get("default_sampler", "—")
        self.inspect_samplers.configure(text=samplers)

        self._update_advanced_model_details(model)
        self._set_package_detail_values(model)
        self._set_package_action_states(self._resolved_package_status(model_id))

        # Update status bar feedback: "Modell ausgewählt: <Modellname>"
        self.status_lbl.configure(text=tr("model_selected_status", "Modell ausgewählt: {name}", name=self._safe_text(model.get('display_name'))))

        # Download panel visibility and state update
        if is_complete:
            self.download_frame.pack_forget()
        else:
            self.download_frame.pack(side="bottom", fill="x", padx=16, pady=(10, 16))
            if self.downloader.is_downloading(model_id):
                self.download_button.configure(
                    text=tr("cancel", "Abbrechen"),
                    command=self._cancel_model_download,
                    bg=PHOENIX_THEME.elevated_bg,
                    fg=PHOENIX_THEME.text_primary,
                )
                self.download_progress.grid(row=1, column=0, sticky="ew", pady=4)
                self.download_status_lbl.grid(row=2, column=0, sticky="ew")
            else:
                self.download_button.configure(
                    text=tr("download_model_btn", "Modell herunterladen"),
                    command=self._start_model_download,
                    bg=PHOENIX_THEME.accent,
                    fg=PHOENIX_THEME.text_on_accent,
                )
                self.download_progress.grid_remove()
                self.download_status_lbl.grid_remove()

    def _start_model_download(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        model_id = selected[0]
        
        # Show progress widgets immediately
        self.download_button.configure(
            text=tr("cancel", "Abbrechen"),
            command=self._cancel_model_download,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
        )
        self.download_progress.configure(value=0.0)
        self.download_progress.grid(row=1, column=0, sticky="ew", pady=4)
        self.download_status_lbl.configure(text=tr("download_starting", "Download wird gestartet..."))
        self.download_status_lbl.grid(row=2, column=0, sticky="ew")

        # Start download using ModelDownloader
        self.downloader.start_download(
            model_id=model_id,
            progress_callback=lambda report: self._on_download_progress(model_id, report)
        )

    def _cancel_model_download(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        model_id = selected[0]
        self.downloader.cancel_download(model_id)
        self.download_status_lbl.configure(text=tr("download_cancelling", "Download wird abgebrochen..."))

    def _on_download_progress(self, model_id: str, report: dict[str, Any]) -> None:
        self.after_idle(self._update_download_ui, model_id, report)

    def _update_download_ui(self, model_id: str, report: dict[str, Any]) -> None:
        # Check if the model is still selected
        selected = self.tree.selection()
        if not selected or selected[0] != model_id:
            # If the user changed selection, we still want to refresh the table once completed
            if report["status"] in {"completed", "failed", "cancelled"}:
                self.refresh()
            return

        status = report["status"]
        percent = report["percent"]
        speed = report.get("speed", 0.0)
        error_msg = report.get("error_message")

        if status == "downloading":
            self.download_progress.configure(value=percent)
            self.download_progress.grid(row=1, column=0, sticky="ew", pady=4)
            
            speed_text = f"{speed:.2f} MB/s" if speed > 0 else "— MB/s"
            status_text = tr("downloading_status", "Lade herunter... {percent:.1f}% ({speed})", percent=percent, speed=speed_text)
            self.download_status_lbl.configure(text=status_text)
            self.download_status_lbl.grid(row=2, column=0, sticky="ew")
        
        elif status == "verifying":
            self.download_progress.configure(value=100.0)
            self.download_status_lbl.configure(text=tr("verifying_status", "Prüfsumme wird verifiziert..."))
        
        elif status == "extracting":
            self.download_progress.configure(value=100.0)
            self.download_status_lbl.configure(text=tr("extracting_status", "Modell wird entpackt..."))
            
        elif status == "completed":
            self.refresh()
            messagebox.showinfo(tr("download_completed_title", "Download abgeschlossen"), tr("download_completed_msg", "Das Modell wurde erfolgreich heruntergeladen und entpackt."))
            
        elif status == "failed":
            self.refresh()
            messagebox.showerror(tr("download_failed_title", "Download fehlgeschlagen"), tr("download_failed_msg", "Download fehlgeschlagen: {error}", error=error_msg or "Unbekannter Fehler"))
            
        elif status == "cancelled":
            self.refresh()
            messagebox.showinfo(tr("download_cancelled_title", "Download abgebrochen"), tr("download_cancelled_msg", "Der Download wurde abgebrochen."))

    def _format_validation_summary(self, validation: dict[str, object]) -> str:
        issues = validation.get("issues") if isinstance(validation, dict) else []
        warnings = validation.get("warnings") if isinstance(validation, dict) else []
        missing_files = validation.get("missing_files") if isinstance(validation, dict) else []

        lines = [self._safe_text(validation.get("message") if isinstance(validation, dict) else None)]
        if issues:
            lines.append("")
            lines.append("Probleme:")
            lines.extend(f"- {self._safe_text(issue)}" for issue in issues)
        if missing_files:
            lines.append("")
            lines.append("Fehlende Dateien:")
            lines.extend(f"- {self._safe_text(path)}" for path in missing_files[:8])
            if len(missing_files) > 8:
                lines.append(f"- ... {len(missing_files) - 8} weitere")
        if warnings:
            lines.append("")
            lines.append("Hinweise:")
            lines.extend(f"- {self._safe_text(warning)}" for warning in warnings)
        return "\n".join(lines)

    def _apply_validation_result(self, validation: dict[str, object]) -> None:
        status = "READY" if validation.get("success") else "INVALID"
        self.inspect_capabilities.configure(
            text=self._safe_text(validation.get("capabilities_hint"), "Nicht verfügbar")
        )
        if not self._advanced_popup_is_open():
            return
        self._configure_status_badge(self.inspect_package_status, status)
        self.inspect_package_version.configure(text=self._safe_text(validation.get("package_version"), "Nicht verfügbar"))
        self.inspect_update_hint.configure(text=self._safe_text(validation.get("version_hint"), "Nicht verfügbar"))
        self.inspect_runtime_available.configure(text=self._safe_text(validation.get("runtime_hint"), "Nicht verfügbar"))
        self.inspect_checksum.configure(text=self._safe_text(validation.get("checksum_hint"), "Nicht geprüft"))

    def _validate_selected_package(self) -> None:
        selected = self.tree.selection()
        if not selected:
            message = "Kein Package ausgewählt."
            self.status_lbl.configure(text=message)
            messagebox.showinfo("Package Validation", message)
            return

        model_id = selected[0]
        model = self.controller.get_model_details(model_id)
        package_name = self._safe_text(model.get("display_name") if model else model_id)

        try:
            validation = self.controller.validate_package(model_id)
        except Exception as exc:
            validation = {
                "success": False,
                "message": f"Invalid: Validierung konnte nicht abgeschlossen werden: {exc}",
                "issues": [str(exc)],
                "warnings": [],
                "missing_files": [],
            }

        self._apply_validation_result(validation)
        state_label = "Valid" if validation.get("success") else "Invalid"
        self.status_lbl.configure(text=f"{package_name}: {state_label} - {self._safe_text(validation.get('message'))}")
        summary = self._format_validation_summary(validation)
        if validation.get("success"):
            messagebox.showinfo("Package Validation", summary)
        else:
            messagebox.showwarning("Package Validation", summary)

    def _get_selected_package_context(self) -> tuple[str, dict[str, object] | None, str] | None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Package Action", "Kein Package ausgewählt.")
            self.status_lbl.configure(text="Kein Package ausgewählt.")
            return None
        model_id = selected[0]
        model = self.controller.get_model_details(model_id)
        package_name = self._safe_text(model.get("display_name") if model else model_id)
        return model_id, model, package_name

    def _select_local_package_source(self, title: str) -> str:
        source_path = filedialog.askdirectory(title=title)
        if source_path:
            return source_path
        archive_path = filedialog.askopenfilename(
            title=title,
            filetypes=[
                ("SMP Packages", "*.smp *.zip"),
                ("ZIP Packages", "*.zip"),
                ("Alle Dateien", "*.*"),
            ],
        )
        return archive_path or ""

    def _install_selected_package(self) -> None:
        context = self._get_selected_package_context()
        if not context:
            return
        model_id, _model, package_name = context
        source_path = self._select_local_package_source("Lokales SMP-Package auswählen")
        if not source_path:
            self.status_lbl.configure(text="Installation abgebrochen.")
            return

        self.status_lbl.configure(text=f"{package_name}: Installiere lokales Package...")
        self.update_idletasks()
        success = self.controller.install_package(model_id, source_path)
        self.refresh()
        if success:
            self.status_lbl.configure(text=f"{package_name}: Package installiert.")
            messagebox.showinfo("Package Installation", f"{package_name} wurde lokal installiert.")
        else:
            self.status_lbl.configure(text=f"{package_name}: Installation fehlgeschlagen.")
            messagebox.showerror(
                "Package Installation",
                "Installation fehlgeschlagen. Bitte Package-Verzeichnis, Manifest und Package-ID prüfen.",
            )

    def _update_selected_package(self) -> None:
        context = self._get_selected_package_context()
        if not context:
            return
        model_id, _model, package_name = context
        source_path = self._select_local_package_source("Lokales Update-Package auswählen")
        if not source_path:
            self.status_lbl.configure(text="Update abgebrochen.")
            return

        self.status_lbl.configure(text=f"{package_name}: Aktualisiere lokales Package...")
        self.update_idletasks()
        success = self.controller.update_package(model_id, source_path)
        self.refresh()
        if success:
            self.status_lbl.configure(text=f"{package_name}: Package aktualisiert.")
            messagebox.showinfo("Package Update", f"{package_name} wurde lokal aktualisiert.")
        else:
            self.status_lbl.configure(text=f"{package_name}: Update fehlgeschlagen.")
            messagebox.showerror(
                "Package Update",
                "Update fehlgeschlagen. Bitte lokales Package, Manifest und Version prüfen.",
            )

    def _remove_selected_package(self) -> None:
        context = self._get_selected_package_context()
        if not context:
            return
        model_id, _model, package_name = context
        confirmed = messagebox.askyesno(
            tr("remove", "Entfernen"),
            tr("package_remove_confirm", package_name=package_name, model_id=model_id),
        )
        if not confirmed:
            self.status_lbl.configure(text="Entfernen abgebrochen.")
            return

        self.status_lbl.configure(text=f"{package_name}: Entferne lokales Package...")
        self.update_idletasks()
        success = self.controller.remove_package(model_id)
        self.refresh()
        if success:
            self.status_lbl.configure(text=f"{package_name}: Package entfernt.")
            messagebox.showinfo("Package entfernen", f"{package_name} wurde lokal entfernt.")
        else:
            self.status_lbl.configure(text=f"{package_name}: Entfernen fehlgeschlagen.")
            messagebox.showerror("Package entfernen", "Package konnte nicht sicher entfernt werden.")

    def _on_package_action(self, action: str) -> None:
        if action == "install":
            self._install_selected_package()
            return
        if action == "validate":
            self._validate_selected_package()
            return
        if action == "update":
            self._update_selected_package()
            return
        if action == "remove":
            self._remove_selected_package()
            return

        message = "Package workflow is not implemented yet."
        self.status_lbl.configure(text=message)
        messagebox.showinfo("Package Action", message)

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

        if model.get("product_available") is not True:
            self.status_lbl.configure(
                text=self._safe_text(
                    model.get("availability_message"),
                    "Official Qualcomm NPU package not available.",
                )
            )
            return

        display_name = model["display_name"]

        # Set as active model in ModelRepository
        self.controller.set_active_model_id(model_id)

        # Refresh visually to apply the checkmark marker and update inspector
        self.refresh()

        # Update status bar feedback: "Aktives Modell geändert: <Modellname>"
        self.status_lbl.configure(text=tr("active_model_changed", "Aktives Modell geändert: {name}", name=display_name))

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
