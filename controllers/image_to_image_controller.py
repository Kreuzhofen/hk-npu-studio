from __future__ import annotations

import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

from PIL import Image

from config import TEMP_DIR
from engine.backends.sd15_qnn_inpainting_adapter import (
    SD15QnnInpaintingAdapter,
    SD15QnnInpaintingResult,
)


class ImageToImageController:
    """Threaded Studio boundary for SD1.5 Image-to-Image on Qualcomm Hexagon HTP."""

    MODEL_SIZE = (512, 512)

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

    def cancel(self) -> None:
        """Cancel active inference if running."""
        if self.adapter:
            self.adapter.cancel()

    def start(
        self,
        *,
        input_image_path: str | Path,
        prompt: str,
        output_path: str | Path,
        steps: int = 20,
        seed: int = 42,
        negative_prompt: str | None = None,
        cfg_scale: float = 7.5,
        denoising_strength: float = 0.65,
        enable_reference_control: bool = False,
        reference_mode: str = "canny_qnn",
        reference_fidelity: float = 0.75,
        reference_image_path: str | Path | None = None,
        on_progress: Callable[[str, float, str | None], None] | None = None,
        on_complete: Callable[[SD15QnnInpaintingResult], None] | None = None,
        asynchronous: bool = True,
    ) -> None:
        if self.running:
            raise RuntimeError("Image-to-Image inference is already running")

        cfg_scale = max(1.0, min(15.0, float(cfg_scale)))
        denoising_strength = max(0.1, min(1.0, float(denoising_strength)))
        steps = max(10, min(50, int(steps)))

        def progress(phase: str, value: float, detail: str | None) -> None:
            if on_progress is not None:
                self.ui_dispatch(lambda: on_progress(phase, value, detail))

        def execute() -> None:
            try:
                result = self._run_product_path(
                    input_image_path=Path(input_image_path),
                    prompt=prompt,
                    output_path=Path(output_path),
                    negative_prompt=negative_prompt or "",
                    steps=steps,
                    seed=seed,
                    cfg_scale=cfg_scale,
                    denoising_strength=denoising_strength,
                    enable_reference_control=enable_reference_control,
                    reference_mode=reference_mode,
                    reference_fidelity=reference_fidelity,
                    reference_image_path=Path(reference_image_path) if reference_image_path else None,
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
            self._thread = threading.Thread(target=execute, name="sd15-img2img-ui", daemon=True)
            self._thread.start()
        else:
            execute()

    def _run_product_path(
        self,
        *,
        input_image_path: Path,
        prompt: str,
        output_path: Path,
        negative_prompt: str,
        steps: int,
        seed: int,
        cfg_scale: float = 7.5,
        denoising_strength: float = 0.65,
        enable_reference_control: bool = False,
        reference_mode: str = "canny_qnn",
        reference_fidelity: float = 0.75,
        reference_image_path: Path | None = None,
        progress: Callable[[str, float, str | None], None],
    ) -> SD15QnnInpaintingResult:
        if not input_image_path.is_file():
            raise FileNotFoundError(f"Eingabebild nicht gefunden: {input_image_path}")

        if input_image_path.resolve() == output_path.resolve():
            raise ValueError("Das Originalbild kann nicht als Ausgabepfad überschrieben werden")

        with Image.open(input_image_path) as opened:
            source = opened.convert("RGB")

        clean_temp = None
        if source.size == self.MODEL_SIZE:
            model_input_path = input_image_path
        else:
            progress("prepare", 0.02, "Bild wird auf 512x512 skaliert...")
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
            temp_dir = tempfile.mkdtemp(prefix="img2img_prep_", dir=TEMP_DIR)
            clean_temp = Path(temp_dir)
            model_input_path = clean_temp / "input_512.png"
            resized = source.resize(self.MODEL_SIZE, Image.Resampling.LANCZOS)
            resized.save(model_input_path, format="PNG")

        # If custom reference image is provided, prepare it
        model_ref_path = None
        if enable_reference_control and reference_image_path and reference_image_path.is_file():
            if reference_image_path.resolve() == input_image_path.resolve():
                model_ref_path = model_input_path
            else:
                with Image.open(reference_image_path) as ref_op:
                    ref_src = ref_op.convert("RGB")
                if ref_src.size == self.MODEL_SIZE:
                    model_ref_path = reference_image_path
                else:
                    if clean_temp is None:
                        TEMP_DIR.mkdir(parents=True, exist_ok=True)
                        temp_dir = tempfile.mkdtemp(prefix="img2img_prep_", dir=TEMP_DIR)
                        clean_temp = Path(temp_dir)
                    model_ref_path = clean_temp / "ref_512.png"
                    ref_resized = ref_src.resize(self.MODEL_SIZE, Image.Resampling.LANCZOS)
                    ref_resized.save(model_ref_path, format="PNG")
        elif enable_reference_control:
            model_ref_path = model_input_path

        try:
            return self.adapter.run_img2img(
                input_image_path=model_input_path,
                prompt=prompt,
                output_path=output_path,
                negative_prompt=negative_prompt,
                steps=steps,
                seed=seed,
                cfg_scale=cfg_scale,
                denoising_strength=denoising_strength,
                enable_reference_control=enable_reference_control,
                reference_mode=reference_mode,
                reference_fidelity=reference_fidelity,
                reference_image_path=model_ref_path,
                progress_callback=progress,
            )
        finally:
            if clean_temp and clean_temp.exists():
                import shutil
                shutil.rmtree(clean_temp, ignore_errors=True)
