from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from controllers.gallery_model import GalleryImage
from widgets.phoenix.layout.workspace import WorkspaceInfoCard, WorkspacePanel
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr
from widgets.phoenix.controls.button import PhoenixButton


class GalleryInspector(WorkspacePanel):
    """Inspector area for selected Gallery image metadata."""

    def __init__(
        self,
        master: tk.Misc,
        on_apply_settings: Callable[[dict], None] | None = None,
        on_show_in_explorer: Callable[[GalleryImage], None] | None = None,
        on_delete_image: Callable[[GalleryImage], None] | None = None,
    ) -> None:
        self.on_apply_settings = on_apply_settings
        self.on_show_in_explorer = on_show_in_explorer
        self.on_delete_image = on_delete_image
        self._current_image: GalleryImage | None = None
        super().__init__(
            master,
            title=tr("inspector_title", "Inspector"),
            subtitle=tr("inspector_subtitle", "Bilddetails und Auswahlstatus"),
            width=286,
        )
        self.selection_card: WorkspaceInfoCard
        self.file_card: WorkspaceInfoCard
        self.generation_card: WorkspaceInfoCard
        self.path_card: WorkspaceInfoCard

        # Configure layout row weights to support stretching content vertically
        self.grid_rowconfigure(2, weight=1)
        self.content.grid_configure(sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)

        self._build()
        self.update_selection([])

    def _add_button_hover(self, button: tk.Button, hover_bg: str | None = None, hover_fg: str | None = None) -> None:
        original_bg = button.cget("bg")
        original_fg = button.cget("fg")
        h_bg = hover_bg or PHOENIX_THEME.accent
        h_fg = hover_fg or PHOENIX_THEME.text_on_accent

        def on_enter(event):
            if str(button.cget("state")) != "disabled":
                button.configure(bg=h_bg, fg=h_fg)

        def on_leave(event):
            if str(button.cget("state")) != "disabled":
                button.configure(bg=original_bg, fg=original_fg)

        button.bind("<Enter>", on_enter, add="+")
        button.bind("<Leave>", on_leave, add="+")

    def _show_in_explorer(self) -> None:
        if self._current_image and self.on_show_in_explorer:
            self.on_show_in_explorer(self._current_image)

    def _delete_image(self) -> None:
        if self._current_image and self.on_delete_image:
            self.on_delete_image(self._current_image)

    def _build(self) -> None:
        # Fixed area in self.content for Quick Actions (row 0)
        self.fixed_header = tk.Frame(self.content, bg=PHOENIX_THEME.card_bg)
        self.fixed_header.grid(row=0, column=0, sticky="ew")
        self.fixed_header.grid_columnconfigure(0, weight=1)

        self.apply_btn = PhoenixButton(
            self.fixed_header,
            text=tr("apply_settings_btn", "Prompt & Settings übernehmen"),
            command=self._apply_settings,
            button_type="primary",
            icon_name="start",
            height=36,
        )
        self.apply_btn.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(0, 4),
        )

        self.explorer_btn = PhoenixButton(
            self.fixed_header,
            text=tr("show_in_explorer_btn", "Im Explorer anzeigen"),
            command=self._show_in_explorer,
            button_type="neutral",
            icon_name="folder",
            height=36,
        )
        self.explorer_btn.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=4,
        )

        self.delete_btn = PhoenixButton(
            self.fixed_header,
            text=tr("delete_btn", "Löschen"),
            command=self._delete_image,
            button_type="danger",
            icon_name="delete",
            height=36,
        )
        self.delete_btn.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(4, PHOENIX_THEME.space_md),
        )

        self.fixed_header.grid_remove()

        # Scrollable container under fixed_header
        self.content.grid_rowconfigure(1, weight=1)

        self.scroll_canvas = tk.Canvas(
            self.content,
            bg=PHOENIX_THEME.card_bg,
            highlightthickness=0,
            bd=0,
            width=266,
        )
        self.scrollbar = ttk.Scrollbar(
            self.content,
            orient="vertical",
            command=self.scroll_canvas.yview,
            style="Phoenix.Vertical.TScrollbar"
        )
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scroll_canvas.grid(row=1, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=1, sticky="ns")

        self.scroll_content = tk.Frame(self.scroll_canvas, bg=PHOENIX_THEME.card_bg)
        self.scroll_content.grid_columnconfigure(0, weight=1)

        self.canvas_window = self.scroll_canvas.create_window(
            (0, 0),
            window=self.scroll_content,
            anchor="nw",
            width=266
        )

        def configure_scroll(event):
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        self.scroll_content.bind("<Configure>", configure_scroll)

        def _on_mousewheel(event):
            if self.scroll_canvas.winfo_exists():
                self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(event):
            self.scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(event):
            self.scroll_canvas.unbind_all("<MouseWheel>")

        self.scroll_canvas.bind("<Enter>", _bind_mousewheel)
        self.scroll_canvas.bind("<Leave>", _unbind_mousewheel)

        # Build cards inside scrollable container
        self.selection_card = self._create_section(tr("inspector_selection", "Auswahl"), 0)
        self.file_card = self._create_section(tr("inspector_file", "Datei"), 1)
        self.generation_card = self._create_section(tr("inspector_generation", "Generierung"), 2)
        self.path_card = self._create_section(tr("inspector_path", "Pfad"), 3)

    def _apply_settings(self) -> None:
        if self._current_image and self.on_apply_settings:
            meta = dict(self._current_image.metadata)
            if "prompt" not in meta and self._current_image.prompt:
                meta["prompt"] = self._current_image.prompt
            if "model" not in meta and self._current_image.model_id:
                meta["model"] = self._current_image.model_id
            if "seed" not in meta and self._current_image.seed is not None:
                meta["seed"] = self._current_image.seed
            self.on_apply_settings(meta)

    def update_selection(self, images: list[GalleryImage]) -> None:
        if not images:
            self._current_image = None
            self.apply_btn.grid_remove()
            self.fixed_header.grid_remove()
            self._set_section(self.selection_card, (tr("no_selection", "Keine Auswahl"), tr("select_thumbnail_instruction", "Klicke ein Thumbnail an.")))
            self._set_section(
                self.file_card,
                (
                    tr("name_label", "Name: {name}", name="-"),
                    tr("resolution_label", "Auflösung: {res}", res="-"),
                    tr("format_label", "Format: {fmt}", fmt="-"),
                    tr("size_label", "Dateigröße: {size}", size="-"),
                    tr("created_label", "Erstellt: {date}", date="-"),
                ),
            )
            self._set_section(
                self.generation_card,
                (
                    tr("model_label", "Modell: {model}", model="-"),
                    tr("prompt_label", "Prompt: {prompt}", prompt="-"),
                    tr("seed_label", "Seed: {seed}", seed="-"),
                ),
            )
            self._set_section(self.path_card, ("-",))
            return

        if len(images) > 1:
            self._current_image = None
            self.apply_btn.grid_remove()
            self.fixed_header.grid_remove()
            self._set_section(
                self.selection_card,
                (
                    tr("multiple_images_selected", "{count} Bilder ausgewählt", count=len(images)),
                    tr("ctrl_shift_active", "Ctrl/Shift-Auswahl aktiv."),
                ),
            )
            self._set_section(self.file_card, (tr("multiple_selection", "Mehrfachauswahl"), tr("multiple_selection_details", "Einzeldetails werden nicht erzwungen.")))
            self._set_section(self.generation_card, (tr("multiple_selection", "Mehrfachauswahl"), ""))
            self._set_section(self.path_card, ("-",))
            return

        image = images[0]
        self._current_image = image
        self.apply_btn.grid()
        self.fixed_header.grid()

        self._set_section(self.selection_card, (tr("one_image_selected", "1 Bild ausgewählt"), image.filename))
        self._set_section(
            self.file_card,
            (
                tr("name_label", "Name: {name}", name=image.filename),
                tr("resolution_label", "Auflösung: {res}", res=image.resolution_label),
                tr("format_label", "Format: {fmt}", fmt=image.format_label),
                tr("size_label", "Dateigröße: {size}", size=image.size_label),
                tr("created_label", "Erstellt: {date}", date=image.created_label),
            ),
        )

        prompt_val = image.prompt or "-"
        model_val = image.model_id or "-"
        seed_val = str(image.seed) if image.seed is not None else "-"

        meta = image.metadata
        steps_val = str(meta.get("steps", "-"))
        cfg_val = str(meta.get("cfg") or meta.get("cfg_scale", "-"))
        sampler_val = meta.get("sampler", "-")
        scheduler_val = meta.get("scheduler", "-")

        gen_lines: list[str] = []

        if meta.get("_metadata_error"):
            gen_lines.append(tr("metadata_corrupt_label", "Status: Metadaten unvollständig oder beschädigt"))
        elif not image.prompt and not image.model_id and not meta.get("feature") and not meta.get("mode"):
            gen_lines.append(tr("asset_type_original", "Typ: Originalbild (Eingabe / Import)"))
            gen_lines.append(tr("no_generation_metadata", "Keine KI-Generierungsparameter vorhanden"))
        else:
            feature_raw = meta.get("feature") or meta.get("mode") or ""
            if feature_raw in ("Image-to-Image", "img2img"):
                feature_name = "Bild-zu-Bild (Image-to-Image)"
            elif feature_raw in ("Inpainting", "inpaint"):
                feature_name = "Inpainting"
            else:
                feature_name = "Text-to-Image"

            gen_lines.append(tr("asset_type_generated", "Typ: KI-Generierung ({feature})", feature=feature_name))
            gen_lines.append(tr("model_label", "Modell: {model}", model=model_val))
            gen_lines.append(tr("prompt_label", "Prompt: {prompt}", prompt=prompt_val))

            neg_prompt = meta.get("negative_prompt")
            if neg_prompt:
                gen_lines.append(tr("negative_prompt_label", "Negativ-Prompt: {neg_prompt}", neg_prompt=neg_prompt))

            gen_lines.append(tr("seed_label", "Seed: {seed}", seed=seed_val))

            # Denoising Strength if present (Image-to-Image / Inpainting)
            denoising_val = meta.get("denoising_strength")
            if denoising_val is not None:
                try:
                    d_flt = float(denoising_val)
                    if abs(d_flt - 0.30) < 0.01:
                        d_str = "0.30 (Subtil)"
                    elif abs(d_flt - 0.45) < 0.01:
                        d_str = "0.45 (Moderat)"
                    elif abs(d_flt - 0.65) < 0.01:
                        d_str = "0.65 (Ausgewogen)"
                    elif abs(d_flt - 0.80) < 0.01:
                        d_str = "0.80 (Kreativ)"
                    elif abs(d_flt - 1.00) < 0.01:
                        d_str = "1.00 (Neugenerierung)"
                    else:
                        d_str = f"{d_flt:.2f}"
                except (ValueError, TypeError):
                    d_str = str(denoising_val)
                gen_lines.append(tr("denoising_label", "Denoising-Stärke: {denoising}", denoising=d_str))

            # Steps & Actual Steps
            actual_steps_val = meta.get("actual_steps") or meta.get("actual_inference_steps")
            if actual_steps_val is not None and str(actual_steps_val) != steps_val:
                gen_lines.append(tr("actual_steps_label", "HTP-Schritte: {actual} (von {total})", actual=actual_steps_val, total=steps_val))
            else:
                gen_lines.append(tr("steps_label", "Schritte: {steps}", steps=steps_val))

            gen_lines.extend([
                tr("cfg_label", "CFG-Skala: {cfg}", cfg=cfg_val),
                tr("sampler_label", "Sampler: {sampler}", sampler=sampler_val),
                tr("scheduler_label", "Scheduler: {scheduler}", scheduler=scheduler_val),
            ])

            # Reference Control details
            ref_ctrl = meta.get("reference_control")
            if isinstance(ref_ctrl, dict) and ref_ctrl.get("enabled"):
                ref_mode = ref_ctrl.get("mode", "unknown")
                if ref_mode == "canny_qnn":
                    ref_mode_str = "Modus A · Konturtreue (Canny QNN)"
                elif ref_mode == "latent_anchor":
                    ref_mode_str = "Modus B · Strukturtreue (Latent Anchor)"
                else:
                    ref_mode_str = str(ref_mode)
                gen_lines.append(tr("ref_mode_label_insp", "Referenz-Modus: {mode}", mode=ref_mode_str))

                fidelity_val = ref_ctrl.get("fidelity")
                if fidelity_val is not None:
                    try:
                        gen_lines.append(tr("ref_fidelity_label_insp", "Bindungsstärke: {fidelity}", fidelity=f"{float(fidelity_val):.2f}"))
                    except (ValueError, TypeError):
                        pass

                ref_img = ref_ctrl.get("reference_image")
                if ref_img:
                    gen_lines.append(tr("ref_source_label_insp", "Referenzbild: {src}", src=Path(ref_img).name))

            # Input source image path
            in_path = meta.get("input_image_path")
            if in_path:
                gen_lines.append(tr("ref_source_label_insp", "Ausgangsbild: {src}", src=Path(in_path).name))

            # Material Priming
            mat_preset = meta.get("material_preset")
            if mat_preset:
                preset_display_names = {
                    "24k_gold": "24k Gold",
                    "antique_brass": "Antik-Messing",
                    "copper": "Kupfer",
                    "chrome": "Chrom",
                }
                mat_name = preset_display_names.get(mat_preset, str(mat_preset))
                mat_intensity = meta.get("material_priming_intensity")
                if mat_intensity is not None:
                    try:
                        mat_str = f"{mat_name} ({int(float(mat_intensity) * 100)}%)"
                    except (ValueError, TypeError):
                        mat_str = f"{mat_name} ({mat_intensity})"
                else:
                    mat_str = mat_name
                gen_lines.append(tr("material_priming_label_insp", "Material-Priming: {preset}", preset=mat_str))

            # Backend
            backend_str = meta.get("backend")
            if backend_str:
                gen_lines.append(tr("backend_label_insp", "Backend: {backend}", backend=backend_str))

            # Runtime
            total_sec = meta.get("total_seconds")
            if total_sec is not None:
                try:
                    gen_lines.append(tr("inference_time_label_insp", "NPU-Laufzeit: {time:.1f} s", time=float(total_sec)))
                except (ValueError, TypeError):
                    pass

        if meta.get("controlnet_enabled"):
            cn_model = meta.get("controlnet_model") or "canny"
            low_thresh = meta.get("canny_low_threshold")
            high_thresh = meta.get("canny_high_threshold")
            cond_scale = meta.get("controlnet_conditioning_scale")

            gen_lines.extend([
                tr("controlnet_model_label", "ControlNet-Modell: {cn_model}", cn_model=cn_model),
                tr("canny_low_threshold_label_insp", "Canny Low Threshold: {low}", low=str(low_thresh) if low_thresh is not None else "-"),
                tr("canny_high_threshold_label_insp", "Canny High Threshold: {high}", high=str(high_thresh) if high_thresh is not None else "-"),
                tr("controlnet_strength_label_insp", "ControlNet-Stärke: {scale}", scale=str(cond_scale) if cond_scale is not None else "-"),
            ])

        self._set_section(self.generation_card, tuple(gen_lines))
        self._set_section(self.path_card, (str(image.path),))

    def _create_section(self, title: str, row: int) -> WorkspaceInfoCard:
        card = WorkspaceInfoCard(self.scroll_content, title)
        card.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(0, PHOENIX_THEME.space_md),
        )
        return card

    def _set_section(self, card: WorkspaceInfoCard, lines: tuple[str, ...]) -> None:
        card.set_lines(lines)
