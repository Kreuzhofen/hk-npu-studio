from __future__ import annotations

from controllers.compare_workspace_model import CompareWorkspaceModel, CompareWorkspaceState


class CompareWorkspaceController:
    """Controller for Compare Workspace UI state and future compare actions."""

    def __init__(self, model: CompareWorkspaceModel | None = None) -> None:
        self.model = model or CompareWorkspaceModel()

    def get_state(self) -> CompareWorkspaceState:
        return self.model.state

    def prepare_original_open(self) -> None:
        self.model.set_status("Original öffnen vorbereitet")

    def prepare_output_open(self) -> None:
        self.model.set_status("Ausgabe öffnen vorbereitet")

    def set_zoom(self, zoom_label: str) -> None:
        self.model.set_zoom(zoom_label)

    def prepare_sync(self) -> None:
        self.model.set_sync_status("Synchron")

    def prepare_swap(self) -> None:
        self.model.set_status("Swap vorbereitet")

    def status_items(self) -> dict[str, str]:
        state = self.get_state()
        return {
            "Original": "Geladen" if state.original_loaded else "Nicht geladen",
            "Output": "Geladen" if state.output_loaded else "Nicht geladen",
            "Zoom": state.zoom_label,
            "Sync": state.sync_label,
            "Status": state.status,
        }

    def inspector_sections(self) -> dict[str, tuple[str, ...]]:
        state = self.get_state()
        return {
            "Original": ("Quelle: -", "Auflösung: -", "Status: Nicht geladen"),
            "Output": ("Quelle: -", "Auflösung: -", "Status: Nicht geladen"),
            "Bildinformationen": (f"Zoom: {state.zoom_label}", f"Synchronisation: {state.sync_label}"),
            "Verarbeitung": ("AI-Daten: -", "Pipeline: Noch nicht angebunden"),
        }
