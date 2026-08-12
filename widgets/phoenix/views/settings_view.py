from __future__ import annotations

import os
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox
from tkinter import ttk as ttk_real

class _TtkProxy:
    def __getattr__(self, name):
        if name == "Combobox":
            def make_phoenix_combobox(master, **kwargs):
                textvariable = kwargs.pop("textvariable", None)
                if textvariable is None:
                    textvariable = tk.StringVar(master)
                values = kwargs.pop("values", [])
                width = kwargs.pop("width", None)
                kwargs.pop("state", None)
                kwargs.pop("style", None)
                kwargs.pop("font", None)
                width_px = int(width) * 8 if width is not None else None

                icon_name = None
                var_name = str(textvariable).lower()
                if "theme" in var_name:
                    icon_name = "settings"
                elif "lang" in var_name:
                    icon_name = "info"
                elif "thread" in var_name:
                    icon_name = "settings"
                elif "ep" in var_name:
                    icon_name = "models"

                from widgets.phoenix.controls.dropdown import PhoenixDropdown
                return PhoenixDropdown(
                    master,
                    variable=textvariable,
                    values=values,
                    icon_name=icon_name,
                    width=width_px,
                    radius=6,
                    **kwargs
                )
            return make_phoenix_combobox
        return getattr(ttk_real, name)

ttk = _TtkProxy()

from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr
from app.settings_manager import SettingsManager


