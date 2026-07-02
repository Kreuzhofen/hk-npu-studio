from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Any

from widgets.phoenix.cards.progress_card import PhoenixProgressCard
from widgets.phoenix.cards.status_card import PhoenixStatusCard
from widgets.phoenix.theme import PHOENIX_THEME


@dataclass(frozen=True)
class PhoenixDashboardSnapshot:
    workspace_status: str = "Aktiv"
    batch_status: str = "Bereit"
    lifecycle_status: str = "Idle"
    output_status: str = "Kein Output ausgewählt"
    detail: str = "Phoenix Dashboard Foundation ist bereit."
    current: int = 0
    total: int = 0
    percent: int = 0


class PhoenixDashboard(tk.Frame):
    """Read-only dashboard view for Phoenix runtime status."""

    def __init__(self, master: tk.Misc, controller: object | None = None) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.controller = controller
        self._cards: dict[str, PhoenixStatusCard] = {}
        self._progress_card: PhoenixProgressCard | None = None
        self._build()
        self.refresh()

    def _build(self) -> None:
        tk.Label(
            self,
            text="Dashboard",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=("Segoe UI", 22, "bold"),
            anchor="w",
        ).pack(fill="x", padx=28, pady=(28, 8))

        tk.Label(
            self,
            text="Phoenix Statuszentrale für Batch-Lifecycle, Engine, Queue und Output.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=("Segoe UI", 11),
            anchor="w",
        ).pack(fill="x", padx=28, pady=(0, 22))

        cards_host = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        cards_host.pack(fill="x", padx=28, pady=(0, 18))
        cards_host.grid_columnconfigure(0, weight=1, uniform="dashboard_cards")
        cards_host.grid_columnconfigure(1, weight=1, uniform="dashboard_cards")
        cards_host.grid_rowconfigure(0, weight=1, uniform="dashboard_rows")
        cards_host.grid_rowconfigure(1, weight=1, uniform="dashboard_rows")

        self._create_status_card(cards_host, "workspace", "Workspace", "Bereit", 0, 0)
        self._create_status_card(cards_host, "batch", "Batch", "Bereit", 0, 1)
        self._create_status_card(cards_host, "engine", "Engine", "Idle", 1, 0)
        self._create_status_card(cards_host, "output", "Output", "Kein Output", 1, 1)

        self._progress_card = PhoenixProgressCard(
            self,
            title="Queue Progress",
            current=0,
            total=0,
            percent=0,
            detail="Noch kein Batch gestartet.",
        )
        self._progress_card.pack(fill="x", padx=28, pady=(0, 16))

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
        card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        self._cards[key] = card

    def refresh(self) -> None:
        snapshot = self._read_snapshot()
        self._render(snapshot)

    def _read_snapshot(self) -> PhoenixDashboardSnapshot:
        provider = getattr(self.controller, "get_dashboard_snapshot", None)
        if callable(provider):
            try:
                return self._coerce_snapshot(provider())
            except Exception:
                return PhoenixDashboardSnapshot(
                    batch_status="Unbekannt",
                    lifecycle_status="Unbekannt",
                    output_status="Unbekannt",
                    detail="Dashboard-Daten konnten nicht gelesen werden.",
                )

        return PhoenixDashboardSnapshot()

    def _coerce_snapshot(self, data: Any) -> PhoenixDashboardSnapshot:
        if isinstance(data, PhoenixDashboardSnapshot):
            return data

        if isinstance(data, dict):
            return PhoenixDashboardSnapshot(
                workspace_status=str(data.get("workspace_status", "Aktiv")),
                batch_status=str(data.get("batch_status", "Bereit")),
                lifecycle_status=str(data.get("lifecycle_status", "Idle")),
                output_status=str(data.get("output_status", "Kein Output ausgewählt")),
                detail=str(data.get("detail", "Phoenix Dashboard Foundation ist bereit.")),
                current=int(data.get("current", 0)),
                total=int(data.get("total", 0)),
                percent=int(data.get("percent", 0)),
            )

        return PhoenixDashboardSnapshot()

    def _render(self, snapshot: PhoenixDashboardSnapshot) -> None:
        self._update_card("workspace", "Workspace", snapshot.workspace_status, "Phoenix UI aktiv.")
        self._update_card("batch", "Batch", snapshot.batch_status, snapshot.detail)
        self._update_card("engine", "Engine", snapshot.lifecycle_status, "Controller-/Lifecycle-Schicht.")
        self._update_card("output", "Output", snapshot.output_status, "Letzter bekannter Output.")

        if self._progress_card is not None:
            self._progress_card.update(
                title="Queue Progress",
                current=snapshot.current,
                total=snapshot.total,
                percent=snapshot.percent,
                detail=snapshot.detail,
            )

    def _update_card(self, key: str, title: str, value: str, detail: str) -> None:
        card = self._cards.get(key)
        if card is not None:
            card.update(title=title, value=value, detail=detail)
