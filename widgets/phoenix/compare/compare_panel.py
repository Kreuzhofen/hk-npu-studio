from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from PIL import Image

from widgets.phoenix.compare.compare_image_canvas import CompareImageCanvas
from widgets.phoenix.compare.compare_placeholder import ComparePlaceholder
from widgets.phoenix.theme import PHOENIX_THEME


class ComparePanel(tk.Frame):
    """Panel shell for compare sources, managing placeholder, image canvas slots, and metadata."""

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        empty_title: str,
        empty_text: str,
        icon_name: str,
        on_load_clicked: Callable[[], None],
        on_combobox_selected: Callable[[str], None],
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.title = title
        self.empty_title = empty_title
        self.empty_text = empty_text
        self.icon_name = icon_name
        self.on_load_clicked = on_load_clicked
        self.on_combobox_selected = on_combobox_selected
        self.active_image: Image.Image | None = None
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Style TTK Combobox for Dark Theme integration
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Phoenix.TCombobox",
            background=PHOENIX_THEME.elevated_bg,
            foreground=PHOENIX_THEME.text_primary,
            fieldbackground=PHOENIX_THEME.elevated_bg,
            bordercolor=PHOENIX_THEME.border,
            lightcolor=PHOENIX_THEME.border,
            darkcolor=PHOENIX_THEME.border,
            arrowcolor=PHOENIX_THEME.text_muted,
            borderwidth=1,
            relief="flat",
        )
        style.map(
            "Phoenix.TCombobox",
            background=[("readonly", PHOENIX_THEME.elevated_bg)],
            foreground=[("readonly", PHOENIX_THEME.text_primary)],
            fieldbackground=[("readonly", PHOENIX_THEME.elevated_bg)],
            bordercolor=[("readonly", PHOENIX_THEME.border)],
        )

        self.option_add("*TCombobox*Listbox.background", PHOENIX_THEME.elevated_bg)
        self.option_add("*TCombobox*Listbox.foreground", PHOENIX_THEME.text_primary)
        self.option_add("*TCombobox*Listbox.selectBackground", PHOENIX_THEME.accent)
        self.option_add("*TCombobox*Listbox.selectForeground", PHOENIX_THEME.text_on_accent)
        self.option_add("*TCombobox*Listbox.font", PHOENIX_THEME.font_body)

        # Row 0: Dropdown selection bar
        dropdown_frame = tk.Frame(self, bg=PHOENIX_THEME.card_bg)
        dropdown_frame.grid(row=0, column=0, sticky="ew", padx=PHOENIX_THEME.card_pad_x, pady=(PHOENIX_THEME.card_pad_y, 4))
        
        self.combobox = ttk.Combobox(
            dropdown_frame,
            values=["Keine Auswahl"],
            state="readonly",
            style="Phoenix.TCombobox",
        )
        self.combobox.set("Keine Auswahl")
        self.combobox.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.combobox.bind("<<ComboboxSelected>>", self._on_combobox_changed)
        
        # Load Image button
        self.load_btn = tk.Button(
            dropdown_frame,
            text="Bild laden",
            command=self.on_load_clicked,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            bd=0,
            relief="flat",
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
            padx=10,
            pady=4,
        )
        self.load_btn.pack(side="right")
        self._add_button_hover(self.load_btn)

        # Row 1: Panel Header
        tk.Label(
            self,
            text=self.title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(4, PHOENIX_THEME.space_sm),
        )

        # Row 2: Create content slot frame
        self.content_frame = tk.Frame(self, bg=PHOENIX_THEME.card_bg)
        self.content_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(0, 4),
        )
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # 1. Placeholder
        self.placeholder = ComparePlaceholder(
            self.content_frame,
            title=self.empty_title,
            subtitle=self.empty_text,
            icon_name=self.icon_name,
        )
        self.placeholder.grid(row=0, column=0, sticky="nsew")

        # 2. Image Canvas
        self.image_canvas = CompareImageCanvas(self.content_frame)

        # Row 3: Metadata card
        self.meta_card = tk.Frame(
            self,
            bg=PHOENIX_THEME.elevated_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        self.meta_card.grid(row=3, column=0, sticky="ew", padx=PHOENIX_THEME.card_pad_x, pady=(4, PHOENIX_THEME.card_pad_y))
        self.meta_card.columnconfigure(1, weight=1)
        
        # Helper to create label pair
        def create_meta_row(row_idx, label_text):
            lbl_key = tk.Label(
                self.meta_card,
                text=label_text,
                bg=PHOENIX_THEME.elevated_bg,
                fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_small,
                anchor="w",
            )
            lbl_key.grid(row=row_idx, column=0, sticky="w", padx=10, pady=4)
            
            lbl_val = tk.Label(
                self.meta_card,
                text="-",
                bg=PHOENIX_THEME.elevated_bg,
                fg=PHOENIX_THEME.text_primary,
                font=PHOENIX_THEME.font_small,
                anchor="w",
                justify="left",
                wraplength=350,
            )
            lbl_val.grid(row=row_idx, column=1, sticky="w", padx=10, pady=4)
            return lbl_val

        self.meta_prompt_val = create_meta_row(0, "Prompt:")
        self.meta_seed_val = create_meta_row(1, "Seed:")
        self.meta_sampler_val = create_meta_row(2, "Sampler:")

    def _on_combobox_changed(self, event) -> None:
        val = self.combobox.get()
        self.on_combobox_selected(val)

    def _add_button_hover(self, button: tk.Button) -> None:
        original_bg = button.cget("bg")
        original_fg = button.cget("fg")
        h_bg = PHOENIX_THEME.accent
        h_fg = PHOENIX_THEME.text_on_accent

        def on_enter(event):
            if str(button.cget("state")) != "disabled":
                button.configure(bg=h_bg, fg=h_fg)

        def on_leave(event):
            if str(button.cget("state")) != "disabled":
                button.configure(bg=original_bg, fg=original_fg)

        button.bind("<Enter>", on_enter, add="+")
        button.bind("<Leave>", on_leave, add="+")

    def set_image(self, image: Image.Image | None) -> None:
        """Sets the panel image, switching between placeholder and image canvas views."""
        self.active_image = image

        if image is None:
            self.image_canvas.grid_forget()
            self.placeholder.grid(row=0, column=0, sticky="nsew")
            self.image_canvas.set_image(None)
        else:
            self.placeholder.grid_forget()
            self.image_canvas.grid(row=0, column=0, sticky="nsew")
            self.image_canvas.set_image(image)

    def set_zoom(self, zoom_scale: float | None) -> None:
        """Sets the zoom scale on the image canvas component."""
        self.image_canvas.set_zoom(zoom_scale)

    def update_panel(self, image: Image.Image | None, zoom_scale: float | None) -> None:
        """Updates the panel content slot with image and zoom scale."""
        self.active_image = image

        if image is None:
            self.image_canvas.grid_forget()
            self.placeholder.grid(row=0, column=0, sticky="nsew")
            self.image_canvas.update_viewport(None, zoom_scale)
        else:
            self.placeholder.grid_forget()
            self.image_canvas.grid(row=0, column=0, sticky="nsew")
            self.image_canvas.update_viewport(image, zoom_scale)
