"""
HK NPU STUDIO

Unified Studio Dialog Foundation

Created by Holger Kreuzhofen
Phoenix UI
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import tkinter as tk

from PIL import ImageTk

from engine.brand_manager import BrandManager
from widgets.phoenix.theme import PHOENIX_THEME


class StudioDialog(tk.Toplevel):
    """Shared dialog foundation for HK NPU STUDIO."""

    DEFAULT_SIZE = (520, 360)
    MIN_SIZE = (420, 280)
    WORK_AREA_MARGIN = (32, 48)

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str,
        brand: BrandManager | None = None,
        size: tuple[int, int] | None = None,
        min_size: tuple[int, int] | None = None,
        resizable: bool = False,
    ) -> None:
        super().__init__(master)

        self.brand = brand or getattr(master, "brand", BrandManager())
        self.work_area = self._get_work_area()
        self.dialog_size, self.dialog_min_size = self._fit_to_work_area(
            size or self.DEFAULT_SIZE,
            min_size or self.MIN_SIZE,
            self.work_area,
        )
        self._dialog_images: list[ImageTk.PhotoImage] = []

        self.title(title)
        BrandManager.apply_window_icon(self)
        self.configure(bg=PHOENIX_THEME.app_bg)
        self.minsize(*self.dialog_min_size)
        self.resizable(resizable, resizable)
        self.transient(master)
        self.grab_set()

        self.container = tk.Frame(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.container.pack(
            fill="both",
            expand=True,
            padx=PHOENIX_THEME.space_lg,
            pady=PHOENIX_THEME.space_lg,
        )
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=0)

        self.body = tk.Frame(self.container, bg=PHOENIX_THEME.card_bg)
        self.body.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=PHOENIX_THEME.space_xl,
            pady=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_md),
        )

        self.footer = tk.Frame(self.container, bg=PHOENIX_THEME.card_bg)
        self.footer.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_xl,
            pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.space_lg),
        )

        self.bind("<Escape>", lambda _event: self.close())
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _get_work_area(self) -> tuple[int, int, int, int]:
        try:
            rect = wintypes.RECT()
            if ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0):
                return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
        except (AttributeError, OSError):
            pass
        return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

    @classmethod
    def _fit_to_work_area(
        cls,
        size: tuple[int, int],
        min_size: tuple[int, int],
        work_area: tuple[int, int, int, int],
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        _, _, work_width, work_height = work_area
        margin_width, margin_height = cls.WORK_AREA_MARGIN
        max_width = max(1, work_width - margin_width)
        max_height = max(1, work_height - margin_height)
        return (
            (min(size[0], max_width), min(size[1], max_height)),
            (min(min_size[0], max_width), min(min_size[1], max_height)),
        )

    def add_title(self, title: str, subtitle: str | None = None) -> tk.Frame:
        title_frame = tk.Frame(self.body, bg=PHOENIX_THEME.card_bg)
        title_frame.pack(fill="x", pady=(0, PHOENIX_THEME.space_lg))

        tk.Label(
            title_frame,
            text=title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).pack(fill="x")

        if subtitle:
            tk.Label(
                title_frame,
                text=subtitle,
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_small,
                anchor="w",
            ).pack(fill="x", pady=(PHOENIX_THEME.space_xs, 0))

        return title_frame

    def add_card(self, master: tk.Misc | None = None) -> tk.Frame:
        parent = master or self.body
        card = tk.Frame(
            parent,
            bg=PHOENIX_THEME.elevated_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        card.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))
        return card

    def add_separator(self, master: tk.Misc | None = None) -> tk.Frame:
        parent = master or self.body
        separator = tk.Frame(parent, bg=PHOENIX_THEME.border, height=1)
        separator.pack(fill="x", pady=(0, PHOENIX_THEME.space_lg))
        return separator

    def add_footer_button(self, text: str, command) -> tk.Button:
        button = tk.Button(
            self.footer,
            text=text,
            command=command,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground=PHOENIX_THEME.text_on_accent,
            disabledforeground=PHOENIX_THEME.text_disabled,
            relief="flat",
            bd=0,
            padx=PHOENIX_THEME.button_pad_x,
            pady=PHOENIX_THEME.button_pad_y,
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            width=12,
        )
        button.pack(anchor="center")
        return button

    def load_logo_image(self, size: int) -> ImageTk.PhotoImage | None:
        image = ImageTk.PhotoImage(self.brand.logo_image(size))
        self._dialog_images.append(image)
        return image

    def center(self, master: tk.Misc) -> None:
        self.update_idletasks()

        width, height = self.dialog_size
        master_x = master.winfo_rootx()
        master_y = master.winfo_rooty()
        master_width = master.winfo_width()
        master_height = master.winfo_height()

        x = master_x + (master_width // 2) - (width // 2)
        y = master_y + (master_height // 2) - (height // 2)
        work_x, work_y, work_width, work_height = self.work_area
        x = max(work_x, min(x, work_x + work_width - width))
        y = max(work_y, min(y, work_y + work_height - height))

        self.geometry(f"{width}x{height}+{x}+{y}")

    def close(self) -> None:
        self.destroy()
