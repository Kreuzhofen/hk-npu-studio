from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable

from controllers.plugin_controller import PluginMetadata
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.controls.card import PhoenixCard
from resources.icons import IconManager


class PhoenixPluginCard(PhoenixCard):
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
            border_color=PHOENIX_THEME.border,
            radius=10,
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
        from widgets.phoenix.controls.vector_icons import PhoenixIcon
        icon_canvas = PhoenixIcon(
            self,
            name="plugins",
            size=24,
            color=PHOENIX_THEME.accent,
            bg=PHOENIX_THEME.card_bg
        )
        icon_canvas.grid(row=0, column=0, sticky="nsw", padx=16, pady=12)

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
        status_text = tr("plugin_status_active", "Aktiv") if self.plugin.enabled else tr("plugin_status_inactive", "Inaktiv")
        self.toggle_btn = tk.Checkbutton(
            controls_frame,
            text=status_text,
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

        # Settings Icon Button
        self.settings_btn = PhoenixButton(
            controls_frame,
            command=lambda: self.on_configure(self.plugin.id),
            button_type="neutral",
            icon_name="settings",
            width=36,
            height=32,
        )
        self.settings_btn.pack(side="left", padx=4)

        # Delete/Remove Icon Button
        self.delete_btn = PhoenixButton(
            controls_frame,
            command=lambda: self.on_uninstall(self.plugin.id),
            button_type="danger",
            icon_name="delete",
            width=36,
            height=32,
        )
        self.delete_btn.pack(side="left", padx=4)

    def _on_toggle(self) -> None:
        is_enabled = self.toggle_var.get()
        status_text = tr("plugin_status_active", "Aktiv") if is_enabled else tr("plugin_status_inactive", "Inaktiv")
        self.toggle_btn.configure(text=status_text)
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