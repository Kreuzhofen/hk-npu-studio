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
        )

        self._title_var = tk.StringVar(value=title)
        self._filename_var = tk.StringVar(value=filename)
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
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 4))

        tk.Label(
            self,
            textvariable=self._filename_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16)

        tk.Label(
            self,
            textvariable=self._plugin_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(6, 0))

        tk.Label(
            self,
            textvariable=self._backend_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(2, 0))

        tk.Label(
            self,
            textvariable=self._detail_var,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=520,
        ).pack(fill="x", padx=16, pady=(8, 14))

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
            self._filename_var.set(filename)

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