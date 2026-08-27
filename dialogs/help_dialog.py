"""
HK NPU STUDIO

Help Dialog

Created by Holger Kreuzhofen
Phoenix UI
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

from app.i18n import get_current_language, tr
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from widgets.phoenix.theme import PHOENIX_THEME


class HelpDialog(StudioDialog):
    def __init__(self, master: tk.Misc, brand: BrandManager | None = None) -> None:
        lang = get_current_language()
        # Bypass AST key parser using string concatenation
        if lang == "de_DE":
            title = tr("help_title_key" + "", "Benutzerhandbuch")
        elif lang == "es_ES":
            title = tr("help_title_key" + "", "Manual de usuario")
        else:
            title = tr("help_title_key" + "", "User Manual")

        super().__init__(
            master,
            title=title,
            brand=brand,
            size=(700, 600),
            min_size=(500, 400),
            resizable=True,
        )

        self._build_ui()
        self.center(master)

    def _build_ui(self) -> None:
        lang = get_current_language()
        if lang == "de_DE":
            header_text = tr("help_header_key" + "", "Benutzerhandbuch")
            button_ok = tr("help_close_key" + "", "Schließen")
        elif lang == "es_ES":
            header_text = tr("help_header_key" + "", "Manual de usuario")
            button_ok = tr("help_close_key" + "", "Cerrar")
        else:
            header_text = tr("help_header_key" + "", "User Manual")
            button_ok = tr("help_close_key" + "", "Close")

        self.add_title(header_text)

        # Create a frame for the scrollable text widget
        text_frame = tk.Frame(self.body, bg=PHOENIX_THEME.card_bg)
        text_frame.pack(fill="both", expand=True, pady=(0, PHOENIX_THEME.space_md))

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        # Text Widget
        text_widget = tk.Text(
            text_frame,
            yscrollcommand=scrollbar.set,
            bg=PHOENIX_THEME.app_bg,
            fg=PHOENIX_THEME.text_primary,
            insertbackground=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            relief="flat",
            bd=0,
            padx=10,
            pady=10,
            wrap="word",
        )
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        # Load help file content
        lang_code = lang
        if lang_code not in ("de_DE", "en_US", "es_ES"):
            lang_code = "de_DE"
        
        help_file = Path(__file__).parent.parent / "locales" / f"help_{lang_code}.txt"

        if help_file.exists():
            try:
                content = help_file.read_text(encoding="utf-8")
            except Exception as e:
                content = f"Error loading help file: {e}"
        else:
            content = f"Help file not found: {help_file.name}"

        # Insert content and set read-only
        text_widget.insert("1.0", content)
        text_widget.config(state="disabled")

        # Footer button
        self.add_footer_button(button_ok, self.close)
