from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Sequence

from widgets.phoenix.theme import PHOENIX_THEME
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.controls.card import PhoenixCard


class WorkspaceHeader(tk.Frame):
    """Shared title and toolbar area for all Phoenix workspaces."""

    def __init__(self, master: tk.Misc, title: str, subtitle: str) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.grid_columnconfigure(0, weight=1)

        title_group = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        title_group.grid(row=0, column=0, sticky="ew")
        title_group.grid_columnconfigure(0, weight=1)

        tk.Label(
            title_group,
            text=title,
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            title_group,
            text=subtitle,
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(PHOENIX_THEME.space_xs, 0))

        self.toolbar_slot = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        self.toolbar_slot.grid(row=1, column=0, sticky="ew", pady=(PHOENIX_THEME.space_md, 0))
        self.toolbar_slot.grid_columnconfigure(0, weight=1)


class WorkspaceFrame(tk.Frame):
    """Reusable workspace shell with header, content, inspector and status slots."""

    def __init__(self, master: tk.Misc, title: str, subtitle: str, has_inspector: bool = True) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.has_inspector = has_inspector

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        if has_inspector:
            self.grid_columnconfigure(1, weight=0)

        columnspan = 2 if has_inspector else 1
        self.header = WorkspaceHeader(self, title, subtitle)
        self.header.grid(
            row=0,
            column=0,
            columnspan=columnspan,
            sticky="ew",
            padx=PHOENIX_THEME.space_lg,
            pady=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_md),
        )

        self.content_slot = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        self.content_slot.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(PHOENIX_THEME.space_lg, PHOENIX_THEME.space_md if has_inspector else PHOENIX_THEME.space_lg),
            pady=(0, PHOENIX_THEME.space_md),
        )
        self.content_slot.grid_rowconfigure(0, weight=1)
        self.content_slot.grid_columnconfigure(0, weight=1)

        self.inspector_slot: tk.Frame | None = None
        if has_inspector:
            self.inspector_slot = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
            self.inspector_slot.grid(
                row=1,
                column=1,
                sticky="nsew",
                padx=(0, PHOENIX_THEME.space_lg),
                pady=(0, PHOENIX_THEME.space_md),
            )
            self.inspector_slot.grid_rowconfigure(0, weight=1)
            self.inspector_slot.grid_columnconfigure(0, weight=1)

        self.status_slot = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        self.status_slot.grid(
            row=2,
            column=0,
            columnspan=columnspan,
            sticky="ew",
            padx=PHOENIX_THEME.space_lg,
            pady=(0, PHOENIX_THEME.space_lg),
        )
        self.status_slot.grid_columnconfigure(0, weight=1)


