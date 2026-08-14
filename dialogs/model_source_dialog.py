from __future__ import annotations

import tkinter as tk
import webbrowser

from app.i18n import tr, get_current_language
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.theme import PHOENIX_THEME


class ModelSourceDialog(StudioDialog):
    """Explain OFFICIAL_EXTERNAL and LOCAL_ONLY acquisition before file selection."""

    OFFICIAL_SIZE = (720, 660)
    OFFICIAL_MIN_SIZE = (640, 600)
    SD35_SIZE = (740, 800)
    SD35_MIN_SIZE = (660, 720)

    def __init__(
        self,
        master: tk.Misc,
        model_name: str,
        source_type: str,
        source_url: str | None = None,
        reference_url: str | None = None,
        package_format: str = "smp_or_zip",
        required_variant: str | None = None,
        requires_hf_token: bool = False,
        brand: BrandManager | None = None,
    ) -> None:
        self.choice: str | None = None
        self.source_type = source_type
        self.source_url = source_url if source_type == "official_external" else None
        self.reference_url = str(reference_url or "").strip() or None
        self.sd35_guided = source_type == "local_only" and "stable_diffusion_v3_5" in str(self.reference_url or "")
        self.model_name = model_name
        self.package_format = package_format
        self.required_variant = str(required_variant or "").strip()
        self.requires_hf_token = bool(requires_hf_token)
        super().__init__(
            master,
            title=tr("model_src_title_key", "Model installation"),
            brand=brand,
            size=self.SD35_SIZE if self.sd35_guided else self.OFFICIAL_SIZE if source_type == "official_external" or self.reference_url else (660, 470),
            min_size=self.SD35_MIN_SIZE if self.sd35_guided else self.OFFICIAL_MIN_SIZE if source_type == "official_external" or self.reference_url else (580, 440),
            resizable=True,
        )
        self._build_ui()
        self.center(master)
        self.wait_window(self)

    @staticmethod
    def package_format_text(package_format: str) -> str:
        return {
            "zip": tr("model_src_format_zip", "ZIP package"),
            "smp": tr("model_src_format_smp", "SMP package"),
            "smp_or_zip": tr("model_src_format_smp_zip", "SMP or ZIP package"),
        }.get(package_format, tr("model_src_format_smp_zip", "SMP or ZIP package"))

    def _build_ui(self) -> None:
        if self.sd35_guided:
            self._build_guided_ui()
        else:
            self._build_normal_ui()

    def _build_guided_ui(self) -> None:
        self.current_step = 1
        self.STEP_TITLE = "title"
        self.STEP_TEXT = "text"
        self.STEP_BTN_TEXT = "button_text"

        self.reference_url = "https://github.com/qualcomm/qai-appbuilder/archive/refs/heads/main.zip"

        self.step_data = {
            1: {
                self.STEP_TITLE: tr("model_src_sd35_step1_title", "Step 1 of 2 – Download Qualcomm QAI AppBuilder"),
                self.STEP_TEXT: tr("model_src_sd35_guided_description", "The official Qualcomm files are required to install Stable Diffusion 3.5 Medium."),
                self.STEP_BTN_TEXT: tr("model_src_sd35_open_official", "Download Qualcomm QAI AppBuilder"),
            },
            2: {
                self.STEP_TITLE: tr("model_src_sd35_step2_title", "Step 2 of 2 – Set up SD3.5 automatically"),
                self.STEP_TEXT: tr("model_src_sd35_step2_text", "Snapdragon AI Studio can now prepare and set up the model fully automatically for you.\n\nPhoenix will locate the downloaded ZIP file in your Downloads folder, extract it to a temporary directory, install all required Python components, and run the Qualcomm script to automatically retrieve and convert the model files.\n\nClick the 'Set up SD3.5 automatically' button and wait for the process to complete. This may take several minutes."),
                self.STEP_BTN_TEXT: tr("model_src_sd35_step2_btn_text", "Set up SD3.5 automatically"),
            },
        }

        self.add_title(self.model_name, tr("model_src_subtitle", "Guided model installation"))
        self.step_card = self.add_card()

        self.step_container = tk.Frame(self.step_card, bg=PHOENIX_THEME.elevated_bg)
        self.step_container.pack(
            fill="both",
            expand=True,
            padx=PHOENIX_THEME.card_pad_x,
            pady=PHOENIX_THEME.card_pad_y,
        )

        lbl_prev = tr("model_src_back", "< Back")
        lbl_next = tr("model_src_next", "Next >")
        lbl_cancel = tr("cancel", "Cancel")

        self.prev_button = PhoenixButton(
            self.footer,
            text=lbl_prev,
            command=self._on_prev,
            button_type="secondary",
            width=140,
        )
        self.prev_button.pack(side="left", padx=(0, 10))

        self.cancel_button = PhoenixButton(
            self.footer,
            text=lbl_cancel,
            command=self._on_cancel,
            button_type="neutral",
            width=140,
        )
        self.cancel_button.pack(side="left", expand=True)

        self.next_button = PhoenixButton(
            self.footer,
            text=lbl_next,
            command=self._on_next,
            button_type="primary",
            width=140,
        )
        self.next_button.pack(side="right", padx=(10, 0))

        self._show_current_step()

    def _on_prev(self) -> None:
        if self.current_step > 1:
            self.current_step -= 1
            self._show_current_step()

    def _on_next(self) -> None:
        if self.sd35_guided and self.current_step == 1:
            self._on_auto_install()
        elif self.current_step < 2:
            self.current_step += 1
            self._show_current_step()

    def _copy_text(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_idletasks()

    def _on_auto_install(self) -> None:
        self.choice = "install_sd35_auto"
        self.close()

    def _show_current_step(self) -> None:
        for child in self.step_container.winfo_children():
            child.destroy()

        step = self.step_data[self.current_step]

        title_lbl = tk.Label(
            self.step_container,
            text=step[self.STEP_TITLE],
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
            justify="left",
        )
        title_lbl.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))

        body_lbl = tk.Label(
            self.step_container,
            text=step[self.STEP_TEXT],
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            justify="left",
            wraplength=640,
        )
        body_lbl.pack(fill="x", pady=(0, PHOENIX_THEME.space_lg))
        self._bind_responsive_wrap(self.step_container, body_lbl)

        tk.Label(
            self.step_container,
            text=tr(
                "model_hf_token_required" if self.requires_hf_token else "model_hf_token_not_required",
                "Hugging Face Access Token: Required." if self.requires_hf_token else "Hugging Face Access Token: Not required.",
            ),
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small, anchor="w",
        ).pack(fill="x", pady=(0, PHOENIX_THEME.space_md))

        if self.current_step == 1:
            btn = PhoenixButton(
                self.step_container,
                text=step[self.STEP_BTN_TEXT],
                command=self._on_reference,
                button_type="primary",
                width=320,
            )
            btn.pack(anchor="w", pady=(0, PHOENIX_THEME.space_md))

        elif self.current_step == 2:
            btn = PhoenixButton(
                self.step_container,
                text=step[self.STEP_BTN_TEXT],
                command=self._on_auto_install,
                button_type="primary",
                width=320,
            )
            btn.pack(anchor="w", pady=(0, PHOENIX_THEME.space_md))

        if self.current_step == 1:
            self.prev_button.configure(state="disabled")
        else:
            self.prev_button.configure(state="normal")

        if self.current_step == 2:
            self.next_button.configure(state="disabled")
        else:
            self.next_button.configure(state="normal")

    def _build_normal_ui(self) -> None:
        self.add_title(self.model_name, tr("model_src_subtitle", "Guided model installation"))
        card = self.add_card()
        content = tk.Frame(card, bg=PHOENIX_THEME.elevated_bg)
        content.pack(
            fill="x",
            padx=PHOENIX_THEME.card_pad_x,
            pady=PHOENIX_THEME.card_pad_y,
        )

        official = self.source_type == "official_external"
        referenced_local = not official and bool(self.reference_url)
        description = tr(
            "model_src_sd35_guided_description",
            "Stable Diffusion 3.5 Medium for Snapdragon is provided by Qualcomm. Snapdragon AI Studio cannot currently perform the Qualcomm model download itself because it uses only clearly documented download and usage rights. This guide takes you through the official Qualcomm route; afterwards, Snapdragon AI Studio handles verification and installation automatically.",
        ) if self.sd35_guided else tr(
            "model_src_official_description",
            "A fully automated download path is not yet available for this model.",
        ) if official else tr(
            "model_src_local_description",
            "Automatic download is not currently configured for this model.",
        )
        description_label = tk.Label(
            content, text=description,
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body, anchor="w", justify="left", wraplength=520,
        )
        description_label.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))
        self._bind_responsive_wrap(content, description_label)

        if referenced_local:
            source_label = tk.Label(
                content,
                text=tr(
                    "model_src_sd35_official_source",
                    "Official technology source: Qualcomm QAI AppBuilder",
                ),
                bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_small, anchor="w", justify="left", wraplength=520,
            )
            source_label.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))
            self._bind_responsive_wrap(content, source_label)

        if official and self.source_url:
            source_label = tk.Label(
                content,
                text=tr("model_src_official_source_name", "Official source: Qualcomm AI Hub"),
                bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_muted,
                font=PHOENIX_THEME.font_small, anchor="w", justify="left", wraplength=520,
            )
            source_label.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))
            self._bind_responsive_wrap(content, source_label)

        tk.Label(
            content,
            text=(
                tr("model_src_sd35_expected_folder", "Expected: folder created by the Qualcomm sample")
                if self.sd35_guided
                else tr(
                    "model_src_expected_format",
                    "Expected package: {format}",
                    format=self.package_format_text(self.package_format),
                )
            ),
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title, anchor="w",
        ).pack(fill="x")

        token_label = tk.Label(
            content,
            text=tr(
                "model_hf_token_required" if self.requires_hf_token else "model_hf_token_not_required",
                "Hugging Face Access Token: Required." if self.requires_hf_token else "Hugging Face Access Token: Not required.",
            ),
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small, anchor="w", justify="left", wraplength=520,
        )
        token_label.pack(fill="x", pady=(PHOENIX_THEME.space_sm, 0))
        self._bind_responsive_wrap(content, token_label)

        if referenced_local:
            reference_label = tk.Label(
                content,
                text=tr(
                    "model_src_sd35_reference_explanation",
                    "This is Qualcomm's official guide for Stable Diffusion 3.5 Medium on Snapdragon. The Qualcomm sample downloads and extracts the matching model for your processor.",
                ),
                bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.warning,
                font=PHOENIX_THEME.font_small, anchor="w", justify="left", wraplength=520,
            )
            reference_label.pack(fill="x", pady=(PHOENIX_THEME.space_md, 0))
            self._bind_responsive_wrap(content, reference_label)

        if self.sd35_guided:
            steps_card = self.add_card()
            steps_content = tk.Frame(steps_card, bg=PHOENIX_THEME.elevated_bg)
            steps_content.pack(fill="x", padx=PHOENIX_THEME.card_pad_x, pady=PHOENIX_THEME.card_pad_y)
            steps_label = tk.Label(
                steps_content,
                text=tr(
                    "model_src_sd35_steps",
                    "1. Open the official Qualcomm instructions.\n2. Prepare QAI AppBuilder and run the SD3.5 sample.\n3. Wait until Qualcomm has downloaded and extracted the model.\n4. Return here and select the generated model folder.",
                ),
                bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
                font=PHOENIX_THEME.font_body, anchor="w", justify="left", wraplength=520,
            )
            steps_label.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))
            self._bind_responsive_wrap(steps_content, steps_label)
            self.command_text = "python GenerativeAI\\Image_Generation\\stable_diffusion_v3_5\\stable_diffusion_v3_5.py"
            command_label = tk.Label(
                steps_content, text=self.command_text,
                bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_caption, anchor="w", justify="left", wraplength=520,
            )
            command_label.pack(fill="x", pady=(0, PHOENIX_THEME.space_sm))
            self._bind_responsive_wrap(steps_content, command_label)
            PhoenixButton(
                steps_content,
                text=tr("model_src_sd35_copy_command", "Copy command"),
                command=self._copy_command,
                button_type="secondary",
                width=180,
            ).pack(anchor="w")

        if official:
            if self.required_variant:
                contract_text = tr(
                    "model_src_required_variant",
                    "Select on Qualcomm AI Hub: {variant}",
                    variant=self.required_variant,
                )
                contract_color = PHOENIX_THEME.text_primary
            else:
                contract_text = tr(
                    "model_src_variant_missing",
                    "Snapdragon AI Studio can verify and install a compatible package automatically, but the exact Qualcomm file variant is not yet defined in the model contract.",
                )
                contract_color = PHOENIX_THEME.warning
            contract_label = tk.Label(
                content, text=contract_text,
                bg=PHOENIX_THEME.elevated_bg, fg=contract_color,
                font=PHOENIX_THEME.font_small, anchor="w", justify="left", wraplength=520,
            )
            contract_label.pack(fill="x", pady=(PHOENIX_THEME.space_md, 0))
            self._bind_responsive_wrap(content, contract_label)

        if official:
            help_card = self.add_card()
            help_content = tk.Frame(help_card, bg=PHOENIX_THEME.elevated_bg)
            help_content.pack(
                fill="x",
                padx=PHOENIX_THEME.card_pad_x,
                pady=PHOENIX_THEME.card_pad_y,
            )
            help_label = tk.Label(
                help_content,
                text=tr(
                    "model_src_official_compatible_help",
                    "Select only an already prepared ZIP or SMP package compatible with Snapdragon AI Studio.",
                ),
                bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_body, anchor="w", justify="left", wraplength=520,
            )
            help_label.pack(fill="x")
            self._bind_responsive_wrap(help_content, help_label)
        elif not referenced_local:
            tk.Label(
                self.body,
                text=tr(
                    "model_src_local_install_note",
                    "Select an existing model package. Snapdragon AI Studio handles verification and installation.",
                ),
                bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_body, anchor="w", justify="left", wraplength=540,
            ).pack(fill="x", pady=(0, PHOENIX_THEME.space_lg))

        if referenced_local:
            help_card = self.add_card()
            help_content = tk.Frame(help_card, bg=PHOENIX_THEME.elevated_bg)
            help_content.pack(
                fill="x",
                padx=PHOENIX_THEME.card_pad_x,
                pady=PHOENIX_THEME.card_pad_y,
            )
            help_label = tk.Label(
                help_content,
                text=tr(
                    "model_src_sd35_compatible_help",
                    "After the Qualcomm sample has finished, select the model folder it created. Snapdragon AI Studio then creates the manifest and checksums automatically.",
                ),
                bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_body, anchor="w", justify="left", wraplength=520,
            )
            help_label.pack(fill="x")
            self._bind_responsive_wrap(help_content, help_label)

        if official:
            self.download_button = PhoenixButton(
                self.body,
                text=tr("model_src_open_official", "Open Qualcomm AI Hub"),
                command=self._on_download,
                button_type="primary",
                width=460,
            )
            self.download_button.pack(anchor="center", pady=(0, PHOENIX_THEME.space_md))
        elif referenced_local:
            self.download_button = PhoenixButton(
                self.body,
                text=tr("model_src_sd35_open_official_instr", "Open Qualcomm instructions"),
                command=self._on_reference,
                button_type="primary",
                width=460,
            )
            self.download_button.pack(anchor="center", pady=(0, PHOENIX_THEME.space_md))

        self.install_button = PhoenixButton(
            self.body,
            text=(
                tr("model_src_sd35_select_folder", "Select Qualcomm model folder")
                if self.sd35_guided
                else tr("model_src_select_existing", "Select existing model package")
            ),
            command=self._on_install,
            button_type="secondary",
            width=460,
        )
        self.install_button.pack(anchor="center")

        self.cancel_button = PhoenixButton(
            self.footer, text=tr("cancel", "Cancel"), command=self._on_cancel,
            button_type="neutral", width=140,
        )
        self.cancel_button.pack(anchor="center")

    @staticmethod
    def _bind_responsive_wrap(container: tk.Misc, label: tk.Label) -> None:
        container.bind(
            "<Configure>",
            lambda event: label.configure(wraplength=max(240, event.width - 2)),
            add="+",
        )

    def _on_download(self) -> None:
        if self.source_url:
            webbrowser.open(self.source_url)

    def _on_reference(self) -> None:
        if self.reference_url:
            webbrowser.open(self.reference_url)

    def _on_install(self) -> None:
        self.choice = "install_folder" if self.sd35_guided else "install"
        self.close()

    def _copy_command(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.command_text)
        self.update_idletasks()

    def _on_cancel(self) -> None:
        self.choice = "cancel"
        self.close()
