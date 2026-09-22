"""
HK NPU STUDIO - FiDeSR Strong Photo Restore Backend

Integration bridge for the validated FiDeSR Strong full-NPU path.

AI inference:
    VAE Encoder -> UNet -> LRRB -> VAE Decoder
    Qualcomm QNN / HTP only.

CPU:
    orchestration, tiling, LF/HF deterministic math,
    wavelet color correction, image I/O.

Important:
    FiDeSR Strong already produces the 4x final image.
    RealESRGAN must NOT be chained after this backend.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

import config
from engine.file_utils import get_unique_filename
from engine.backends.photo_restore_backend import (
    PhotoRestoreResult,
    PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
    PHOTO_RESTORE_INPUT_INVALID,
    PHOTO_RESTORE_CANCELLED,
    PHOTO_RESTORE_DDCOLOR_MISSING,
    PHOTO_RESTORE_DDCOLOR_FAILED,
    is_grayscale_image,
    rgb2lab_np,
    lab2rgb_np,
)


PHOTO_RESTORE_FIDESR_MISSING = "PHOTO_RESTORE_FIDESR_MISSING"
PHOTO_RESTORE_FIDESR_FAILED = "PHOTO_RESTORE_FIDESR_FAILED"

ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = ROOT / "models" / "photo_restore"
CONTEXT_DIR = ROOT / "models" / "photo_restore_context"

FIDESR_REQUIRED = (
    CONTEXT_DIR / "fidesr_vae_encoder" / "fidesr_vae_encoder.serialized.bin.bin",
    CONTEXT_DIR / "fidesr_unet" / "fidesr_unet_merged.serialized.bin.bin",
    CONTEXT_DIR / "fidesr_lrrb" / "fidesr_lrrb.serialized.bin.bin",
    CONTEXT_DIR / "fidesr_vae_decoder" / "fidesr_vae_decoder.serialized.bin.bin",
    MODEL_DIR / "fidesr_empty_prompt_embeds.bin",
    MODEL_DIR / "fidesr_epsilon_seed231.bin",
)


class FiDeSRPhotoRestoreBackend:
    """
    PhotoRestore-compatible wrapper around the frozen FiDeSR Strong runner.

    This first product-integration version deliberately preserves the exact
    validated Strong implementation to establish Studio/reference parity.
    """

    def __init__(
        self,
        runner_template: Path | str | None = None,
    ) -> None:
        self.runner_template = (
            Path(runner_template)
            if runner_template
            else Path(__file__).with_name("fidesr_strong_runner_template.py")
        )

        self._status = "UNINITIALIZED"
        self._cancel_requested = threading.Event()
        self._lock = threading.RLock()
        self._process: subprocess.Popen[str] | None = None

    @property
    def status(self) -> str:
        return self._status

    def initialize(self) -> None:
        with self._lock:
            if self._status == "CLOSED":
                raise RuntimeError("FiDeSR backend is closed.")

            if self._status == "INITIALIZED":
                return

            if not self.runner_template.is_file():
                raise RuntimeError(
                    f"FiDeSR Strong runner template missing: {self.runner_template}"
                )

            missing = [p for p in FIDESR_REQUIRED if not p.is_file()]
            if missing:
                raise RuntimeError(
                    "FiDeSR model artifacts missing: "
                    + ", ".join(str(p) for p in missing)
                )

            self._status = "INITIALIZED"

    def cancel(self) -> None:
        self._cancel_requested.set()

        with self._lock:
            proc = self._process

        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

    def close(self) -> None:
        self.cancel()
        with self._lock:
            self._process = None
            self._status = "CLOSED"

    def _check_cancel(self) -> None:
        if self._cancel_requested.is_set():
            raise RuntimeError(PHOTO_RESTORE_CANCELLED)

    @staticmethod
    def _replace_required(text: str, old: str, new: str) -> str:
        if old not in text:
            raise RuntimeError(
                f"Frozen FiDeSR runner contract changed; token missing: {old}"
            )
        return text.replace(old, new, 1)

    def _create_job_runner(
        self,
        *,
        input_path: Path,
        work_dir: Path,
        output_path: Path,
    ) -> Path:
        source = self.runner_template.read_text(
            encoding="utf-8",
            errors="strict",
        )

        def py_string(path: Path) -> str:
            # repr() produces a valid Python string literal and safely
            # escapes Windows backslashes such as C:\Users\...
            return repr(str(path))

        source = self._replace_required(
            source,
            r'ROOT = Path(r"C:\SnapdragonAI")',
            f"ROOT = Path({py_string(ROOT)})",
        )

        source = self._replace_required(
            source,
            'WORK = TEMP_DIR / "photo_restore"',
            f"WORK = Path({py_string(work_dir)})",
        )

        source = re.sub(
            r'^INPUT_IMAGE\s*=.*$',
            lambda _match: f"INPUT_IMAGE = Path({py_string(input_path)})",
            source,
            count=1,
            flags=re.MULTILINE,
        )

        source = re.sub(
            r'^OUTPUT_IMAGE\s*=.*$',
            lambda _match: f"OUTPUT_IMAGE = Path({py_string(output_path)})",
            source,
            count=1,
            flags=re.MULTILINE,
        )

        runner_path = work_dir / "run_fidesr_strong_job.py"
        runner_path.write_text(source, encoding="utf-8")
        return runner_path

    @staticmethod
    def _progress_from_line(
        line: str,
    ) -> tuple[str, float, str] | None:
        # 1. Granular Tile-Progress event: TILE_PROGRESS: stage=STAGE tile=K total=N
        match_tile = re.search(
            r"TILE_PROGRESS:\s*stage=(\w+)\s+tile=(\d+)\s+total=(\d+)",
            line,
            re.IGNORECASE,
        )
        if match_tile:
            stage = match_tile.group(1).upper()
            tile = int(match_tile.group(2))
            total = max(1, int(match_tile.group(3)))
            ratio = min(1.0, max(0.0, tile / total))

            if stage == "VAE_ENCODER":
                pct = 0.02 + 0.23 * ratio
                return ("restore", pct, f"VAE Encoder – Kachel {tile}/{total} auf NPU")
            if stage == "UNET":
                pct = 0.25 + 0.25 * ratio
                return ("restore", pct, f"UNet – Kachel {tile}/{total} auf NPU")
            if stage == "LRRB":
                pct = 0.50 + 0.25 * ratio
                return ("restore", pct, f"LRRB – Kachel {tile}/{total} auf NPU")
            if stage == "VAE_DECODER":
                pct = 0.76 + 0.18 * ratio
                return ("restore", pct, f"VAE Decoder – Kachel {tile}/{total} auf NPU")

        # 2. Stage-Start event: STAGE_START: stage=STAGE total=N
        match_start = re.search(
            r"STAGE_START:\s*stage=(\w+)\s+total=(\d+)",
            line,
            re.IGNORECASE,
        )
        if match_start:
            stage = match_start.group(1).upper()
            total = int(match_start.group(2))
            if stage == "VAE_ENCODER":
                return ("restore", 0.02, f"VAE Encoder – NPU-Initialisierung (0/{total})")
            if stage == "UNET":
                return ("restore", 0.25, f"UNet – NPU-Initialisierung (0/{total})")
            if stage == "LRRB":
                return ("restore", 0.50, f"LRRB – NPU-Initialisierung (0/{total})")
            if stage == "VAE_DECODER":
                return ("restore", 0.76, f"VAE Decoder – NPU-Initialisierung (0/{total})")

        u = line.upper()

        if "PREFLIGHT=PASS" in u:
            return ("prepare", 0.02, "FiDeSR Strong: NPU-Prüfung abgeschlossen")

        if "LF_HF_CPU" in u:
            return ("restore", 0.755, "FiDeSR: LF/HF Detailrekonstruktion")

        if "WAVELET_COLOR_FIX" in u:
            return ("restore", 0.95, "FiDeSR: Farb- und Detailfinalisierung")

        if "DETAIL_PRESERVATION_BYPASS" in u:
            return ("restore", 0.97, "FiDeSR: Detailwiederherstellung")

        if "FULL_PIPELINE_TECH_PASS=YES" in u:
            return ("restore", 0.975, "FiDeSR Strong abgeschlossen")

        # 3. Fallback milestone events when TILE_PROGRESS is not available (e.g. legacy logs)
        if "VAE_ENCODER" in u and "TILE_PROGRESS" not in u and "STAGE_START" not in u:
            return ("restore", 0.12, "FiDeSR: VAE Encoder auf NPU")

        if "UNET" in u and "LRRB" not in u and "TILE_PROGRESS" not in u and "STAGE_START" not in u:
            return ("restore", 0.35, "FiDeSR: UNet auf NPU")

        if "LRRB" in u and "TILE_PROGRESS" not in u and "STAGE_START" not in u:
            return ("restore", 0.55, "FiDeSR: LRRB auf NPU")

        if "VAE_DECODER" in u and "TILE_PROGRESS" not in u and "STAGE_START" not in u:
            return ("restore", 0.80, "FiDeSR: VAE Decoder auf NPU")

        return None

    def _run_strong(
        self,
        *,
        input_path: Path,
        work_dir: Path,
        progress: Callable[[str, float, str | None], None],
    ) -> tuple[Path, str]:
        output_path = work_dir / "fidesr_strong_x4.png"

        runner_path = self._create_job_runner(
            input_path=input_path,
            work_dir=work_dir,
            output_path=output_path,
        )

        cmd = [
            sys.executable,
            "-u",
            str(runner_path),
        ]

        log_lines: list[str] = []

        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        with self._lock:
            self._process = proc

        try:
            assert proc.stdout is not None

            last_pct = 0.0
            for raw_line in proc.stdout:
                line = raw_line.rstrip()
                log_lines.append(line)
                print(f"[FiDeSR Studio] {line}", flush=True)

                mapped = self._progress_from_line(line)
                if mapped is not None:
                    phase, pct, detail = mapped
                    if pct < last_pct:
                        pct = last_pct
                    else:
                        last_pct = pct
                    progress(phase, pct, detail)

                if self._cancel_requested.is_set():
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    raise RuntimeError(PHOTO_RESTORE_CANCELLED)

            return_code = proc.wait()

        finally:
            with self._lock:
                self._process = None

        log_text = "\n".join(log_lines)

        if return_code != 0:
            raise RuntimeError(
                f"FiDeSR Strong runner failed with exit code {return_code}.\n"
                f"{log_text[-6000:]}"
            )

        if "ALL_FIDESR_AI_INFERENCE_QNN_HTP=PASS" not in log_text:
            raise RuntimeError(
                "FiDeSR finished without QNN/HTP AI inference PASS marker."
            )

        if "FULL_PIPELINE_TECH_PASS=YES" not in log_text:
            raise RuntimeError(
                "FiDeSR finished without full pipeline TECH PASS marker."
            )

        if not output_path.is_file():
            raise RuntimeError(
                f"FiDeSR output missing: {output_path}"
            )

        return output_path, log_text


    def _run_ddcolor_npu(
        self,
        img: Image.Image,
    ) -> Image.Image:
        """
        Run DDColor exclusively through Qualcomm QNN/HTP.

        CPU work in this method is limited to deterministic image
        preparation, Lab conversion, resize and chroma compositing.
        The DDColor neural-network inference itself runs on HTP.
        """

        ddcolor_path = config.PHOTO_RESTORE_DDCOLOR_DLC

        if not ddcolor_path.is_file():
            raise RuntimeError(
                f"{PHOTO_RESTORE_DDCOLOR_MISSING}: "
                f"DDColor QNN context not found: {ddcolor_path}"
            )

        try:
            from qai_appbuilder import (
                QNNConfig,
                QNNContext,
                Runtime,
                LogLevel,
                ProfilingLevel,
                PerfProfile,
            )
        except ImportError as exc:
            raise RuntimeError(
                f"{PHOTO_RESTORE_DDCOLOR_FAILED}: "
                f"qai_appbuilder unavailable: {exc}"
            ) from exc

        self._check_cancel()

        context = None

        try:
            QNNConfig.Config(
                Runtime.HTP,
                LogLevel.WARN,
                ProfilingLevel.BASIC,
                "",
            )

            context = QNNContext(
                "ddcolor",
                str(ddcolor_path),
            )

            orig_w, orig_h = img.size

            img_np = (
                np.asarray(
                    img.convert("RGB"),
                    dtype=np.float32,
                )
                / 255.0
            )

            orig_lab = rgb2lab_np(
                img_np
            )

            orig_l = orig_lab[..., :1]

            pil_resized = img.convert("RGB").resize(
                (256, 256),
                Image.Resampling.BILINEAR,
            )

            resized_np = (
                np.asarray(
                    pil_resized,
                    dtype=np.float32,
                )
                / 255.0
            )

            resized_lab = rgb2lab_np(
                resized_np
            )

            resized_l = resized_lab[..., :1]

            gray_lab = np.concatenate(
                [
                    resized_l,
                    np.zeros_like(resized_l),
                    np.zeros_like(resized_l),
                ],
                axis=-1,
            )

            gray_rgb = (
                lab2rgb_np(
                    gray_lab
                )[np.newaxis, ...]
                .astype(np.float32)
            )

            self._check_cancel()

            out = context.Inference(
                [gray_rgb],
                perf_profile=PerfProfile.BURST,
            )

            self._check_cancel()

            out_ab = out[0]

            if out_ab.ndim != 4:
                raise RuntimeError(
                    f"Unexpected DDColor output rank: "
                    f"{out_ab.shape}"
                )

            if out_ab.shape[0] != 1:
                raise RuntimeError(
                    f"Unexpected DDColor batch shape: "
                    f"{out_ab.shape}"
                )

            if out_ab.shape[1] != 2:
                raise RuntimeError(
                    f"Unexpected DDColor channel shape: "
                    f"{out_ab.shape}"
                )

            a_low = out_ab[
                0,
                0,
                :,
                :,
            ].astype(
                np.float32
            )

            b_low = out_ab[
                0,
                1,
                :,
                :,
            ].astype(
                np.float32
            )

            a_pil = Image.fromarray(
                a_low,
                mode="F",
            ).resize(
                (orig_w, orig_h),
                Image.Resampling.BILINEAR,
            )

            b_pil = Image.fromarray(
                b_low,
                mode="F",
            ).resize(
                (orig_w, orig_h),
                Image.Resampling.BILINEAR,
            )

            a_up = np.asarray(
                a_pil,
                dtype=np.float32,
            )[..., np.newaxis]

            b_up = np.asarray(
                b_pil,
                dtype=np.float32,
            )[..., np.newaxis]

            out_lab = np.concatenate(
                [
                    orig_l,
                    a_up,
                    b_up,
                ],
                axis=-1,
            )

            out_rgb = lab2rgb_np(
                out_lab
            )

            result = Image.fromarray(
                (
                    np.clip(
                        out_rgb,
                        0.0,
                        1.0,
                    )
                    * 255.0
                )
                .round()
                .astype(np.uint8)
            )

            return result

        except RuntimeError:
            raise

        except Exception as exc:
            raise RuntimeError(
                f"{PHOTO_RESTORE_DDCOLOR_FAILED}: "
                f"DDColor QNN/HTP inference failed: {exc}"
            ) from exc

        finally:
            if context is not None:
                try:
                    if hasattr(
                        context,
                        "release",
                    ):
                        context.release()
                except Exception:
                    pass

    def _run_realesrgan_npu(
        self,
        img: Image.Image,
        work_dir: Path,
        progress: Callable[[str, float, str | None], None],
    ) -> Image.Image:
        self._check_cancel()
        from modules.realesrgan_core import upscale_tiled

        temp_input = work_dir / "fidesr_intermediate.png"
        img.save(temp_input, format="PNG")

        self._check_cancel()

        def _esrgan_progress(msg: str) -> None:
            self._check_cancel()
            progress("upscale", 0.985, f"RealESRGAN x4 QNN/HTP: {msg}")

        out_path = upscale_tiled(
            temp_input,
            progress=_esrgan_progress,
        )

        with Image.open(out_path) as loaded:
            return loaded.convert("RGB")

    def restore(
        self,
        image_path: Path | str,
        output_dir: Path | str | None = None,
        upscale_factor: int = 4,
        auto_colorize: bool = True,
        mode: str = "faithful",
        progress_callback: Callable[[str, float, str | None], None] | None = None,
    ) -> PhotoRestoreResult:

        progress = progress_callback or (
            lambda _phase, _pct, _detail: None
        )

        with self._lock:
            if self._status == "CLOSED":
                return PhotoRestoreResult(
                    success=False,
                    error_code=PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
                    error_message="FiDeSR backend is closed.",
                )

            if self._status == "BUSY":
                return PhotoRestoreResult(
                    success=False,
                    error_code=PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
                    error_message="FiDeSR backend is already processing a job.",
                )

            if self._status == "UNINITIALIZED":
                try:
                    self.initialize()
                except Exception as exc:
                    return PhotoRestoreResult(
                        success=False,
                        error_code=PHOTO_RESTORE_FIDESR_MISSING,
                        error_message=str(exc),
                    )

            self._status = "BUSY"

        self._cancel_requested.clear()
        started = time.perf_counter()

        job_dir: Path | None = None

        try:
            in_path = Path(image_path)

            if not in_path.is_file():
                return PhotoRestoreResult(
                    success=False,
                    error_code=PHOTO_RESTORE_INPUT_INVALID,
                    error_message=f"Input image does not exist: {in_path}",
                )

            if upscale_factor not in (2, 4):
                return PhotoRestoreResult(
                    success=False,
                    error_code=PHOTO_RESTORE_INPUT_INVALID,
                    error_message=(
                        f"Unsupported upscale factor: {upscale_factor}. "
                        "Supported factors: 2, 4."
                    ),
                )

            if mode not in ("faithful", "enhanced", "fidesr_strong"):
                return PhotoRestoreResult(
                    success=False,
                    error_code=PHOTO_RESTORE_INPUT_INVALID,
                    error_message=(
                        f"Unsupported restoration mode: '{mode}'. "
                        "Supported modes: 'faithful', 'enhanced'."
                    ),
                )

            self._check_cancel()

            with Image.open(in_path) as probe:
                probe.load()
                orig_w, orig_h = probe.size
                input_is_grayscale = is_grayscale_image(probe)

            progress(
                "prepare",
                0.02,
                f"FiDeSR Strong wird vorbereitet: {orig_w}x{orig_h}",
            )

            job_root = ROOT / "temp" / "fidesr_studio_jobs"
            job_root.mkdir(parents=True, exist_ok=True)

            job_dir = job_root / (
                time.strftime("%Y%m%d_%H%M%S")
                + "_"
                + uuid.uuid4().hex[:8]
            )
            job_dir.mkdir(parents=True, exist_ok=False)

            strong_output, log_text = self._run_strong(
                input_path=in_path,
                work_dir=job_dir,
                progress=progress,
            )

            self._check_cancel()

            progress(
                "save",
                0.98,
                "FiDeSR Strong Ergebnis wird gespeichert",
            )

            out_directory = (
                Path(output_dir)
                if output_dir
                else config.OUTPUT_DIR
            )
            out_directory.mkdir(parents=True, exist_ok=True)

            if mode == "faithful":
                final_name = (
                    f"{in_path.stem}_faithful_x{upscale_factor}.png"
                )
            elif mode == "enhanced":
                final_name = (
                    f"{in_path.stem}_enhanced_x{upscale_factor}.png"
                )
            else:
                final_name = (
                    f"{in_path.stem}_fidesr_strong_x{upscale_factor}.png"
                )
            final_path = get_unique_filename(
                out_directory,
                final_name,
            )

            is_colorized = False
            ddcolor_seconds = 0.0

            with Image.open(strong_output) as result_img:
                result_rgb = result_img.convert("RGB")

                if input_is_grayscale and auto_colorize:
                    progress(
                        "colorize",
                        0.965,
                        "DDColor-Farbrekonstruktion auf NPU...",
                    )

                    self._check_cancel()

                    ddcolor_started = time.perf_counter()

                    result_rgb = self._run_ddcolor_npu(
                        result_rgb
                    )

                    ddcolor_seconds = (
                        time.perf_counter()
                        - ddcolor_started
                    )

                    is_colorized = True

                    progress(
                        "colorize",
                        0.980,
                        (
                            "DDColor-Farbrekonstruktion "
                            f"abgeschlossen ({ddcolor_seconds:.2f}s)"
                        ),
                    )

                elif auto_colorize:
                    progress(
                        "colorize",
                        0.980,
                        (
                            "DDColor übersprungen: "
                            "Eingabe enthält bereits Farbe"
                        ),
                    )

                else:
                    progress(
                        "colorize",
                        0.980,
                        "DDColor vom Benutzer deaktiviert",
                    )

                self._check_cancel()

                fidesr_w, fidesr_h = result_rgb.size
                realesrgan_raw_size: list[int] | None = None
                is_enhanced = (mode == "enhanced")

                if is_enhanced:
                    progress(
                        "upscale",
                        0.982,
                        "RealESRGAN x4 NPU-Verfeinerung...",
                    )
                    self._check_cancel()
                    result_rgb = self._run_realesrgan_npu(
                        img=result_rgb,
                        work_dir=job_dir,
                        progress=progress,
                    )
                    realesrgan_raw_w, realesrgan_raw_h = result_rgb.size
                    realesrgan_raw_size = [realesrgan_raw_w, realesrgan_raw_h]

                    self._check_cancel()

                    # Section 3 Contract: Deterministically downsample back to target dimensions
                    # Target dimensions: (orig_w * upscale_factor, orig_h * upscale_factor)
                    target_w = orig_w * upscale_factor
                    target_h = orig_h * upscale_factor
                    result_rgb = result_rgb.resize(
                        (target_w, target_h),
                        Image.Resampling.LANCZOS,
                    )
                else:
                    # Faithful mode: RealESRGAN strictly NOT called
                    if upscale_factor == 2:
                        result_rgb = result_rgb.resize(
                            (orig_w * 2, orig_h * 2),
                            Image.Resampling.LANCZOS,
                        )

                # Deterministic CPU-only safe finishing (no AI fallback, strict dynamic range clipping)
                arr_finishing = np.clip(
                    np.asarray(result_rgb, dtype=np.float32), 0.0, 255.0
                ).astype(np.uint8)
                result_rgb = Image.fromarray(arr_finishing, mode="RGB")

                result_rgb.save(
                    final_path,
                    format="PNG",
                )

                final_w, final_h = result_rgb.size

            elapsed = time.perf_counter() - started

            metadata = {
                "feature": "AI Photo Restore",
                "mode": mode,
                "restore_model": (
                    "FiDeSR Strong + RealESRGAN x4"
                    if is_enhanced
                    else "FiDeSR Strong"
                ),
                "pipeline": [
                    "VAE Encoder QNN/HTP",
                    "UNet QNN/HTP",
                    "LRRB QNN/HTP",
                    "LF/HF deterministic CPU math",
                    "VAE Decoder QNN/HTP",
                    "Wavelet color fix",
                ] + (
                    [
                        "RealESRGAN x4 QNN/HTP",
                        "Deterministic Lanczos downsample to target size",
                    ]
                    if is_enhanced
                    else []
                ) + [
                    "Deterministic CPU finishing",
                ],
                "upscale_factor": upscale_factor,
                "native_fidesr_scale": 4,
                "runtime": "QNN/HTP",
                "cpu_model_inference": False,
                "gpu_model_inference": False,
                "realesrgan_after_fidesr": is_enhanced,
                "realesrgan_called": is_enhanced,
                "fidesr_output_size": [fidesr_w, fidesr_h],
                "realesrgan_raw_output_size": realesrgan_raw_size,
                "final_output_size": [final_w, final_h],
                "final_resize_method": "Lanczos",
                "ddcolor_applied": bool(is_colorized),
                "auto_colorize_requested": bool(auto_colorize),
                "input_is_grayscale": bool(input_is_grayscale),
                "colorization_model": (
                    "DDColor QNN/HTP"
                    if is_colorized
                    else "skipped"
                ),
                "ddcolor_seconds": round(ddcolor_seconds, 4),
                "input_path": str(in_path),
                "output_path": str(final_path),
                "input_size": [orig_w, orig_h],
                "output_size": [final_w, final_h],
                "total_seconds": round(elapsed, 4),
                "qnn_htp_pass": (
                    "ALL_FIDESR_AI_INFERENCE_QNN_HTP=PASS"
                    in log_text
                ),
            }

            try:
                final_path.with_suffix(".json").write_text(
                    json.dumps(metadata, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass

            progress(
                "save",
                1.0,
                "FiDeSR Strong fertiggestellt",
            )

            return PhotoRestoreResult(
                success=True,
                output_path=str(final_path),
                is_colorized=is_colorized,
                upscale_factor=upscale_factor,
                generation_time=elapsed,
                metadata=metadata,
            )

        except RuntimeError as exc:
            if str(exc) == PHOTO_RESTORE_CANCELLED:
                return PhotoRestoreResult(
                    success=False,
                    error_code=PHOTO_RESTORE_CANCELLED,
                    error_message="Photo restore operation was cancelled.",
                )

            message = str(exc)

            if message.startswith(
                PHOTO_RESTORE_DDCOLOR_MISSING
            ):
                return PhotoRestoreResult(
                    success=False,
                    error_code=PHOTO_RESTORE_DDCOLOR_MISSING,
                    error_message=message,
                )

            if message.startswith(
                PHOTO_RESTORE_DDCOLOR_FAILED
            ):
                return PhotoRestoreResult(
                    success=False,
                    error_code=PHOTO_RESTORE_DDCOLOR_FAILED,
                    error_message=message,
                )

            return PhotoRestoreResult(
                success=False,
                error_code=PHOTO_RESTORE_FIDESR_FAILED,
                error_message=str(exc),
            )

        except Exception as exc:
            return PhotoRestoreResult(
                success=False,
                error_code=PHOTO_RESTORE_FIDESR_FAILED,
                error_message=f"{type(exc).__name__}: {exc}",
            )

        finally:
            with self._lock:
                if self._status != "CLOSED":
                    self._status = "INITIALIZED"
