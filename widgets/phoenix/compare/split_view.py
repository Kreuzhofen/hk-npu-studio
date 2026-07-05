from __future__ import annotations

import tkinter as tk

from PIL import Image, ImageTk

from controllers.compare_workspace_model import CompareWorkspaceState
from resources.icons import IconManager
from widgets.phoenix.theme import PHOENIX_THEME


class ComparePreviewPanel(tk.Frame):
    """Single preview panel with empty state and canvas-based image rendering."""

    def __init__(self, master: tk.Misc, title: str, empty_title: str, empty_text: str, icon_name: str) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.title = title
        self.empty_title = empty_title
        self.empty_text = empty_text
        self.icon_name = icon_name
        self.photo_image: ImageTk.PhotoImage | None = None
        self.display_image: Image.Image | None = None
        self.zoom_scale: float | None = None
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        tk.Label(
            self,
            text=self.title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(PHOENIX_THEME.card_pad_y, PHOENIX_THEME.space_sm),
        )

        self.canvas = tk.Canvas(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(0, PHOENIX_THEME.card_pad_y),
        )
        self.canvas.bind("<Configure>", lambda _event: self.render(self.display_image, self.zoom_scale))

    def render(self, image: Image.Image | None, zoom_scale: float | None) -> None:
        self.display_image = image
        self.zoom_scale = zoom_scale
        self.canvas.delete("all")
        self.photo_image = None

        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        if image is None or width <= 1 or height <= 1:
            self._draw_empty_state(width, height)
            return

        render_size = self._render_size(image, width, height, zoom_scale)
        if render_size[0] < 1 or render_size[1] < 1:
            self._draw_empty_state(width, height)
            return

        resized = image.resize(render_size, Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(resized)
        self.canvas.create_image(width // 2, height // 2, image=self.photo_image, anchor="center")

    def _render_size(
        self,
        image: Image.Image,
        canvas_width: int,
        canvas_height: int,
        zoom_scale: float | None,
    ) -> tuple[int, int]:
        image_width, image_height = image.size
        if image_width <= 0 or image_height <= 0:
            return (0, 0)

        fit_scale = min(canvas_width / image_width, canvas_height / image_height)
        if zoom_scale is None:
            scale = fit_scale
        else:
            scale = zoom_scale

        return (max(1, int(image_width * scale)), max(1, int(image_height * scale)))

    def _draw_empty_state(self, width: int, height: int) -> None:
        center_x = width // 2
        center_y = height // 2
        self.canvas.create_text(
            center_x,
            max(48, center_y - 56),
            text=IconManager.get_symbol(self.icon_name),
            fill=PHOENIX_THEME.accent,
            font=(PHOENIX_THEME.font_title[0], 42, "bold"),
            anchor="center",
        )
        self.canvas.create_text(
            center_x,
            center_y + 8,
            text=self.empty_title,
            fill=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="center",
            width=max(240, width - 64),
        )
        self.canvas.create_text(
            center_x,
            center_y + 46,
            text=self.empty_text,
            fill=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="center",
            width=max(240, width - 72),
            justify="center",
        )


class CompareSplitView(tk.Frame):
    """Responsive split preview for original and output images."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.grid_columnconfigure(0, weight=1, uniform="compare_preview")
        self.grid_columnconfigure(1, weight=1, uniform="compare_preview")
        self.grid_rowconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        self.original_panel = ComparePreviewPanel(
            self,
            title="Original",
            empty_title="Originalbild laden",
            empty_text="Öffne links ein Ausgangsbild für den Qualitätsvergleich.",
            icon_name="image",
        )
        self.original_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, PHOENIX_THEME.space_sm),
            pady=0,
        )

        self.output_panel = ComparePreviewPanel(
            self,
            title="Ergebnis",
            empty_title="Ausgabe laden",
            empty_text="Öffne rechts ein Ergebnisbild, z. B. einen Batch-Output.",
            icon_name="output",
        )
        self.output_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(PHOENIX_THEME.space_sm, 0),
            pady=0,
        )

    def update_images(
        self,
        original_image: Image.Image | None,
        output_image: Image.Image | None,
        state: CompareWorkspaceState,
    ) -> None:
        self.original_panel.render(original_image, state.zoom_scale)
        self.output_panel.render(output_image, state.zoom_scale)
