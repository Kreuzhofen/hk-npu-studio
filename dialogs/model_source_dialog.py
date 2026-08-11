from __future__ import annotations

import tkinter as tk
import webbrowser

from app.i18n import tr
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.theme import PHOENIX_THEME


class ModelSourceDialog(StudioDialog):
    """Explain OFFICIAL_EXTERNAL and LOCAL_ONLY acquisition before file selection."""

    OFFICIAL_SIZE = (720, 660)
    OFFICIAL_MIN_SIZE = (640, 600)

    def __init__(
        self,
        master: tk.Misc,
        model_name: str,
        source_type: str,
        source_url: str | None = None,
        package_format: str = "smp_or_zip",
        required_variant: str | None = None,
        brand: BrandManager | None = None,
    ) -> None:
        self.choice: str | None = None
        self.source_type = source_type
        self.source_url = source_url if source_type == "official_external" else None
        self.model_name = model_name
        self.package_format = package_format
        self.required_variant = str(required_variant or "").strip()
        super().__init__(
            master,
            title=tr("model_src_title_key", "Model installation"),
            brand=brand,
            size=self.OFFICIAL_SIZE if source_type == "official_external" else (660, 470),
            min_size=self.OFFICIAL_MIN_SIZE if source_type == "official_external" else (580, 440),
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
        self.add_title(self.model_name, tr("model_src_subtitle", "Guided model installation"))
        card = self.add_card()
        content = tk.Frame(card, bg=PHOENIX_THEME.elevated_bg)
        content.pack(
            fill="x",
            padx=PHOENIX_THEME.card_pad_x,
            pady=PHOENIX_THEME.card_pad_y,
        )

        official = self.source_type == "official_external"
        description = tr(
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
            text=tr(
                "model_src_expected_format",
                "Expected package: {format}",
                format=self.package_format_text(self.package_format),
            ),
            bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title, anchor="w",
        ).pack(fill="x")

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
        else:
            tk.Label(
                self.body,
                text=tr(
                    "model_src_local_install_note",
                    "Select an existing model package. Snapdragon AI Studio handles verification and installation.",
                ),
                bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_body, anchor="w", justify="left", wraplength=540,
            ).pack(fill="x", pady=(0, PHOENIX_THEME.space_lg))

        if official:
            self.download_button = PhoenixButton(
                self.body,
                text=tr("model_src_open_official", "Open Qualcomm AI Hub"),
                command=self._on_download,
                button_type="primary",
                width=460,
            )
            self.download_button.pack(anchor="center", pady=(0, PHOENIX_THEME.space_md))

        self.install_button = PhoenixButton(
            self.body,
            text=tr("model_src_select_existing", "Select existing model package"),
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

    def _on_install(self) -> None:
        self.choice = "install"
        self.close()

    def _on_cancel(self) -> None:
        self.choice = "cancel"
        self.close()
