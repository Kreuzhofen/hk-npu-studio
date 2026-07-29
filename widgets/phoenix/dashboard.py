from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Any

from app.i18n import tr
from app.runtime_localization import localize_runtime_text
from widgets.phoenix.cards.progress_card import PhoenixProgressCard
from widgets.phoenix.cards.status_card import PhoenixStatusCard
from widgets.phoenix.theme import PHOENIX_THEME


@dataclass(frozen=True)
class PhoenixDashboardSnapshot:
    workspace_status: str = "active"
    batch_status: str = "ready"
    lifecycle_status: str = "idle"
    output_status: str = "no_output"
    detail: str = ""
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
            text=tr("dashboard", "Dashboard"),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.space_xl, pady=(PHOENIX_THEME.space_xl, PHOENIX_THEME.space_sm))

        tk.Label(
            self,
            text=tr(
                "dashboard_subtitle",
                "Phoenix-Statuszentrale für Batch-Lifecycle, Engine, Warteschlange und Ausgabe.",
            ),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).pack(fill="x", padx=PHOENIX_THEME.space_xl, pady=(0, 22))

        cards_host = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        cards_host.pack(fill="x", padx=PHOENIX_THEME.space_xl, pady=(0, PHOENIX_THEME.space_lg))
        cards_host.grid_columnconfigure(0, weight=1, uniform="dashboard_cards")
        cards_host.grid_columnconfigure(1, weight=1, uniform="dashboard_cards")
        cards_host.grid_rowconfigure(0, weight=1, uniform="dashboard_rows")
        cards_host.grid_rowconfigure(1, weight=1, uniform="dashboard_rows")

        self._create_status_card(cards_host, "workspace", tr("workspace", "Workspace"), tr("ready", "Bereit"), 0, 0)
        self._create_status_card(cards_host, "batch", tr("batch", "Batch"), tr("ready", "Bereit"), 0, 1)
        self._create_status_card(cards_host, "engine", "Engine", tr("idle", "Inaktiv"), 1, 0)
        self._create_status_card(cards_host, "output", tr("output_title", "Ausgabe"), tr("no_output", "Keine Ausgabe"), 1, 1)

        self._progress_card = PhoenixProgressCard(
            self,
            title=tr("queue_progress", "Warteschlangenfortschritt"),
            current=0,
            total=0,
            percent=0,
            detail=tr("no_batch_started", "Noch kein Batch gestartet."),
        )
        self._progress_card.pack(fill="x", padx=PHOENIX_THEME.space_xl, pady=(0, 16))

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
        card.grid(row=row, column=column, sticky="nsew", padx=PHOENIX_THEME.space_sm, pady=PHOENIX_THEME.space_sm)
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
                    batch_status=tr("unknown", "Unbekannt"),
                    lifecycle_status=tr("unknown", "Unbekannt"),
                    output_status=tr("unknown", "Unbekannt"),
                    detail=tr("dashboard_read_failed", "Dashboard-Daten konnten nicht gelesen werden."),
                )

        return PhoenixDashboardSnapshot()

    def _coerce_snapshot(self, data: Any) -> PhoenixDashboardSnapshot:
        if isinstance(data, PhoenixDashboardSnapshot):
            return data

        if isinstance(data, dict):
            return PhoenixDashboardSnapshot(
                workspace_status=str(data.get("workspace_status", "active")),
                batch_status=str(data.get("batch_status", "ready")),
                lifecycle_status=str(data.get("lifecycle_status", "idle")),
                output_status=str(data.get("output_status", tr("no_output_selected", "Keine Ausgabe ausgewählt"))),
                detail=str(data.get("detail", tr("dashboard_ready", "Phoenix-Dashboard ist bereit."))),
                current=int(data.get("current", 0)),
                total=int(data.get("total", 0)),
                percent=int(data.get("percent", 0)),
            )

        return PhoenixDashboardSnapshot()

    def _render(self, snapshot: PhoenixDashboardSnapshot) -> None:
        self._update_card("workspace", tr("workspace", "Workspace"), localize_runtime_text(snapshot.workspace_status), tr("phoenix_ui_active", "Phoenix UI aktiv."))
        detail = snapshot.detail or tr("dashboard_ready", "Phoenix-Dashboard ist bereit.")
        self._update_card("batch", tr("batch", "Batch"), localize_runtime_text(snapshot.batch_status), detail)
        self._update_card("engine", "Engine", localize_runtime_text(snapshot.lifecycle_status), tr("lifecycle_layer", "Controller-/Lifecycle-Schicht."))
        self._update_card("output", tr("output_title", "Ausgabe"), localize_runtime_text(snapshot.output_status), tr("last_known_output", "Letzte bekannte Ausgabe."))

        if self._progress_card is not None:
            self._progress_card.update(
                title=tr("queue_progress", "Warteschlangenfortschritt"),
                current=snapshot.current,
                total=snapshot.total,
                percent=snapshot.percent,
                detail=detail,
            )

    def _update_card(self, key: str, title: str, value: str, detail: str) -> None:
        card = self._cards.get(key)
        if card is not None:
            card.update(title=title, value=value, detail=detail)
