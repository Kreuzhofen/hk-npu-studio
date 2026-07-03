from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixJobCard(tk.Frame):
    """Reusable card for the currently active Phoenix job."""

    def __init__(
        self,
        master: tk.Misc,
        title: str = "Aktueller Job",
        filename: str = "Kein aktiver Job",
        plugin: str = "RealESRGAN",
        backend: str = "QNN / Snapdragon NPU",
        detail: str = "Noch kein Batch gestartet.",
    ) -> None:
        super().__init__(
            master,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            height=178,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._title_var = tk.StringVar(value=title)
        self._full_filename = filename
        self._filename_var = tk.StringVar(value=self._format_filename(filename))
        self._plugin_var = tk.StringVar(value=plugin)
        self._backend_var = tk.StringVar(value=backend)
        self._detail_var = tk.StringVar(value=detail)

        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            textvariable=self._title_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
            height=1,
        ).pack(fill="x", padx=PHOENIX_THEME.card_pad_x, pady=(PHOENIX_THEME.card_pad_y, 6))

        tk.Label(
            self,
            textvariable=self._filename_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_value,
            anchor="w",
            height=1,
        ).pack(fill="x", padx=PHOENIX_THEME.card_pad_x)

        tk.Label(
            self,
            textvariable=self._plugin_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.card_pad_x, pady=(10, 0))

        tk.Label(
            self,
            textvariable=self._backend_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.card_pad_x, pady=(2, 0))

        tk.Label(
            self,
            textvariable=self._detail_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
            justify="left",
            wraplength=520,
        ).pack(fill="x", padx=PHOENIX_THEME.card_pad_x, pady=(12, PHOENIX_THEME.card_pad_y))

    def update(
        self,
        *,
        title: str | None = None,
        filename: str | None = None,
        plugin: str | None = None,
        backend: str | None = None,
        detail: str | None = None,
    ) -> None:
        if title is not None:
            self._title_var.set(title)

        if filename is not None:
            self._full_filename = filename
            self._filename_var.set(self._format_filename(filename))

        if plugin is not None:
            self._plugin_var.set(plugin)

        if backend is not None:
            self._backend_var.set(backend)

        if detail is not None:
            self._detail_var.set(detail)

    def configure_content(
        self,
        *,
        title: str | None = None,
        filename: str | None = None,
        plugin: str | None = None,
        backend: str | None = None,
        detail: str | None = None,
    ) -> None:
        self.update(
            title=title,
            filename=filename,
            plugin=plugin,
            backend=backend,
            detail=detail,
        )

    def _format_filename(self, filename: str) -> str:
        if len(filename) > 30:
            return f"{filename[:30]}..."

        return filename
