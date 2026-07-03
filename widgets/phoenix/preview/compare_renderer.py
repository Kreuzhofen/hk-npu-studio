from __future__ import annotations

from PIL import Image, ImageColor, ImageTk

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

        return ImageTk.PhotoImage(self.render_image_canvas(image, preview_size))

    def render_image_canvas(
        self,
        image: Image.Image,
        preview_size: tuple[int, int],
    ) -> Image.Image:
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

        return canvas_image

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
    """Rendert Original und Output als Before/After-Slider."""

    def render_original(self, preview_size: tuple[int, int]) -> ImageTk.PhotoImage | None:
        original = self.controller.original_image
        output = self.controller.output_image

        if original is None and output is None:
            return None

        if original is None:
            return self.render_image(output, preview_size)

        if output is None:
            return self.render_image(original, preview_size)

        original_canvas = self.render_image_canvas(original, preview_size)
        output_canvas = self.render_image_canvas(output, preview_size)
        preview_width, preview_height = preview_size
        split_x = int(preview_width * self.controller.get_slider_position())

        combined = Image.new(
            "RGB",
            (preview_width, preview_height),
            PHOENIX_THEME.card_bg,
        )
        combined.paste(original_canvas.crop((0, 0, split_x, preview_height)), (0, 0))
        combined.paste(
            output_canvas.crop((split_x, 0, preview_width, preview_height)),
            (split_x, 0),
        )
        self._draw_split_line(combined, split_x)

        return ImageTk.PhotoImage(combined)

    def render_output(self, preview_size: tuple[int, int]) -> ImageTk.PhotoImage | None:
        return None

    def _draw_split_line(self, image: Image.Image, split_x: int) -> None:
        line_color = ImageColor.getrgb(getattr(PHOENIX_THEME, "accent", "#3B82F6"))
        left = max(0, split_x - 1)
        right = min(image.width, split_x + 1)

        for x in range(left, right):
            for y in range(image.height):
                image.putpixel((x, y), line_color)


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
