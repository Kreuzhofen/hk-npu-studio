from __future__ import annotations

import tkinter as tk
from typing import Optional

from engine.brand_manager import BrandManager


class StartupOverlay(tk.Frame):
    def __init__(self, master: tk.Misc, brand: BrandManager) -> None:
        super().__init__(
            master,
            bg=brand.color("COLOR_BACKGROUND"),
            highlightthickness=0,
            bd=0,
        )

        self.brand = brand
        self._progress = 0
        self._fade_step = 0
        self._progress_job: Optional[str] = None
        self.logo_image: tk.PhotoImage | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = tk.Frame(
            self,
            bg=self.brand.color("COLOR_BACKGROUND"),
        )
        container.grid(row=0, column=0)

        logo_path = self.brand.png(128)
        if logo_path.exists():
            self.logo_image = tk.PhotoImage(file=str(logo_path))
            self.logo_label = tk.Label(
                container,
                image=self.logo_image,
                bg=self.brand.color("COLOR_BACKGROUND"),
                bd=0,
            )
        else:
            self.logo_label = tk.Label(
                container,
                text=self.brand.app_name()[:1],
                font=(self.brand.font("FONT_TITLE"), 64, "bold"),
                fg=self.brand.color("COLOR_PRIMARY"),
                bg=self.brand.color("COLOR_BACKGROUND"),
            )
        self.logo_label.pack(pady=(0, 20))

        self.title_label = tk.Label(
            container,
            text=self.brand.app_name(),
            font=(self.brand.font("FONT_TITLE"), 30, "bold"),
            fg=self.brand.color("COLOR_TEXT"),
            bg=self.brand.color("COLOR_BACKGROUND"),
        )
        self.title_label.pack()

        self.slogan_label = tk.Label(
            container,
            text=self.brand.slogan(),
            font=(self.brand.font("FONT_BODY"), 13),
            fg=self.brand.color("COLOR_TEXT_SECONDARY"),
            bg=self.brand.color("COLOR_BACKGROUND"),
        )
        self.slogan_label.pack(pady=(8, 8))

        self.copyright_label = tk.Label(
            container,
            text=self.brand.copyright(),
            font=(self.brand.font("FONT_BODY"), 10),
            fg=self.brand.color("COLOR_TEXT_SECONDARY"),
            bg=self.brand.color("COLOR_BACKGROUND"),
        )
        self.copyright_label.pack(pady=(0, 32))

        self.status_label = tk.Label(
            container,
            text=f"Initializing {self.brand.engine_name()}...",
            font=(self.brand.font("FONT_BODY"), 12),
            fg=self.brand.color("COLOR_TEXT"),
            bg=self.brand.color("COLOR_BACKGROUND"),
        )
        self.status_label.pack(pady=(0, 12))

        self.progress_canvas = tk.Canvas(
            container,
            width=360,
            height=8,
            bg=self.brand.color("COLOR_BACKGROUND"),
            highlightthickness=0,
            bd=0,
        )
        self.progress_canvas.pack()

        self.progress_bg = self.progress_canvas.create_rectangle(
            0,
            0,
            360,
            8,
            fill=self.brand.color("COLOR_SURFACE"),
            outline="",
        )

        self.progress_fg = self.progress_canvas.create_rectangle(
            0,
            0,
            0,
            8,
            fill=self.brand.color("COLOR_PRIMARY"),
            outline="",
        )

        self.version_label = tk.Label(
            container,
            text=self.brand.version_string(),
            font=(self.brand.font("FONT_SMALL"), 10),
            fg=self.brand.color("COLOR_TEXT_SECONDARY"),
            bg=self.brand.color("COLOR_BACKGROUND"),
        )
        self.version_label.pack(pady=(24, 0))

    def show(self) -> None:
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self._progress = 0
        self._animate_progress()

    def fade_out(self) -> None:
        if self._progress_job is not None:
            self.after_cancel(self._progress_job)
            self._progress_job = None

        self._fade_step = 0
        self._fade()

    def _animate_progress(self) -> None:
        self._progress = min(self._progress + 4, 100)
        width = int(360 * (self._progress / 100))

        self.progress_canvas.coords(
            self.progress_fg,
            0,
            0,
            width,
            8,
        )

        if self._progress < 100:
            self._progress_job = self.after(45, self._animate_progress)
        else:
            self._progress_job = None

    def _fade(self) -> None:
        self._fade_step += 1

        if self._fade_step >= 8:
            self.destroy()
            return

        self.after(35, self._fade)
