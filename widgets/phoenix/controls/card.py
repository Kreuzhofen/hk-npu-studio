from __future__ import annotations

import tkinter as tk
from widgets.phoenix.theme import PHOENIX_THEME

class PhoenixCard(tk.Canvas):
    """
    A premium card container widget with rounded corners and a fine border.
    Behaves like a tk.Frame but draws a modern rounded container background.
    """

    def __init__(
        self,
        master: tk.Misc,
        bg: str | None = None,
        border_color: str | None = None,
        radius: int = 10,
        **kwargs
    ) -> None:
        self.radius = radius
        self.fill_color = bg or PHOENIX_THEME.card_bg
        self.border_color = border_color or PHOENIX_THEME.border
        
        # Determine behind-card background to mask corners properly
        parent_bg = PHOENIX_THEME.content_bg
        if hasattr(master, "cget"):
            try:
                parent_bg = master.cget("bg")
            except Exception:
                pass

        # Pop standard border parameters to prevent duplicate keyword arguments
        for k in ["bd", "borderwidth"]:
            kwargs.pop(k, None)

        super().__init__(
            master,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            **kwargs
        )

        self.bind("<Configure>", lambda e: self._redraw())
        self._redraw()

    def configure(self, **kwargs) -> None:
        if "bg" in kwargs:
            self.fill_color = kwargs.pop("bg")
        if "border_color" in kwargs:
            self.border_color = kwargs.pop("border_color")
        if "highlightbackground" in kwargs:
            self.border_color = kwargs.pop("highlightbackground")
        if "radius" in kwargs:
            self.radius = kwargs.pop("radius")
        super().configure(**kwargs)
        self._redraw()

    config = configure

    def cget(self, key: str) -> Any:
        if key in ("bg", "background"):
            return self.fill_color
        return super().cget(key)

    def _redraw(self) -> None:
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        
        if w < 2 or h < 2:
            return

        r = self.radius
        r = min(r, w // 2, h // 2)

        # Draw rounded rectangle polygon
        points = [
            r, 0, r, 0,
            w - r, 0, w - r, 0,
            w, 0,
            w, r, w, r,
            w, h - r, w, h - r,
            w, h,
            w - r, h, w - r, h,
            r, h, r, h,
            0, h,
            0, h - r, 0, h - r,
            0, r, 0, r,
            0, 0
        ]

        self.create_polygon(
            points,
            fill=self.fill_color,
            outline=self.border_color,
            width=1,
            smooth=True,
            tags="bg"
        )