class WorkspaceToolbarBase(tk.Frame):
    """Shared visual foundation for compact workspace toolbars."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )

    def group_frame(self) -> tk.Frame:
        return tk.Frame(self, bg=PHOENIX_THEME.card_bg)

    def separator(self, master: tk.Misc) -> tk.Frame:
        return tk.Frame(master, bg=PHOENIX_THEME.border, width=1)

    def toolbar_button(
        self,
        master: tk.Misc,
        text: str,
        command: Callable[[], None],
        width_px: int,
        icon_name: str | None = None,
    ) -> PhoenixButton:
        # Auto-parse vector icon name if unicode symbol is used
        symbol, _, label = text.partition("  ")
        if label:
            if not icon_name:
                from resources.icons import IconManager
                for k, v in IconManager.FALLBACK_SYMBOLS.items():
                    if v == symbol:
                        icon_name = k
                        break
            text = label

        button = PhoenixButton(
            master,
            text=text,
            command=command,
            button_type="neutral",
            icon_name=icon_name,
            width=width_px,
            height=30,
            radius=6
        )
        return button

    def toolbar_dropdown(
        self,
        master: tk.Misc,
        label: str,
        variable: tk.StringVar,
        values: Sequence[str],
        width_px: int,
        callback: Callable[[str], None],
    ) -> Any:
        icon_name = None
        label_lower = label.lower()
        if "sort" in label_lower:
            icon_name = "sort"
        elif "zoom" in label_lower or "size" in label_lower or "größe" in label_lower or "grosse" in label_lower:
            icon_name = "zoom"
        elif "filter" in label_lower:
            icon_name = "filter"
        elif "preset" in label_lower:
            icon_name = "preset"

        from widgets.phoenix.controls.dropdown import PhoenixDropdown
        button = PhoenixDropdown(
            master,
            variable=variable,
            values=values,
            label=label,
            icon_name=icon_name,
            callback=callback,
            width=width_px,
            height=30,
            radius=6
        )
        return button

    def _set_dropdown_value(
        self,
        variable: tk.StringVar,
        value: str,
        callback: Callable[[str], None],
    ) -> None:
        variable.set(value)
        callback(value)


class WorkspaceStatusBar(tk.Frame):
    """Shared status bar with labeled values and quiet separators."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.surface,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.values: dict[str, tk.Label] = {}

    def add_item(self, label: str, value: str, column: int, sticky: str = "w") -> None:
        host = tk.Frame(self, bg=PHOENIX_THEME.surface)
        host.grid(
            row=0,
            column=column,
            sticky=sticky,
            padx=PHOENIX_THEME.space_md,
            pady=PHOENIX_THEME.space_sm,
        )

        tk.Label(
            host,
            text=label,
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        ).pack(side="left")

        value_label = tk.Label(
            host,
            text=value,
            bg=PHOENIX_THEME.surface,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        )
        value_label.pack(side="left", padx=(PHOENIX_THEME.space_xs, 0))
        self.values[label] = value_label

    def add_divider(self, column: int) -> None:
        tk.Frame(self, bg=PHOENIX_THEME.border, width=1).grid(
            row=0,
            column=column,
            sticky="ns",
            pady=PHOENIX_THEME.space_sm,
        )

    def update_item(self, label: str, value: str) -> None:
        value_label = self.values.get(label)
        if value_label is not None:
            value_label.configure(text=value)


class WorkspacePanel(PhoenixCard):
    """Reusable side panel with shared header spacing and surface styling."""

    def __init__(self, master: tk.Misc, title: str, subtitle: str, width: int | None = None) -> None:
        kwargs: dict[str, object] = {
            "bg": PHOENIX_THEME.card_bg,
            "border_color": PHOENIX_THEME.border,
            "radius": 10,
        }
        if width is not None:
            kwargs["width"] = width
        super().__init__(master, **kwargs)
        if width is not None:
            self.grid_propagate(False)

        self.grid_columnconfigure(0, weight=1)

        tk.Label(
            self,
            text=title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(PHOENIX_THEME.card_pad_y, PHOENIX_THEME.space_xs),
        )

        tk.Label(
            self,
            text=subtitle,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(0, PHOENIX_THEME.space_lg),
        )

        self.content = tk.Frame(self, bg=PHOENIX_THEME.card_bg)
        self.content.grid(row=2, column=0, sticky="ew")
        self.content.grid_columnconfigure(0, weight=1)


class WorkspaceInfoCard(PhoenixCard):
    """Reusable information card for inspectors and future workspace panels."""

    def __init__(self, master: tk.Misc, title: str) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.elevated_bg,
            border_color=PHOENIX_THEME.border,
            radius=8
        )
        self.grid_columnconfigure(0, weight=1)

        tk.Label(
            self,
            text=title,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_md,
            pady=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_sm),
        )

    def set_lines(self, lines: tuple[str, ...], wraplength: int = 220) -> None:
        for child in self.grid_slaves():
            info = child.grid_info()
            if int(info.get("row", 0)) > 0:
                child.destroy()

        for index, line in enumerate(lines, start=1):
            tk.Label(
                self,
                text=line,
                bg=PHOENIX_THEME.elevated_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_small,
                anchor="w",
                justify="left",
                wraplength=wraplength,
            ).grid(
                row=index,
                column=0,
                sticky="ew",
                padx=PHOENIX_THEME.space_md,
                pady=(0, PHOENIX_THEME.space_xs),
            )

        tk.Frame(self, bg=PHOENIX_THEME.elevated_bg, height=PHOENIX_THEME.space_sm).grid(
            row=len(lines) + 1,
            column=0,
            sticky="ew",
        )
