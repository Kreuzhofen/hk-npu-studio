import tkinter as tk
from app import theme


class BasePage(tk.Frame):
    """
    Basisklasse für alle künftigen Seiten.

    Jede Seite bekommt:
    - einheitlichen Hintergrund
    - einheitliche Überschrift
    - einheitliche Beschreibung
    """

    page_title = "Page"
    page_subtitle = ""

    def __init__(self, parent, app=None):
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self._build_header()

    def _build_header(self):
        tk.Label(
            self,
            text=self.page_title,
            bg=theme.BG,
            fg=theme.TEXT,
            font=(theme.FONT, theme.FONT_SIZE_XL, "bold"),
            anchor="w",
        ).pack(anchor="w", padx=theme.SPACE_MD, pady=(theme.SPACE_MD, 4))

        if self.page_subtitle:
            tk.Label(
                self,
                text=self.page_subtitle,
                bg=theme.BG,
                fg=theme.MUTED,
                font=(theme.FONT, theme.FONT_SIZE_BASE),
                anchor="w",
            ).pack(anchor="w", padx=theme.SPACE_MD, pady=(0, theme.SPACE_MD))
