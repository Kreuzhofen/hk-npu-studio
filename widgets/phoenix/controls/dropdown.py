from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Sequence, Any

from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.controls.vector_icons import draw_vector_icon
from widgets.phoenix.theme import PHOENIX_THEME

class PhoenixDropdown(PhoenixButton):
    """
    A premium custom dropdown control designed for HK NPU STUDIO.
    Inherits hover/animation states from PhoenixButton but renders a modern combobox dropdown layout
    with a left icon, current value text, and a right vector chevron.
    """
    def __init__(
        self,
        master: tk.Misc,
        variable: tk.StringVar,
        values: Sequence[str],
        label: str = "",
        icon_name: str | None = None,
        callback: Callable[[str], None] | None = None,
        width: int | None = None,
        height: int = 30,
        radius: int = 6,
        **kwargs
    ) -> None:
        self.variable = variable
        self.values = values
        self.dropdown_label = label
        self.callback = callback
        
        # Pop standard button configurations to initialize cleanly
        kwargs.pop("command", None)
        kwargs.pop("text", None)

        super().__init__(
            master,
            text=variable.get(),
            command=self._show_menu,
            button_type="neutral",
            icon_name=icon_name,
            width=width,
            height=height,
            radius=radius,
            **kwargs
        )
        
        # Create drop down menu
        self.menu = tk.Menu(
            self,
            tearoff=False,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_body,
        )
        self._update_menu()
        
        # Trace changes in variable to sync label text
        self._trace_id = self.variable.trace_add("write", lambda *args: self._on_var_changed())

    def _update_menu(self) -> None:
        self.menu.delete(0, "end")
        for value in self.values:
            menu_label = f"{self.dropdown_label}: {value}" if self.dropdown_label else value
            self.menu.add_command(
                label=menu_label,
                command=lambda val=value: self._select_value(val)
            )

    def update_values(self, new_values: Sequence[str]) -> None:
        self.values = new_values
        self._update_menu()

    def _select_value(self, value: str) -> None:
        self.variable.set(value)
        if self.callback:
            self.callback(value)
        # Generate <<ComboboxSelected>> event to support ttk.Combobox event bindings
        try:
            self.event_generate("<<ComboboxSelected>>")
        except Exception:
            pass

    def _on_var_changed(self) -> None:
        if self.winfo_exists():
            self.text = self.variable.get()
            self._redraw()

    def _show_menu(self) -> None:
        # Post the menu at the bottom-left coordinate of the dropdown button
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        try:
            self.menu.post(x, y)
        except Exception:
            pass

    def get(self) -> str:
        return self.variable.get()

    def set(self, value: str) -> None:
        self.variable.set(value)

    def cget(self, key: str) -> Any:
        if key == "menu":
            return self.menu
        if key == "values":
            return self.values
        return super().cget(key)

    __getitem__ = cget

    def configure(self, **kwargs) -> None:
        if "values" in kwargs:
            self.update_values(kwargs.pop("values"))
        if "textvariable" in kwargs:
            try:
                self.variable.trace_remove("write", self._trace_id)
            except Exception:
                pass
            self.variable = kwargs.pop("textvariable")
            self._trace_id = self.variable.trace_add("write", lambda *args: self._on_var_changed())
            self.text = self.variable.get()
            self._redraw()
        super().configure(**kwargs)

    config = configure

    def destroy(self) -> None:
        try:
            self.variable.trace_remove("write", self._trace_id)
        except Exception:
            pass
        super().destroy()

    def _redraw(self) -> None:
        self.delete("all")

        # 1. Measure text width
        try:
            f = tkfont.Font(font=self.font)
            text_w = f.measure(self.text)
        except Exception:
            text_w = len(self.text) * 7

        icon_w = 14 if self.icon_name else 0

        # 2. Auto-size canvas width if not explicitly fixed
        if self._width is None:
            # Padding: left (12) + icon space (icon_w + 8) + gap (12) + chevron (10) + right (12)
            padding = 12 + (icon_w + 8 if self.icon_name else 0) + 12 + 10 + 12
            required_w = text_w + padding
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
        r = min(r, w // 2, h // 2)

        # Draw rounded rectangle
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
        if self._state == "disabled":
            fg_color = PHOENIX_THEME.text_disabled
        elif self._is_hovered and not self._is_pressed:
            fg_color = self.hover_fg

        # Resolve icon accent color
        icon_color = fg_color
        if self._state != "disabled" and self.icon_name:
            if self.icon_name == "filter":
                icon_color = PHOENIX_THEME.success
            elif self.icon_name == "zoom":
                icon_color = PHOENIX_THEME.warning
            else:
                icon_color = PHOENIX_THEME.accent

        # Draw left icon
        start_x = 12
        if self.icon_name:
            icon_x = start_x + icon_w / 2
            draw_vector_icon(self, self.icon_name, icon_x, h / 2, icon_w, icon_color)
            start_x += icon_w + 8

        # Draw right chevron
        chevron_w = 10
        chevron_x = w - 12 - chevron_w / 2
        draw_vector_icon(self, "chevron", chevron_x, h / 2, chevron_w, fg_color)

        # Draw center value text (left-aligned relative to text box start coordinate)
        if self.text:
            self.create_text(
                start_x,
                h / 2,
                text=self.text,
                fill=fg_color,
                font=self.font,
                anchor="w",
                tags="text"
            )
