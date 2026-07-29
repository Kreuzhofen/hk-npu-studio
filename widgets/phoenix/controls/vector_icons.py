from __future__ import annotations

import tkinter as tk
from typing import Any
from widgets.phoenix.theme import PHOENIX_THEME

def draw_vector_icon(
    canvas: tk.Canvas,
    name: str,
    x: float,
    y: float,
    size: float,
    color: str,
    stroke_width: float = 1.6
) -> list[int]:
    """
    Draws a vector icon on a canvas centered at (x, y) with a given bounding size and color.
    Returns the canvas item IDs.
    """
    ids = []
    r = size / 2.0
    
    # Normalize name
    name = name.lower().strip().replace("-", "_").replace(" ", "_")
    if name == "prompt" or name == "ai_generate" or name == "generate":
        name = "start"
    elif name == "models" or name == "model_manager" or name == "ai_model_manager":
        name = "grid"
    elif name == "trash" or name == "delete_preset" or name == "remove":
        name = "delete"
    elif name == "import":
        name = "load_image"
        
    if name == "close" or name == "remove_image":
        # Draw an 'X'
        d = r * 0.7
        ids.append(canvas.create_line(x - d, y - d, x + d, y + d, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x + d, y - d, x - d, y + d, fill=color, width=stroke_width, capstyle="round"))
        
    elif name == "back":
        # Draw a left arrow
        d = r * 0.7
        ids.append(canvas.create_line(x - d, y, x + d, y, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x - d, y, x - d + d*0.5, y - d*0.5, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x - d, y, x - d + d*0.5, y + d*0.5, fill=color, width=stroke_width, capstyle="round"))
        
    elif name == "forward":
        # Draw a right arrow
        d = r * 0.7
        ids.append(canvas.create_line(x - d, y, x + d, y, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x + d, y, x + d - d*0.5, y - d*0.5, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x + d, y, x + d - d*0.5, y + d*0.5, fill=color, width=stroke_width, capstyle="round"))
        
    elif name == "home" or name == "dashboard":
        # Draw a house
        d = r * 0.8
        # Roof
        ids.append(canvas.create_line(x - d, y, x, y - d, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x, y - d, x + d, y, fill=color, width=stroke_width, capstyle="round"))
        # Walls
        ids.append(canvas.create_line(x - d + 2, y, x - d + 2, y + d, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x + d - 2, y, x + d - 2, y + d, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x - d + 2, y + d, x + d - 2, y + d, fill=color, width=stroke_width, capstyle="round"))

    elif name == "start" or name == "play":
        # Draw play triangle
        d = r * 0.7
        points = [
            x - d * 0.5, y - d,
            x + d * 0.8, y,
            x - d * 0.5, y + d
        ]
        ids.append(canvas.create_polygon(points, outline=color, fill="", width=stroke_width, joinstyle="round"))

    elif name == "stop":
        # Draw square
        d = r * 0.7
        ids.append(canvas.create_rectangle(x - d, y - d, x + d, y + d, outline=color, fill="", width=stroke_width))

    elif name == "settings":
        # Draw a gear shape
        from engine.theme_manager import ThemeManager
        draw_color = color
        if ThemeManager.active_theme() == ThemeManager.PROFESSIONAL_LIGHT and color == PHOENIX_THEME.text_secondary:
            draw_color = PHOENIX_THEME.text_primary

        # Inner circle
        ids.append(canvas.create_oval(x - r*0.3, y - r*0.3, x + r*0.3, y + r*0.3, outline=draw_color, fill="", width=stroke_width))
        # Outer circle
        ids.append(canvas.create_oval(x - r*0.65, y - r*0.65, x + r*0.65, y + r*0.65, outline=draw_color, fill="", width=stroke_width))
        # Spokes (8 spokes around)
        import math
        for i in range(8):
            angle = i * math.pi / 4
            x1 = x + math.cos(angle) * r*0.65
            y1 = y + math.sin(angle) * r*0.65
            x2 = x + math.cos(angle) * r*0.85
            y2 = y + math.sin(angle) * r*0.85
            ids.append(canvas.create_line(x1, y1, x2, y2, fill=draw_color, width=stroke_width * 1.5, capstyle="round"))

    elif name == "plugins":
        # Draw double diamonds (premium plugins style)
        d = r * 0.7
        points1 = [x, y - d, x + d*0.7, y - d*0.3, x, y + d*0.4, x - d*0.7, y - d*0.3]
        points2 = [x, y - d*0.1, x + d*0.7, y + d*0.5, x, y + d*1.1, x - d*0.7, y + d*0.5]
        ids.append(canvas.create_polygon(points1, outline=color, fill="", width=stroke_width))
        ids.append(canvas.create_polygon(points2, outline=color, fill="", width=stroke_width))

    elif name == "gallery" or name == "image":
        # Draw overlapping photo frame vectors
        d = r * 0.8
        # Background frame offset
        ids.append(canvas.create_rectangle(x - d + 3, y - d - 1, x + d - 1, y + d - 5, outline=color, fill="", width=stroke_width))
        # Foreground frame
        ids.append(canvas.create_rectangle(x - d + 1, y - d + 3, x + d - 3, y + d - 1, outline=color, fill="", width=stroke_width))
        # Little circle for sun
        ids.append(canvas.create_oval(x - d + 5, y - d + 7, x - d + 8, y - d + 10, outline=color, fill="", width=stroke_width))
        # Mountain peaks
        points = [
            x - d + 3, y + d - 2,
            x - d + 8, y - d + 14,
            x + d - 10, y + d - 2
        ]
        ids.append(canvas.create_line(x - d + 3, y + d - 2, x - d + 10, y + d - 8, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x - d + 10, y + d - 8, x + d - 5, y + d - 2, fill=color, width=stroke_width))

    elif name == "compare":
        # Two panes split icon
        d = r * 0.8
        ids.append(canvas.create_rectangle(x - d, y - d, x + d, y + d, outline=color, fill="", width=stroke_width))
        ids.append(canvas.create_line(x, y - d, x, y + d, fill=color, width=stroke_width))

    elif name == "grid" or name == "model_manager":
        # Draw grid / NPU qualifications capsule servers
        d = r * 0.85
        # Draw 3 server stack bars
        ids.append(canvas.create_rectangle(x - d, y - d*0.7, x + d, y - d*0.2, outline=color, fill="", width=stroke_width))
        ids.append(canvas.create_rectangle(x - d, y - d*0.1, x + d, y + d*0.4, outline=color, fill="", width=stroke_width))
        ids.append(canvas.create_rectangle(x - d, y + d*0.5, x + d, y + d*1.0, outline=color, fill="", width=stroke_width))
        # Little indicator dots
        ids.append(canvas.create_oval(x - d + 4, y - d*0.55, x - d + 6, y - d*0.35, outline=color, fill=color, width=1))
        ids.append(canvas.create_oval(x - d + 4, y - d*0.0, x - d + 6, y + d*0.2, outline=color, fill=color, width=1))
        ids.append(canvas.create_oval(x - d + 4, y + d*0.6, x - d + 6, y + d*0.8, outline=color, fill=color, width=1))

    elif name == "refresh":
        # Circular arrow
        d = r * 0.7
        ids.append(canvas.create_arc(x - d, y - d, x + d, y + d, start=50, extent=280, outline=color, fill="", width=stroke_width, style="arc"))
        # Arrow head
        import math
        angle = 50 * math.pi / 180
        ax = x + math.cos(angle) * d
        ay = y - math.sin(angle) * d
        ids.append(canvas.create_line(ax, ay, ax + 4, ay, fill=color, width=stroke_width))
        ids.append(canvas.create_line(ax, ay, ax, ay + 4, fill=color, width=stroke_width))

    elif name == "folder":
        # Folder shape
        d = r * 0.8
        points = [
            x - d, y - d + 3,
            x - d + 4, y - d + 3,
            x - d + 8, y - d + 7,
            x + d, y - d + 7,
            x + d, y + d,
            x - d, y + d
        ]
        ids.append(canvas.create_polygon(points, outline=color, fill="", width=stroke_width, joinstyle="miter"))

    elif name == "open_folder":
        # Open folder shape
        d = r * 0.8
        ids.append(canvas.create_line(x - d, y - d + 3, x - d + 4, y - d + 3, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x - d + 4, y - d + 3, x - d + 8, y - d + 7, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x - d + 8, y - d + 7, x + d, y - d + 7, fill=color, width=stroke_width))
        # Front flap open
        flap = [
            x - d, y - d + 7,
            x - d + 3, y + d,
            x + d - 3, y + d,
            x + d, y - d + 7
        ]
        ids.append(canvas.create_polygon(flap, outline=color, fill="", width=stroke_width))

    elif name == "load_image":
        # Box with arrow pointing in
        d = r * 0.8
        # Box outline (bottom, sides)
        ids.append(canvas.create_line(x - d, y - d + 5, x - d, y + d, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x - d, y + d, x + d, y + d, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x + d, y + d, x + d, y - d + 5, fill=color, width=stroke_width))
        # Arrow pointing down in the middle
        ids.append(canvas.create_line(x, y - d, x, y + d - 4, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x - 4, y + d - 8, x, y + d - 4, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x + 4, y + d - 8, x, y + d - 4, fill=color, width=stroke_width))

    elif name == "delete":
        # Trash can
        d = r * 0.75
        # Lid
        ids.append(canvas.create_line(x - d - 2, y - d + 2, x + d + 2, y - d + 2, fill=color, width=stroke_width))
        # Lid handle
        ids.append(canvas.create_line(x - 3, y - d + 2, x - 3, y - d - 1, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x + 3, y - d + 2, x + 3, y - d - 1, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x - 3, y - d - 1, x + 3, y - d - 1, fill=color, width=stroke_width))
        # Bin body
        ids.append(canvas.create_line(x - d + 1, y - d + 2, x - d + 3, y + d, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x + d - 1, y - d + 2, x + d - 3, y + d, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x - d + 3, y + d, x + d - 3, y + d, fill=color, width=stroke_width))
        # Vertical lines on bin
        ids.append(canvas.create_line(x - 3, y - d + 6, x - 2, y + d - 4, fill=color, width=stroke_width))
        ids.append(canvas.create_line(x + 3, y - d + 6, x + 2, y + d - 4, fill=color, width=stroke_width))

    elif name == "warning":
        # Triangle warning
        d = r * 0.85
        points = [
            x, y - d,
            x + d, y + d - 1,
            x - d, y + d - 1
        ]
        ids.append(canvas.create_polygon(points, outline=color, fill="", width=stroke_width, joinstyle="round"))
        # Exclamation point
        ids.append(canvas.create_line(x, y - d + 6, x, y + d - 6, fill=color, width=stroke_width))
        ids.append(canvas.create_oval(x - 1, y + d - 4, x + 1, y + d - 2, outline=color, fill=color, width=1))

    elif name == "success":
        # Success checkmark circle
        d = r * 0.85
        ids.append(canvas.create_oval(x - d, y - d, x + d, y + d, outline=color, fill="", width=stroke_width))
        # Checkmark
        ids.append(canvas.create_line(x - d*0.4, y, x - d*0.1, y + d*0.3, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x - d*0.1, y + d*0.3, x + d*0.5, y - d*0.3, fill=color, width=stroke_width, capstyle="round"))

    elif name == "info" or name == "information":
        # Info circle
        d = r * 0.85
        ids.append(canvas.create_oval(x - d, y - d, x + d, y + d, outline=color, fill="", width=stroke_width))
        # Dot
        ids.append(canvas.create_oval(x - 1, y - d*0.5, x + 1, y - d*0.3, outline=color, fill=color, width=1))
        # "i" body
        ids.append(canvas.create_line(x, y - d*0.1, x, y + d*0.5, fill=color, width=stroke_width, capstyle="round"))

    elif name == "search":
        # Magnifying glass
        d = r * 0.8
        cx, cy = x - d*0.2, y - d*0.2
        cr = d * 0.45
        ids.append(canvas.create_oval(cx - cr, cy - cr, cx + cr, cy + cr, outline=color, fill="", width=stroke_width))
        # Handle
        ids.append(canvas.create_line(cx + cr*0.7, cy + cr*0.7, x + d, y + d, fill=color, width=stroke_width*1.4, capstyle="round"))

    elif name == "zoom":
        # Magnifying glass with plus
        d = r * 0.8
        cx, cy = x - d*0.2, y - d*0.2
        cr = d * 0.45
        ids.append(canvas.create_oval(cx - cr, cy - cr, cx + cr, cy + cr, outline=color, fill="", width=stroke_width))
        # Plus inside
        ids.append(canvas.create_line(cx - 3, cy, cx + 3, cy, fill=color, width=stroke_width))
        ids.append(canvas.create_line(cx, cy - 3, cx, cy + 3, fill=color, width=stroke_width))
        # Handle
        ids.append(canvas.create_line(cx + cr*0.7, cy + cr*0.7, x + d, y + d, fill=color, width=stroke_width*1.4, capstyle="round"))

    elif name == "save":
        # Floppy disk
        d = r * 0.8
        points = [
            x - d, y - d,
            x + d - 3, y - d,
            x + d, y - d + 3,
            x + d, y + d,
            x - d, y + d
        ]
        ids.append(canvas.create_polygon(points, outline=color, fill="", width=stroke_width, joinstyle="round"))
        # Inner top label area
        ids.append(canvas.create_rectangle(x - d + 4, y - d, x + d - 6, y - d + 6, outline=color, fill="", width=stroke_width))
        # Inner bottom slider
        ids.append(canvas.create_rectangle(x - d + 3, y + d - 7, x + d - 3, y + d, outline=color, fill="", width=stroke_width))

    elif name == "chevron" or name == "chevron_down" or name == "arrow_down":
        d = r * 0.5
        ids.append(canvas.create_line(x - d, y - d * 0.3, x, y + d * 0.4, fill=color, width=stroke_width, capstyle="round", joinstyle="round"))
        ids.append(canvas.create_line(x, y + d * 0.4, x + d, y - d * 0.3, fill=color, width=stroke_width, capstyle="round", joinstyle="round"))

    elif name == "sort":
        d = r * 0.7
        # Up arrow on left
        ids.append(canvas.create_line(x - 3, y + d, x - 3, y - d, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x - 6, y - d + 3, x - 3, y - d, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x, y - d + 3, x - 3, y - d, fill=color, width=stroke_width, capstyle="round"))
        # Down arrow on right
        ids.append(canvas.create_line(x + 3, y - d, x + 3, y + d, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x, y + d - 3, x + 3, y + d, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x + 6, y + d - 3, x + 3, y + d, fill=color, width=stroke_width, capstyle="round"))

    elif name == "filter":
        d = r * 0.8
        points = [
            x - d, y - d,
            x + d, y - d,
            x + d * 0.3, y,
            x + d * 0.3, y + d,
            x - d * 0.3, y + d * 0.6,
            x - d * 0.3, y,
            x - d, y - d
        ]
        ids.append(canvas.create_polygon(points, outline=color, fill="", width=stroke_width, joinstyle="round"))

    elif name == "preset" or name == "sparkles" or name == "star":
        d = r * 0.8
        ids.append(canvas.create_line(x, y - d, x, y + d, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x - d, y, x + d, y, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x - d * 0.5, y - d * 0.5, x + d * 0.5, y + d * 0.5, fill=color, width=stroke_width, capstyle="round"))
        ids.append(canvas.create_line(x - d * 0.5, y + d * 0.5, x + d * 0.5, y - d * 0.5, fill=color, width=stroke_width, capstyle="round"))

    elif name == "lock":
        d = r * 0.7
        ids.append(canvas.create_rectangle(x - d, y - d * 0.1, x + d, y + d, outline=color, fill="", width=stroke_width))
        ids.append(canvas.create_arc(x - d * 0.6, y - d * 0.8, x + d * 0.6, y + d * 0.2, start=0, extent=180, outline=color, fill="", width=stroke_width, style="arc"))

    else:
        # Default placeholder (a simple dot circle)
        d = r * 0.7
        ids.append(canvas.create_oval(x - d, y - d, x + d, y + d, outline=color, fill="", width=stroke_width))
        ids.append(canvas.create_oval(x - 2, y - 2, x + 2, y + 2, outline=color, fill=color, width=1))

    return ids


