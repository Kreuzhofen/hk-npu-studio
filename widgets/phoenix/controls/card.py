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

        x_min = 1
        x_max = w - 1
        y_min = 1
        y_max = h - 1

        r = self.radius
        r = min(r, (x_max - x_min) // 2, (y_max - y_min) // 2)

        # Draw rounded rectangle polygon within the visible canvas boundaries (0 to w-1, 0 to h-1)
        points = [
            x_min + r, y_min, x_min + r, y_min,
            x_max - r, y_min, x_max - r, y_min,
            x_max, y_min,
            x_max, y_min + r, x_max, y_min + r,
            x_max, y_max - r, x_max, y_max - r,
            x_max, y_max,
            x_max - r, y_max, x_max - r, y_max,
            x_min + r, y_max, x_min + r, y_max,
            x_min, y_max,
            x_min, y_max - r, x_min, y_max - r,
            x_min, y_min + r, x_min, y_min + r,
            x_min, y_min
        ]

        self.create_polygon(
            points,
            fill=self.fill_color,
            outline=self.border_color,
            width=1,
            smooth=True,
            tags="bg"
        )
