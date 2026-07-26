from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from collections.abc import Callable

from controllers.plugin_controller import PluginController, PluginMetadata
from widgets.phoenix.cards.plugin_card import PhoenixPluginCard
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr


class PhoenixPluginView(WorkspaceFrame):
    """Plugins Workspace page for discovering, enabling, and installing extensions."""

    def __init__(self, master: tk.Misc, controller: PluginController | None = None) -> None:
        super().__init__(
            master,
            title="Plugins",
            subtitle="Verwalte Erweiterungen und Zusatzmodule für das Snapdragon AI Studio.",
            has_inspector=False,
        )
        self.controller = controller or PluginController()
        self.active_tab = "Alle"
        self.tab_buttons: dict[str, tk.Button] = {}
        self._plugin_cards: dict[str, PhoenixPluginCard] = {}
        self._search_timer: str | None = None
        
        self._build()
        self.refresh()

    def _build(self) -> None:
        # Build search and filter header bar in content_slot
        self.header_bar = tk.Frame(self.content_slot, bg=PHOENIX_THEME.content_bg)
        self.header_bar.pack(fill="x", padx=24, pady=(12, 8))

        # 1. Search Box
        search_label = tk.Label(
            self.header_bar,
            text="Suchen:",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
        )
        search_label.pack(side="left", padx=(0, 8))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        self.search_entry = tk.Entry(
            self.header_bar,
            textvariable=self.search_var,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
            font=PHOENIX_THEME.font_body,
            width=28,
        )
        self.search_entry.pack(side="left", ipady=4)

        # Separator spacing
        tk.Frame(self.header_bar, width=32, bg=PHOENIX_THEME.content_bg).pack(side="left")

        # 2. Segmented Filter Tabs
        tabs_container = tk.Frame(self.header_bar, bg=PHOENIX_THEME.content_bg)
        tabs_container.pack(side="left")

        for tab_name in ("Alle", "Aktiv", "Verfügbar"):
            btn = tk.Button(
                tabs_container,
                text=tab_name,
                command=lambda t=tab_name: self._on_tab_changed(t),
                bg=PHOENIX_THEME.elevated_bg,
                fg=PHOENIX_THEME.text_secondary,
                activebackground=PHOENIX_THEME.accent,
                activeforeground=PHOENIX_THEME.text_on_accent,
                bd=0,
                relief="flat",
                font=PHOENIX_THEME.font_caption,
                cursor="hand2",
                padx=16,
                pady=6,
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons[tab_name] = btn
            self._add_tab_hover(btn, tab_name)

        # 3. Middle Slot: Scrollable Card Container for Responsive/Zero-Scroll Layout
        self.middle_frame = tk.Frame(self.content_slot, bg=PHOENIX_THEME.content_bg)
        self.middle_frame.pack(fill="both", expand=True, padx=24, pady=8)

        self.canvas = tk.Canvas(
            self.middle_frame,
            bg=PHOENIX_THEME.content_bg,
            highlightthickness=0,
            bd=0,
        )
        self.scrollbar = ttk.Scrollbar(
            self.middle_frame,
            orient="vertical",
            command=self.canvas.yview,
            style="Phoenix.Vertical.TScrollbar",
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.cards_container = tk.Frame(self.canvas, bg=PHOENIX_THEME.content_bg)
        self.canvas_window_id = self.canvas.create_window(
            (0, 0),
            window=self.cards_container,
            anchor="nw",
        )

        self.cards_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window_id, width=e.width),
        )

        # Pre-create empty state label
        self._no_plugins_lbl = tk.Label(
            self.cards_container,
            text="Keine Plugins gefunden.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
        )

        # Bind MouseWheel locally
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        # 4. Bottom action panel for "Plugin installieren..."
        self.install_frame = tk.Frame(
            self.content_slot,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.install_frame.pack(side="bottom", fill="x", padx=24, pady=(12, 24))

        tk.Label(
            self.install_frame,
            text="Plugin installieren:",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_button,
        ).pack(side="left", padx=16, pady=16)

        self.install_path_var = tk.StringVar()
        self.install_path_entry = tk.Entry(
            self.install_frame,
            textvariable=self.install_path_var,
            state="readonly",
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_secondary,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
            font=PHOENIX_THEME.font_body,
        )
        self.install_path_entry.pack(side="left", fill="x", expand=True, padx=8, ipady=4)

        self.browse_btn = tk.Button(
            self.install_frame,
            text="Ordner wählen...",
            command=self._on_browse_plugin,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=14,
            pady=8,
        )
        self.browse_btn.pack(side="left", padx=4)
        self._add_button_hover(self.browse_btn)

        self.install_btn = tk.Button(
            self.install_frame,
            text="Installieren",
            command=self._on_install_plugin,
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
        self.install_btn.pack(side="left", padx=(4, 16))
        self._add_button_hover(self.install_btn)

    def _on_tab_changed(self, tab_name: str) -> None:
        self.active_tab = tab_name
        self.refresh()

    def _on_search_changed(self, *args) -> None:
        if self._search_timer is not None:
            try:
                self.after_cancel(self._search_timer)
            except Exception:
                pass
        self._search_timer = self.after(150, self.refresh)

    def _add_tab_hover(self, button: tk.Button, tab_name: str) -> None:
        h_bg = PHOENIX_THEME.accent
        h_fg = PHOENIX_THEME.text_on_accent

        def enter(e):
            if self.active_tab != tab_name:
                button.configure(bg=h_bg, fg=h_fg)

        def leave(e):
            if self.active_tab != tab_name:
                button.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_secondary)

        button.bind("<Enter>", enter, add="+")
        button.bind("<Leave>", leave, add="+")

    def _add_button_hover(self, button: tk.Button) -> None:
        orig_bg = button.cget("bg")
        orig_fg = button.cget("fg")
        h_bg = PHOENIX_THEME.accent
        h_fg = PHOENIX_THEME.text_on_accent

        def enter(e):
            if str(button.cget("state")) != "disabled":
                button.configure(bg=h_bg, fg=h_fg)

        def leave(e):
            if str(button.cget("state")) != "disabled":
                button.configure(bg=orig_bg, fg=orig_fg)

        button.bind("<Enter>", enter, add="+")
        button.bind("<Leave>", leave, add="+")

    def refresh(self) -> None:
        # Update tab visual indicators
        for name, button in self.tab_buttons.items():
            if name == self.active_tab:
                button.configure(bg=PHOENIX_THEME.accent, fg=PHOENIX_THEME.text_on_accent)
            else:
                button.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_secondary)

        # Get all plugins from the directory structure
        plugins = self.controller.get_plugins("Alle", "")
        current_ids = {p.id for p in plugins}

        # 1. Sync plugin cards dictionary: Remove uninstalled cards
        for p_id in list(self._plugin_cards.keys()):
            if p_id not in current_ids:
                try:
                    self._plugin_cards[p_id].destroy()
                except Exception:
                    pass
                del self._plugin_cards[p_id]

        # 2. Sync plugin cards dictionary: Create new installed cards
        for p in plugins:
            if p.id not in self._plugin_cards:
                card = PhoenixPluginCard(
                    self.cards_container,
                    plugin=p,
                    on_toggle=self._on_toggle_plugin,
                    on_uninstall=self._on_uninstall_plugin,
                    on_configure=self._on_configure_plugin,
                )
                self._plugin_cards[p.id] = card

        # 3. Update visibility of cards based on search and filters
        query = self.search_var.get().strip().lower()
        visible_count = 0

        # Sort the plugins according to directory scanning sorted logic
        for p in plugins:
            card = self._plugin_cards.get(p.id)
            if not card:
                continue

            # Update the underlying plugin object in the card to keep toggle state updated
            card.plugin = p

            # Tab filter
            match_tab = True
            if self.active_tab == "Aktiv" and not p.enabled:
                match_tab = False
            elif self.active_tab == "Verfügbar" and p.enabled:
                match_tab = False

            # Search query filter
            match_query = True
            if query:
                match_query = (
                    query in p.name.lower() or
                    query in p.description.lower() or
                    query in p.author.lower()
                )

            if match_tab and match_query:
                card.pack(fill="x", pady=6)
                visible_count += 1
            else:
                card.pack_forget()

        # 4. Handle empty state visibility
        if visible_count == 0:
            self._no_plugins_lbl.pack(pady=40)
        else:
            self._no_plugins_lbl.pack_forget()

        # 5. Flush and apply batch layout updates using update_idletasks
        self.update_idletasks()

    def _on_toggle_plugin(self, plugin_id: str, enabled: bool) -> None:
        self.controller.toggle_plugin(plugin_id, enabled)

    def _on_uninstall_plugin(self, plugin_id: str) -> None:
        confirm = messagebox.askyesno(
            "Plugin entfernen",
            f"Möchtest du das Plugin '{plugin_id}' wirklich dauerhaft deinstallieren?",
        )
        if confirm:
            try:
                self.controller.uninstall_plugin(plugin_id)
                self.refresh()
                messagebox.showinfo("Erfolg", f"Das Plugin '{plugin_id}' wurde erfolgreich deinstalliert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Plugin konnte nicht deinstalliert werden: {e}")

    def _on_configure_plugin(self, plugin_id: str) -> None:
        messagebox.showinfo(
            "Plugin-Einstellungen",
            f"Konfiguration für das Plugin '{plugin_id}' ist derzeit bereit für die Integration der Engine.",
        )

    def _on_browse_plugin(self) -> None:
        folder = filedialog.askdirectory(title="Wähle einen Plugin-Ordner")
        if folder:
            self.install_path_var.set(folder)

    def _on_install_plugin(self) -> None:
        src = self.install_path_var.get().strip()
        if not src:
            messagebox.showwarning("Warnung", "Bitte wähle zuerst einen Plugin-Ordner aus.")
            return

        try:
            plugin_id = self.controller.install_plugin(src)
            self.install_path_var.set("")
            self.refresh()
            messagebox.showinfo("Erfolg", f"Das Plugin '{plugin_id}' wurde erfolgreich installiert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Plugin-Installation fehlgeschlagen: {e}")