class PhoenixIcon(tk.Canvas):
    """
    A standalone, light-weight vector icon widget.
    Automatically responds to width/height resizes and color updates.
    """
    def __init__(
        self,
        master: tk.Misc,
        name: str,
        size: int = 16,
        color: str | None = None,
        bg: str | None = None,
        **kwargs
    ) -> None:
        # Extract/pop fg or foreground to avoid Canvas TclErrors
        fg_val = kwargs.pop("fg", None) or kwargs.pop("foreground", None)
        self.color = color or fg_val or PHOENIX_THEME.text_secondary
        
        self.name = name
        self.size = size
        
        canvas_bg = bg or (master.cget("bg") if hasattr(master, "cget") else PHOENIX_THEME.card_bg)
        
        super().__init__(
            master,
            bg=canvas_bg,
            highlightthickness=0,
            bd=0,
            width=size,
            height=size,
            **kwargs
        )
        
        self.bind("<Configure>", lambda e: self._draw())
        self._draw()

    def configure(self, **kwargs) -> None:
        fg_val = kwargs.pop("fg", None) or kwargs.pop("foreground", None)
        if fg_val is not None:
            self.color = fg_val

        if "name" in kwargs:
            self.name = kwargs.pop("name")
        if "color" in kwargs:
            self.color = kwargs.pop("color")
        if "size" in kwargs:
            self.size = kwargs.pop("size")
            self.config(width=self.size, height=self.size)
        if "bg" in kwargs:
            super().configure(bg=kwargs.pop("bg"))
        super().configure(**kwargs)
        self._draw()

    config = configure

    def _draw(self) -> None:
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            w = self.size
            h = self.size
        
        draw_vector_icon(self, self.name, w / 2, h / 2, min(w, h), self.color)
