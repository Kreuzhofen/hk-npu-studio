from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompareWorkspaceState:
    original_loaded: bool = False
    output_loaded: bool = False
    zoom_label: str = "Fit"
    sync_label: str = "Bereit"
    status: str = "Bereit"


class CompareWorkspaceModel:
    """State container for the Compare Workspace foundation."""

    def __init__(self) -> None:
        self.state = CompareWorkspaceState()

    def set_status(self, status: str) -> None:
        self.state = CompareWorkspaceState(
            original_loaded=self.state.original_loaded,
            output_loaded=self.state.output_loaded,
            zoom_label=self.state.zoom_label,
            sync_label=self.state.sync_label,
            status=status,
        )

    def set_zoom(self, zoom_label: str) -> None:
        self.state = CompareWorkspaceState(
            original_loaded=self.state.original_loaded,
            output_loaded=self.state.output_loaded,
            zoom_label=zoom_label,
            sync_label=self.state.sync_label,
            status=f"Zoom vorbereitet: {zoom_label}",
        )

    def set_sync_status(self, sync_label: str) -> None:
        self.state = CompareWorkspaceState(
            original_loaded=self.state.original_loaded,
            output_loaded=self.state.output_loaded,
            zoom_label=self.state.zoom_label,
            sync_label=sync_label,
            status="Synchronisation vorbereitet",
        )
