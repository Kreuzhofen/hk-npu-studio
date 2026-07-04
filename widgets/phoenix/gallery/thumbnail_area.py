from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class GalleryThumbnailArea(tk.Frame):
    """Scrollable thumbnail area foundation with a professional empty state."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.canvas: tk.Canvas
        self.grid_frame: tk.Frame
        self.empty_state: tk.Frame
        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightthickness=0,
            bd=0,
        )
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.grid_frame = tk.Frame(self.canvas, bg=PHOENIX_THEME.card_bg)
        self.canvas.create_window(
            (0, 0),
            window=self.grid_frame,
            anchor="nw",
            tags="thumbnail_grid",
        )

        self.grid_frame.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_grid)
        self._build_empty_state()

    def _build_empty_state(self) -> None:
        self.grid_frame.grid_rowconfigure(0, weight=1)
        self.grid_frame.grid_columnconfigure(0, weight=1)

        self.empty_state = tk.Frame(self.grid_frame, bg=PHOENIX_THEME.card_bg)
        self.empty_state.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=PHOENIX_THEME.space_xl,
            pady=PHOENIX_THEME.space_xl,
        )
        self.empty_state.grid_columnconfigure(0, weight=1)

        icon = tk.Label(
            self.empty_state,
            text="▧",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=(PHOENIX_THEME.font_title[0], 38, "bold"),
            anchor="center",
        )
        icon.grid(row=0, column=0, pady=(0, PHOENIX_THEME.space_lg))

        tk.Label(
            self.empty_state,
            text="Noch keine Bilder in der Galerie",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="center",
        ).grid(row=1, column=0, sticky="ew")

        tk.Label(
            self.empty_state,
            text="Öffne später einen Ordner, um Bilder als responsive Thumbnail-Ansicht zu verwalten.",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="center",
            justify="center",
            wraplength=420,
        ).grid(row=2, column=0, sticky="ew", pady=(PHOENIX_THEME.space_md, 0))

    def _update_scroll_region(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_grid(self, event: tk.Event) -> None:
        self.canvas.itemconfigure("thumbnail_grid", width=event.width)
        self.grid_frame.configure(height=event.height)
