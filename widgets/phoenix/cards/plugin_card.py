from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable

from controllers.plugin_controller import PluginMetadata
from widgets.phoenix.theme import PHOENIX_THEME
from resources.icons import IconManager


class PhoenixPluginCard(tk.Frame):
    """A premium, compact plugin card showing status, metadata, and control actions."""

    def __init__(
        self,
        master: tk.Misc,
        plugin: PluginMetadata,
        on_toggle: Callable[[str, bool], None],
        on_uninstall: Callable[[str], None],
        on_configure: Callable[[str], None],
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.plugin = plugin
        self.on_toggle = on_toggle
        self.on_uninstall = on_uninstall
        self.on_configure = on_configure
        self._build()

    def _build(self) -> None:
        # Symmetrical internal column configuration
        self.columnconfigure(0, weight=0)  # Icon
        self.columnconfigure(1, weight=1)  # Details
        self.columnconfigure(2, weight=0)  # Controls

        # 1. Left Slot: Plugin Extension Icon
        icon_lbl = tk.Label(
            self,
            text=IconManager.get_symbol("extension") or "🔌",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=("Segoe UI", 20, "bold"),
            width=3,
        )
        icon_lbl.grid(row=0, column=0, sticky="nsw", padx=16, pady=12)

        # 2. Middle Slot: Detailed Information
        info_frame = tk.Frame(self, bg=PHOENIX_THEME.card_bg)
        info_frame.grid(row=0, column=1, sticky="nsew", pady=12)
        info_frame.columnconfigure(0, weight=1)

        # Title / Name
        name_lbl = tk.Label(
            info_frame,
            text=self.plugin.name,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_button,
            anchor="w",
        )
        name_lbl.grid(row=0, column=0, sticky="w")

        # Version & Author
        meta_str = f"v{self.plugin.version} • Von {self.plugin.author}"
        meta_lbl = tk.Label(
            info_frame,
            text=meta_str,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        )
        meta_lbl.grid(row=1, column=0, sticky="w", pady=(2, 4))

        # Description
        desc_lbl = tk.Label(
            info_frame,
            text=self.plugin.description,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
            justify="left",
            wraplength=480,
        )
        desc_lbl.grid(row=2, column=0, sticky="w")

        # 3. Right Slot: Actions and Activation Toggle
        controls_frame = tk.Frame(self, bg=PHOENIX_THEME.card_bg)
        controls_frame.grid(row=0, column=2, sticky="nsew", padx=16, pady=12)

        # Toggle Switch (Checkbutton styled as slider/toggle status)
        self.toggle_var = tk.BooleanVar(value=self.plugin.enabled)
        self.toggle_btn = tk.Checkbutton(
            controls_frame,
            text="Aktiv" if self.plugin.enabled else "Inaktiv",
            variable=self.toggle_var,
            command=self._on_toggle,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.card_bg,
            activeforeground=PHOENIX_THEME.text_primary,
            selectcolor=PHOENIX_THEME.elevated_bg,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_caption,
            cursor="hand2",
        )
        self.toggle_btn.pack(side="left", padx=8)

        # Settings Icon Button (⚙️)
        self.settings_btn = tk.Button(
            controls_frame,
            text="⚙️",
            command=lambda: self.on_configure(self.plugin.id),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=10,
            pady=6,
        )
        self.settings_btn.pack(side="left", padx=4)
        self._add_hover(self.settings_btn)

        # Delete/Remove Icon Button (🗑️)
        from engine.theme_manager import ThemeManager
        danger_bg = getattr(ThemeManager.palette(), "error", "#cf6679")
        self.delete_btn = tk.Button(
            controls_frame,
            text="🗑️",
            command=lambda: self.on_uninstall(self.plugin.id),
            bg=danger_bg,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=danger_bg,
            activeforeground=PHOENIX_THEME.text_on_accent,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=10,
            pady=6,
        )
        self.delete_btn.pack(side="left", padx=4)
        self._add_hover(self.delete_btn, hover_bg="#b00020")

    def _on_toggle(self) -> None:
        is_enabled = self.toggle_var.get()
        self.toggle_btn.configure(text="Aktiv" if is_enabled else "Inaktiv")
        self.on_toggle(self.plugin.id, is_enabled)

    def _add_hover(self, btn: tk.Button, hover_bg: str | None = None) -> None:
        orig_bg = btn.cget("bg")
        orig_fg = btn.cget("fg")
        h_bg = hover_bg or PHOENIX_THEME.accent
        h_fg = PHOENIX_THEME.text_on_accent

        def enter(e):
            if str(btn.cget("state")) != "disabled":
                btn.configure(bg=h_bg, fg=h_fg)

        def leave(e):
            if str(btn.cget("state")) != "disabled":
                btn.configure(bg=orig_bg, fg=orig_fg)

        btn.bind("<Enter>", enter, add="+")
        btn.bind("<Leave>", leave, add="+")