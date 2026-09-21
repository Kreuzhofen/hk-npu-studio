from __future__ import annotations

import shutil
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from config import OUTPUT_DIR, TEMP_DIR
from controllers.inpainting_controller import InpaintingController
from app.i18n import tr
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.inpainting_canvas import PhoenixInpaintingCanvas
from widgets.phoenix.layout.workspace import WorkspaceFrame
from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixInpaintingView(WorkspaceFrame):
    """Phoenix Image Lab: RORem object removal on Qualcomm HTP."""

    def __init__(self, master: tk.Misc, controller: InpaintingController | None = None) -> None:
        super().__init__(
            master,
            title=tr("image_lab_editor_title", "Generatives Füllen & Retusche"),
            subtitle=tr("image_lab_editor_subtitle", "Maskierte Bildbereiche auf der Snapdragon NPU bearbeiten"),
        )
        self.controller = controller or InpaintingController(ui_dispatch=lambda callback: self.after(0, callback))
        self.input_path: Path | None = None
        self.result_path: Path | None = None
        self._build_canvas()
        self._build_inspector()
        self._build_status()

    def _build_canvas(self) -> None:
        toolbar = tk.Frame(self.header.toolbar_slot, bg=PHOENIX_THEME.content_bg)
        self.toolbar = toolbar
        toolbar.grid(row=0, column=0, sticky="ew")
        self.load_button = PhoenixButton(
            toolbar, text="Bild laden", command=self._load_image, button_type="neutral",
            icon_name="load_image", icon_color=PHOENIX_THEME.warning,
            font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        self.remove_button = PhoenixButton(
            toolbar, text="Bild entfernen", command=self._remove_image, button_type="neutral",
            icon_name="remove_image", font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        self.brush_button = PhoenixButton(
            toolbar, text="Pinsel", command=lambda: self._select_tool(False), button_type="nav_active",
            icon_name="sparkles",
            font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        self.eraser_button = PhoenixButton(
            toolbar, text="Radierer", command=lambda: self._select_tool(True), button_type="neutral",
            icon_name="remove_image",
            font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        self.clear_button = PhoenixButton(
            toolbar, text=tr("clear_mask", "Maske löschen"), command=self._clear_mask, button_type="neutral",
            icon_name="delete", icon_color=PHOENIX_THEME.danger,
            font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        self.undo_button = PhoenixButton(
            toolbar, text="Rückgängig", command=lambda: self.canvas.undo(), button_type="neutral",
            icon_name="back", font=PHOENIX_THEME.font_small, height=32, radius=6,
        )
        brush_controls = tk.Frame(self.header.toolbar_slot, bg=PHOENIX_THEME.content_bg)
        brush_controls.grid(row=1, column=0, sticky="w", pady=PHOENIX_THEME.space_xs)
        tk.Label(brush_controls, text="Pinselgröße", bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.text_secondary).pack(side="left")
        self.brush_size = tk.IntVar(value=48)
        tk.Scale(
            brush_controls, from_=8, to=160, orient="horizontal", variable=self.brush_size,
            command=lambda value: setattr(self.canvas, "brush_size", int(float(value))),
            bg=PHOENIX_THEME.content_bg, fg=PHOENIX_THEME.text_secondary,
            troughcolor=PHOENIX_THEME.card_bg, highlightthickness=0, length=150, showvalue=False,
        ).pack(side="left", padx=PHOENIX_THEME.space_sm)
        tk.Label(
            brush_controls, textvariable=self.brush_size, bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_secondary, font=PHOENIX_THEME.font_small,
        ).pack(side="left")
        self._toolbar_items = (
            self.load_button, self.remove_button, self.brush_button, self.eraser_button,
            self.undo_button, self.clear_button,
        )
        toolbar.bind("<Configure>", lambda event: self._reflow(toolbar, self._toolbar_items, event.width))
        self._reflow(toolbar, self._toolbar_items, 0)

        self.canvas = PhoenixInpaintingCanvas(self.content_slot)
        self.canvas.grid(row=0, column=0, sticky="nsew")

    def _build_inspector(self) -> None:
        host = self.inspector_slot
        host.grid_rowconfigure(0, weight=1)
        host.grid_columnconfigure(0, weight=1)
        scroll = tk.Canvas(host, width=300, bg=PHOENIX_THEME.card_bg, highlightthickness=0)
        bar = ttk.Scrollbar(host, orient="vertical", command=scroll.yview, style="Phoenix.Vertical.TScrollbar")
        scroll.grid(row=0, column=0, sticky="nsew")
        bar.grid(row=0, column=1, sticky="ns")
        scroll.configure(yscrollcommand=bar.set)
        panel = tk.Frame(scroll, bg=PHOENIX_THEME.card_bg)
        window = scroll.create_window((0, 0), window=panel, anchor="nw")
        panel.bind("<Configure>", lambda _event: scroll.configure(scrollregion=scroll.bbox("all")))
        scroll.bind("<Configure>", lambda event: scroll.itemconfigure(window, width=event.width))

        self._label(panel, "Prompt").pack(fill="x", padx=16, pady=(16, 4))
        self.prompt = tk.Text(
            panel, height=7, wrap="word", bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary, insertbackground=PHOENIX_THEME.text_primary,
            relief="flat", font=PHOENIX_THEME.font_body,
        )
        self.prompt.pack(fill="x", padx=16)
        self._label(panel, "Steps").pack(fill="x", padx=16, pady=(14, 4))
        self.steps = tk.IntVar(value=1)
        tk.Spinbox(panel, from_=1, to=4, textvariable=self.steps, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary).pack(fill="x", padx=16)
        self._label(panel, "Seed").pack(fill="x", padx=16, pady=(14, 4))
        self.seed = tk.StringVar(value="20260830")
        tk.Entry(panel, textvariable=self.seed, bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary, relief="flat").pack(fill="x", padx=16)

        buttons = tk.Frame(host, bg=PHOENIX_THEME.card_bg)
        buttons.grid(row=1, column=0, columnspan=2, sticky="ew", pady=PHOENIX_THEME.space_sm)
        self.start_button = PhoenixButton(
            buttons, text="Start", command=self._start, button_type="primary",
            icon_name="start", height=34, radius=8,
        )
        self.cancel_button = PhoenixButton(
            buttons, text=tr("cancel", "Abbrechen"), command=self.controller.cancel, button_type="danger",
            icon_name="stop", height=34, radius=8,
        )
        self.save_button = PhoenixButton(
            buttons, text="Speichern", command=self._save_result, button_type="secondary",
            icon_name="save", height=34, radius=8,
        )
        actions = (self.start_button, self.cancel_button, self.save_button)
        self.action_buttons = actions
        self.action_bar = buttons
        # Reserve the natural three-button width for the normal inspector.
        scroll.configure(width=sum(button.winfo_reqwidth() + 2 * PHOENIX_THEME.space_xs for button in actions))
        buttons.bind("<Configure>", lambda event: self._reflow(buttons, actions, event.width))
        self._reflow(buttons, actions, 0)

    @staticmethod
    def _reflow(host, items, width: int) -> None:
        # Same Configure/grid pattern as the generation toolbar; use font-sized
        # widget requests rather than fixed pixel thresholds at high DPI.
        gap = PHOENIX_THEME.space_xs
        widths = [item.winfo_reqwidth() + 2 * gap for item in items]
        columns = 1
        for candidate in range(len(items), 1, -1):
            required = sum(max(widths[column::candidate]) for column in range(candidate))
            if required <= width:
                columns = candidate
                break
        for column in range(len(items)):
            host.grid_columnconfigure(column, weight=0)
        for index, item in enumerate(items):
            item.grid(row=index // columns, column=index % columns, sticky="w", padx=gap, pady=gap)

    def _build_status(self) -> None:
        self.status_text = tk.StringVar(value="Bereit")
        tk.Label(
            self.status_slot, textvariable=self.status_text, bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_secondary, anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        self.progress = ttk.Progressbar(self.status_slot, maximum=1.0, style="Phoenix.Horizontal.TProgressbar")
        self.progress.grid(row=1, column=0, sticky="ew", pady=(4, 0))

    @staticmethod
    def _label(master: tk.Misc, text: str) -> tk.Label:
        return tk.Label(master, text=text, bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary, anchor="w")

    def _load_image(self) -> None:
        selected = filedialog.askopenfilename(filetypes=(("Bilddateien", "*.png *.jpg *.jpeg *.webp *.bmp"),))
        if selected:
            self.input_path = Path(selected)
            self.result_path = None
            self.canvas.load_image(selected)

    def _clear_mask(self) -> None:
        self.canvas.clear_mask()

    def _remove_image(self) -> None:
        self.input_path = self.result_path = None
        self.canvas.remove_image()
        self.status_text.set("Bereit")
        self.progress.configure(value=0.0)

    def _select_tool(self, erase: bool) -> None:
        self.canvas.set_tool(erase)
        self.brush_button.configure(button_type="neutral" if erase else "nav_active")
        self.eraser_button.configure(button_type="nav_active" if erase else "neutral")

    def _start(self) -> None:
        if self.input_path is None:
            messagebox.showerror("Phoenix Image Lab", "Bitte zuerst ein Bild laden.")
            return
        prompt = self.prompt.get("1.0", "end").strip()
        if not prompt:
            messagebox.showerror("Phoenix Image Lab", "Bitte einen Prompt eingeben.")
            return
        mask_path = TEMP_DIR / "image_lab" / "inpainting_mask.png"
        output_path = OUTPUT_DIR / f"generative_fill_{time.time_ns()}.png"
        self.canvas.save_mask(mask_path)
        self.controller.start(
            input_image_path=self.input_path,
            mask_image_path=mask_path,
            prompt=prompt,
            output_path=output_path,
            steps=self.steps.get(),
            seed=int(self.seed.get()),
            on_progress=self._on_progress,
            on_complete=self._on_complete,
        )

    def _on_progress(self, phase: str, value: float, detail: str | None) -> None:
        self.progress.configure(value=value)
        self.status_text.set(f"{phase}: {detail}" if detail else phase)

    def _on_complete(self, result) -> None:
        if self.input_path is None:
            return
        if result.success and result.output_path:
            self.result_path = Path(result.output_path)
            self.canvas.set_result(self.result_path)
            self.status_text.set("Abgeschlossen")
        else:
            self.status_text.set(f"{result.error_code}: {result.error_message}")

    def _save_result(self) -> None:
        if self.result_path is None:
            return
        selected = filedialog.asksaveasfilename(defaultextension=".png", filetypes=(("PNG", "*.png"),))
        if selected:
            shutil.copy2(self.result_path, selected)
