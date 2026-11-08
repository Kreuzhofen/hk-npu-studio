from __future__ import annotations

import json
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

import numpy as np
from PIL import Image

from config import TEMP_DIR
from engine.backends.sd15_qnn_inpainting_adapter import (
    SD15QnnInpaintingAdapter,
    SD15QnnInpaintingResult,
    align_color_lab,
    generate_feathered_mask,
)

# Compatibility alias for legacy tests/views
RORemDlcResult = SD15QnnInpaintingResult


class InpaintingController:
    """Threaded Studio boundary for SD1.5 Inpainting on Qualcomm Hexagon HTP."""

    MODEL_SIZE = (512, 512)
    MIN_CROP_SIZE = 256
    CONTEXT_RATIO = 0.25
    MIN_CONTEXT_PIXELS = 32

    def __init__(
        self,
        adapter: SD15QnnInpaintingAdapter | None = None,
        ui_dispatch: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self.adapter = adapter or SD15QnnInpaintingAdapter()
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
        steps: int = 20,
        seed: int = 42,
        negative_prompt: str | None = None,
        cfg_scale: float = 7.5,
        denoising_strength: float = 1.0,
        feather_radius: int = 5,
        dilate_pixels: int = 0,
        material_preset: str | None = None,
        material_priming_intensity: float = 1.0,
        on_progress: Callable[[str, float, str | None], None] | None = None,
        on_complete: Callable[[SD15QnnInpaintingResult], None] | None = None,
        asynchronous: bool = True,
    ) -> None:
        if self.running:
            raise RuntimeError("Inpainting is already running")

        # Defensive bounds enforcement: feathering (0-15 px), dilation (0-8 px), cfg (1.0-15.0), strength (0.1-1.0)
        feather_radius = max(0, min(15, int(feather_radius)))
        dilate_pixels = max(0, min(8, int(dilate_pixels)))
        cfg_scale = max(1.0, min(15.0, float(cfg_scale)))
        denoising_strength = max(0.1, min(1.0, float(denoising_strength)))

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
                    cfg_scale=cfg_scale,
                    denoising_strength=denoising_strength,
                    feather_radius=feather_radius,
                    dilate_pixels=dilate_pixels,
                    material_preset=material_preset,
                    material_priming_intensity=material_priming_intensity,
                    progress=progress,
                )
            except Exception as exc:
                result = SD15QnnInpaintingResult(
                    success=False,
                    error_code="ERR_NPU_INFERENCE_FAILED",
                    error_message=f"{type(exc).__name__}: {exc}",
                )
            if on_complete is not None:
                self.ui_dispatch(lambda: on_complete(result))

        if asynchronous:
            self._thread = threading.Thread(target=execute, name="sd15-inpainting-ui", daemon=True)
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
        cfg_scale: float = 7.5,
        denoising_strength: float = 1.0,
        feather_radius: int = 5,
        dilate_pixels: int = 0,
        material_preset: str | None = None,
        material_priming_intensity: float = 1.0,
        progress: Callable[[str, float, str | None], None],
    ) -> SD15QnnInpaintingResult:
        feather_radius = max(0, min(15, int(feather_radius)))
        dilate_pixels = max(0, min(8, int(dilate_pixels)))
        cfg_scale = max(1.0, min(15.0, float(cfg_scale)))
        denoising_strength = max(0.1, min(1.0, float(denoising_strength)))

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
        bbox = mask.getbbox()
        if bbox is None:
            raise ValueError("The inpainting mask is empty")

        # Optional Non-destructive Material Priming (Phoenix Material Lab)
        working_source = source
        if material_preset is not None:
            from engine.material_priming import prime_material_chrominance
            progress("prime_material", 0.01, f"Material-Priming ({material_preset}) wird angewendet...")
            working_source = prime_material_chrominance(
                source,
                mask,
                preset_name=material_preset,
                intensity=material_priming_intensity,
            )

        crop_box = self._square_crop_box(mask)
        crop_side = crop_box[2] - crop_box[0]
        max_mask_dim = max(bbox[2] - bbox[0], bbox[3] - bbox[1])

        # Full-frame inpainting is preserved only if the image is already MODEL_SIZE (512, 512)
        # AND the mask is sufficiently large (spanning >= 75% of model dimension or crop covers entire image)
        use_full_frame = (
            source.size == self.MODEL_SIZE
            and (crop_side >= source.width or max_mask_dim >= round(self.MODEL_SIZE[0] * 0.75))
        )

        if use_full_frame:
            actual_input_path = input_image_path
            clean_temp_full = None
            if material_preset is not None:
                TEMP_DIR.mkdir(parents=True, exist_ok=True)
                temp_full = tempfile.NamedTemporaryFile(prefix="primed_full_", suffix=".png", dir=TEMP_DIR, delete=False)
                clean_temp_full = Path(temp_full.name)
                temp_full.close()
                working_source.save(clean_temp_full, format="PNG")
                actual_input_path = clean_temp_full

            try:
                res = self.adapter.run(
                    actual_input_path,
                    mask_image_path,
                    prompt,
                    output_path,
                    negative_prompt=negative_prompt,
                    steps=steps,
                    seed=seed,
                    cfg_scale=cfg_scale,
                    denoising_strength=denoising_strength,
                    feather_radius=feather_radius,
                    dilate_pixels=dilate_pixels,
                    progress_callback=progress,
                )
            finally:
                if clean_temp_full and clean_temp_full.exists():
                    clean_temp_full.unlink(missing_ok=True)

            if res.success and res.output_path:
                self._save_sidecar(
                    output_path=Path(res.output_path),
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    steps=steps,
                    seed=seed,
                    cfg_scale=cfg_scale,
                    denoising_strength=denoising_strength,
                    feather_radius=feather_radius,
                    dilate_pixels=dilate_pixels,
                    source_size=source.size,
                    input_image_path=input_image_path,
                    working_crop=[0, 0, source.width, source.height],
                    material_preset=material_preset,
                    material_priming_intensity=material_priming_intensity,
                )
            return res

        progress("prepare", 0.02, "Arbeitsausschnitt wird für die NPU vorbereitet")
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="image_lab_", dir=TEMP_DIR) as directory:
            work_dir = Path(directory)
            source_crop, mask_crop = self._crop_and_pad(working_source, mask, crop_box)
            model_source = source_crop.resize(self.MODEL_SIZE, Image.Resampling.LANCZOS)
            model_mask = mask_crop.resize(self.MODEL_SIZE, Image.Resampling.BILINEAR)
            model_input_path = work_dir / "source_512.png"
            model_mask_path = work_dir / "mask_512.png"
            model_output_path = work_dir / "result_512.png"
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
                cfg_scale=cfg_scale,
                denoising_strength=denoising_strength,
                feather_radius=feather_radius,
                dilate_pixels=dilate_pixels,
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
                feather_radius=feather_radius,
                dilate_pixels=dilate_pixels,
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
                    "cfg_scale": cfg_scale,
                    "denoising_strength": denoising_strength,
                    "feather_radius": feather_radius,
                    "dilate_pixels": dilate_pixels,
                    "material_preset": material_preset,
                    "material_priming_intensity": material_priming_intensity if material_preset else None,
                }
            )
            self._save_sidecar(
                output_path=output_path,
                prompt=prompt,
                negative_prompt=negative_prompt,
                steps=steps,
                seed=seed,
                cfg_scale=cfg_scale,
                denoising_strength=denoising_strength,
                feather_radius=feather_radius,
                dilate_pixels=dilate_pixels,
                source_size=source.size,
                input_image_path=input_image_path,
                working_crop=list(crop_box),
                material_preset=material_preset,
                material_priming_intensity=material_priming_intensity,
            )
            return result

    @staticmethod
    def _save_sidecar(
        output_path: Path,
        *,
        prompt: str,
        negative_prompt: str,
        steps: int,
        seed: int,
        cfg_scale: float,
        denoising_strength: float,
        feather_radius: int,
        dilate_pixels: int,
        source_size: tuple[int, int],
        input_image_path: Path,
        working_crop: list[int] | None = None,
        material_preset: str | None = None,
        material_priming_intensity: float = 1.0,
    ) -> None:
        """Persist generation parameters into standard JSON sidecar for Gallery and Inspector."""
        try:
            sidecar_path = output_path.with_suffix(".json")
            data = {
                "feature": "Inpainting",
                "mode": "generative_fill",
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "model": "stable_diffusion_v1_5_inpainting_qnn",
                "model_id": "stable_diffusion_v1_5_inpainting_qnn",
                "seed": seed,
                "steps": steps,
                "cfg": cfg_scale,
                "denoising_strength": denoising_strength,
                "feather_radius": feather_radius,
                "dilate_pixels": dilate_pixels,
                "width": source_size[0],
                "height": source_size[1],
                "backend": "Qualcomm SD1.5 Inpainting QNN (HTP)",
                "input_image_path": str(input_image_path),
                "output_path": str(output_path),
                "working_crop": working_crop if working_crop else [0, 0, source_size[0], source_size[1]],
                "focused_crop": working_crop is not None and (working_crop[2] - working_crop[0] < source_size[0]),
                "material_preset": material_preset,
                "material_priming_intensity": material_priming_intensity if material_preset else None,
            }
            with open(sidecar_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @classmethod
    def _square_crop_box(cls, mask: Image.Image) -> tuple[int, int, int, int]:
        bbox = mask.getbbox()
        if bbox is None:
            raise ValueError("The inpainting mask is empty")
        left, top, right, bottom = bbox
        bbox_width = right - left
        bbox_height = bottom - top
        max_dim = max(bbox_width, bbox_height)
        context = max(
            cls.MIN_CONTEXT_PIXELS,
            round(max_dim * cls.CONTEXT_RATIO),
        )
        needed_side = max_dim + 2 * context
        target_side = max(needed_side, cls.MIN_CROP_SIZE)

        # If both image dimensions are smaller than MIN_CROP_SIZE, scale side to max image dimension
        if mask.width < cls.MIN_CROP_SIZE and mask.height < cls.MIN_CROP_SIZE:
            side = max(mask.width, mask.height)
        else:
            side = target_side

        center_x = (left + right) / 2.0
        center_y = (top + bottom) / 2.0
        crop_left = round(center_x - side / 2.0)
        crop_top = round(center_y - side / 2.0)

        # Boundary clamping: ensure crop box stays inside image when side fits
        if side <= mask.width:
            crop_left = max(0, min(crop_left, mask.width - side))
        else:
            crop_left = round((mask.width - side) / 2.0)

        if side <= mask.height:
            crop_top = max(0, min(crop_top, mask.height - side))
        else:
            crop_top = round((mask.height - side) / 2.0)

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
        feather_radius: int = 5,
        dilate_pixels: int = 0,
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
        feathered_mask = generate_feathered_mask(
            mask_region,
            dilate_pixels=dilate_pixels,
            feather_radius=feather_radius,
        )
        # Note: generated_crop was already color-aligned by the adapter during NPU inpainting.
        # Running align_color_lab a second time here causes duplicate color drift/damping.
        # Direct composite with the feathered mask ensures single-stage, clean integration.
        composed_region = Image.composite(generated_region, original_region, feathered_mask)
        final_image = source.copy()
        final_image.paste(composed_region, (src_left, src_top))
        return final_image

    def cancel(self) -> None:
        self.adapter.cancel()

    def close(self) -> None:
        close = getattr(self.adapter, "close", None)
        if close is not None:
            close()
