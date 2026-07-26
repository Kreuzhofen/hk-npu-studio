from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixRightPanel(tk.Frame):
    """Phoenix inspector panel for actions and runtime status."""

    def __init__(self, master: tk.Misc, controller: object | None = None) -> None:
        # Use content_bg for the panel itself to match workspace card styling
        super().__init__(master, bg=PHOENIX_THEME.content_bg, width=280)

        self.controller = controller

        self.start_button: tk.Button | None = None
        self.stop_button: tk.Button | None = None
        self.output_button: tk.Button | None = None

        self._status_value: tk.StringVar = tk.StringVar(value="Ready")
        self._plugin_value: tk.StringVar = tk.StringVar(value="Nicht verbunden")
        self._backend_value: tk.StringVar = tk.StringVar(value="Noch keine Engine aktiv")
        self._file_value: tk.StringVar = tk.StringVar(value="Keine Auswahl")

        self.grid_propagate(False)
        self.pack_propagate(False)

        self._build()

    def _build(self) -> None:
        # Symmetrical Title Frame (aligns with left view title frames)
        self.title_frame = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        self.title_frame.pack(fill="x", padx=(0, 24), pady=(24, 16))

        self.title_lbl = tk.Label(
            self.title_frame,
            text="Inspector",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        )
        self.title_lbl.pack(fill="x")

        self.subtitle_lbl = tk.Label(
            self.title_frame,
            text="Aktionen und Status",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        )
        self.subtitle_lbl.pack(fill="x", pady=(4, 0))

        # Main Symmetrical Card Frame (aligns with left view cards)
        self.card = tk.Frame(
            self,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            bd=0,
        )
        self.card.pack(fill="both", expand=True, padx=(0, 24), pady=(0, 24))

        # Content container inside the card
        self.inspector_content = tk.Frame(self.card, bg=PHOENIX_THEME.card_bg)
        self.inspector_content.pack(fill="both", expand=True)

        self._build_actions_section()
        self._build_status_section()
        self._build_info_section()

        self.disable_cancel_button()
        self.disable_output_button()

    def _build_actions_section(self) -> None:
        section = self._section("Aktionen")
        section.pack(fill="x", padx=PHOENIX_THEME.space_lg, pady=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_md))

        self.start_button = self._button(section, "▶ Start", self._start_plugin)
        self.start_button.pack(fill="x", padx=PHOENIX_THEME.space_md, pady=(0, PHOENIX_THEME.space_sm))

        self.stop_button = self._button(section, "■ Stop", self._stop_plugin)
        self.stop_button.pack(fill="x", padx=PHOENIX_THEME.space_md, pady=(0, PHOENIX_THEME.space_sm))

        self.output_button = self._button(section, "📂 Output öffnen", self._open_output)
        self.output_button.pack(fill="x", padx=PHOENIX_THEME.space_md, pady=(0, PHOENIX_THEME.space_md))

    def _build_status_section(self) -> None:
        section = self._section("Status")
        section.pack(fill="x", padx=PHOENIX_THEME.space_lg, pady=(0, PHOENIX_THEME.space_md))

        self._info_row(section, "Runtime", self._status_value)
        self._info_row(section, "Engine", self._plugin_value)
        self._info_row(section, "Backend", self._backend_value)

    def _build_info_section(self) -> None:
        section = self._section("Datei")
        section.pack(fill="both", expand=True, padx=PHOENIX_THEME.space_lg, pady=(0, PHOENIX_THEME.space_lg))

        self._info_row(section, "Auswahl", self._file_value)

        tk.Label(
            section,
            text=(
                "Der Inspector zeigt künftig Details zum aktiven Job, "
                "zur Queue und zum letzten Output."
            ),
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_caption,
            justify="left",
            anchor="nw",
            wraplength=200,
        ).pack(fill="x", padx=PHOENIX_THEME.space_md, pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.space_md))

    def _section(self, title: str) -> tk.Frame:
        frame = tk.Frame(
            self.inspector_content,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )

        tk.Label(
            frame,
            text=title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.space_md, pady=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_xs))

        return frame

    def _info_row(self, master: tk.Misc, label: str, value: tk.StringVar) -> None:
        tk.Label(
            master,
            text=label,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_caption,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.space_md)

        tk.Label(
            master,
            textvariable=value,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            wraplength=200,
        ).pack(fill="x", padx=PHOENIX_THEME.space_md, pady=(PHOENIX_THEME.space_xs, PHOENIX_THEME.space_sm))

    def _button(self, master: tk.Misc, text: str, command) -> tk.Button:
        return tk.Button(
            master,
            text=text,
            command=command,
            bg=PHOENIX_THEME.accent,
            fg=PHOENIX_THEME.text_on_accent,
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground=PHOENIX_THEME.text_on_accent,
            disabledforeground=PHOENIX_THEME.text_disabled,
            relief="flat",
            bd=0,
            padx=PHOENIX_THEME.button_pad_x,
            pady=PHOENIX_THEME.button_pad_y,
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
        )

    def refresh(self) -> None:
        provider = getattr(self.controller, "get_dashboard_snapshot", None)

        if not callable(provider):
            return

        try:
            snapshot = provider()
        except Exception:
            self._status_value.set("Unbekannt")
            return

        if isinstance(snapshot, dict):
            self._status_value.set(str(snapshot.get("batch_status", "Ready")))
            self._plugin_value.set(str(snapshot.get("plugin", "RealESRGAN")))
            self._backend_value.set(str(snapshot.get("backend", "QNN / Snapdragon NPU")))
            self._file_value.set(str(snapshot.get("last_output", "Keine Auswahl")))

    def enable_start_button(self) -> None:
        if self.start_button is not None:
            self.start_button.configure(state="normal")

    def disable_start_button(self) -> None:
        if self.start_button is not None:
            self.start_button.configure(state="disabled")

    def enable_cancel_button(self) -> None:
        if self.stop_button is not None:
            self.stop_button.configure(state="normal")

    def disable_cancel_button(self) -> None:
        if self.stop_button is not None:
            self.stop_button.configure(state="disabled")

    def enable_output_button(self) -> None:
        if self.output_button is not None:
            self.output_button.configure(state="normal")

    def disable_output_button(self) -> None:
        if self.output_button is not None:
            self.output_button.configure(state="disabled")

    def _app(self):
        return self.winfo_toplevel()

    def _start_plugin(self) -> None:
        app = self._app()

        if hasattr(app, "start_plugin"):
            app.start_plugin()

    def _stop_plugin(self) -> None:
        app = self._app()

        if hasattr(app, "cancel_processing"):
            app.cancel_processing()

    def _open_output(self) -> None:
        app = self._app()

        if hasattr(app, "open_output"):
            app.open_output()
