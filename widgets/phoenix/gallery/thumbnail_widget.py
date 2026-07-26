from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from controllers.gallery_model import GalleryImage
from resources.icons import IconManager
from widgets.phoenix.theme import PHOENIX_THEME


class ThumbnailWidget(tk.Frame):
    """Single selectable thumbnail card with resolution and format display."""

    # Klassenkonstanten zur Vermeidung von Magic Numbers und für besseren Unterhalt
    PLACEHOLDER_ICON_SIZE = 28
    MIN_WRAP_LENGTH = 96
    MAX_FILENAME_DISPLAY_LENGTH = 28
    TRUNCATED_LENGTH_NO_EXTENSION = 25
    TRUNCATED_STEM_LENGTH = 20

    def __init__(
        self,
        master: tk.Misc,
        image: GalleryImage,
        thumbnail_image: tk.PhotoImage | None,
        size: int,
        selected: bool,
        command: Callable[[GalleryImage, tk.Event], None],
        double_command: Callable[[GalleryImage], None],
        right_click_command: Callable[[GalleryImage, tk.Event], None] | None = None,
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.elevated_bg,
            highlightbackground=PHOENIX_THEME.accent if selected else PHOENIX_THEME.border,
            highlightthickness=2 if selected else 1,
        )
        self.image = image
        self.thumbnail_image = thumbnail_image
        self.command = command
        self.double_command = double_command
        self.right_click_command = right_click_command
        self.size = size
        self.selected = selected
        self._build()
        self._bind_events(self)

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # 0. Vorschaubereich (Bild oder Platzhaltersymbol)
        preview = tk.Frame(
            self,
            bg=PHOENIX_THEME.card_bg,
            width=self.size,
            height=self.size,
        )
        preview.grid(
            row=0,
            column=0,
            padx=PHOENIX_THEME.space_sm,
            pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.space_xs),
        )
        preview.grid_propagate(False)
        preview.grid_columnconfigure(0, weight=1)
        preview.grid_rowconfigure(0, weight=1)

        if self.thumbnail_image is None:
            self.image_label = tk.Label(
                preview,
                text=IconManager.get_symbol("gallery"),
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=(PHOENIX_THEME.font_title[0], self.PLACEHOLDER_ICON_SIZE),
            )
        else:
            self.image_label = tk.Label(
                preview,
                image=self.thumbnail_image,
                bg=PHOENIX_THEME.card_bg,
                bd=0,
            )
        self.image_label.grid(row=0, column=0)
        self._bind_events(preview)
        self._bind_events(self.image_label)

        # 1. Dateiname
        self.name_label = tk.Label(
            self,
            text=self._short_filename(self.image.filename),
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary if self.selected else PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="center",
            justify="center",
            wraplength=max(self.MIN_WRAP_LENGTH, self.size + PHOENIX_THEME.space_md),
        )
        self.name_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_sm,
            pady=(PHOENIX_THEME.space_xs, 0),
        )
        self._bind_events(self.name_label)

        # 2. Auflösung
        res_text = self.image.resolution_label
        res_label = tk.Label(
            self,
            text=res_text,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="center",
        )
        res_label.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_sm,
            pady=0,
        )
        self._bind_events(res_label)

        # 3. Format
        fmt_text = self.image.format_label
        fmt_label = tk.Label(
            self,
            text=fmt_text,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="center",
        )
        fmt_label.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_sm,
            pady=(0, PHOENIX_THEME.space_sm),
        )
        self._bind_events(fmt_label)

    def _bind_events(self, widget: tk.Widget) -> None:
        widget.bind("<Button-1>", self._on_click)
        widget.bind("<Double-Button-1>", self._on_double_click)
        widget.bind("<Button-3>", self._on_right_click)
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)

    def _on_click(self, event: tk.Event) -> str:
        try:
            if hasattr(self, "_hover_preview") and self._hover_preview:
                self._hover_preview.destroy()
                self._hover_preview = None
        except Exception:
            pass
        self.command(self.image, event)
        return "break"

    def _on_double_click(self, _event: tk.Event) -> str:
        try:
            if hasattr(self, "_hover_preview") and self._hover_preview:
                self._hover_preview.destroy()
                self._hover_preview = None
        except Exception:
            pass
        self.double_command(self.image)
        return "break"

    def _on_right_click(self, event: tk.Event) -> str:
        if self.right_click_command is not None:
            self.right_click_command(self.image, event)
        return "break"

    def _on_enter(self, event: tk.Event) -> None:
        if not self.selected:
            self.configure(highlightbackground=PHOENIX_THEME.accent)

        try:
            if hasattr(self, "_hover_preview") and self._hover_preview:
                self._hover_preview.destroy()
        except Exception:
            pass
        self._hover_preview = None

        if self.thumbnail_image is None or not self.image.path.is_file():
            return

        try:
            preview_win = tk.Toplevel(self)
            preview_win.withdraw()
            preview_win.overrideredirect(True)
            preview_win.configure(bg=PHOENIX_THEME.border, padx=1, pady=1)

            from PIL import Image, ImageTk
            with Image.open(self.image.path) as img:
                img.thumbnail((480, 480))
                thumb_w, thumb_h = img.size
                zoom_photo = ImageTk.PhotoImage(img.copy())

            preview_win.zoom_photo = zoom_photo
            lbl = tk.Label(preview_win, image=zoom_photo, bg=PHOENIX_THEME.card_bg, bd=0)
            lbl.pack()

            # Calculate safe placement within screen boundaries
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            win_w = thumb_w + 2
            win_h = thumb_h + 2

            # Offset position relative to cursor
            x = event.x_root + 20
            y = event.y_root + 20

            # Wrap horizontally
            if x + win_w > screen_w:
                x = event.x_root - win_w - 20
            if x < 0:
                x = 10

            # Wrap vertically
            if y + win_h > screen_h:
                y = event.y_root - win_h - 20
            if y < 0:
                y = 10

            preview_win.geometry(f"{win_w}x{win_h}+{x}+{y}")
            preview_win.deiconify()
            self._hover_preview = preview_win
        except Exception:
            pass

    def _on_leave(self, _event: tk.Event) -> None:
        if not self.selected:
            self.configure(highlightbackground=PHOENIX_THEME.border)

        try:
            if hasattr(self, "_hover_preview") and self._hover_preview:
                self._hover_preview.destroy()
        except Exception:
            pass
        self._hover_preview = None

    def _short_filename(self, filename: str) -> str:
        if len(filename) <= self.MAX_FILENAME_DISPLAY_LENGTH:
            return filename
        stem, dot, suffix = filename.rpartition(".")
        if not dot:
            return f"{filename[:self.TRUNCATED_LENGTH_NO_EXTENSION]}..."
        return f"{stem[:self.TRUNCATED_STEM_LENGTH]}...{suffix}"

    def set_thumbnail(self, thumbnail_image: ImageTk.PhotoImage) -> None:
        """Dynamically updates the thumbnail image on the card, replacing placeholder."""
        self.thumbnail_image = thumbnail_image
        self.image_label.configure(
            image=self.thumbnail_image,
            text="",
            font=None,
        )

    def set_selected(self, selected: bool) -> None:
        """Update selection styling without rebuilding or reloading the thumbnail."""
        self.selected = selected
        self.configure(
            highlightbackground=PHOENIX_THEME.accent if selected else PHOENIX_THEME.border,
            highlightthickness=2 if selected else 1,
        )
        self.name_label.configure(
            fg=PHOENIX_THEME.text_primary if selected else PHOENIX_THEME.text_secondary,
        )

    def destroy(self) -> None:
        """Releases the PhotoImage reference immediately to free memory."""
        try:
            if hasattr(self, "_hover_preview") and self._hover_preview:
                self._hover_preview.destroy()
        except Exception:
            pass
        self._hover_preview = None
        self.thumbnail_image = None
        if hasattr(self, "image_label"):
            self.image_label = None
        super().destroy()
