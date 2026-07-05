from __future__ import annotations

import tkinter as tk

from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixGalleryView(WorkspaceFrame):
    """Phoenix Gallery Workspace Shell."""

    def __init__(self, master: tk.Misc, controller: object | None = None) -> None:
        super().__init__(
            master,
            title="Gallery Workspace",
            subtitle="Bildkatalog durchsuchen und verwalten",
            has_inspector=False,
        )
        self.controller = controller

        self.scroll_canvas: tk.Canvas
        self.scroll_frame: tk.Frame
        self.scrollbar: tk.Scrollbar

        self._build_shell()

    def _build_shell(self) -> None:
        # Konfigurieren des Grid-Layouts im Inhaltsbereich
        self.content_slot.grid_rowconfigure(0, weight=1)
        self.content_slot.grid_columnconfigure(0, weight=1)

        # Vorbereiteter scrollbarer Container (Canvas + Scrollbar)
        self.scroll_canvas = tk.Canvas(
            self.content_slot,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
        )
        self.scrollbar = tk.Scrollbar(
            self.content_slot,
            orient="vertical",
            command=self.scroll_canvas.yview,
        )
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scroll_canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Innerer Frame für den zukünftigen Inhalt
        self.scroll_frame = tk.Frame(self.scroll_canvas, bg=PHOENIX_THEME.card_bg)
        self.scroll_canvas.create_window(
            (0, 0),
            window=self.scroll_frame,
            anchor="nw",
            tags="scroll_content",
        )

        self.scroll_frame.bind("<Configure>", self._update_scroll_region)
        self.scroll_canvas.bind("<Configure>", self._on_canvas_resize)

        # Platzhalter für die Galerie-Inhalte
        placeholder = tk.Label(
            self.scroll_frame,
            text="Galerie-Platzhalter\n\nThumbnail-Ansicht wird in einem zukünftigen Sprint integriert.",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            justify="center",
        )
        placeholder.pack(expand=True, fill="both", padx=PHOENIX_THEME.space_xl, pady=PHOENIX_THEME.space_xl)

    def _update_scroll_region(self, _event: tk.Event | None) -> None:
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _on_canvas_resize(self, event: tk.Event) -> None:
        self.scroll_canvas.itemconfigure("scroll_content", width=event.width)
        self.scroll_frame.configure(height=event.height)