class PhoenixSettingsView(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        
        # Configure variables
        self.thread_var = tk.StringVar(value="Auto")
        self.ep_var = tk.StringVar(value="QNN EP")
        self.hw_acc_var = tk.BooleanVar(value=True)
        self.theme_var = tk.StringVar(value="Dunkel")
        self.language_var = tk.StringVar(value="Deutsch")
        
        self._build()
        self._load_values()

    def _add_button_hover(self, button: tk.Button, hover_bg: str | None = None, hover_fg: str | None = None) -> None:
        original_bg = button.cget("bg")
        original_fg = button.cget("fg")
        h_bg = hover_bg or PHOENIX_THEME.accent
        h_fg = hover_fg or PHOENIX_THEME.text_on_accent

        def on_enter(event):
            if str(button.cget("state")) != "disabled":
                button.configure(bg=h_bg, fg=h_fg)

        def on_leave(event):
            if str(button.cget("state")) != "disabled":
                button.configure(bg=original_bg, fg=original_fg)

        button.bind("<Enter>", on_enter, add="+")
        button.bind("<Leave>", on_leave, add="+")

    def _create_card(self, parent: tk.Widget, title: str, row: int, col: int) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
        )
        card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
        
        # Title Label
        tk.Label(
            card,
            text=title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 12))
        
        return card

    def _build(self) -> None:
        # Title Block
        title_frame = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        title_frame.pack(fill="x", padx=24, pady=(24, 12))

        tk.Label(
            title_frame,
            text=tr("settings_title", "Einstellungen"),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            title_frame,
            text=tr("settings_subtitle", "Anwendungspräferenzen, Pfade und API-Zugriffe konfigurieren"),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Footer Action Bar (Fixed at the bottom)
        footer_frame = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        footer_frame.pack(side="bottom", fill="x", padx=24, pady=(8, 24))
        
        # Left-aligned status message
        self.status_lbl = tk.Label(
            footer_frame,
            text="",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        self.status_lbl.pack(side="left", fill="x", expand=True)

        # Right-aligned actions
        btn_frame = tk.Frame(footer_frame, bg=PHOENIX_THEME.content_bg)
        btn_frame.pack(side="right")

        # Save Button
        self.save_btn = tk.Button(
            btn_frame,
            text=tr("save_settings", "Speichern"),
            command=self._save_settings,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground=PHOENIX_THEME.text_on_accent,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=18,
            pady=8,
        )
        self.save_btn.pack(side="left", padx=6)
        self._add_button_hover(self.save_btn)

        # Reset Button
        self.reset_btn = tk.Button(
            btn_frame,
            text=tr("settings_reset_btn", "Zurücksetzen"),
            command=self._reset_defaults,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent_soft,
            activeforeground=PHOENIX_THEME.text_primary,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=18,
            pady=8,
        )
        self.reset_btn.pack(side="left", padx=6)
        self._add_button_hover(self.reset_btn)

        # Style TTK Combobox for Dark Theme integration
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Phoenix.TCombobox",
            background=PHOENIX_THEME.elevated_bg,
            foreground=PHOENIX_THEME.text_primary,
            fieldbackground=PHOENIX_THEME.elevated_bg,
            bordercolor=PHOENIX_THEME.border,
            lightcolor=PHOENIX_THEME.border,
            darkcolor=PHOENIX_THEME.border,
            arrowcolor=PHOENIX_THEME.text_muted,
            borderwidth=1,
            relief="flat",
        )
        style.map(
            "Phoenix.TCombobox",
            background=[("readonly", PHOENIX_THEME.elevated_bg)],
            foreground=[("readonly", PHOENIX_THEME.text_primary)],
            fieldbackground=[("readonly", PHOENIX_THEME.elevated_bg)],
            bordercolor=[("readonly", PHOENIX_THEME.border)],
        )

        # Style the dropdown popdown list using options database
        self.option_add("*TCombobox*Listbox.background", PHOENIX_THEME.elevated_bg)
        self.option_add("*TCombobox*Listbox.foreground", PHOENIX_THEME.text_primary)
        self.option_add("*TCombobox*Listbox.selectBackground", PHOENIX_THEME.accent)
        self.option_add("*TCombobox*Listbox.selectForeground", PHOENIX_THEME.text_on_accent)
        self.option_add("*TCombobox*Listbox.font", PHOENIX_THEME.font_body)
        self.option_add("*TCombobox*Listbox.relief", "flat")
        self.option_add("*TCombobox*Listbox.borderWidth", 0)
        self.option_add("*TCombobox*Listbox.highlightThickness", 0)

        # Main Category Cards Grid Container
        grid_frame = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        grid_frame.pack(fill="both", expand=True, padx=16, pady=0)
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.rowconfigure(1, weight=1)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # ==========================================
        # CARD 1: SYSTEM & NPU
        # ==========================================
        sys_card = self._create_card(grid_frame, tr("settings_title_system_npu", "System & NPU"), 0, 0)
        
        sys_form = tk.Frame(sys_card, bg=PHOENIX_THEME.card_bg)
        sys_form.pack(fill="both", expand=True, padx=16, pady=0)
        sys_form.columnconfigure(1, weight=1)

        # Thread count
        tk.Label(
            sys_form,
            text=tr("settings_thread_count", "Thread-Anzahl:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.thread_cb = ttk.Combobox(
            sys_form,
            textvariable=self.thread_var,
            values=["Auto", "2", "4", "8", "12", "16"],
            state="readonly",
            style="Phoenix.TCombobox",
            font=PHOENIX_THEME.font_body,
        )
        self.thread_cb.grid(row=0, column=1, sticky="ew", pady=8)

        # EP Preference
        tk.Label(
            sys_form,
            text=tr("settings_execution_provider", "Execution Provider:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.ep_cb = ttk.Combobox(
            sys_form,
            textvariable=self.ep_var,
            values=["QNN EP", "CPU EP"],
            state="readonly",
            style="Phoenix.TCombobox",
            font=PHOENIX_THEME.font_body,
        )
        self.ep_cb.grid(row=1, column=1, sticky="ew", pady=8)

        # Hardware Acceleration
        self.hw_acc_cb = tk.Checkbutton(
            sys_form,
            text=tr("settings_npu_acceleration", "Qualcomm Snapdragon NPU-Beschleunigung aktivieren"),
            variable=self.hw_acc_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.elevated_bg,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_caption,
            bd=0,
            highlightthickness=0,
        )
        self.hw_acc_cb.grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 8))

        self.system_npu_hint = tk.Label(
            sys_form,
            text=tr(
                "settings_system_npu_hint",
                "Hinweis: Snapdragon AI Studio wählt die passende Verarbeitung für das verwendete Modell automatisch aus. Sie müssen hier normalerweise nichts einstellen.",
            ),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
            justify="left",
            wraplength=440,
        )
        self.system_npu_hint.grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(8, 4)
        )

        # ==========================================
        # CARD 2: PFADE & SPEICHER
        # ==========================================
        paths_card = self._create_card(grid_frame, tr("settings_title_paths_storage", "Pfade & Speicher"), 0, 1)
        
        paths_form = tk.Frame(paths_card, bg=PHOENIX_THEME.card_bg)
        paths_form.pack(fill="both", expand=True, padx=16, pady=0)
        paths_form.columnconfigure(0, weight=1)

        # Output folder
        tk.Label(
            paths_form,
            text=tr("settings_default_output_dir", "Standard-Ausgabeordner:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(4, 2))

        self.out_dir_entry = tk.Entry(
            paths_form,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
            font=PHOENIX_THEME.font_body,
        )
        self.out_dir_entry.grid(row=1, column=0, sticky="ew", ipady=5, pady=(0, 10))

        self.out_dir_btn = tk.Button(
            paths_form,
            text="...",
            command=self._browse_output_dir,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.border,
            activeforeground=PHOENIX_THEME.text_primary,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=10,
        )
        self.out_dir_btn.grid(row=1, column=1, sticky="ns", padx=(6, 0), pady=(0, 10))
        self._add_button_hover(self.out_dir_btn)

        # Model directory
        tk.Label(
            paths_form,
            text=tr("settings_models_dir", "Modell-Verzeichnis:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 2))

        self.models_dir_entry = tk.Entry(
            paths_form,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
            font=PHOENIX_THEME.font_body,
        )
        self.models_dir_entry.grid(row=3, column=0, sticky="ew", ipady=5, pady=(0, 10))

        self.models_dir_btn = tk.Button(
            paths_form,
            text="...",
            command=self._browse_models_dir,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.border,
            activeforeground=PHOENIX_THEME.text_primary,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=10,
        )
        self.models_dir_btn.grid(row=3, column=1, sticky="ns", padx=(6, 0), pady=(0, 10))
        self._add_button_hover(self.models_dir_btn)

        # ==========================================
        # CARD 3: UI & SPRACHE
        # ==========================================
        ui_card = self._create_card(grid_frame, tr("settings_title_ui_language", "UI & Sprache"), 1, 0)
        
        ui_form = tk.Frame(ui_card, bg=PHOENIX_THEME.card_bg)
        ui_form.pack(fill="both", expand=True, padx=16, pady=0)
        ui_form.columnconfigure(1, weight=1)

        # Theme option
        tk.Label(
            ui_form,
            text=tr("settings_theme_options", "Theme-Optionen:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.theme_cb = ttk.Combobox(
            ui_form,
            textvariable=self.theme_var,
            values=[
                tr("theme_dark", "Dunkel"),
                tr("theme_light", "Hell"),
            ],
            state="readonly",
            style="Phoenix.TCombobox",
            font=PHOENIX_THEME.font_body,
        )
        self.theme_cb.grid(row=0, column=1, sticky="ew", pady=8)

        # Language
        tk.Label(
            ui_form,
            text=tr("settings_language", "Sprache:"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.language_cb = ttk.Combobox(
            ui_form,
            textvariable=self.language_var,
            values=["Deutsch", "English", "Español"],
            state="readonly",
            style="Phoenix.TCombobox",
            font=PHOENIX_THEME.font_body,
        )
        self.language_cb.grid(row=1, column=1, sticky="ew", pady=8)

        self.ui_language_save_hint = tk.Label(
            ui_form,
            text=tr(
                "settings_ui_language_save_hint",
                "Hinweis: Änderungen an Sprache und Benutzeroberfläche werden erst nach dem Speichern übernommen.",
            ),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
            justify="left",
            wraplength=440,
        )
        self.ui_language_save_hint.grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(8, 4)
        )

        # ==========================================
        # CARD 4: HUGGING FACE INTEGRATION
        # ==========================================
        hf_card = self._create_card(grid_frame, tr("settings_title_huggingface", "Hugging Face Integration"), 1, 1)
        
        hf_form = tk.Frame(hf_card, bg=PHOENIX_THEME.card_bg)
        hf_form.pack(fill="both", expand=True, padx=16, pady=0)
        hf_form.columnconfigure(0, weight=1)

        # Access Token Label
        tk.Label(
            hf_form,
            text=tr("hf_token_label", "Hugging Face Access Token (HF_TOKEN):"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))

        # Entry Row
        self.token_entry = tk.Entry(
            hf_form,
            show="*",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
            font=PHOENIX_THEME.font_body,
        )
        self.token_entry.grid(row=1, column=0, sticky="ew", ipady=5, pady=(0, 4))
        self.token_entry.bind("<KeyRelease>", self._update_token_format_status)

        # Toggle Show/Hide Button
        self.show_toggle = False
        self.toggle_btn = tk.Button(
            hf_form,
            text=tr("show_token", "Anzeigen"),
            command=self._toggle_token_visibility,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.border,
            activeforeground=PHOENIX_THEME.text_primary,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=10,
        )
        self.toggle_btn.grid(row=1, column=1, sticky="ns", padx=(6, 0), pady=(0, 4))
        self._add_button_hover(self.toggle_btn)

        # Format & Helper links stacked
        links_frame = tk.Frame(hf_form, bg=PHOENIX_THEME.card_bg)
        links_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

        tk.Label(
            links_frame,
            text=tr(
                "settings_hf_token_optional",
                "Optional — required only for models that need Hugging Face authentication.",
            ),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left",
            wraplength=360,
        ).pack(fill="x", pady=(2, 0))

        self.token_help_lbl = tk.Label(
            links_frame,
            text=tr("settings_hf_token_hint", "Token erstellen unter: huggingface.co/settings/tokens ↗"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left",
            cursor="hand2"
        )
        self.token_help_lbl.pack(anchor="w", pady=(2, 0))
        self.token_help_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://huggingface.co/settings/tokens"))

        self.token_format_lbl = tk.Label(
            links_frame,
            text="",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left"
        )
        self.token_format_lbl.pack(anchor="w", pady=(2, 0))

        # Horizontal buttons panel inside HF Integration Card
        hf_actions = tk.Frame(hf_form, bg=PHOENIX_THEME.card_bg)
        hf_actions.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        self.test_btn = tk.Button(
            hf_actions,
            text=tr("test_token_btn", "Token testen"),
            command=self._test_token,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.border,
            activeforeground=PHOENIX_THEME.text_primary,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_caption,
            cursor="hand2",
            padx=12,
            pady=6,
        )
        self.test_btn.pack(side="left")
        self._add_button_hover(self.test_btn)

    def _toggle_token_visibility(self) -> None:
        self.show_toggle = not self.show_toggle
        if self.show_toggle:
            self.token_entry.configure(show="")
            self.toggle_btn.configure(text=tr("hide_token", "Verbergen"))
        else:
            self.token_entry.configure(show="*")
            self.toggle_btn.configure(text=tr("show_token", "Anzeigen"))

    def _browse_output_dir(self) -> None:
        initial = self.out_dir_entry.get().strip() or r"C:\SnapdragonAI"
        folder = filedialog.askdirectory(
            title=tr("settings_choose_output_dir", "Standard-Ausgabeordner wählen"),
            initialdir=initial,
        )
        if folder:
            self.out_dir_entry.delete(0, tk.END)
            self.out_dir_entry.insert(0, os.path.normpath(folder))

    def _browse_models_dir(self) -> None:
        initial = self.models_dir_entry.get().strip() or r"C:\SnapdragonAI"
        folder = filedialog.askdirectory(
            title=tr("settings_choose_models_dir", "Modell-Verzeichnis wählen"),
            initialdir=initial,
        )
        if folder:
            self.models_dir_entry.delete(0, tk.END)
            self.models_dir_entry.insert(0, os.path.normpath(folder))

    def _load_values(self) -> None:
        prefs = SettingsManager.load_settings()
        
        # System & NPU
        self.thread_var.set(prefs.get("thread_count", "Auto"))
        self.ep_var.set(prefs.get("execution_provider", "QNN EP"))
        self.hw_acc_var.set(prefs.get("hardware_accel", "True") == "True")
        
        # Paths & Storage
        out_dir = prefs.get("output_dir", r"C:\SnapdragonAI\output")
        self.out_dir_entry.delete(0, tk.END)
        self.out_dir_entry.insert(0, out_dir)
        
        models_dir = prefs.get("models_dir", r"C:\SnapdragonAI\models")
        self.models_dir_entry.delete(0, tk.END)
        self.models_dir_entry.insert(0, models_dir)
        
        # UI & Language
        self.theme_var.set(self._theme_display_value(prefs.get("theme", "Dunkel")))
        self.language_var.set(prefs.get("language", "Deutsch"))
        
        # Hugging Face Access Token
        token = SettingsManager.get_hf_token()
        self.token_entry.delete(0, tk.END)
        self.token_entry.insert(0, token)
        
        self._update_token_format_status()

    def _save_settings(self) -> None:
        token = self.token_entry.get().strip()
        
        # Load current preferences to compare modifications
        prefs = SettingsManager.load_settings()
        old_theme = prefs.get("theme", "Dunkel")
        old_lang = prefs.get("language", "Deutsch")
        
        new_theme = self._theme_storage_value(self.theme_var.get())
        new_lang = self.language_var.get()
        
        settings = {
            "thread_count": self.thread_var.get(),
            "execution_provider": self.ep_var.get(),
            "hardware_accel": str(self.hw_acc_var.get()),
            "output_dir": self.out_dir_entry.get().strip(),
            "models_dir": self.models_dir_entry.get().strip(),
            "theme": new_theme,
            "language": new_lang,
            "hf_token": token,
        }
        
        success = SettingsManager.save_settings(settings)
        if success:
            # 1. Check if theme OR language changed, and trigger a clean restart
            if old_theme != new_theme or old_lang != new_lang:
                from tkinter import messagebox
                import sys
                import subprocess
                
                messagebox.showinfo(
                    tr("settings_restart_title", "Neustart erforderlich"),
                    tr("settings_restart_msg", "Die Einstellungen wurden gespeichert. Snapdragon AI Studio wird jetzt neu gestartet, um die Änderungen anzuwenden.")
                )
                
                # Windows-kompatibler Neustart der App
                subprocess.Popen([sys.executable] + sys.argv)
                
                # Aktuelle Instanz sauber beenden
                self.winfo_toplevel().destroy()
                return
            
            self.status_lbl.configure(
                text=tr("settings_save_success", "Einstellungen erfolgreich gespeichert."),
                fg=PHOENIX_THEME.accent
            )
        else:
            self.status_lbl.configure(
                text=tr("settings_save_failed", "Fehler beim Speichern der Einstellungen."),
                fg="#f87171"
            )

    def _reset_defaults(self) -> None:
        self.thread_var.set("Auto")
        self.ep_var.set("QNN EP")
        self.hw_acc_var.set(True)
        
        self.out_dir_entry.delete(0, tk.END)
        self.out_dir_entry.insert(0, r"C:\SnapdragonAI\output")
        
        self.models_dir_entry.delete(0, tk.END)
        self.models_dir_entry.insert(0, r"C:\SnapdragonAI\models")
        
        self.theme_var.set(tr("theme_dark", "Dunkel"))
        self.language_var.set("Deutsch")
        
        self.token_entry.delete(0, tk.END)
        self.token_entry.insert(0, "")
        self._update_token_format_status()
        
        self.status_lbl.configure(
            text=tr("settings_reset_success", "Einstellungen auf Standardwerte zurückgesetzt."),
            fg=PHOENIX_THEME.text_secondary
        )

    @staticmethod
    def _theme_storage_value(display_value: str) -> str:
        dark_values = {"Dunkel", "Dark", tr("theme_dark", "Dunkel")}
        return "Dunkel" if display_value in dark_values else "Hell"

    @staticmethod
    def _theme_display_value(stored_value: str) -> str:
        if stored_value in {"Dunkel", "Dark", "dark", "professional_dark"}:
            return tr("theme_dark", "Dunkel")
        return tr("theme_light", "Hell")

    def _test_token(self) -> None:
        self.status_lbl.configure(
            text=tr("testing_token_progress", "Verbindung zu Hugging Face wird geprüft..."),
            fg=PHOENIX_THEME.text_muted
        )
        self.test_btn.configure(state="disabled")
        token = self.token_entry.get().strip()
        
        # Run API test in background thread to prevent UI freezing
        threading.Thread(
            target=self._test_token_worker,
            args=(token,),
            daemon=True
        ).start()

    def _test_token_worker(self, token: str) -> None:
        valid, msg = SettingsManager.test_hf_token(token)
        self.after_idle(self._apply_test_result, valid, msg)

    def _apply_test_result(self, valid: bool, msg: str) -> None:
        self.test_btn.configure(state="normal")
        title = tr("test_token_btn", "Token testen")
        if valid:
            self.status_lbl.configure(text=msg, fg=PHOENIX_THEME.accent)
            messagebox.showinfo(title, msg)
        else:
            self.status_lbl.configure(text=msg, fg="#f87171")
            messagebox.showwarning(title, msg)

    def _update_token_format_status(self, *args) -> None:
        token = self.token_entry.get().strip()
        if not token:
            self.token_format_lbl.configure(text=tr("settings_token_none", "❌ Kein Token angegeben"), fg="#ef4444")
        elif token.startswith("hf_"):
            self.token_format_lbl.configure(text=tr("settings_token_valid", "✔ Format gültig (HF Standard)"), fg="#22c55e")
        else:
            self.token_format_lbl.configure(text=tr("settings_token_unusual", "⚠ Format ungewöhnlich (sollte mit 'hf_' beginnen)"), fg="#eab308")

    def refresh(self) -> None:
        self._update_token_format_status()

    def _setup_context_menus(self) -> None:
        def show_menu(event: tk.Event) -> None:
            w = event.widget
            menu = tk.Menu(w, tearoff=0)
            
            has_sel = False
            try:
                if w.selection_present():
                    has_sel = True
            except Exception:
                try:
                    if w.tag_ranges("sel"):
                        has_sel = True
                except Exception:
                    pass
                    
            menu.add_command(
                label=tr("cut", "Ausschneiden"),
                command=lambda: w.event_generate("<<Cut>>"),
                state="normal" if has_sel else "disabled"
            )
            menu.add_command(
                label=tr("copy", "Kopieren"),
                command=lambda: w.event_generate("<<Copy>>"),
                state="normal" if has_sel else "disabled"
            )
            menu.add_command(
                label=tr("paste", "Einfügen"),
                command=lambda: w.event_generate("<<Paste>>")
            )
            menu.tk_popup(event.x_root, event.y_root)

        self.bind_class("Entry", "<Button-3>", show_menu)
        self.bind_class("Text", "<Button-3>", show_menu)
