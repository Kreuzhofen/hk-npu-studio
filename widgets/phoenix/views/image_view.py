from __future__ import annotations

import tkinter as tk
from pathlib import Path

from PIL import Image, ImageOps, ImageTk
Image.MAX_IMAGE_PIXELS = None

from widgets.phoenix.preview.compare_controller import CompareController
from widgets.phoenix.preview.compare_renderer import CompareRenderer
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixImageView(tk.Frame):
    def __init__(self, master: tk.Misc, on_gallery_select=None) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)

        self.on_gallery_select = on_gallery_select
        self.compare_controller = CompareController()
        self.compare_renderer = CompareRenderer(self.compare_controller)
        self.current_image_path: Path | None = None
        self.preview_image: ImageTk.PhotoImage | None = None
        self.output_preview_image: ImageTk.PhotoImage | None = None
        self.original_display_image: Image.Image | None = None
        self.output_display_image: Image.Image | None = None
        self.gallery_thumbnail_images: list[ImageTk.PhotoImage] = []
        self.gallery_thumbnail_cards: list[tk.Frame] = []
        self.selected_gallery_path: Path | None = None
        self.selected_image_paths: list[Path] = []
        self.gallery_window_id: int | None = None
        self._syncing_zoom_controls = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_start_pan_x = 0
        self.drag_start_pan_y = 0

        self.title_label: tk.Label
        self.path_label: tk.Label
        self.compare_container: tk.Frame
        self.compare_toolbar: tk.Frame
        self.compare_mode_buttons: dict[str, tk.Button] = {}
        self.zoom_buttons: dict[str, tk.Button] = {}
        self.zoom_slider: tk.Scale
        self.zoom_value_label: tk.Label
        self.preview_container: tk.Frame
        self.original_preview_frame: tk.Frame
        self.output_preview_frame: tk.Frame
        self.preview_label: tk.Label
        self.output_preview_label: tk.Label
        self.gallery_canvas: tk.Canvas
        self.gallery_content: tk.Frame
        self.gallery_scrollbar: tk.Scrollbar
        self.image_info_value: tk.Label
        self.output_info_value: tk.Label

        self._build()

    @property
    def zoom_mode(self) -> str:
        return self.compare_controller.zoom_mode

    @zoom_mode.setter
    def zoom_mode(self, value: str) -> None:
        self.compare_controller.zoom_mode = value

    @property
    def zoom_level(self) -> float:
        return self.compare_controller.zoom_level

    @zoom_level.setter
    def zoom_level(self, value: float) -> None:
        self.compare_controller.zoom_level = value

    @property
    def pan_x(self) -> float:
        return self.compare_controller.pan_x

    @pan_x.setter
    def pan_x(self, value: float) -> None:
        self.compare_controller.pan_x = value

    @property
    def pan_y(self) -> float:
        return self.compare_controller.pan_y

    @pan_y.setter
    def pan_y(self, value: float) -> None:
        self.compare_controller.pan_y = value

    def set_compare_mode(self, compare_mode: str) -> None:
        self.compare_controller.set_compare_mode(compare_mode)
        self._update_compare_mode_buttons()
        self._update_compare_cursor()
        self._apply_compare_view_state()

    def get_compare_mode(self) -> str:
        return self.compare_controller.get_compare_mode()

    def set_slider_position(self, value: float) -> None:
        self.compare_controller.set_slider_position(value)
        self._apply_compare_view_state()

    def set_overlay_opacity(self, value: float) -> None:
        self.compare_controller.set_overlay_opacity(value)
        self._apply_compare_view_state()

    def _build(self) -> None:
        page_padding = 28
        card_padding = 16
        section_gap = 18
        panel_gap = 16
        control_gap = 8

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=3, minsize=220)
        self.grid_rowconfigure(3, weight=0, minsize=236)

        self.title_label = tk.Label(
            self,
            text="Image Workspace",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 22, "bold"),
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="ew", padx=page_padding, pady=(28, 8))

        self.path_label = tk.Label(
            self,
            text="Noch kein Bild geladen.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 11),
            anchor="w",
        )
        self.path_label.grid(row=1, column=0, sticky="ew", padx=page_padding, pady=(0, 18))

        preview_frame = tk.Frame(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        preview_frame.grid(row=2, column=0, sticky="nsew", padx=page_padding, pady=(0, section_gap))
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)

        self.compare_container = tk.Frame(
            preview_frame,
            bg=PHOENIX_THEME.card_bg,
        )
        self.preview_container = self.compare_container
        self.preview_container.grid(row=0, column=0, sticky="nsew", padx=card_padding, pady=card_padding)
        self.preview_container.grid_columnconfigure(0, weight=1, uniform="preview_columns")
        self.preview_container.grid_columnconfigure(1, weight=1, uniform="preview_columns")
        self.preview_container.grid_rowconfigure(0, weight=0)
        self.preview_container.grid_rowconfigure(1, weight=1)

        self.compare_toolbar = tk.Frame(
            self.preview_container,
            bg=PHOENIX_THEME.card_bg,
        )
        self.compare_toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        tk.Label(
            self.compare_toolbar,
            text="Compare",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(0, control_gap))

        for index, (mode, label) in enumerate(
            (
                ("side", "Side"),
                ("slider", "Slider"),
                ("overlay", "Overlay"),
                ("difference", "Difference"),
            )
        ):
            button = tk.Button(
                self.compare_toolbar,
                text=label,
                command=lambda selected_mode=mode: self._set_compare_mode(selected_mode),
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_secondary,
                activebackground=PHOENIX_THEME.card_bg,
                activeforeground=PHOENIX_THEME.text_primary,
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=PHOENIX_THEME.border,
                font=("Segoe UI", 9, "bold"),
                padx=10,
                pady=5,
            )
            button.grid(row=0, column=index + 1, sticky="w", padx=(0, control_gap))
            self.compare_mode_buttons[mode] = button

        tk.Label(
            self.compare_toolbar,
            text="Zoom",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).grid(row=0, column=6, sticky="w", padx=(panel_gap, control_gap))

        for index, (mode, label) in enumerate((("fit", "Fit"), ("100", "100 %")), start=7):
            button = tk.Button(
                self.compare_toolbar,
                text=label,
                command=lambda selected_mode=mode: self._set_zoom_mode(selected_mode),
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_secondary,
                activebackground=PHOENIX_THEME.card_bg,
                activeforeground=PHOENIX_THEME.text_primary,
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=PHOENIX_THEME.border,
                font=("Segoe UI", 9, "bold"),
                padx=10,
                pady=5,
            )
            button.grid(row=0, column=index, sticky="w", padx=(0, control_gap))
            self.zoom_buttons[mode] = button

        self.zoom_slider = tk.Scale(
            self.compare_toolbar,
            from_=25,
            to=300,
            orient="horizontal",
            command=self._set_zoom_percent,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            activebackground=getattr(PHOENIX_THEME, "accent", "#3B82F6"),
            highlightthickness=0,
            troughcolor=PHOENIX_THEME.border,
            bd=0,
            showvalue=False,
            length=220,
        )
        self.zoom_slider.grid(row=0, column=9, sticky="w", padx=(0, control_gap))
        self.zoom_slider.set(100)

        self.zoom_value_label = tk.Label(
            self.compare_toolbar,
            text="Zoom: Fit",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            width=11,
        )
        self.zoom_value_label.grid(row=0, column=10, sticky="w")

        self.original_preview_frame = tk.Frame(
            self.preview_container,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        original_preview = self.original_preview_frame
        original_preview.grid(row=1, column=0, sticky="nsew", padx=(0, panel_gap // 2))
        original_preview.grid_columnconfigure(0, weight=1)
        original_preview.grid_rowconfigure(1, weight=1)

        tk.Label(
            original_preview,
            text="Original",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))

        self.preview_label = tk.Label(
            original_preview,
            text="Keine Vorschau verfügbar",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 12),
            anchor="center",
        )
        self.preview_label.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self._bind_pan_events(self.preview_label)

        self.output_preview_frame = tk.Frame(
            self.preview_container,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        output_preview = self.output_preview_frame
        output_preview.grid(row=1, column=1, sticky="nsew", padx=(panel_gap // 2, 0))
        output_preview.grid_columnconfigure(0, weight=1)
        output_preview.grid_rowconfigure(1, weight=1)

        tk.Label(
            output_preview,
            text="Bearbeitet",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))

        self.output_preview_label = tk.Label(
            output_preview,
            text="Noch kein Output",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 12),
            anchor="center",
        )
        self.output_preview_label.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self._bind_pan_events(self.output_preview_label)

        gallery_frame = tk.Frame(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        gallery_frame.grid(row=3, column=0, sticky="nsew", padx=page_padding, pady=(0, section_gap))
        gallery_frame.grid_columnconfigure(0, weight=1)
        gallery_frame.grid_rowconfigure(1, weight=0)

        tk.Label(
            gallery_frame,
            text="Gallery",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=card_padding, pady=(14, 8))

        gallery_host = tk.Frame(gallery_frame, bg=PHOENIX_THEME.card_bg)
        gallery_host.grid(row=1, column=0, sticky="nsew", padx=card_padding, pady=(0, card_padding))
        gallery_host.grid_columnconfigure(0, weight=1)
        gallery_host.grid_columnconfigure(1, weight=0)
        gallery_host.grid_rowconfigure(0, weight=0, minsize=172)

        self.gallery_canvas = tk.Canvas(
            gallery_host,
            bg=PHOENIX_THEME.card_bg,
            highlightthickness=0,
            bd=0,
            height=176,
        )
        self.gallery_canvas.grid(row=0, column=0, sticky="nsew")

        self.gallery_scrollbar = tk.Scrollbar(
            gallery_host,
            orient="vertical",
            command=self.gallery_canvas.yview,
        )
        self.gallery_scrollbar.grid(row=0, column=1, sticky="ns")
        self.gallery_canvas.configure(yscrollcommand=self.gallery_scrollbar.set)

        self.gallery_content = tk.Frame(
            self.gallery_canvas,
            bg=PHOENIX_THEME.card_bg,
        )
        self.gallery_window_id = self.gallery_canvas.create_window(
            (0, 0),
            window=self.gallery_content,
            anchor="nw",
        )
        self.gallery_canvas.bind("<Configure>", self._sync_gallery_canvas)
        self.gallery_content.bind(
            "<Configure>",
            lambda event: self.gallery_canvas.configure(
                scrollregion=self.gallery_canvas.bbox("all")
            ),
        )

        info_host = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        info_host.grid(row=4, column=0, sticky="ew", padx=page_padding, pady=(0, section_gap))
        info_host.grid_columnconfigure(0, weight=1, uniform="image_info_cards")
        info_host.grid_columnconfigure(1, weight=1, uniform="image_info_cards")

        image_info = self._build_info_card(info_host, "Bildinformationen")
        image_info.grid(row=0, column=0, sticky="nsew", padx=(0, panel_gap // 2))
        self.image_info_value = tk.Label(
            image_info,
            text="Keine Bildinformationen verfügbar.",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        )
        self.image_info_value.pack(fill="x", padx=card_padding, pady=(0, card_padding))

        output_info = self._build_info_card(info_host, "Ausgabeinformationen")
        output_info.grid(row=0, column=1, sticky="nsew", padx=(panel_gap // 2, 0))
        self.output_info_value = tk.Label(
            output_info,
            text="Keine Ausgabeinformationen verfügbar.",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        )
        self.output_info_value.pack(fill="x", padx=card_padding, pady=(0, card_padding))
        self._update_compare_mode_buttons()
        self._update_zoom_buttons()

    def _build_info_card(self, master: tk.Misc, title: str) -> tk.Frame:
        card = tk.Frame(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            height=124,
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
        ).pack(fill="x", padx=16, pady=(16, 8))

        return card

    def _load_display_image(self, image_path: Path) -> Image.Image:
        with Image.open(image_path) as source_image:
            w, h = source_image.size
            if w * h > 50_000_000:
                scale_factor = min(4096 / w, 4096 / h)
                if scale_factor < 1.0:
                    target_w = int(w * scale_factor)
                    target_h = int(h * scale_factor)
                    image = ImageOps.exif_transpose(source_image)
                    return image.resize((target_w, target_h), resample=Image.Resampling.BILINEAR)
            image = ImageOps.exif_transpose(source_image)
            return image.convert("RGB")

    def show_image(self, filename: str | Path) -> None:
        image_path = Path(filename)

        if not image_path.exists():
            self.current_image_path = None
            self.preview_image = None
            self.output_preview_image = None
            self.original_display_image = None
            self.output_display_image = None
            self.compare_controller.set_images(None, None)
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

            self._reset_compare_view_state()
            file_size = self._format_file_size(image_path.stat().st_size)
            self.original_display_image = image
            self.current_image_path = image_path
            self.compare_controller.set_images(
                self.original_display_image,
                self.output_display_image,
            )

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
                    "Generation Engine: Nicht verbunden\n"
                    "Backend: Noch keine Engine aktiv"
                )
            )
            self._apply_compare_view_state()

        except Exception as error:
            self.current_image_path = None
            self.preview_image = None
            self.original_display_image = None
            self.compare_controller.set_images(None, self.output_display_image)
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
            self.output_display_image = None
            self.compare_controller.set_images(
                self.original_display_image,
                None,
            )
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
            self.output_display_image = image
            self.compare_controller.set_images(
                self.original_display_image,
                self.output_display_image,
            )
            self.output_info_value.configure(
                text=(
                    f"Output: {image_path.name}\n"
                    f"Auflösung: {image_size[0]} x {image_size[1]}\n"
                    f"Format: {image_format}\n"
                    f"Farbmodus: {image_mode}\n"
                    f"Dateigröße: {file_size}"
                )
            )
            self._apply_compare_view_state()

        except Exception as error:
            self.output_preview_image = None
            self.output_display_image = None
            self.compare_controller.set_images(
                self.original_display_image,
                None,
            )
            self.output_info_value.configure(text="Keine Ausgabeinformationen verfügbar.")
            self.output_preview_label.configure(
                image="",
                text=f"Output-Fehler:\n{error}",
            )

    def show_image_pair(self, input_filename: str | Path, output_filename: str | Path) -> None:
        self.show_image(input_filename)
        self.show_output_image(output_filename)

    def _reset_compare_view_state(self) -> None:
        self.compare_controller.reset_camera()
        self._update_zoom_buttons()

    def _apply_compare_view_state(self) -> None:
        self._apply_pan_state()
        self.preview_image = self.compare_renderer.render_original(
            self._get_preview_size(self.preview_label),
        )
        if self.preview_image is not None:
            self.preview_label.configure(image=self.preview_image, text="")

        self.output_preview_image = self.compare_renderer.render_output(
            self._get_preview_size(self.output_preview_label),
        )
        if self.output_preview_image is not None:
            self.output_preview_label.configure(image=self.output_preview_image, text="")
        elif self.get_compare_mode() in {"slider", "overlay", "difference"}:
            self.output_preview_label.configure(image="", text="")

    def _reset_pan_state(self) -> None:
        self.compare_controller.reset_pan()

    def _apply_pan_state(self) -> None:
        pass

    def _bind_pan_events(self, target_label: tk.Label) -> None:
        target_label.bind("<ButtonPress-1>", self._start_pan)
        target_label.bind("<B1-Motion>", self._drag_pan)
        target_label.bind("<ButtonRelease-1>", self._end_pan)
        target_label.bind("<Double-Button-1>", self._reset_to_fit)

    def _start_pan(self, event) -> None:
        if self._is_slider_mode():
            self._update_slider_from_event(event)
            return

        if not self._is_pan_enabled():
            return

        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.drag_start_pan_x = self.pan_x
        self.drag_start_pan_y = self.pan_y

    def _drag_pan(self, event) -> None:
        if self._is_slider_mode():
            self._update_slider_from_event(event)
            return

        if not self._is_pan_enabled():
            return

        max_pan_x, max_pan_y = self._get_widget_pan_bounds(event.widget)
        delta_x = event.x - self.drag_start_x
        delta_y = event.y - self.drag_start_y

        if max_pan_x > 0:
            pan_x = self.drag_start_pan_x + delta_x / max_pan_x
        else:
            pan_x = 0

        if max_pan_y > 0:
            pan_y = self.drag_start_pan_y + delta_y / max_pan_y
        else:
            pan_y = 0

        self.compare_controller.pan_x = self.drag_start_pan_x
        self.compare_controller.pan_y = self.drag_start_pan_y
        self.compare_controller.pan_by(
            pan_x - self.drag_start_pan_x,
            pan_y - self.drag_start_pan_y,
        )
        self._apply_compare_view_state()

    def _end_pan(self, event) -> None:
        if self._is_slider_mode():
            return

        self._clamp_pan_state()

    def _reset_to_fit(self, event=None) -> None:
        if self._is_slider_mode():
            self._reset_slider_position(event)
            return

        self.compare_controller.fit()
        self._update_zoom_buttons()
        self._apply_compare_view_state()

    def _is_slider_mode(self) -> bool:
        return self.get_compare_mode() == "slider"

    def _update_slider_from_event(self, event) -> None:
        preview_width, _preview_height = self._get_preview_size(event.widget)

        if preview_width <= 0:
            return

        self.compare_controller.set_slider_position(event.x / preview_width)
        self._apply_compare_view_state()

    def _reset_slider_position(self, event=None) -> None:
        self.compare_controller.set_slider_position(0.5)
        self._apply_compare_view_state()

    def _update_compare_cursor(self) -> None:
        cursor = "sb_h_double_arrow" if self._is_slider_mode() else ""

        if hasattr(self, "preview_label"):
            self.preview_label.configure(cursor=cursor)

        if hasattr(self, "output_preview_label"):
            self.output_preview_label.configure(cursor=cursor)

    def _is_pan_enabled(self) -> bool:
        return self.compare_controller.is_pan_enabled()

    def _clamp_pan_state(self) -> None:
        self.compare_controller.clamp_pan()

    def _get_widget_pan_bounds(self, target_label: tk.Label) -> tuple[int, int]:
        if target_label == self.output_preview_label:
            image = self.output_display_image
        else:
            image = self.original_display_image

        if image is None:
            return (0, 0)

        return self.compare_renderer.get_pan_bounds(
            image,
            self._get_preview_size(target_label),
        )

    def _set_zoom_mode(self, zoom_mode: str) -> None:
        self.compare_controller.set_zoom_mode(zoom_mode)
        self._update_zoom_buttons()
        self._apply_compare_view_state()

    def _set_compare_mode(self, compare_mode: str) -> None:
        self.set_compare_mode(compare_mode)

    def _set_zoom_percent(self, value: str) -> None:
        if self._syncing_zoom_controls:
            return

        zoom_percent = int(float(value))
        self.compare_controller.zoom_to(zoom_percent / 100)
        self._update_zoom_buttons()
        self._apply_compare_view_state()

    def _update_zoom_buttons(self) -> None:
        selected_border = getattr(PHOENIX_THEME, "accent", "#3B82F6")

        for mode, button in self.zoom_buttons.items():
            if mode == self.zoom_mode:
                button.configure(
                    fg=PHOENIX_THEME.text_primary,
                    highlightbackground=selected_border,
                )
            else:
                button.configure(
                    fg=PHOENIX_THEME.text_secondary,
                    highlightbackground=PHOENIX_THEME.border,
                )

        if hasattr(self, "zoom_slider"):
            self._syncing_zoom_controls = True
            self.zoom_slider.set(int(self.zoom_level * 100))
            self._syncing_zoom_controls = False

        if hasattr(self, "zoom_value_label"):
            if self.zoom_mode == "fit":
                self.zoom_value_label.configure(text="Zoom: Fit")
            else:
                self.zoom_value_label.configure(text=f"Zoom: {int(self.zoom_level * 100)} %")

    def _update_compare_mode_buttons(self) -> None:
        selected_border = getattr(PHOENIX_THEME, "accent", "#3B82F6")
        current_mode = self.get_compare_mode()

        for mode, button in self.compare_mode_buttons.items():
            if mode == current_mode:
                button.configure(
                    fg=PHOENIX_THEME.text_primary,
                    highlightbackground=selected_border,
                )
            else:
                button.configure(
                    fg=PHOENIX_THEME.text_secondary,
                    highlightbackground=PHOENIX_THEME.border,
                )

    def _get_preview_size(self, target_label: tk.Label) -> tuple[int, int]:
        target_label.update_idletasks()
        preview_width = target_label.winfo_width()
        preview_height = target_label.winfo_height()

        if preview_width <= 1 or preview_height <= 1:
            preview_width = 420
            preview_height = 360

        return (preview_width, preview_height)

    def set_gallery_images(self, filenames: list[str | Path]) -> None:
        self._clear_gallery()

        for filename in filenames:
            image_path = Path(filename)

            if image_path.exists():
                self._add_gallery_thumbnail(image_path)

    def get_selected_image_path(self) -> Path | None:
        return self.selected_gallery_path

    def get_selected_image_paths(self) -> list[Path]:
        return list(self.selected_image_paths)

    def _clear_gallery(self) -> None:
        self.gallery_thumbnail_images.clear()
        self.gallery_thumbnail_cards.clear()
        self.selected_gallery_path = None
        self.selected_image_paths.clear()

        for child in self.gallery_content.winfo_children():
            child.destroy()

    def _sync_gallery_canvas(self, event=None) -> None:
        if self.gallery_window_id is not None:
            self.gallery_canvas.itemconfigure(
                self.gallery_window_id,
                width=self.gallery_canvas.winfo_width(),
            )

        self._relayout_gallery()

    def _get_gallery_column_count(self) -> int:
        canvas_width = self.gallery_canvas.winfo_width()

        if canvas_width <= 1:
            canvas_width = 720

        return max(1, canvas_width // 136)

    def _relayout_gallery(self) -> None:
        columns = self._get_gallery_column_count()

        for index, child in enumerate(self.gallery_content.winfo_children()):
            child.grid_configure(
                row=index // columns,
                column=index % columns,
            )

    def _set_selected_gallery_thumbnail(self, image_path: Path, selected_card: tk.Frame) -> None:
        self.selected_gallery_path = image_path
        self.selected_image_paths = [image_path]
        selected_border = getattr(PHOENIX_THEME, "accent", "#3B82F6")

        for card in self.gallery_thumbnail_cards:
            card.configure(highlightbackground=PHOENIX_THEME.border)

        selected_card.configure(highlightbackground=selected_border)

    def _add_gallery_thumbnail(self, image_path: Path) -> None:
        thumbnail = self._load_thumbnail_image(image_path)
        photo_image = ImageTk.PhotoImage(thumbnail)
        thumbnail_index = len(self.gallery_thumbnail_images)
        self.gallery_thumbnail_images.append(photo_image)
        column_count = self._get_gallery_column_count()

        card = tk.Frame(
            self.gallery_content,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            width=120,
            height=128,
        )
        card.grid(
            row=thumbnail_index // column_count,
            column=thumbnail_index % column_count,
            sticky="nsew",
            padx=(0, 12),
            pady=(0, 12),
        )
        card.pack_propagate(False)
        self.gallery_thumbnail_cards.append(card)

        thumbnail_label = tk.Label(
            card,
            image=photo_image,
            bg=PHOENIX_THEME.card_bg,
            anchor="center",
        )
        thumbnail_label.pack(fill="both", expand=True, padx=12, pady=(12, 4))

        filename_label = tk.Label(
            card,
            text=image_path.name,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 8),
            anchor="center",
            wraplength=96,
        )
        filename_label.pack(fill="x", padx=10, pady=(0, 10))

        def select_thumbnail(event, selected_path=image_path):
            self._set_selected_gallery_thumbnail(selected_path, card)
            self.show_image(selected_path)
            if callable(self.on_gallery_select):
                self.on_gallery_select(selected_path)

        card.bind("<Button-1>", select_thumbnail)
        thumbnail_label.bind("<Button-1>", select_thumbnail)
        filename_label.bind("<Button-1>", select_thumbnail)
        self._relayout_gallery()

    def _load_thumbnail_image(self, image_path: Path) -> Image.Image:
        image = self._load_display_image(image_path)
        image.thumbnail((96, 96))
        return image

    def clear_image(self) -> None:
        self.current_image_path = None
        self.preview_image = None
        self.output_preview_image = None
        self.original_display_image = None
        self.output_display_image = None
        self.compare_controller.set_images(None, None)
        self._reset_compare_view_state()
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
