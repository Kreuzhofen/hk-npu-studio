from __future__ import annotations

import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox

from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr
from app.settings_manager import SettingsManager


class PhoenixSettingsView(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self._build()
        self._setup_context_menus()

    def _build(self) -> None:
        # Title Block
        title_frame = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        title_frame.pack(fill="x", padx=24, pady=(24, 16))

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
        ).pack(fill="x", pady=(4, 0))

        # Main Settings Container Card
        self.card = tk.Frame(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
        )
        self.card.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        # Hugging Face Settings Section
        section_frame = tk.Frame(self.card, bg=PHOENIX_THEME.card_bg)
        section_frame.pack(fill="x", padx=20, pady=20)

        tk.Label(
            section_frame,
            text=tr("hf_integration_title", "Hugging Face Integration"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_button,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        tk.Label(
            section_frame,
            text=tr("hf_integration_desc", "Geben Sie Ihren Hugging Face User Access Token (HF_TOKEN) an, um Zugriff auf eingeschränkte Modelle (z.B. SDXL) freizuschalten."),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left",
            wraplength=700,
        ).pack(fill="x", pady=(0, 16))

        # Token Form Row
        form_frame = tk.Frame(section_frame, bg=PHOENIX_THEME.card_bg)
        form_frame.pack(fill="x", pady=(0, 16))
        form_frame.columnconfigure(0, weight=1)

        tk.Label(
            form_frame,
            text=tr("hf_token_label", "Hugging Face Access Token (HF_TOKEN):"),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        # Entry field
        self.token_entry = tk.Entry(
            form_frame,
            show="*",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
            font=PHOENIX_THEME.font_body,
        )
        self.token_entry.grid(row=1, column=0, sticky="ew", ipady=8, ipadx=8, padx=(0, 8))

        # Populate with existing token
        self.token_entry.insert(0, SettingsManager.get_hf_token())

        # Toggle Show/Hide Button
        self.show_toggle = False
        self.toggle_btn = tk.Button(
            form_frame,
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
            padx=12,
            pady=6,
        )
        self.toggle_btn.grid(row=1, column=1, sticky="ns")

        # Dynamic Token Help Label (clickable instruction link)
        self.token_help_lbl = tk.Label(
            form_frame,
            text="Token erstellen unter: https://huggingface.co/settings/tokens ↗",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left",
            cursor="hand2"
        )
        self.token_help_lbl.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.token_help_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://huggingface.co/settings/tokens"))

        # Dynamic Format/Status check label
        self.token_format_lbl = tk.Label(
            form_frame,
            text="",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left"
        )
        self.token_format_lbl.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        # Bind validation update to typing events
        self.token_entry.bind("<KeyRelease>", self._update_token_format_status)

        # Action Buttons Row
        actions_frame = tk.Frame(section_frame, bg=PHOENIX_THEME.card_bg)
        actions_frame.pack(fill="x", pady=10)

        # Save Button
        self.save_btn = tk.Button(
            actions_frame,
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
            padx=16,
            pady=8,
        )
        self.save_btn.pack(side="left", padx=(0, 10))

        # Test Button
        self.test_btn = tk.Button(
            actions_frame,
            text=tr("test_token_btn", "Token testen"),
            command=self._test_token,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.border,
            activeforeground=PHOENIX_THEME.text_primary,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=16,
            pady=8,
        )
        self.test_btn.pack(side="left")

        # Status Label
        self.status_lbl = tk.Label(
            section_frame,
            text="",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        self.status_lbl.pack(fill="x", pady=(12, 0))

        # Perform initial format check
        self._update_token_format_status()

    def _toggle_token_visibility(self) -> None:
        self.show_toggle = not self.show_toggle
        if self.show_toggle:
            self.token_entry.configure(show="")
            self.toggle_btn.configure(text=tr("hide_token", "Verbergen"))
        else:
            self.token_entry.configure(show="*")
            self.toggle_btn.configure(text=tr("show_token", "Anzeigen"))

    def _save_settings(self) -> None:
        token = self.token_entry.get().strip()
        success = SettingsManager.save_settings({"hf_token": token})
        if success:
            self.status_lbl.configure(
                text=tr("settings_save_success", "Einstellungen erfolgreich gespeichert."),
                fg=PHOENIX_THEME.accent
            )
        else:
            self.status_lbl.configure(
                text=tr("settings_save_failed", "Fehler beim Speichern der Einstellungen."),
                fg="#f87171"
            )

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
            self.token_format_lbl.configure(text="❌ Kein Token angegeben", fg="#ef4444")
        elif token.startswith("hf_"):
            self.token_format_lbl.configure(text="✔ Format gültig (HF Standard)", fg="#22c55e")
        else:
            self.token_format_lbl.configure(text="⚠ Format ungewöhnlich (sollte mit 'hf_' beginnen)", fg="#eab308")

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