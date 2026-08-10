"""
Snapdragon AI Studio

Model Source Selection Dialog

Created by Holger Kreuzhofen
Phoenix UI
"""

from __future__ import annotations

import tkinter as tk
import webbrowser
from app.i18n import get_current_language, tr
from dialogs.studio_dialog import StudioDialog
from engine.brand_manager import BrandManager
from widgets.phoenix.theme import PHOENIX_THEME


class ModelSourceDialog(StudioDialog):
    def __init__(self, master: tk.Misc, model_name: str, source_url: str | None = None, brand: BrandManager | None = None) -> None:
        self.choice: str | None = None
        self.source_url = source_url
        self.model_name = model_name

        lang = get_current_language()
        if lang == "de_DE":
            title = tr("model_src_title_key" + "", "Modell-Installation")
        elif lang == "es_ES":
            title = tr("model_src_title_key" + "", "Instalación del modelo")
        else:
            title = tr("model_src_title_key" + "", "Model Installation")

        super().__init__(
            master,
            title=title,
            brand=brand,
            size=(480, 360),
            min_size=(440, 320),
            resizable=False,
        )

        self._build_ui()
        self.center(master)
        self.wait_window(self)

    def _build_ui(self) -> None:
        lang = get_current_language()
        if lang == "de_DE":
            desc_text = tr("model_src_desc_key" + "", "Das Modell wird nicht mit Snapdragon AI Studio ausgeliefert und muss separat von der offiziellen Quelle bezogen werden.")
            btn_download_text = tr("model_src_dl_key" + "", "Von offizieller Quelle herunterladen")
            btn_install_text = tr("model_src_inst_key" + "", "Bereits heruntergeladenes Modell installieren")
            btn_cancel_text = tr("model_src_cancel_key" + "", "Abbrechen")
        elif lang == "es_ES":
            desc_text = tr("model_src_desc_key" + "", "El modelo no se distribuye con Snapdragon AI Studio y debe obtenerse por separado de la fuente oficial.")
            btn_download_text = tr("model_src_dl_key" + "", "Descargar de la fuente oficial")
            btn_install_text = tr("model_src_inst_key" + "", "Instalar modelo ya descargado")
            btn_cancel_text = tr("model_src_cancel_key" + "", "Cancelar")
        else:
            desc_text = tr("model_src_desc_key" + "", "The model is not distributed with Snapdragon AI Studio and must be obtained separately from the official source.")
            btn_download_text = tr("model_src_dl_key" + "", "Download from official source")
            btn_install_text = tr("model_src_inst_key" + "", "Install already downloaded model")
            btn_cancel_text = tr("model_src_cancel_key" + "", "Cancel")

        if not self.source_url:
            btn_download_text = f"{btn_download_text} ({tr('not_available', 'Not available')})"

        self.add_title(self.model_name)

        # Description label
        desc_lbl = tk.Label(
            self.body,
            text=desc_text,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            wraplength=400,
            justify="left",
            anchor="nw",
        )
        desc_lbl.pack(fill="x", pady=(0, PHOENIX_THEME.space_lg))

        # Download Button
        btn_dl = tk.Button(
            self.body,
            text=btn_download_text,
            command=self._on_download,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            font=PHOENIX_THEME.font_button,
            cursor="hand2" if self.source_url else "arrow",
            state="normal" if self.source_url else "disabled",
            disabledforeground=PHOENIX_THEME.text_disabled,
        )
        btn_dl.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))
        if self.source_url:
            btn_dl.bind("<Enter>", lambda e: btn_dl.configure(bg=PHOENIX_THEME.accent_dark))
            btn_dl.bind("<Leave>", lambda e: btn_dl.configure(bg=PHOENIX_THEME.accent))

        # Install Button
        btn_inst = tk.Button(
            self.body,
            text=btn_install_text,
            command=self._on_install,
            bg=PHOENIX_THEME.button,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.button_active,
            activeforeground=PHOENIX_THEME.text_primary,
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
        )
        btn_inst.pack(fill="x", pady=(0, PHOENIX_THEME.space_md))
        btn_inst.bind("<Enter>", lambda e: btn_inst.configure(bg=PHOENIX_THEME.button_hover))
        btn_inst.bind("<Leave>", lambda e: btn_inst.configure(bg=PHOENIX_THEME.button))

        # Cancel Button in footer
        self.add_footer_button(btn_cancel_text, self._on_cancel)

    def _on_download(self) -> None:
        self.choice = "download"
        if self.source_url:
            try:
                webbrowser.open(self.source_url)
            except Exception:
                pass
        self.close()

    def _on_install(self) -> None:
        self.choice = "install"
        self.close()

    def _on_cancel(self) -> None:
        self.choice = "cancel"
        self.close()
