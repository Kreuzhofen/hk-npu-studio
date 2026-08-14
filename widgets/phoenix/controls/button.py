from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable
from widgets.phoenix.theme import PHOENIX_THEME
from widgets.phoenix.controls.vector_icons import draw_vector_icon

def interpolate_color(color1: str, color2: str, t: float) -> str:
    """Linearly interpolates between two hex colors."""
    try:
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return color2

def brighten_color(hex_color: str, amount: float = 0.12) -> str:
    """Brightens a hex color by blending it with white."""
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color

def darken_color(hex_color: str, amount: float = 0.12) -> str:
    """Darkens a hex color by blending it with black."""
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = max(0, int(r * (1 - amount)))
        g = max(0, int(g * (1 - amount)))
        b = max(0, int(b * (1 - amount)))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color

class PhoenixButton(tk.Canvas):
    """
    A premium, modern button with rounded corners, custom typography,
    and smooth micro-animations.
    """

    def __init__(
        self,
        master: tk.Misc,
        text: str = "",
        command: Callable[[], None] | None = None,
        button_type: str = "primary",  # primary, secondary, neutral, danger
        icon_name: str | None = None,
        icon_color: str | None = None,
        width: int | None = None,
        height: int = 34,
        state: str = "normal",
        font: tuple | None = None,
        radius: int = 8,
        **kwargs
    ) -> None:
        self.text = text
        self.command = command
        self.button_type = button_type
        self.icon_name = icon_name
        self.icon_color = icon_color
        self.radius = radius
        self._state = state
        self.font = font or PHOENIX_THEME.font_button
        self._height = height
        self._width = width

        # Resolve initial color styles
        self._resolve_colors()

        # Extract custom colors if provided in kwargs
        custom_bg = kwargs.pop("bg", None) or kwargs.pop("background", None)
        custom_fg = kwargs.pop("fg", None) or kwargs.pop("foreground", None)
        if custom_bg is not None:
            self.normal_bg = custom_bg
            self.hover_bg = brighten_color(self.normal_bg, 0.12)
            self.active_bg = darken_color(self.normal_bg, 0.12)
            self.current_bg = self.normal_bg
        if custom_fg is not None:
            self.normal_fg = custom_fg
            self.hover_fg = custom_fg

        # Pop standard button properties to prevent Canvas TclErrors
        for k in ["compound", "image", "padx", "pady", "anchor", "relief", "bd", "borderwidth", 
                  "activebackground", "activeforeground", "disabledforeground", 
                  "highlightbackground", "highlightthickness", "highlightcolor", "overrelief",
                  "height", "width"]:
            kwargs.pop(k, None)

        # Canvas bg is matched to button's parent bg to hide corners
        parent_bg = PHOENIX_THEME.card_bg
        if hasattr(master, "cget"):
            try:
                parent_bg = master.cget("bg")
            except Exception:
                pass

        super().__init__(
            master,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            height=height,
            width=width or 100,
            **kwargs
        )

        self._anim_id = None
        self._is_pressed = False
        self._is_hovered = False

        # Bind events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda e: self._redraw())

        # Initial redraw
        self._redraw()
        self._update_cursor()

    def _resolve_colors(self) -> None:
        """Sets the color properties based on the button type."""
        # Defaults
        self.normal_fg = PHOENIX_THEME.text_on_accent
        self.normal_bg = PHOENIX_THEME.accent
        self.border_color = ""
        
        has_custom_hover_active = False

        if self._state == "disabled":
            self.normal_bg = PHOENIX_THEME.elevated_bg
            self.normal_fg = PHOENIX_THEME.text_disabled
            self.border_color = PHOENIX_THEME.border
        elif self.button_type == "primary":
            self.normal_bg = PHOENIX_THEME.accent
            self.normal_fg = PHOENIX_THEME.text_on_accent
            self.border_color = ""
        elif self.button_type == "secondary":
            self.normal_bg = PHOENIX_THEME.accent_soft
            self.normal_fg = PHOENIX_THEME.accent
            self.border_color = PHOENIX_THEME.accent
        elif self.button_type == "neutral":
            self.normal_bg = PHOENIX_THEME.card_bg
            self.normal_fg = PHOENIX_THEME.text_primary
            self.border_color = PHOENIX_THEME.border
        elif self.button_type == "danger":
            self.normal_bg = PHOENIX_THEME.danger
            self.normal_fg = PHOENIX_THEME.text_on_accent
            self.border_color = ""
        elif self.button_type == "nav":
            self.normal_bg = PHOENIX_THEME.panel_bg
            self.normal_fg = PHOENIX_THEME.text_secondary
            self.border_color = ""
            self.hover_bg = PHOENIX_THEME.accent_soft
            self.hover_fg = PHOENIX_THEME.text_primary
            self.active_bg = darken_color(PHOENIX_THEME.accent_soft, 0.05) if PHOENIX_THEME.accent_soft else self.normal_bg
            has_custom_hover_active = True
        elif self.button_type == "nav_active":
            self.normal_bg = PHOENIX_THEME.accent_soft
            self.normal_fg = PHOENIX_THEME.accent
            self.border_color = ""
            self.hover_bg = PHOENIX_THEME.accent_soft
            self.hover_fg = PHOENIX_THEME.accent
            self.active_bg = self.normal_bg
            has_custom_hover_active = True

        # Compute Hover and Active states
        if not has_custom_hover_active:
            if self._state == "disabled":
                self.hover_bg = self.normal_bg
                self.active_bg = self.normal_bg
                self.hover_fg = self.normal_fg
            else:
                self.hover_bg = brighten_color(self.normal_bg, 0.12)
                self.active_bg = darken_color(self.normal_bg, 0.12)
                self.hover_fg = self.normal_fg

        self.current_bg = self.normal_bg

    def _update_cursor(self) -> None:
        if self._state == "normal":
            self.configure(cursor="hand2")
        else:
            self.configure(cursor="")

    def configure(self, **kwargs) -> None:
        # Pop standard button properties to prevent Canvas TclErrors
        for k in ["activebackground", "activeforeground", "relief", "bd", "borderwidth", "padx", "pady", "anchor", "disabledforeground", "highlightbackground", "highlightthickness", "highlightcolor", "overrelief"]:
            kwargs.pop(k, None)

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._resolve_colors()
            self._update_cursor()
        if "text" in kwargs:
            self.text = kwargs.pop("text")
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if "icon_name" in kwargs:
            self.icon_name = kwargs.pop("icon_name")
        if "icon_color" in kwargs:
            self.icon_color = kwargs.pop("icon_color")
        if "button_type" in kwargs:
            self.button_type = kwargs.pop("button_type")
            self._resolve_colors()
        if "font" in kwargs:
            self.font = kwargs.pop("font")
        if "bg" in kwargs:
            self.normal_bg = kwargs.pop("bg")
            self.hover_bg = brighten_color(self.normal_bg, 0.12)
            self.active_bg = darken_color(self.normal_bg, 0.12)
            self.current_bg = self.normal_bg
        if "fg" in kwargs:
            self.normal_fg = kwargs.pop("fg")
            self.hover_fg = self.normal_fg
            
        super().configure(**kwargs)
        self._redraw()

    config = configure

    def cget(self, key: str) -> Any:
        if key == "state":
            return self._state
        if key == "text":
            return self.text
        if key in ("bg", "background"):
            return self.normal_bg
        if key in ("fg", "foreground"):
            return self.normal_fg
        return super().cget(key)

    def invoke(self) -> Any:
        if self._state == "normal" and self.command:
            try:
                return self.command()
            except Exception as e:
                print(f"Error executing button invoke command: {e}")
        return None

    def _on_enter(self, event) -> None:
        if self._state == "disabled":
            return
        self._is_hovered = True
        self._animate_hover(self.hover_bg)

    def _on_leave(self, event) -> None:
        if self._state == "disabled":
            return
        self._is_hovered = False
        self._animate_hover(self.normal_bg)

    def _on_press(self, event) -> None:
        if self._state == "disabled":
            return
        self._is_pressed = True
        # Immediate pressed state (no transition delay for press)
        if self._anim_id:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None
        self.current_bg = self.active_bg
        self._redraw()

    def _on_release(self, event) -> None:
        if self._state == "disabled" or not self._is_pressed:
            return
        self._is_pressed = False
        
        # Check if released inside
        w = self.winfo_width()
        h = self.winfo_height()
        in_bounds = (0 <= event.x <= w) and (0 <= event.y <= h)

        if in_bounds:
            # Trigger command
            if self.command:
                try:
                    self.command()
                except Exception as e:
                    print(f"Error executing button command: {e}")
            target = self.hover_bg if self._is_hovered else self.normal_bg
        else:
            target = self.normal_bg

        self._animate_hover(target)

    def _animate_hover(self, target_color: str) -> None:
        if self._anim_id:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None
        self._animate_step(self.current_bg, target_color, 0)

    def _animate_step(self, start_color: str, target_color: str, step: int) -> None:
        if not self.winfo_exists():
            return
        total_steps = 10
        if step > total_steps:
            self.current_bg = target_color
            self._redraw()
            return

        t = step / total_steps
        self.current_bg = interpolate_color(start_color, target_color, t)
        self._redraw()

        self._anim_id = self.after(12, lambda: self._animate_step(start_color, target_color, step + 1))

    def _redraw(self) -> None:
        if not self.winfo_exists():
            return
        self.delete("all")

        # 1. Calculate text and icon sizes first to know content width
        try:
            f = tkfont.Font(font=self.font)
            text_w = f.measure(self.text)
            text_h = f.metrics("linespace")
        except Exception:
            text_w = len(self.text) * 7
            text_h = 14

        icon_w = 0
        if self.icon_name:
            icon_w = 18 if self.button_type in ("nav", "nav_active") else 16

        spacing = 8 if (self.text and self.icon_name) else 0
        total_content_w = icon_w + spacing + text_w

        # 2. Auto-size canvas width if not explicitly fixed
        if self._width is None:
            padding = 40 if self.button_type in ("nav", "nav_active") else 28
            required_w = total_content_w + padding
            try:
                current_req_w = int(self.cget("width"))
            except Exception:
                current_req_w = 0
            if current_req_w != required_w:
                self.configure(width=required_w)
            w = required_w
        else:
            w = self.winfo_width()
            if w < 2:
                w = self._width

        h = self.winfo_height()
        if h < 2:
            h = self._height

        r = self.radius
        # Clamp radius
        r = min(r, w // 2, h // 2)

        # Draw rounded rectangle
        # Using canvas smooth polygon trick for nice rounded corners
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

        # Border options
        border_kwargs = {}
        if self.border_color:
            border_kwargs = {"outline": self.border_color, "width": 1}

        self.create_polygon(
            points,
            fill=self.current_bg,
            smooth=True,
            tags="bg",
            **border_kwargs
        )

        fg_color = self.normal_fg
        # If disabled, override fg color
        if self._state == "disabled":
            fg_color = PHOENIX_THEME.text_disabled
        elif self._is_hovered and not self._is_pressed:
            fg_color = self.hover_fg

        # Draw content (left-aligned for nav items, centered otherwise)
        if self.button_type in ("nav", "nav_active"):
            start_x = 16
        else:
            start_x = (w - total_content_w) / 2
        center_y = h / 2

        if self.button_type == "nav_active":
            # Sleek vertical indicator line on the left edge
            self.create_line(
                4,
                8,
                4,
                h - 8,
                fill=self.icon_color or PHOENIX_THEME.accent,
                width=3,
                capstyle="round",
            )

        if self.icon_name:
            icon_x = start_x + icon_w / 2
            draw_vector_icon(self, self.icon_name, icon_x, center_y, icon_w, self.icon_color or fg_color)

        if self.text:
            text_x = start_x + icon_w + spacing
            
            self.create_text(
                text_x,
                center_y,
                text=self.text,
                fill=fg_color,
                font=self.font,
                anchor="w",
                tags="text"
            )

    def destroy(self) -> None:
        if getattr(self, "_anim_id", None):
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None
        super().destroy()
