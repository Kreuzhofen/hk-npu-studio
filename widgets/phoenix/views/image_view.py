from __future__ import annotations

import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixImageView(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)

        self.current_image_path: Path | None = None
        self.preview_image: ImageTk.PhotoImage | None = None

        self.title_label: tk.Label
        self.path_label: tk.Label
        self.preview_label: tk.Label

        self._build()

    def _build(self) -> None:
        self.title_label = tk.Label(
            self,
            text="Image Workspace",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 22, "bold"),
            anchor="w",
        )
        self.title_label.pack(fill="x", padx=24, pady=(24, 8))

        self.path_label = tk.Label(
            self,
            text="Noch kein Bild geladen.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 11),
            anchor="w",
        )
        self.path_label.pack(fill="x", padx=24, pady=(0, 16))

        preview_frame = tk.Frame(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        preview_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        self.preview_label = tk.Label(
            preview_frame,
            text="Keine Vorschau verfügbar",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 12),
            anchor="center",
        )
        self.preview_label.pack(fill="both", expand=True, padx=16, pady=16)

    def show_image(self, filename: str | Path) -> None:
        image_path = Path(filename)

        if not image_path.exists():
            self.current_image_path = None
            self.preview_image = None
            self.path_label.configure(text=f"Bild nicht gefunden: {image_path}")
            self.preview_label.configure(
                image="",
                text="Bild nicht gefunden",
            )
            return

        try:
            image = Image.open(image_path).convert("RGB")
            image.thumbnail((900, 620))

            self.preview_image = ImageTk.PhotoImage(image)
            self.current_image_path = image_path

            self.path_label.configure(text=str(image_path))
            self.preview_label.configure(
                image=self.preview_image,
                text="",
            )

        except Exception as error:
            self.current_image_path = None
            self.preview_image = None
            self.path_label.configure(text=str(image_path))
            self.preview_label.configure(
                image="",
                text=f"Vorschaufehler:\n{error}",
            )

    def clear_image(self) -> None:
        self.current_image_path = None
        self.preview_image = None
        self.path_label.configure(text="Noch kein Bild geladen.")
        self.preview_label.configure(
            image="",
            text="Keine Vorschau verfügbar",
        )