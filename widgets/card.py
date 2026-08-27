import tkinter as tk
from app import theme


class Card(tk.Frame):
    """
    Wiederverwendbare Karte für HK NPU STUDIO.

    Beispiel:
        Card(parent, title="RealESRGAN", subtitle="QNN / Snapdragon NPU")
    """

    def __init__(self, parent, title="", subtitle="", status="", **kwargs):
        super().__init__(parent, bg=theme.PANEL, **kwargs)

        self.title_label = tk.Label(
            self,
            text=title,
            bg=theme.PANEL,
            fg=theme.TEXT,
            font=(theme.FONT, theme.FONT_SIZE_MD, "bold"),
            anchor="w",
        )
        self.title_label.pack(anchor="w", padx=theme.CARD_PAD, pady=(theme.CARD_PAD, 2))

        if subtitle:
            self.subtitle_label = tk.Label(
                self,
                text=subtitle,
                bg=theme.PANEL,
                fg=theme.MUTED,
                font=(theme.FONT, theme.FONT_SIZE_BASE),
                anchor="w",
            )
            self.subtitle_label.pack(anchor="w", padx=theme.CARD_PAD, pady=(0, 8))

        if status:
            self.status_label = tk.Label(
                self,
                text=status,
                bg=theme.PANEL,
                fg=theme.status_color(status),
                font=(theme.FONT, theme.FONT_SIZE_SM, "bold"),
                anchor="w",
            )
            self.status_label.pack(anchor="w", padx=theme.CARD_PAD, pady=(0, theme.CARD_PAD))
