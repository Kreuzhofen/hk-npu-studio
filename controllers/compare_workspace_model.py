from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class CompareImageMetadata:
    path: Path
    filename: str
    resolution: str
    image_format: str
    color_mode: str
    file_size: str


@dataclass(frozen=True)
class CompareWorkspaceState:
    original_loaded: bool = False
    output_loaded: bool = False
    zoom_label: str = "Fit"
    zoom_scale: float | None = None
    sync_label: str = "Synchron"
    status: str = "Bereit"
    original_metadata: CompareImageMetadata | None = None
    output_metadata: CompareImageMetadata | None = None


class CompareWorkspaceModel:
    """State and image container for the Compare Workspace."""

    def __init__(self) -> None:
        self.state = CompareWorkspaceState()
        self.original_image: Image.Image | None = None
        self.output_image: Image.Image | None = None

    def set_original(self, image: Image.Image, metadata: CompareImageMetadata) -> None:
        self.original_image = image
        self.state = CompareWorkspaceState(
            original_loaded=True,
            output_loaded=self.state.output_loaded,
            zoom_label=self.state.zoom_label,
            zoom_scale=self.state.zoom_scale,
            sync_label=self.state.sync_label,
            status=f"Original geladen: {metadata.filename}",
            original_metadata=metadata,
            output_metadata=self.state.output_metadata,
        )

    def set_output(self, image: Image.Image, metadata: CompareImageMetadata) -> None:
        self.output_image = image
        self.state = CompareWorkspaceState(
            original_loaded=self.state.original_loaded,
            output_loaded=True,
            zoom_label=self.state.zoom_label,
            zoom_scale=self.state.zoom_scale,
            sync_label=self.state.sync_label,
            status=f"Output geladen: {metadata.filename}",
            original_metadata=self.state.original_metadata,
            output_metadata=metadata,
        )

    def clear_output(self) -> None:
        self.output_image = None
        self.state = CompareWorkspaceState(
            original_loaded=self.state.original_loaded,
            output_loaded=False,
            zoom_label=self.state.zoom_label,
            zoom_scale=self.state.zoom_scale,
            sync_label=self.state.sync_label,
            status=self.state.status,
            original_metadata=self.state.original_metadata,
            output_metadata=None,
        )

    def swap_images(self) -> None:
        self.original_image, self.output_image = self.output_image, self.original_image
        original_metadata = self.state.output_metadata
        output_metadata = self.state.original_metadata
        self.state = CompareWorkspaceState(
            original_loaded=self.original_image is not None,
            output_loaded=self.output_image is not None,
            zoom_label=self.state.zoom_label,
            zoom_scale=self.state.zoom_scale,
            sync_label=self.state.sync_label,
            status="Original und Output getauscht",
            original_metadata=original_metadata,
            output_metadata=output_metadata,
        )

    def set_status(self, status: str) -> None:
        self.state = CompareWorkspaceState(
            original_loaded=self.state.original_loaded,
            output_loaded=self.state.output_loaded,
            zoom_label=self.state.zoom_label,
            zoom_scale=self.state.zoom_scale,
            sync_label=self.state.sync_label,
            status=status,
            original_metadata=self.state.original_metadata,
            output_metadata=self.state.output_metadata,
        )

    def set_zoom(self, zoom_label: str, zoom_scale: float | None) -> None:
        self.state = CompareWorkspaceState(
            original_loaded=self.state.original_loaded,
            output_loaded=self.state.output_loaded,
            zoom_label=zoom_label,
            zoom_scale=zoom_scale,
            sync_label=self.state.sync_label,
            status=f"Zoom: {zoom_label}",
            original_metadata=self.state.original_metadata,
            output_metadata=self.state.output_metadata,
        )

    def set_sync_status(self, sync_label: str) -> None:
        self.state = CompareWorkspaceState(
            original_loaded=self.state.original_loaded,
            output_loaded=self.state.output_loaded,
            zoom_label=self.state.zoom_label,
            zoom_scale=self.state.zoom_scale,
            sync_label=sync_label,
            status="Synchronisierte Ansicht aktiv",
            original_metadata=self.state.original_metadata,
            output_metadata=self.state.output_metadata,
        )
