from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Any

from widgets.phoenix.cards.activity_card import PhoenixActivityCard
from widgets.phoenix.cards.job_card import PhoenixJobCard
from widgets.phoenix.cards.output_card import PhoenixOutputCard
from widgets.phoenix.cards.progress_card import PhoenixProgressCard
from widgets.phoenix.cards.status_card import PhoenixStatusCard
from widgets.phoenix.controls.command_bar import PhoenixCommandBar
from widgets.phoenix.theme import PHOENIX_THEME


@dataclass(frozen=True)
class PhoenixHomeSnapshot:
    workspace_status: str = "Aktiv"
    batch_status: str = "Bereit"
    lifecycle_status: str = "Idle"
    output_status: str = "Kein Output ausgewählt"
    detail: str = "Phoenix Dashboard Foundation ist bereit."
    current: int = 0
    total: int = 0
    percent: int = 0
    current_job: str = "Kein aktiver Job"
    last_output: str = "Kein Output vorhanden"
    plugin: str = "RealESRGAN"
    backend: str = "QNN / Snapdragon NPU"
    activity: tuple[str, ...] = ()


class PhoenixHomeView(tk.Frame):
    """Phoenix home dashboard."""

    def __init__(self, master: tk.Misc, controller: object | None = None) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.controller = controller

        self._cards: dict[str, PhoenixStatusCard] = {}
        self._progress_card: PhoenixProgressCard | None = None
        self._job_card: PhoenixJobCard | None = None
        self._output_card: PhoenixOutputCard | None = None
        self._activity_card: PhoenixActivityCard | None = None

        self._build()
        self.refresh()

    def _build(self) -> None:
        command_bar = PhoenixCommandBar(self)
        command_bar.pack(fill="x", padx=PHOENIX_THEME.space_xl, pady=(24, PHOENIX_THEME.space_md))

        tk.Label(
            self,
            text="Home",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.space_xl, pady=(PHOENIX_THEME.space_xs, 6))

        tk.Label(
            self,
            text="Phoenix Statuszentrale für Workspace, Batch-Lifecycle, Engine und Output.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.space_xl, pady=(0, 22))

        cards_host = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        cards_host.pack(fill="x", padx=PHOENIX_THEME.space_xl, pady=(0, PHOENIX_THEME.space_lg))

        for column in range(4):
            cards_host.grid_columnconfigure(column, weight=1, uniform="status_cards")
        cards_host.grid_rowconfigure(0, weight=1, uniform="status_rows", minsize=156)

        self._create_status_card(cards_host, "workspace", "Workspace", "Aktiv", 0, 0)
        self._create_status_card(cards_host, "batch", "Batch", "Bereit", 0, 1)
        self._create_status_card(cards_host, "engine", "Engine", "Idle", 0, 2)
        self._create_status_card(cards_host, "output", "Output", "Kein Output", 0, 3)

        self._progress_card = PhoenixProgressCard(
            self,
            title="Queue Progress",
            current=0,
            total=0,
            percent=0,
            detail="Noch kein Batch gestartet.",
        )
        self._progress_card.pack(fill="x", padx=PHOENIX_THEME.space_xl, pady=(0, 20))

        lower_host = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        lower_host.pack(fill="x", padx=PHOENIX_THEME.space_xl, pady=(0, 16))
        lower_host.grid_columnconfigure(0, weight=1, uniform="lower_cards")
        lower_host.grid_columnconfigure(1, weight=1, uniform="lower_cards")
        lower_host.grid_rowconfigure(0, weight=1, minsize=210)

        self._job_card = PhoenixJobCard(lower_host)
        self._job_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)

        self._output_card = PhoenixOutputCard(lower_host)
        self._output_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)

        self._activity_card = PhoenixActivityCard(self)
        self._activity_card.pack(fill="x", padx=PHOENIX_THEME.space_xl, pady=(0, 16))

    def _create_status_card(
        self,
        master: tk.Misc,
        key: str,
        title: str,
        value: str,
        row: int,
        column: int,
    ) -> None:
        card = PhoenixStatusCard(master, title=title, value=value)
        left_pad = 0 if column == 0 else PHOENIX_THEME.space_sm
        right_pad = 0 if column == 3 else PHOENIX_THEME.space_sm
        card.grid(row=row, column=column, sticky="nsew", padx=(left_pad, right_pad), pady=0)
        self._cards[key] = card

    def refresh(self) -> None:
        snapshot = self._read_snapshot()
        self._render(snapshot)

    def _read_snapshot(self) -> PhoenixHomeSnapshot:
        provider = getattr(self.controller, "get_dashboard_snapshot", None)
        if callable(provider):
            try:
                return self._coerce_snapshot(provider())
            except Exception:
                return PhoenixHomeSnapshot(
                    batch_status="Unbekannt",
                    lifecycle_status="Unbekannt",
                    output_status="Unbekannt",
                    detail="Dashboard-Daten konnten nicht gelesen werden.",
                )

        return PhoenixHomeSnapshot()

    def _coerce_snapshot(self, data: Any) -> PhoenixHomeSnapshot:
        if isinstance(data, PhoenixHomeSnapshot):
            return data

        if isinstance(data, dict):
            return PhoenixHomeSnapshot(
                workspace_status=str(data.get("workspace_status", "Aktiv")),
                batch_status=str(data.get("batch_status", "Bereit")),
                lifecycle_status=str(data.get("lifecycle_status", "Idle")),
                output_status=str(data.get("output_status", "Kein Output ausgewählt")),
                detail=str(data.get("detail", "Phoenix Dashboard Foundation ist bereit.")),
                current=int(data.get("current", 0)),
                total=int(data.get("total", 0)),
                percent=int(data.get("percent", 0)),
                current_job=str(data.get("current_job", "Kein aktiver Job")),
                last_output=str(data.get("last_output", "Kein Output vorhanden")),
                plugin=str(data.get("plugin", "RealESRGAN")),
                backend=str(data.get("backend", "QNN / Snapdragon NPU")),
                activity=tuple(str(item) for item in data.get("activity", ())),
            )

        return PhoenixHomeSnapshot()

    def _render(self, snapshot: PhoenixHomeSnapshot) -> None:
        self._update_card(
            "workspace",
            "Workspace",
            snapshot.workspace_status,
            "Phoenix UI aktiv.",
        )
        self._update_card(
            "batch",
            "Batch",
            snapshot.batch_status,
            snapshot.detail,
        )
        self._update_card(
            "engine",
            "Engine",
            snapshot.lifecycle_status,
            "Lifecycle-Schicht.",
        )
        self._update_card(
            "output",
            "Output",
            snapshot.output_status,
            "Letzter Output.",
        )

        if self._progress_card is not None:
            self._progress_card.update(
                title="Queue Progress",
                current=snapshot.current,
                total=snapshot.total,
                percent=snapshot.percent,
                detail=snapshot.detail,
            )

        if self._job_card is not None:
            self._job_card.update(
                filename=snapshot.current_job,
                plugin=snapshot.plugin,
                backend=snapshot.backend,
                detail=snapshot.detail,
            )

        if self._output_card is not None:
            self._output_card.update(
                filename=snapshot.last_output,
                detail="Smart Output Handling liefert den letzten bekannten Output.",
            )

        if self._activity_card is not None:
            self._activity_card.update(activity=snapshot.activity)

    def _update_card(self, key: str, title: str, value: str, detail: str) -> None:
        card = self._cards.get(key)
        if card is not None:
            card.update(title=title, value=value, detail=detail)
