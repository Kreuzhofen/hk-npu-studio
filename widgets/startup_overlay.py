from __future__ import annotations

import tkinter as tk
from typing import Optional

from PIL import ImageTk

from engine.brand_manager import BrandManager
from app.i18n import tr


class StartupOverlay(tk.Toplevel):
    def __init__(self, master: tk.Misc, brand: BrandManager) -> None:
        super().__init__(
            master,
            bg=brand.color("COLOR_BACKGROUND"),
            highlightthickness=0,
            bd=0,
        )

        # Intercept master deiconify to keep main window hidden during splash screen
        self._orig_deiconify = master.deiconify
        master.deiconify = lambda: None

        self.overrideredirect(True)
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

        self.logo_image = ImageTk.PhotoImage(self.brand.logo_image(128))
        self.logo_label = tk.Label(
            container,
            image=self.logo_image,
            bg=self.brand.color("COLOR_BACKGROUND"),
            bd=0,
        )
        self.logo_label.pack(pady=(16, 12))

        self.title_label = tk.Label(
            container,
            text=self.brand.app_name(),
            font=(self.brand.font("FONT_TITLE"), 30, "bold"),
            fg=self.brand.color("COLOR_TEXT"),
            bg=self.brand.color("COLOR_BACKGROUND"),
        )
        self.title_label.pack(pady=(0, 4))

        self.slogan_label = tk.Label(
            container,
            text=self.brand.slogan(),
            font=(self.brand.font("FONT_BODY"), 13),
            fg=self.brand.color("COLOR_TEXT_SECONDARY"),
            bg=self.brand.color("COLOR_BACKGROUND"),
        )
        self.slogan_label.pack(pady=(4, 4))

        self.copyright_label = tk.Label(
            container,
            text=self.brand.copyright(),
            font=(self.brand.font("FONT_BODY"), 10),
            fg=self.brand.color("COLOR_TEXT_SECONDARY"),
            bg=self.brand.color("COLOR_BACKGROUND"),
        )
        self.copyright_label.pack(pady=(0, 16))

        self.status_label = tk.Label(
            container,
            text=tr(
                "initializing_engine",
                "{engine} wird initialisiert...",
                engine=self.brand.engine_name(),
            ),
            font=(self.brand.font("FONT_BODY"), 12),
            fg=self.brand.color("COLOR_TEXT"),
            bg=self.brand.color("COLOR_BACKGROUND"),
        )
        self.status_label.pack(pady=(8, 6))

        self.progress_canvas = tk.Canvas(
            container,
            width=360,
            height=8,
            bg=self.brand.color("COLOR_BACKGROUND"),
            highlightthickness=0,
            bd=0,
        )
        self.progress_canvas.pack(pady=(0, 12))

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
        self.version_label.pack(pady=(12, 16))

    def show(self) -> None:
        # Define reasonable splash size and center it on screen
        width = 600
        height = 420
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.lift()
        self.focus_force()
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
            # Restore original deiconify and show the main window
            if hasattr(self.master, "deiconify"):
                self.master.deiconify = self._orig_deiconify
                self.master.deiconify()
            self.destroy()
            return

        try:
            # Apply smooth alpha transparency fading on supported platforms
            alpha = 1.0 - (self._fade_step / 8.0)
            self.attributes("-alpha", alpha)
        except Exception:
            pass

        self.after(35, self._fade)
