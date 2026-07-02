from __future__ import annotations

import tkinter as tk
from pathlib import Path

from PIL import Image, ImageOps, ImageTk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixImageView(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)

        self.current_image_path: Path | None = None
        self.preview_image: ImageTk.PhotoImage | None = None
        self.output_preview_image: ImageTk.PhotoImage | None = None

        self.title_label: tk.Label
        self.path_label: tk.Label
        self.preview_container: tk.Frame
        self.preview_label: tk.Label
        self.output_preview_label: tk.Label
        self.image_info_value: tk.Label
        self.output_info_value: tk.Label

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
        self.title_label.pack(fill="x", padx=28, pady=(28, 8))

        self.path_label = tk.Label(
            self,
            text="Noch kein Bild geladen.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 11),
            anchor="w",
        )
        self.path_label.pack(fill="x", padx=28, pady=(0, 20))

        preview_frame = tk.Frame(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            height=500,
        )
        preview_frame.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        preview_frame.pack_propagate(False)

        self.preview_container = tk.Frame(
            preview_frame,
            bg=PHOENIX_THEME.card_bg,
        )
        self.preview_container.pack(fill="both", expand=True, padx=20, pady=20)
        self.preview_container.grid_columnconfigure(0, weight=1, uniform="preview_columns")
        self.preview_container.grid_columnconfigure(1, weight=1, uniform="preview_columns")
        self.preview_container.grid_rowconfigure(0, weight=1)

        original_preview = tk.Frame(
            self.preview_container,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        original_preview.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        original_preview.grid_columnconfigure(0, weight=1)
        original_preview.grid_rowconfigure(1, weight=1)

        tk.Label(
            original_preview,
            text="Original",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))

        self.preview_label = tk.Label(
            original_preview,
            text="Keine Vorschau verfügbar",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 12),
            anchor="center",
        )
        self.preview_label.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        output_preview = tk.Frame(
            self.preview_container,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        output_preview.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        output_preview.grid_columnconfigure(0, weight=1)
        output_preview.grid_rowconfigure(1, weight=1)

        tk.Label(
            output_preview,
            text="Bearbeitet",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))

        self.output_preview_label = tk.Label(
            output_preview,
            text="Noch kein Output",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 12),
            anchor="center",
        )
        self.output_preview_label.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        info_host = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        info_host.pack(fill="x", padx=28, pady=(0, 18))
        info_host.grid_columnconfigure(0, weight=1, uniform="image_info_cards")
        info_host.grid_columnconfigure(1, weight=1, uniform="image_info_cards")

        image_info = self._build_info_card(info_host, "Bildinformationen")
        image_info.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.image_info_value = tk.Label(
            image_info,
            text="Keine Bildinformationen verfügbar.",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        )
        self.image_info_value.pack(fill="x", padx=20, pady=(0, 18))

        output_info = self._build_info_card(info_host, "Ausgabeinformationen")
        output_info.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.output_info_value = tk.Label(
            output_info,
            text="Keine Ausgabeinformationen verfügbar.",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        )
        self.output_info_value.pack(fill="x", padx=20, pady=(0, 18))

    def _build_info_card(self, master: tk.Misc, title: str) -> tk.Frame:
        card = tk.Frame(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            height=112,
        )
        card.grid_propagate(False)
        card.pack_propagate(False)

        tk.Label(
            card,
            text=title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            height=1,
        ).pack(fill="x", padx=20, pady=(18, 8))

        return card

    def _load_display_image(self, image_path: Path) -> Image.Image:
        with Image.open(image_path) as source_image:
            image = ImageOps.exif_transpose(source_image)
            return image.convert("RGB")

    def show_image(self, filename: str | Path) -> None:
        image_path = Path(filename)

        if not image_path.exists():
            self.current_image_path = None
            self.preview_image = None
            self.output_preview_image = None
            self.path_label.configure(text=f"Bild nicht gefunden: {image_path}")
            self.image_info_value.configure(text="Keine Bildinformationen verfügbar.")
            self.output_info_value.configure(text="Keine Ausgabeinformationen verfügbar.")
            self.preview_label.configure(
                image="",
                text="Bild nicht gefunden",
            )
            self.output_preview_label.configure(
                image="",
                text="Noch kein Output",
            )
            return

        try:
            with Image.open(image_path) as source_image:
                image_format = source_image.format or "Unbekannt"
                source_image = ImageOps.exif_transpose(source_image)
                image_mode = source_image.mode
                image_size = source_image.size
            image = self._load_display_image(image_path)

            file_size = self._format_file_size(image_path.stat().st_size)
            self.preview_label.update_idletasks()
            preview_width = self.preview_label.winfo_width()
            preview_height = self.preview_label.winfo_height()
            if preview_width <= 1 or preview_height <= 1:
                preview_width = 860
                preview_height = 440
            image.thumbnail((preview_width, preview_height))

            self.preview_image = ImageTk.PhotoImage(image)
            self.current_image_path = image_path

            self.path_label.configure(text=str(image_path))
            self.image_info_value.configure(
                text=(
                    f"Dateiname: {image_path.name}\n"
                    f"Auflösung: {image_size[0]} x {image_size[1]}\n"
                    f"Format: {image_format}\n"
                    f"Farbmodus: {image_mode}\n"
                    f"Dateigröße: {file_size}"
                )
            )
            self.output_info_value.configure(
                text=(
                    "Output: Noch nicht erzeugt\n"
                    "Plugin: RealESRGAN\n"
                    "Backend: QNN / Snapdragon NPU"
                )
            )
            self.preview_label.configure(
                image=self.preview_image,
                text="",
            )

        except Exception as error:
            self.current_image_path = None
            self.preview_image = None
            self.path_label.configure(text=str(image_path))
            self.image_info_value.configure(text="Keine Bildinformationen verfügbar.")
            self.output_info_value.configure(text="Keine Ausgabeinformationen verfügbar.")
            self.preview_label.configure(
                image="",
                text=f"Vorschaufehler:\n{error}",
            )

    def show_output_image(self, filename: str | Path) -> None:
        image_path = Path(filename)

        if not image_path.exists():
            self.output_preview_image = None
            self.output_info_value.configure(text="Output: Nicht gefunden")
            self.output_preview_label.configure(
                image="",
                text="Output nicht gefunden",
            )
            return

        try:
            with Image.open(image_path) as source_image:
                image_format = source_image.format or "Unbekannt"
                source_image = ImageOps.exif_transpose(source_image)
                image_mode = source_image.mode
                image_size = source_image.size
            image = self._load_display_image(image_path)

            file_size = self._format_file_size(image_path.stat().st_size)
            self.output_preview_label.update_idletasks()
            preview_width = self.output_preview_label.winfo_width()
            preview_height = self.output_preview_label.winfo_height()
            if preview_width <= 1 or preview_height <= 1:
                preview_width = 420
                preview_height = 400
            image.thumbnail((preview_width, preview_height))

            self.output_preview_image = ImageTk.PhotoImage(image)
            self.output_info_value.configure(
                text=(
                    f"Output: {image_path.name}\n"
                    f"Auflösung: {image_size[0]} x {image_size[1]}\n"
                    f"Format: {image_format}\n"
                    f"Farbmodus: {image_mode}\n"
                    f"Dateigröße: {file_size}"
                )
            )
            self.output_preview_label.configure(
                image=self.output_preview_image,
                text="",
            )

        except Exception as error:
            self.output_preview_image = None
            self.output_info_value.configure(text="Keine Ausgabeinformationen verfügbar.")
            self.output_preview_label.configure(
                image="",
                text=f"Output-Fehler:\n{error}",
            )

    def clear_image(self) -> None:
        self.current_image_path = None
        self.preview_image = None
        self.output_preview_image = None
        self.path_label.configure(text="Noch kein Bild geladen.")
        self.image_info_value.configure(text="Keine Bildinformationen verfügbar.")
        self.output_info_value.configure(text="Keine Ausgabeinformationen verfügbar.")
        self.preview_label.configure(
            image="",
            text="Keine Vorschau verfügbar",
        )
        self.output_preview_label.configure(
            image="",
            text="Noch kein Output",
        )

    def _format_file_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"

        size_kb = size_bytes / 1024
        if size_kb < 1024:
            return f"{size_kb:.1f} KB"

        size_mb = size_kb / 1024
        return f"{size_mb:.1f} MB"
