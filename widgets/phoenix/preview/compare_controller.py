from __future__ import annotations

import logging

from PIL import Image


logger = logging.getLogger(__name__)


class CompareController:
    """Zentrale Zustandsverwaltung fuer den Compare Workspace."""

    VALID_COMPARE_MODES = {"side", "slider", "overlay", "difference"}

    def __init__(self) -> None:
        self.original_image: Image.Image | None = None
        self.output_image: Image.Image | None = None
        self.compare_mode = "side"
        self.slider_position = 0.5
        self.overlay_opacity = 0.5
        self.reset_camera()

    def set_images(
        self,
        original: Image.Image | None,
        output: Image.Image | None,
    ) -> None:
        self.original_image = original
        self.output_image = output
        logger.info(
            "Compare mode=%s original=%s output=%s zoom_mode=%s zoom=%.2f",
            self.compare_mode,
            self._format_image_size(original),
            self._format_image_size(output),
            self.zoom_mode,
            self.zoom_level,
        )

    def set_compare_mode(self, mode: str) -> None:
        if mode not in self.VALID_COMPARE_MODES:
            raise ValueError(f"Unsupported compare mode: {mode}")

        self.compare_mode = mode
        logger.info("Compare mode set to %s", mode)

    def get_compare_mode(self) -> str:
        return self.compare_mode

    def get_render_mode(self) -> str:
        return self.compare_mode

    def set_slider_position(self, value: float) -> None:
        self.slider_position = min(max(float(value), 0.0), 1.0)

    def get_slider_position(self) -> float:
        return self.slider_position

    def set_overlay_opacity(self, value: float) -> None:
        self.overlay_opacity = min(max(float(value), 0.0), 1.0)

    def get_overlay_opacity(self) -> float:
        return self.overlay_opacity

    def reset_camera(self) -> None:
        self.zoom_mode = "fit"
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

    def fit(self) -> None:
        self.reset_camera()

    def zoom_to(self, value: float) -> None:
        self.zoom_level = max(0.25, min(float(value), 3.0))

        if self.zoom_level == 1.0:
            self.zoom_mode = "100"
        else:
            self.zoom_mode = "custom"

        self.clamp_pan()

    def set_zoom_mode(self, zoom_mode: str) -> None:
        if zoom_mode == "fit":
            self.fit()
            return

        self.zoom_mode = zoom_mode
        self.zoom_level = {
            "100": 1.0,
        }.get(zoom_mode, 1.0)
        self.clamp_pan()

    def reset_pan(self) -> None:
        self.pan_x = 0.0
        self.pan_y = 0.0

    def pan_by(self, dx: float, dy: float) -> None:
        self.pan_x += dx
        self.pan_y += dy
        self.clamp_pan()

    def clamp_pan(self) -> None:
        self.pan_x = min(max(self.pan_x, -1.0), 1.0)
        self.pan_y = min(max(self.pan_y, -1.0), 1.0)

    def is_pan_enabled(self) -> bool:
        return self.zoom_mode != "fit" and self.zoom_level > 1.0

    def _format_image_size(self, image: Image.Image | None) -> str:
        if image is None:
            return "none"

        return f"{image.width}x{image.height}"
