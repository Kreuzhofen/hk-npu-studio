from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from controllers.compare_workspace_controller import CompareWorkspaceController
from widgets.phoenix.compare.compare_panel import ComparePanel
from widgets.phoenix.compare.status_bar import CompareStatusBar
from widgets.phoenix.compare.compare_toolbar import CompareToolbar
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr


class PhoenixCompareView(WorkspaceFrame):
    """Professional Compare Workspace for manual before/after image review."""

    FILE_TYPES = (
        ("Bilddateien", "*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff"),
        ("JPEG", "*.jpg *.jpeg"),
        ("PNG", "*.png"),
        ("TIFF", "*.tif *.tiff"),
        ("Alle Dateien", "*.*"),
    )

    def __init__(
        self,
        master: tk.Misc,
        controller: CompareWorkspaceController | None = None,
    ) -> None:
        super().__init__(
            master,
            title=tr("compare_title", "Bildvergleich"),
            subtitle=tr("compare_subtitle", "Generierte Bilder und Originale direkt gegenüberstellen"),
            has_inspector=False,
        )
        self.controller = controller or CompareWorkspaceController()
        self.toolbar: CompareToolbar
        self.original_panel: ComparePanel
        self.result_panel: ComparePanel
        self.status_bar: CompareStatusBar
        self._build()
        self.refresh()

    def _build(self) -> None:
        self._build_toolbar()
        self._build_main_area()
        self._build_status_bar()

    def _build_toolbar(self) -> None:
        self.toolbar = CompareToolbar(
            self.header.toolbar_slot,
            on_open_original=self._open_original,
            on_open_output=self._open_output,
            on_fit=lambda: self._set_zoom("Fit"),
            on_zoom_50=lambda: self._set_zoom("50 %"),
            on_zoom_100=lambda: self._set_zoom("100 %"),
            on_zoom_200=lambda: self._set_zoom("200 %"),
            on_sync=self._prepare_sync,
            on_swap=self._swap_images,
            on_compare_metadata=self._compare_metadata,
        )
        self.toolbar.grid(row=0, column=0, sticky="ew")

    def _build_main_area(self) -> None:
        self.split_container = tk.Frame(self.content_slot, bg=PHOENIX_THEME.content_bg)
        self.split_container.grid(row=0, column=0, sticky="nsew")
        self.split_container.grid_columnconfigure(0, weight=1, uniform="compare_panel")
        self.split_container.grid_columnconfigure(1, weight=1, uniform="compare_panel")
        self.split_container.grid_rowconfigure(0, weight=1)

        self.original_panel = ComparePanel(
            self.split_container,
            title=tr("compare_left_title", "Original"),
            empty_title=tr("compare_left_empty_title", "Originalbild laden"),
            empty_text=tr("compare_left_placeholder", "Öffne links ein Ausgangsbild für den Qualitätsvergleich."),
            icon_name="image",
            on_load_clicked=self._open_original,
            on_combobox_selected=self._on_original_selected,
        )
        self.original_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, PHOENIX_THEME.space_sm),
        )

        self.result_panel = ComparePanel(
            self.split_container,
            title=tr("compare_right_title", "Ergebnis"),
            empty_title=tr("compare_right_empty_title", "Ausgabe laden"),
            empty_text=tr("compare_right_placeholder", "Öffne rechts ein Ergebnisbild, z. B. einen AI-Output."),
            icon_name="output",
            on_load_clicked=self._open_output,
            on_combobox_selected=self._on_output_selected,
        )
        self.result_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(PHOENIX_THEME.space_sm, 0),
        )

        # Bind double-click and right-click recursive actions
        self._bind_recursive(self.original_panel.placeholder, "<Double-Button-1>", lambda e: self._open_original())
        self._bind_recursive(self.original_panel.image_canvas, "<Double-Button-1>", lambda e: self._open_original())
        self._bind_recursive(self.original_panel.placeholder, "<Button-3>", lambda e: self._show_panel_context_menu(e, "original"))
        self._bind_recursive(self.original_panel.image_canvas, "<Button-3>", lambda e: self._show_panel_context_menu(e, "original"))

        self._bind_recursive(self.result_panel.placeholder, "<Double-Button-1>", lambda e: self._open_output())
        self._bind_recursive(self.result_panel.image_canvas, "<Double-Button-1>", lambda e: self._open_output())
        self._bind_recursive(self.result_panel.placeholder, "<Button-3>", lambda e: self._show_panel_context_menu(e, "output"))
        self._bind_recursive(self.result_panel.image_canvas, "<Button-3>", lambda e: self._show_panel_context_menu(e, "output"))

    def _bind_recursive(self, widget: tk.Widget, event: str, callback: Callable[[tk.Event], None]) -> None:
        widget.bind(event, callback)
        for child in widget.winfo_children():
            self._bind_recursive(child, event, callback)

    def _show_panel_context_menu(self, event: tk.Event, panel_type: str) -> None:
        menu = tk.Menu(
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
        
        if panel_type == "original":
            remove_cmd = self._remove_original
            replace_cmd = self._open_original
        else:
            remove_cmd = self._remove_output
            replace_cmd = self._open_output
            
        menu.add_command(label=tr("compare_remove_image", "Bild entfernen"), command=remove_cmd)
        menu.add_command(label=tr("compare_replace_image", "Bild durch Datei ersetzen..."), command=replace_cmd)
        menu.post(event.x_root, event.y_root)

    def _remove_original(self) -> None:
        try:
            self.controller.clear_original()
        except Exception as error:
            self._handle_error(error)
        self.refresh()

    def _remove_output(self) -> None:
        try:
            self.controller.clear_output()
        except Exception as error:
            self._handle_error(error)
        self.refresh()

    def _show_context_menu(self, event: tk.Event) -> None:
        """Displays the right-click context menu with generation hooks."""
        menu = tk.Menu(
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
        menu.add_command(
            label=tr("compare_regenerate_todo", "Erneut generieren (TODO)"),
            command=self._on_regenerate_todo,
            state="disabled"
        )
        menu.add_command(
            label=tr("compare_generate_with_current_model_todo", "Mit aktuellem Modell generieren (TODO)"),
            command=self._on_generate_current_model_todo,
            state="disabled"
        )
        menu.post(event.x_root, event.y_root)

    def _on_regenerate_todo(self) -> None:
        """Hook/TODO: Triggers regeneration of the selected output."""
        pass

    def _on_generate_current_model_todo(self) -> None:
        """Hook/TODO: Triggers generation of the original source using the current active model."""
        pass

    def _build_status_bar(self) -> None:
        self.status_bar = CompareStatusBar(self.status_slot, self.controller.status_items())
        self.status_bar.grid(row=0, column=0, sticky="ew")

    def _update_comboboxes(self) -> None:
        from config import OUTPUT_DIR
        images = [tr("no_selection", "Keine Auswahl")]
        if Path(OUTPUT_DIR).exists():
            for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp"):
                images.extend(p.name for p in Path(OUTPUT_DIR).glob(ext))
        images = sorted(list(set(images)), key=lambda x: x.lower())
        
        sel_orig = self.original_panel.combobox.get()
        sel_out = self.result_panel.combobox.get()
        
        self.original_panel.combobox.configure(values=images)
        self.result_panel.combobox.configure(values=images)
        
        if sel_orig in images:
            self.original_panel.combobox.set(sel_orig)
        else:
            self.original_panel.combobox.set(tr("no_selection", "Keine Auswahl"))
            
        if sel_out in images:
            self.result_panel.combobox.set(sel_out)
        else:
            self.result_panel.combobox.set(tr("no_selection", "Keine Auswahl"))

    def refresh(self) -> None:
        state = self.controller.get_state()
        self.status_bar.update_values(self.controller.status_items())
        self.original_panel.update_panel(self.controller.get_original_image(), state.zoom_scale)
        self.result_panel.update_panel(self.controller.get_output_image(), state.zoom_scale)
        self.toolbar.set_zoom_mode(state.zoom_label)
        
        # Populate combobox options
        self._update_comboboxes()
        
        # Update metadata card values
        orig_meta = state.original_metadata
        out_meta = state.output_metadata
        
        # Left Panel metadata (Prompt, Seed, Sampler)
        if orig_meta:
            self.original_panel.meta_prompt_val.configure(text=getattr(orig_meta, "prompt", "-"))
            self.original_panel.meta_seed_val.configure(text=getattr(orig_meta, "seed", "-"))
            self.original_panel.meta_sampler_val.configure(text=getattr(orig_meta, "sampler", "-"))
            if orig_meta.filename in self.original_panel.combobox.cget("values"):
                self.original_panel.combobox.set(orig_meta.filename)
        else:
            self.original_panel.meta_prompt_val.configure(text="-")
            self.original_panel.meta_seed_val.configure(text="-")
            self.original_panel.meta_sampler_val.configure(text="-")
            self.original_panel.combobox.set(tr("no_selection", "Keine Auswahl"))
            
        # Right Panel metadata
        if out_meta:
            self.result_panel.meta_prompt_val.configure(text=getattr(out_meta, "prompt", "-"))
            self.result_panel.meta_seed_val.configure(text=getattr(out_meta, "seed", "-"))
            self.result_panel.meta_sampler_val.configure(text=getattr(out_meta, "sampler", "-"))
            if out_meta.filename in self.result_panel.combobox.cget("values"):
                self.result_panel.combobox.set(out_meta.filename)
        else:
            self.result_panel.meta_prompt_val.configure(text="-")
            self.result_panel.meta_seed_val.configure(text="-")
            self.result_panel.meta_sampler_val.configure(text="-")
            self.result_panel.combobox.set(tr("no_selection", "Keine Auswahl"))
            
        # Reset colors
        for val_lbl in (self.original_panel.meta_prompt_val, self.original_panel.meta_seed_val, self.original_panel.meta_sampler_val,
                        self.result_panel.meta_prompt_val, self.result_panel.meta_seed_val, self.result_panel.meta_sampler_val):
            val_lbl.configure(fg=PHOENIX_THEME.text_primary)

    def _compare_metadata(self) -> None:
        state = self.controller.get_state()
        orig_meta = state.original_metadata
        out_meta = state.output_metadata
        
        if orig_meta and out_meta:
            prompt_diff = getattr(orig_meta, "prompt", "-") != getattr(out_meta, "prompt", "-")
            seed_diff = getattr(orig_meta, "seed", "-") != getattr(out_meta, "seed", "-")
            sampler_diff = getattr(orig_meta, "sampler", "-") != getattr(out_meta, "sampler", "-")
            
            diff_color = PHOENIX_THEME.accent
            
            if prompt_diff:
                self.original_panel.meta_prompt_val.configure(fg=diff_color)
                self.result_panel.meta_prompt_val.configure(fg=diff_color)
            if seed_diff:
                self.original_panel.meta_seed_val.configure(fg=diff_color)
                self.result_panel.meta_seed_val.configure(fg=diff_color)
            if sampler_diff:
                self.original_panel.meta_sampler_val.configure(fg=diff_color)
                self.result_panel.meta_sampler_val.configure(fg=diff_color)
                
            self.controller.model.set_status("Metadaten verglichen - Unterschiede farblich hervorgehoben")
            self.status_bar.update_values(self.controller.status_items())

    def _on_original_selected(self, filename: str) -> None:
        if filename in ("Keine Auswahl", "No Selection", tr("no_selection", "Keine Auswahl")):
            return
        from config import OUTPUT_DIR
        filepath = Path(OUTPUT_DIR) / filename
        if filepath.exists():
            try:
                self.controller.load_original(filepath)
                self.refresh()
            except Exception as error:
                self._handle_error(error)

    def _on_output_selected(self, filename: str) -> None:
        if filename in ("Keine Auswahl", "No Selection", tr("no_selection", "Keine Auswahl")):
            return
        from config import OUTPUT_DIR
        filepath = Path(OUTPUT_DIR) / filename
        if filepath.exists():
            try:
                self.controller.load_output(filepath)
                self.refresh()
            except Exception as error:
                self._handle_error(error)

    def _open_original(self) -> None:
        filename = self._ask_image_filename(tr("open_original_image", "Originalbild öffnen"))
        if not filename:
            return
        try:
            self.controller.load_original(filename)
        except Exception as error:
            self._handle_error(error)
        self.refresh()

    def _open_output(self) -> None:
        filename = self._ask_image_filename(tr("open_output_image", "Ausgabebild öffnen"))
        if not filename:
            return
        try:
            self.controller.load_output(filename)
        except Exception as error:
            self._handle_error(error)
        self.refresh()

    def _set_zoom(self, zoom_label: str) -> None:
        self.controller.set_zoom(zoom_label)
        self.refresh()

    def _prepare_sync(self) -> None:
        self.controller.prepare_sync()
        self.refresh()

    def _swap_images(self) -> None:
        self.controller.swap_images()
        self.refresh()

    def _ask_image_filename(self, title: str) -> str:
        return filedialog.askopenfilename(title=title, filetypes=self.FILE_TYPES)

    def _handle_error(self, error: Exception) -> None:
        message = str(error) or error.__class__.__name__
        self.controller.set_error(message)
        messagebox.showerror("Compare Workspace", message)