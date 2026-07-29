from __future__ import annotations

import tkinter as tk

from app.i18n import tr
from widgets.phoenix.theme import PHOENIX_THEME


def install_text_context_menu(root: tk.Misc) -> None:
    """Install one consistent editing menu for Entry, Text and Spinbox widgets."""

    def invoke(widget: tk.Misc, virtual_event: str) -> None:
        widget.event_generate(virtual_event)

    def has_selection(widget: tk.Misc) -> bool:
        try:
            return bool(widget.selection_present())
        except (AttributeError, tk.TclError):
            try:
                return bool(widget.tag_ranges("sel"))
            except (AttributeError, tk.TclError):
                return False

    def can_edit(widget: tk.Misc) -> bool:
        try:
            return str(widget.cget("state")) not in {"disabled", "readonly"}
        except tk.TclError:
            return True

    def show_menu(event: tk.Event) -> str:
        widget = event.widget
        selected = has_selection(widget)
        editable = can_edit(widget)
        menu = tk.Menu(
            widget,
            tearoff=False,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            disabledforeground=PHOENIX_THEME.text_disabled,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_body,
        )
        menu.add_command(
            label=tr("undo", "Rückgängig"),
            command=lambda: invoke(widget, "<<Undo>>"),
            state="normal" if editable else "disabled",
        )
        menu.add_command(
            label=tr("redo", "Wiederholen"),
            command=lambda: invoke(widget, "<<Redo>>"),
            state="normal" if editable else "disabled",
        )
        menu.add_separator()
        menu.add_command(
            label=tr("cut", "Ausschneiden"),
            command=lambda: invoke(widget, "<<Cut>>"),
            state="normal" if editable and selected else "disabled",
        )
        menu.add_command(
            label=tr("copy", "Kopieren"),
            command=lambda: invoke(widget, "<<Copy>>"),
            state="normal" if selected else "disabled",
        )
        menu.add_command(
            label=tr("paste", "Einfügen"),
            command=lambda: invoke(widget, "<<Paste>>"),
            state="normal" if editable else "disabled",
        )
        menu.add_separator()
        menu.add_command(
            label=tr("select_all", "Alles auswählen"),
            command=lambda: invoke(widget, "<<SelectAll>>"),
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    for widget_class in ("Entry", "TEntry", "Text", "Spinbox", "TSpinbox"):
        root.bind_class(widget_class, "<Button-3>", show_menu, add="+")
