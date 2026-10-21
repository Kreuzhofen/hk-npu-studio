from __future__ import annotations

import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

import numpy as np
from PIL import Image

from config import TEMP_DIR
from engine.backends.rorem_dlc_inpainting_adapter import RORemDlcInpaintingAdapter, RORemDlcResult


class InpaintingController:
    """Threaded Studio boundary for RORem object removal on Qualcomm HTP."""

    MODEL_SIZE = (1024, 1024)
    CONTEXT_RATIO = 0.25
    MIN_CONTEXT_PIXELS = 32

    def __init__(
        self,
        adapter: RORemDlcInpaintingAdapter | None = None,
        ui_dispatch: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self.adapter = adapter or RORemDlcInpaintingAdapter()
        self.ui_dispatch = ui_dispatch or (lambda callback: callback())
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(
        self,
        *,
        input_image_path: str | Path,
        mask_image_path: str | Path,
        prompt: str,
        output_path: str | Path,
        steps: int = 1,
        seed: int = 20260830,
        negative_prompt: str | None = None,
        on_progress: Callable[[str, float, str | None], None] | None = None,
        on_complete: Callable[[RORemDlcResult], None] | None = None,
        asynchronous: bool = True,
    ) -> None:
        if self.running:
            raise RuntimeError("Inpainting is already running")

        def progress(phase: str, value: float, detail: str | None) -> None:
            if on_progress is not None:
                self.ui_dispatch(lambda: on_progress(phase, value, detail))

        def execute() -> None:
            try:
                result = self._run_product_path(
                    input_image_path=Path(input_image_path),
                    mask_image_path=Path(mask_image_path),
                    prompt=prompt,
                    output_path=Path(output_path),
                    negative_prompt=negative_prompt or "",
                    steps=steps,
                    seed=seed,
                    progress=progress,
                )
            except Exception as exc:
                result = RORemDlcResult(
                    success=False,
                    error_code="ERR_NPU_INFERENCE_FAILED",
                    error_message=f"{type(exc).__name__}: {exc}",
                )
            if on_complete is not None:
                self.ui_dispatch(lambda: on_complete(result))

        if asynchronous:
            self._thread = threading.Thread(target=execute, name="rorem-inpainting-ui", daemon=True)
            self._thread.start()
        else:
            execute()

    def _run_product_path(
        self,
        *,
        input_image_path: Path,
        mask_image_path: Path,
        prompt: str,
        output_path: Path,
        negative_prompt: str,
        steps: int,
        seed: int,
        progress: Callable[[str, float, str | None], None],
    ) -> RORemDlcResult:
        if input_image_path.resolve() == output_path.resolve():
            raise ValueError("The original image cannot be used as the output path")

        with Image.open(input_image_path) as opened:
            source = opened.convert("RGB")
        with Image.open(mask_image_path) as opened:
            mask = opened.convert("L")

        if mask.size != source.size:
            raise ValueError(
                f"Mask size {mask.size} does not match source image size {source.size}"
            )
        if mask.getbbox() is None:
            raise ValueError("The inpainting mask is empty")

        if source.size == self.MODEL_SIZE:
            return self.adapter.run(
                input_image_path,
                mask_image_path,
                prompt,
                output_path,
                negative_prompt=negative_prompt,
                steps=steps,
                seed=seed,
                progress_callback=progress,
            )

        progress("prepare", 0.02, "Arbeitsausschnitt wird für die NPU vorbereitet")
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="image_lab_", dir=TEMP_DIR) as directory:
            work_dir = Path(directory)
            crop_box = self._square_crop_box(mask)
            source_crop, mask_crop = self._crop_and_pad(source, mask, crop_box)
            model_source = source_crop.resize(self.MODEL_SIZE, Image.Resampling.LANCZOS)
            model_mask = mask_crop.resize(self.MODEL_SIZE, Image.Resampling.NEAREST)
            model_input_path = work_dir / "source_1024.png"
            model_mask_path = work_dir / "mask_1024.png"
            model_output_path = work_dir / "result_1024.png"
            model_source.save(model_input_path, format="PNG")
            model_mask.save(model_mask_path, format="PNG")

            result = self.adapter.run(
                model_input_path,
                model_mask_path,
                prompt,
                model_output_path,
                negative_prompt=negative_prompt,
                steps=steps,
                seed=seed,
                progress_callback=progress,
            )
            if not result.success or not result.output_path:
                return result

            with Image.open(result.output_path) as opened:
                generated = opened.convert("RGB").resize(
                    source_crop.size,
                    Image.Resampling.LANCZOS,
                )

            final_image = self._composite_crop(
                source=source,
                generated_crop=generated,
                mask_crop=mask_crop,
                crop_box=crop_box,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            final_image.save(output_path, format="PNG")
            result.output_path = output_path
            result.metadata.update(
                {
                    "source_size": list(source.size),
                    "model_input_size": list(self.MODEL_SIZE),
                    "working_crop": list(crop_box),
                    "global_stretch": False,
                }
            )
            return result

    @classmethod
    def _square_crop_box(cls, mask: Image.Image) -> tuple[int, int, int, int]:
        bbox = mask.getbbox()
        if bbox is None:
            raise ValueError("The inpainting mask is empty")
        left, top, right, bottom = bbox
        bbox_width = right - left
        bbox_height = bottom - top
        context = max(
            cls.MIN_CONTEXT_PIXELS,
            round(max(bbox_width, bbox_height) * cls.CONTEXT_RATIO),
        )
        expanded_left = max(0, left - context)
        expanded_top = max(0, top - context)
        expanded_right = min(mask.width, right + context)
        expanded_bottom = min(mask.height, bottom + context)
        side = max(
            expanded_right - expanded_left,
            expanded_bottom - expanded_top,
        )
        center_x = (expanded_left + expanded_right) / 2.0
        center_y = (expanded_top + expanded_bottom) / 2.0
        crop_left = round(center_x - side / 2.0)
        crop_top = round(center_y - side / 2.0)
        return crop_left, crop_top, crop_left + side, crop_top + side

    @staticmethod
    def _crop_and_pad(
        source: Image.Image,
        mask: Image.Image,
        crop_box: tuple[int, int, int, int],
    ) -> tuple[Image.Image, Image.Image]:
        left, top, right, bottom = crop_box
        side = right - left
        source_array = np.asarray(source, dtype=np.uint8)
        mask_array = np.asarray(mask, dtype=np.uint8)
        src_left = max(0, left)
        src_top = max(0, top)
        src_right = min(source.width, right)
        src_bottom = min(source.height, bottom)
        pad_left = src_left - left
        pad_top = src_top - top
        pad_right = right - src_right
        pad_bottom = bottom - src_bottom

        source_region = source_array[src_top:src_bottom, src_left:src_right]
        mask_region = mask_array[src_top:src_bottom, src_left:src_right]
        padded_source = np.pad(
            source_region,
            ((pad_top, pad_bottom), (pad_left, pad_right), (0, 0)),
            mode="edge",
        )
        padded_mask = np.pad(
            mask_region,
            ((pad_top, pad_bottom), (pad_left, pad_right)),
            mode="constant",
            constant_values=0,
        )
        if padded_source.shape[:2] != (side, side):
            raise RuntimeError("Internal crop/pad size mismatch")
        return Image.fromarray(padded_source, mode="RGB"), Image.fromarray(padded_mask, mode="L")

    @staticmethod
    def _composite_crop(
        *,
        source: Image.Image,
        generated_crop: Image.Image,
        mask_crop: Image.Image,
        crop_box: tuple[int, int, int, int],
    ) -> Image.Image:
        left, top, right, bottom = crop_box
        src_left = max(0, left)
        src_top = max(0, top)
        src_right = min(source.width, right)
        src_bottom = min(source.height, bottom)
        offset_x = src_left - left
        offset_y = src_top - top
        width = src_right - src_left
        height = src_bottom - src_top
        local_box = (offset_x, offset_y, offset_x + width, offset_y + height)
        generated_region = generated_crop.crop(local_box)
        mask_region = mask_crop.crop(local_box)
        original_region = source.crop((src_left, src_top, src_right, src_bottom))
        composed_region = Image.composite(generated_region, original_region, mask_region)
        final_image = source.copy()
        final_image.paste(composed_region, (src_left, src_top))
        return final_image

    def cancel(self) -> None:
        self.adapter.cancel()

    def close(self) -> None:
        close = getattr(self.adapter, "close", None)
        if close is not None:
            close()
