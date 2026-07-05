from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from controllers.compare_workspace_model import (
    CompareImageMetadata,
    CompareWorkspaceModel,
    CompareWorkspaceState,
)


class CompareWorkspaceController:
    """Controller for Compare Workspace image loading, state and metadata."""

    SUPPORTED_FORMATS = (
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.bmp",
        "*.webp",
        "*.tif",
        "*.tiff",
    )

    ZOOM_LEVELS = {
        "Fit": None,
        "50 %": 0.5,
        "100 %": 1.0,
        "200 %": 2.0,
    }

    def __init__(self, model: CompareWorkspaceModel | None = None) -> None:
        self.model = model or CompareWorkspaceModel()

    def get_state(self) -> CompareWorkspaceState:
        return self.model.state

    def load_original(self, filename: str | Path) -> None:
        image, metadata = self._load_image(filename)
        self.model.set_original(image, metadata)

    def load_output(self, filename: str | Path) -> None:
        image, metadata = self._load_image(filename)
        self.model.set_output(image, metadata)

    def get_original_image(self) -> Image.Image | None:
        return self.model.original_image

    def get_output_image(self) -> Image.Image | None:
        return self.model.output_image

    def set_zoom(self, zoom_label: str) -> None:
        if zoom_label not in self.ZOOM_LEVELS:
            zoom_label = "Fit"
        self.model.set_zoom(zoom_label, self.ZOOM_LEVELS[zoom_label])

    def prepare_sync(self) -> None:
        self.model.set_sync_status("Synchron")

    def swap_images(self) -> None:
        if self.model.original_image is None and self.model.output_image is None:
            self.model.set_status("Keine Bilder zum Tauschen geladen")
            return
        self.model.swap_images()

    def set_error(self, message: str) -> None:
        self.model.set_status(f"Fehler: {message}")

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
            "Original": self._metadata_lines(state.original_metadata),
            "Output": self._metadata_lines(state.output_metadata),
            "Bildinformationen": (
                f"Zoom: {state.zoom_label}",
                f"Synchronisation: {state.sync_label}",
                self._resolution_delta_label(state),
            ),
            "Verarbeitung": (
                "AI-Daten: -",
                "Pipeline: Manuelle Vergleichsansicht",
                "Status: Bereit für Qualitätskontrolle",
            ),
        }

    def _load_image(self, filename: str | Path) -> tuple[Image.Image, CompareImageMetadata]:
        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {path}")

        with Image.open(path) as source_image:
            image_format = source_image.format or path.suffix.lstrip(".").upper() or "Unbekannt"
            image = ImageOps.exif_transpose(source_image)
            color_mode = image.mode
            resolution = f"{image.size[0]} x {image.size[1]}"
            display_image = image.convert("RGB")

        metadata = CompareImageMetadata(
            path=path,
            filename=path.name,
            resolution=resolution,
            image_format=image_format,
            color_mode=color_mode,
            file_size=self._format_file_size(path.stat().st_size),
        )
        return display_image, metadata

    def _metadata_lines(self, metadata: CompareImageMetadata | None) -> tuple[str, ...]:
        if metadata is None:
            return ("Datei: -", "Auflösung: -", "Format: -", "Größe: -")
        return (
            f"Datei: {metadata.filename}",
            f"Auflösung: {metadata.resolution}",
            f"Format: {metadata.image_format}",
            f"Farbmodus: {metadata.color_mode}",
            f"Größe: {metadata.file_size}",
            f"Pfad: {metadata.path}",
        )

    def _resolution_delta_label(self, state: CompareWorkspaceState) -> str:
        original = state.original_metadata
        output = state.output_metadata
        if original is None or output is None:
            return "Vergleich: wartet auf beide Bilder"
        if original.resolution == output.resolution:
            return "Vergleich: gleiche Auflösung"
        return "Vergleich: unterschiedliche Auflösung"

    def _format_file_size(self, size_bytes: int) -> str:
        size = float(size_bytes)
        units = ("B", "KB", "MB", "GB")
        for unit in units:
            if size < 1024 or unit == units[-1]:
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size_bytes} B"
