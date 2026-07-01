from __future__ import annotations

import tkinter as tk

from widgets.phoenix.theme import PHOENIX_THEME


class PhoenixRightPanel(tk.Frame):
    def __init__(self, master: tk.Misc, controller: object | None = None) -> None:
        super().__init__(master, bg=PHOENIX_THEME.panel_bg, width=280)

        self.controller = controller

        self.grid_propagate(False)
        self.pack_propagate(False)

        self._build()

    def _build(self) -> None:
        title = tk.Label(
            self,
            text="Inspector",
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        )
        title.pack(fill="x", padx=18, pady=(18, 10))

        actions = tk.LabelFrame(
            self,
            text="Aktionen",
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_primary,
            padx=10,
            pady=10,
        )
        actions.pack(fill="x", padx=18, pady=(0, 16))

        self._button(actions, "▶ Start", self._start_plugin).pack(fill="x", pady=(0, 8))
        self._button(actions, "■ Stop", self._stop_plugin).pack(fill="x", pady=(0, 8))
        self._button(actions, "📂 Output öffnen", self._open_output).pack(fill="x")

        info = tk.Label(
            self,
            text=(
                "Noch keine Auswahl.\n\n"
                "Dieser Bereich wird später für\n"
                "Dateiinfos, Pluginstatus,\n"
                "Fortschritt und Batch-Infos\n"
                "genutzt."
            ),
            bg=PHOENIX_THEME.panel_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=("Segoe UI", 10),
            justify="left",
            anchor="nw",
            wraplength=230,
        )
        info.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def _button(self, master: tk.Misc, text: str, command) -> tk.Button:
        return tk.Button(
            master,
            text=text,
            command=command,
            bg=PHOENIX_THEME.accent,
            fg="#FFFFFF",
            activebackground=PHOENIX_THEME.accent_dark,
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )

    def _app(self):
        return self.winfo_toplevel()

    def _start_plugin(self) -> None:
        print("Phoenix Start Button geklickt")
        app = self._app()
        print("App:", app)
        print("Hat start_plugin:", hasattr(app, "start_plugin"))

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