from __future__ import annotations

from PIL import Image, ImageTk

from widgets.phoenix.preview.compare_controller import CompareController
from widgets.phoenix.theme import PHOENIX_THEME


class SideRenderer:
    """Rendert Original und Output im Side-by-Side-Modus."""

    def __init__(self, controller: CompareController) -> None:
        self.controller = controller

    def render_original(self, preview_size: tuple[int, int]) -> ImageTk.PhotoImage | None:
        return self.render_image(self.controller.original_image, preview_size)

    def render_output(self, preview_size: tuple[int, int]) -> ImageTk.PhotoImage | None:
        return self.render_image(self.controller.output_image, preview_size)

    def render_image(
        self,
        image: Image.Image | None,
        preview_size: tuple[int, int],
    ) -> ImageTk.PhotoImage | None:
        if image is None:
            return None

        preview_width, preview_height = preview_size
        canvas_image = Image.new(
            "RGB",
            (preview_width, preview_height),
            PHOENIX_THEME.card_bg,
        )

        if self.controller.zoom_mode == "fit":
            display_image = image.copy()
            display_image.thumbnail((preview_width, preview_height))
        else:
            display_image = image.resize(
                self.get_scaled_display_size(image),
                Image.Resampling.LANCZOS,
            )

        pan_x = self.controller.pan_x if self.controller.is_pan_enabled() else 0
        pan_y = self.controller.pan_y if self.controller.is_pan_enabled() else 0
        max_pan_x = max(0, (display_image.width - preview_width) // 2)
        max_pan_y = max(0, (display_image.height - preview_height) // 2)
        offset_x = (preview_width - display_image.width) // 2 + int(max_pan_x * pan_x)
        offset_y = (preview_height - display_image.height) // 2 + int(max_pan_y * pan_y)

        canvas_image.paste(display_image, (offset_x, offset_y))

        return ImageTk.PhotoImage(canvas_image)

    def get_pan_bounds(
        self,
        image: Image.Image | None,
        preview_size: tuple[int, int],
    ) -> tuple[int, int]:
        if image is None:
            return (0, 0)

        preview_width, preview_height = preview_size
        display_width, display_height = self.get_scaled_display_size(image)

        return (
            max(0, (display_width - preview_width) // 2),
            max(0, (display_height - preview_height) // 2),
        )

    def get_scaled_display_size(self, image: Image.Image) -> tuple[int, int]:
        scale = self.controller.zoom_level
        return (
            max(1, int(image.width * scale)),
            max(1, int(image.height * scale)),
        )


class SliderRenderer(SideRenderer):
    """Vorbereiteter Renderer fuer spaetere Slider-Compare-Ansicht."""


class OverlayRenderer(SideRenderer):
    """Vorbereiteter Renderer fuer spaetere Overlay-Compare-Ansicht."""


class DifferenceRenderer(SideRenderer):
    """Vorbereiteter Renderer fuer spaetere Difference-Compare-Ansicht."""


class CompareRenderer:
    """Koordiniert die Compare-Renderer fuer den aktuellen Compare-Modus."""

    def __init__(self, controller: CompareController) -> None:
        self.controller = controller
        self.renderers = {
            "side": SideRenderer(controller),
            "slider": SliderRenderer(controller),
            "overlay": OverlayRenderer(controller),
            "difference": DifferenceRenderer(controller),
        }

    def render_original(self, preview_size: tuple[int, int]) -> ImageTk.PhotoImage | None:
        return self._get_renderer().render_original(preview_size)

    def render_output(self, preview_size: tuple[int, int]) -> ImageTk.PhotoImage | None:
        return self._get_renderer().render_output(preview_size)

    def get_pan_bounds(
        self,
        image: Image.Image | None,
        preview_size: tuple[int, int],
    ) -> tuple[int, int]:
        return self._get_renderer().get_pan_bounds(image, preview_size)

    def _get_renderer(self) -> SideRenderer:
        return self.renderers.get(
            self.controller.get_render_mode(),
            self.renderers["side"],
        )
