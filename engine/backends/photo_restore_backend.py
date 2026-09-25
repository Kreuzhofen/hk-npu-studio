"""
HK NPU STUDIO - Phoenix Architecture
AI Photo Restore Backend

Production-ready NPU backend orchestrating NAFNet-DeBlur, DDColor, and RealESRGAN
exclusively on Qualcomm Snapdragon X NPU (HTP Execution Provider via QNN).
Zero CPU model inference fallback.
"""

from __future__ import annotations

import json
import math
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
from PIL import Image

import config
from engine.backends.backend_discovery_service import BackendDiscoveryService
from engine.file_utils import get_unique_filename
from modules.realesrgan_core import (
    TILE_SIZE as ESRGAN_TILE_SIZE,
    TILE_OVERLAP as ESRGAN_TILE_OVERLAP,
    SCALE as ESRGAN_SCALE,
    tile_positions,
    tile_overlaps,
    feather_mask,
    pad_tile,
)

# Structured Error Codes
PHOTO_RESTORE_RUNTIME_UNAVAILABLE = "PHOTO_RESTORE_RUNTIME_UNAVAILABLE"
PHOTO_RESTORE_NAFNET_MISSING = "PHOTO_RESTORE_NAFNET_MISSING"
PHOTO_RESTORE_DDCOLOR_MISSING = "PHOTO_RESTORE_DDCOLOR_MISSING"
PHOTO_RESTORE_QNN_HTP_UNAVAILABLE = "PHOTO_RESTORE_QNN_HTP_UNAVAILABLE"
PHOTO_RESTORE_INPUT_INVALID = "PHOTO_RESTORE_INPUT_INVALID"
PHOTO_RESTORE_NAFNET_FAILED = "PHOTO_RESTORE_NAFNET_FAILED"
PHOTO_RESTORE_DDCOLOR_FAILED = "PHOTO_RESTORE_DDCOLOR_FAILED"
PHOTO_RESTORE_UPSCALE_FAILED = "PHOTO_RESTORE_UPSCALE_FAILED"
PHOTO_RESTORE_CANCELLED = "PHOTO_RESTORE_CANCELLED"

HISTORICAL_ACCURACY_DISCLAIMER = (
    "Colors and reconstructed details are AI-estimated "
    "and may not represent historically accurate originals."
)


class PhotoRestoreError(Exception):
    """Structured runtime exception for AI Photo Restore operations."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(slots=True)
class PhotoRestoreResult:
    """Immutable result contract for an AI Photo Restore job."""

    success: bool
    output_path: str | None = None
    is_colorized: bool = False
    upscale_factor: int = 4
    generation_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None


def is_grayscale_image(img: Image.Image, threshold: float = 3.0) -> bool:
    """
    Detects whether an image is effectively grayscale.
    Handles both single-channel modes (L, 1, I, F) and RGB scans with near-identical
    color channels (mean absolute channel difference < threshold).
    """
    if img.mode in ("L", "1", "I", "F"):
        return True

    rgb = img.convert("RGB")
    # Fast evaluation on downsampled image if larger than 256x256
    max_dim = 256
    w, h = rgb.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        sample = rgb.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.BOX)
    else:
        sample = rgb

    arr = np.asarray(sample, dtype=np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    # Mean absolute difference between R, G, and B channels
    diff = (np.abs(r - g) + np.abs(g - b) + np.abs(b - r)) / 3.0
    return bool(float(np.mean(diff)) < threshold)


def rgb2lab_np(rgb: np.ndarray) -> np.ndarray:
    """Convert float32 RGB [0, 1] to CIE Lab [0..100, -128..127]."""
    mask = rgb > 0.04045
    rgb_lin = np.where(mask, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    m_matrix = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ], dtype=np.float32)
    xyz = np.dot(rgb_lin, m_matrix.T)
    xyz[..., 0] /= 0.95047
    xyz[..., 1] /= 1.00000
    xyz[..., 2] /= 1.08883
    delta = 6.0 / 29.0
    mask_xyz = xyz > (delta ** 3)
    f_xyz = np.where(mask_xyz, xyz ** (1.0 / 3.0), (xyz / (3.0 * delta ** 2)) + (4.0 / 29.0))
    l_chan = 116.0 * f_xyz[..., 1] - 16.0
    a_chan = 500.0 * (f_xyz[..., 0] - f_xyz[..., 1])
    b_chan = 200.0 * (f_xyz[..., 1] - f_xyz[..., 2])
    return np.stack([l_chan, a_chan, b_chan], axis=-1)


def lab2rgb_np(lab: np.ndarray) -> np.ndarray:
    """Convert CIE Lab [0..100, -128..127] to float32 RGB [0, 1]."""
    l_chan, a_chan, b_chan = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (l_chan + 16.0) / 116.0
    fx = fy + a_chan / 500.0
    fz = fy - b_chan / 200.0
    delta = 6.0 / 29.0
    fx_cube = fx ** 3
    fz_cube = fz ** 3
    x_chan = np.where(fx > delta, fx_cube, (fx - 16.0 / 116.0) * 3.0 * (delta ** 2)) * 0.95047
    y_chan = np.where(fy > delta, fy ** 3, (fy - 16.0 / 116.0) * 3.0 * (delta ** 2)) * 1.00000
    z_chan = np.where(fz > delta, fz_cube, (fz - 16.0 / 116.0) * 3.0 * (delta ** 2)) * 1.08883
    xyz = np.stack([x_chan, y_chan, z_chan], axis=-1)
    m_inv = np.array([
        [ 3.2404542, -1.5371385, -0.4985314],
        [-0.9692660,  1.8760108,  0.0415560],
        [ 0.0556434, -0.2040259,  1.0572252],
    ], dtype=np.float32)
    rgb_lin = np.dot(xyz, m_inv.T)
    rgb_lin = np.clip(rgb_lin, 0.0, 1.0)
    mask = rgb_lin > 0.0031308
    rgb = np.where(mask, 1.055 * (rgb_lin ** (1.0 / 2.4)) - 0.055, 12.92 * rgb_lin)
    return np.clip(rgb, 0.0, 1.0)


def resolve_photo_restore_models(
    nafnet_path: Path | str | None = None,
    ddcolor_path: Path | str | None = None,
    realesrgan_path: Path | str | None = None,
) -> tuple[Path, Path, Path]:
    """
    Resolves model paths following the Phoenix architecture standard:
    1. Explicit paths if provided (checked directly)
    2. Productive MODELS_DIR / photo_restore
    3. Development / temporary context directory fallback
    """
    if nafnet_path:
        resolved_nafnet = Path(nafnet_path)
    else:
        resolved_nafnet = config.PHOTO_RESTORE_NAFNET_DLC
        if not resolved_nafnet.is_file():
            dev_nafnet = config.PHOTO_RESTORE_DEV_CONTEXT_DIR / "nafnet_deblur.dlc.bin"
            if dev_nafnet.is_file():
                resolved_nafnet = dev_nafnet

    if ddcolor_path:
        resolved_ddcolor = Path(ddcolor_path)
    else:
        resolved_ddcolor = config.PHOTO_RESTORE_DDCOLOR_DLC
        if not resolved_ddcolor.is_file():
            dev_ddcolor = config.PHOTO_RESTORE_DEV_CONTEXT_DIR / "ddcolor.dlc.bin"
            if dev_ddcolor.is_file():
                resolved_ddcolor = dev_ddcolor

    resolved_realesrgan = Path(realesrgan_path) if realesrgan_path else config.REALESRGAN_MODEL
    return resolved_nafnet, resolved_ddcolor, resolved_realesrgan


class AIPhotoRestoreBackend:
    """
    Qualcomm Snapdragon X NPU Backend for AI Photo Restore.
    Guarantees zero CPU model inference fallback.
    Persistent lifecycle: INITIALIZED -> BUSY -> INITIALIZED / CLOSED.
    """

    def __init__(
        self,
        nafnet_path: Path | str | None = None,
        ddcolor_path: Path | str | None = None,
        realesrgan_path: Path | str | None = None,
        discovery_service: Any = None,
        nafnet_context: Any = None,
        ddcolor_context: Any = None,
        realesrgan_context: Any = None,
    ) -> None:
        self.nafnet_path, self.ddcolor_path, self.realesrgan_path = resolve_photo_restore_models(
            nafnet_path, ddcolor_path, realesrgan_path
        )
        self._discovery_service = discovery_service
        self.ctx_nafnet = nafnet_context
        self.ctx_ddcolor = ddcolor_context
        self.ctx_realesrgan = realesrgan_context

        self._status: str = "UNINITIALIZED"
        self._cancel_requested = threading.Event()
        self._lock = threading.RLock()

        # If mock contexts were injected (e.g. for unit tests), mark as initialized
        if self.ctx_nafnet is not None and self.ctx_ddcolor is not None and self.ctx_realesrgan is not None:
            self._status = "INITIALIZED"

    @property
    def status(self) -> str:
        return self._status

    def initialize(self) -> None:
        """
        Initializes the Qualcomm QNN HTP runtime and persistently loads
        NAFNet, DDColor, and RealESRGAN contexts into NPU memory.
        """
        with self._lock:
            if self._status == "CLOSED":
                raise PhotoRestoreError(
                    PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
                    "Cannot initialize a closed PhotoRestoreBackend instance.",
                )
            if self._status == "INITIALIZED":
                return

            # 1. Enforce Qualcomm QNN HTP Hardware Check
            discovery = self._discovery_service
            if discovery is None:
                discovery = BackendDiscoveryService.discover()
            if not getattr(discovery, "qnn_htp_backend_path", None) or not Path(discovery.qnn_htp_backend_path).is_file():
                raise PhotoRestoreError(
                    PHOTO_RESTORE_QNN_HTP_UNAVAILABLE,
                    "Qualcomm QNN HTP runtime (QnnHtp.dll) was not found. "
                    "AI Photo Restore requires local Snapdragon NPU acceleration.",
                )

            # 2. Check model artifacts
            if not self.nafnet_path.is_file():
                raise PhotoRestoreError(
                    PHOTO_RESTORE_NAFNET_MISSING,
                    f"NAFNet context binary not found at: {self.nafnet_path}",
                )
            if not self.ddcolor_path.is_file():
                raise PhotoRestoreError(
                    PHOTO_RESTORE_DDCOLOR_MISSING,
                    f"DDColor context binary not found at: {self.ddcolor_path}",
                )
            if not self.realesrgan_path.is_file():
                raise PhotoRestoreError(
                    PHOTO_RESTORE_UPSCALE_FAILED,
                    f"RealESRGAN model binary not found at: {self.realesrgan_path}",
                )

            # 3. Load QNN contexts via qai_appbuilder
            try:
                from qai_appbuilder import (
                    QNNConfig,
                    QNNContext,
                    Runtime,
                    LogLevel,
                    ProfilingLevel,
                )
            except ImportError as exc:
                raise PhotoRestoreError(
                    PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
                    f"qai_appbuilder is not available: {exc}",
                ) from exc

            try:
                QNNConfig.Config(Runtime.HTP, LogLevel.WARN, ProfilingLevel.BASIC, "")
                self.ctx_nafnet = QNNContext("nafnet_deblur", str(self.nafnet_path))
                self.ctx_ddcolor = QNNContext("ddcolor", str(self.ddcolor_path))
                self.ctx_realesrgan = QNNContext("realesrgan", str(self.realesrgan_path))
                self._status = "INITIALIZED"
            except Exception as exc:
                raise PhotoRestoreError(
                    PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
                    f"Failed to initialize QNN contexts on HTP: {exc}",
                ) from exc

    def cancel(self) -> None:
        """Requests cooperative cancellation of active restore operations."""
        self._cancel_requested.set()

    def close(self) -> None:
        """Releases all resident NPU context objects and marks backend as closed."""
        with self._lock:
            self.cancel()
            for ctx_name in ("ctx_nafnet", "ctx_ddcolor", "ctx_realesrgan"):
                ctx = getattr(self, ctx_name, None)
                if ctx is not None and hasattr(ctx, "release"):
                    try:
                        ctx.release()
                    except Exception:
                        pass
                setattr(self, ctx_name, None)
            self._status = "CLOSED"

    def _check_cancel(self) -> None:
        if self._cancel_requested.is_set():
            raise PhotoRestoreError(
                PHOTO_RESTORE_CANCELLED,
                "Photo restore operation was cancelled by the user.",
            )

    def restore(
        self,
        image_path: Path | str,
        output_dir: Path | str | None = None,
        upscale_factor: int = 4,
        auto_colorize: bool = False,
        progress_callback: Callable[[str, float, str | None], None] | None = None,
        mode: str = "legacy",
        **kwargs: Any,
    ) -> PhotoRestoreResult:
        """
        Executes the full AI Photo Restore pipeline:
        Stage 1: Prepare (input check, grayscale detection)
        Stage 2: Restore (NAFNet-DeBlur on NPU)
        Stage 3: Colorize (DDColor on NPU if grayscale and auto_colorize)
        Stage 4: Upscale (RealESRGAN 2x or 4x on NPU)
        Stage 5: Save (unique output PNG and JSON sidecar metadata)
        """
        progress = progress_callback or (lambda _phase, _pct, _detail: None)

        # 1. State validations
        with self._lock:
            if self._status == "CLOSED":
                return PhotoRestoreResult(
                    success=False,
                    error_code=PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
                    error_message="Backend is closed.",
                )
            if self._status == "BUSY":
                return PhotoRestoreResult(
                    success=False,
                    error_code=PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
                    error_message="Backend is currently processing another job.",
                )
            if self._status == "UNINITIALIZED":
                try:
                    self.initialize()
                except PhotoRestoreError as pre:
                    return PhotoRestoreResult(
                        success=False,
                        error_code=pre.code,
                        error_message=pre.message,
                    )
                except Exception as exc:
                    return PhotoRestoreResult(
                        success=False,
                        error_code=PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
                        error_message=str(exc),
                    )
            self._status = "BUSY"

        self._cancel_requested.clear()
        t_pipeline_start = time.perf_counter()
        t_nafnet = 0.0
        t_ddcolor = 0.0
        t_realesrgan = 0.0

        try:
            # ----------------------------------------------------
            # STAGE 1: PREPARE
            # ----------------------------------------------------
            progress("prepare", 0.02, "Foto wird analysiert...")
            self._check_cancel()

            in_path = Path(image_path)
            if not in_path.is_file():
                raise PhotoRestoreError(
                    PHOTO_RESTORE_INPUT_INVALID,
                    f"Input image file does not exist: {in_path}",
                )

            if upscale_factor not in (2, 4):
                raise PhotoRestoreError(
                    PHOTO_RESTORE_INPUT_INVALID,
                    f"Unsupported upscale factor: {upscale_factor}. Supported factors: 2, 4.",
                )

            try:
                orig_pil = Image.open(in_path)
                orig_pil.load()
            except Exception as exc:
                raise PhotoRestoreError(
                    PHOTO_RESTORE_INPUT_INVALID,
                    f"Failed to open input image: {exc}",
                ) from exc

            is_gray = is_grayscale_image(orig_pil)
            orig_rgb = orig_pil.convert("RGB")
            orig_w, orig_h = orig_rgb.size
            progress("prepare", 0.05, f"Eingabe: {orig_w}x{orig_h}, Schwarzweiss={is_gray}")
            self._check_cancel()

            # ----------------------------------------------------
            # STAGE 2: RESTORE (NAFNet-DeBlur on NPU)
            # ----------------------------------------------------
            progress("restore", 0.08, "NAFNet-Restaurierung auf NPU gestartet...")
            t0_naf = time.perf_counter()
            restored_pil = self._run_nafnet(orig_rgb, progress)
            t_nafnet = time.perf_counter() - t0_naf
            progress("restore", 0.35, f"Restaurierung abgeschlossen ({t_nafnet:.2f}s)")
            self._check_cancel()

            # ----------------------------------------------------
            # STAGE 3: COLORIZE (DDColor on NPU if needed)
            # ----------------------------------------------------
            is_colorized = False
            if is_gray and auto_colorize:
                progress("colorize", 0.38, "DDColor-Farbrekonstruktion auf NPU...")
                t0_dd = time.perf_counter()
                colorized_pil = self._run_ddcolor(restored_pil)
                t_ddcolor = time.perf_counter() - t0_dd
                is_colorized = True
                progress("colorize", 0.50, f"Kolorierung abgeschlossen ({t_ddcolor:.2f}s)")
            else:
                progress("colorize", 0.50, "Kolorierung uebersprungen (Original enthaelt Farbe)")
                colorized_pil = restored_pil
            self._check_cancel()

            # ----------------------------------------------------
            # STAGE 4: UPSCALE (RealESRGAN on NPU)
            # ----------------------------------------------------
            progress("upscale", 0.52, f"RealESRGAN {upscale_factor}x-Upscaling auf NPU...")
            t0_upscale = time.perf_counter()
            upscaled_pil = self._run_realesrgan(colorized_pil, upscale_factor, progress)
            t_realesrgan = time.perf_counter() - t0_upscale
            progress("upscale", 0.95, f"Upscaling abgeschlossen ({t_realesrgan:.2f}s)")
            self._check_cancel()

            # ----------------------------------------------------
            # STAGE 5: SAVE & METADATA
            # ----------------------------------------------------
            progress("save", 0.96, "Ergebnis wird gespeichert...")
            out_directory = Path(output_dir) if output_dir else config.OUTPUT_DIR
            out_directory.mkdir(parents=True, exist_ok=True)

            color_tag = "_color" if is_colorized else ""
            filename_candidate = f"{in_path.stem}_restored{color_tag}_x{upscale_factor}.png"
            final_output_path = get_unique_filename(out_directory, filename_candidate)

            upscaled_pil.save(final_output_path, format="PNG")

            t_pipeline_total = time.perf_counter() - t_pipeline_start
            final_w, final_h = upscaled_pil.size

            meta = {
                "feature": "AI Photo Restore",
                "restore_model": "NAFNet-DeBlur",
                "colorization_model": "DDColor" if is_colorized else "skipped",
                "upscaler": "RealESRGAN",
                "upscale_factor": upscale_factor,
                "runtime": "QNN/HTP",
                "cpu_model_inference": False,
                "input_path": str(in_path),
                "output_path": str(final_output_path),
                "input_size": [orig_w, orig_h],
                "output_size": [final_w, final_h],
                "aspect_ratio_preserved": True,
                "total_seconds": round(t_pipeline_total, 4),
                "nafnet_seconds": round(t_nafnet, 4),
                "ddcolor_seconds": round(t_ddcolor, 4),
                "realesrgan_seconds": round(t_realesrgan, 4),
                "disclaimer": HISTORICAL_ACCURACY_DISCLAIMER,
            }

            sidecar_path = final_output_path.with_suffix(".json")
            try:
                sidecar_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            except Exception:
                pass

            progress("save", 1.0, "Fertiggestellt")
            return PhotoRestoreResult(
                success=True,
                output_path=str(final_output_path),
                is_colorized=is_colorized,
                upscale_factor=upscale_factor,
                generation_time=t_pipeline_total,
                metadata=meta,
            )

        except PhotoRestoreError as pre:
            return PhotoRestoreResult(
                success=False,
                error_code=pre.code,
                error_message=pre.message,
            )
        except Exception as exc:
            return PhotoRestoreResult(
                success=False,
                error_code=PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
                error_message=f"{type(exc).__name__}: {exc}",
            )
        finally:
            with self._lock:
                if self._status != "CLOSED":
                    self._status = "INITIALIZED"

    # --------------------------------------------------------
    # NPU Inference Implementations
    # --------------------------------------------------------

    def _run_nafnet(
        self,
        img: Image.Image,
        progress: Callable[[str, float, str | None], None],
    ) -> Image.Image:
        from qai_appbuilder import PerfProfile

        orig_w, orig_h = img.size
        tile_w, tile_h = 640, 360
        overlap = 64

        # If smaller than native tile, pad with edge replication
        pad_w = max(0, tile_w - orig_w)
        pad_h = max(0, tile_h - orig_h)
        arr_orig = np.array(img, dtype=np.float32) / 255.0

        if pad_w > 0 or pad_h > 0:
            arr_padded = np.pad(arr_orig, ((0, pad_h), (0, pad_w), (0, 0)), mode="edge")
            tile = arr_padded[:tile_h, :tile_w, :][np.newaxis, ...]
            self._check_cancel()
            try:
                out = self.ctx_nafnet.Inference([tile], perf_profile=PerfProfile.BURST)
            except Exception as exc:
                raise PhotoRestoreError(
                    PHOTO_RESTORE_NAFNET_FAILED, f"NAFNet inference failed: {exc}"
                ) from exc
            tile_out = out[0][0][:orig_h, :orig_w, :]
            clipped = np.clip(tile_out, 0.0, 1.0)
            return Image.fromarray((clipped * 255.0).round().astype(np.uint8))

        def get_coords(length: int, t_len: int, ov: int) -> list[int]:
            stride = t_len - ov
            cnt = math.ceil((length - t_len) / stride) + 1
            coords = []
            for i in range(cnt):
                pos = min(i * stride, length - t_len)
                if pos not in coords:
                    coords.append(pos)
            return coords

        x_coords = get_coords(orig_w, tile_w, overlap)
        y_coords = get_coords(orig_h, tile_h, overlap)
        total_tiles = len(x_coords) * len(y_coords)

        # Build feather weight map
        y_w = np.ones(tile_h, dtype=np.float32)
        x_w = np.ones(tile_w, dtype=np.float32)
        fade_len = overlap // 2
        fade = np.linspace(0, 1, fade_len, dtype=np.float32)
        y_w[:fade_len] = fade
        y_w[-fade_len:] = fade[::-1]
        x_w[:fade_len] = fade
        x_w[-fade_len:] = fade[::-1]
        w_map = np.outer(y_w, x_w)[:, :, np.newaxis]

        out_acc = np.zeros((orig_h, orig_w, 3), dtype=np.float32)
        weight_acc = np.zeros((orig_h, orig_w, 1), dtype=np.float32)

        tile_idx = 0
        for yp in y_coords:
            for xp in x_coords:
                self._check_cancel()
                tile_idx += 1
                pct = 0.08 + (0.27 * (tile_idx / total_tiles))
                progress("restore", pct, f"NAFNet Kachel {tile_idx}/{total_tiles}")

                tile = arr_orig[yp:yp+tile_h, xp:xp+tile_w, :][np.newaxis, ...]
                try:
                    out = self.ctx_nafnet.Inference([tile], perf_profile=PerfProfile.BURST)
                except Exception as exc:
                    raise PhotoRestoreError(
                        PHOTO_RESTORE_NAFNET_FAILED, f"NAFNet inference failed: {exc}"
                    ) from exc

                tile_out = out[0][0]
                out_acc[yp:yp+tile_h, xp:xp+tile_w, :] += tile_out * w_map
                weight_acc[yp:yp+tile_h, xp:xp+tile_w, :] += w_map

        res_arr = np.clip(out_acc / (weight_acc + 1e-6), 0.0, 1.0)
        return Image.fromarray((res_arr * 255.0).round().astype(np.uint8))

    def _run_ddcolor(self, img: Image.Image) -> Image.Image:
        from qai_appbuilder import PerfProfile

        orig_w, orig_h = img.size
        img_np = np.array(img, dtype=np.float32) / 255.0
        orig_lab = rgb2lab_np(img_np)
        orig_l = orig_lab[..., :1]

        pil_resized = img.resize((256, 256), Image.Resampling.BILINEAR)
        resized_np = np.array(pil_resized, dtype=np.float32) / 255.0
        resized_lab = rgb2lab_np(resized_np)
        resized_l = resized_lab[..., :1]

        gray_lab = np.concatenate([resized_l, np.zeros_like(resized_l), np.zeros_like(resized_l)], axis=-1)
        gray_rgb = lab2rgb_np(gray_lab)[np.newaxis, ...].astype(np.float32)

        self._check_cancel()
        try:
            out = self.ctx_ddcolor.Inference([gray_rgb], perf_profile=PerfProfile.BURST)
        except Exception as exc:
            raise PhotoRestoreError(
                PHOTO_RESTORE_DDCOLOR_FAILED, f"DDColor inference failed: {exc}"
            ) from exc

        out_ab = out[0]  # Shape (1, 2, 256, 256)
        # Fast high-precision bilinear upsampling of chrominance channels to original dimensions
        a_low = out_ab[0, 0, :, :].astype(np.float32)
        b_low = out_ab[0, 1, :, :].astype(np.float32)

        a_pil = Image.fromarray(a_low, mode="F").resize((orig_w, orig_h), Image.Resampling.BILINEAR)
        b_pil = Image.fromarray(b_low, mode="F").resize((orig_w, orig_h), Image.Resampling.BILINEAR)

        a_up = np.asarray(a_pil, dtype=np.float32)[..., np.newaxis]
        b_up = np.asarray(b_pil, dtype=np.float32)[..., np.newaxis]

        out_lab = np.concatenate([orig_l, a_up, b_up], axis=-1)
        out_rgb = lab2rgb_np(out_lab)
        return Image.fromarray((out_rgb * 255.0).round().astype(np.uint8))

    def _run_realesrgan(
        self,
        img: Image.Image,
        upscale_factor: int,
        progress: Callable[[str, float, str | None], None],
    ) -> Image.Image:
        from qai_appbuilder import PerfProfile

        orig_w, orig_h = img.size
        # The QNN RealESRGAN model operates at fixed 4x scale
        full_4x_w = orig_w * ESRGAN_SCALE
        full_4x_h = orig_h * ESRGAN_SCALE

        x_positions = tile_positions(orig_w, ESRGAN_TILE_SIZE, ESRGAN_TILE_OVERLAP)
        y_positions = tile_positions(orig_h, ESRGAN_TILE_SIZE, ESRGAN_TILE_OVERLAP)
        tiles_x = len(x_positions)
        tiles_y = len(y_positions)
        total_tiles = tiles_x * tiles_y

        canvas = Image.new("RGB", (full_4x_w, full_4x_h))
        tile_idx = 0

        for ty in range(tiles_y):
            for tx in range(tiles_x):
                self._check_cancel()
                tile_idx += 1
                pct = 0.52 + (0.42 * (tile_idx / total_tiles))
                progress("upscale", pct, f"RealESRGAN Kachel {tile_idx}/{total_tiles}")

                left = x_positions[tx]
                top = y_positions[ty]
                right = min(left + ESRGAN_TILE_SIZE, orig_w)
                bottom = min(top + ESRGAN_TILE_SIZE, orig_h)

                tile_crop = img.crop((left, top, right, bottom))
                padded_tile, tw, th = pad_tile(tile_crop)
                left_ov, right_ov, top_ov, bottom_ov = tile_overlaps(
                    x_positions, y_positions, tx, ty, tw, th
                )

                tile_arr = (np.asarray(padded_tile).astype(np.float32) / 255.0).reshape(
                    1, ESRGAN_TILE_SIZE, ESRGAN_TILE_SIZE, 3
                )
                try:
                    out = self.ctx_realesrgan.Inference([tile_arr], perf_profile=PerfProfile.BURST)
                except Exception as exc:
                    raise PhotoRestoreError(
                        PHOTO_RESTORE_UPSCALE_FAILED, f"RealESRGAN inference failed: {exc}"
                    ) from exc

                out_tile_arr = out[0][0]
                out_tile_uint8 = np.clip(out_tile_arr * 255.0, 0, 255).astype(np.uint8)
                upscaled_tile = Image.fromarray(out_tile_uint8).crop(
                    (0, 0, tw * ESRGAN_SCALE, th * ESRGAN_SCALE)
                )

                mask = feather_mask(
                    upscaled_tile.width,
                    upscaled_tile.height,
                    left_ov * ESRGAN_SCALE,
                    top_ov * ESRGAN_SCALE,
                )
                dest = (left * ESRGAN_SCALE, top * ESRGAN_SCALE)
                existing = canvas.crop((
                    dest[0], dest[1],
                    dest[0] + upscaled_tile.width, dest[1] + upscaled_tile.height,
                ))
                canvas.paste(Image.composite(upscaled_tile, existing, mask), dest)

        if upscale_factor == 2:
            # High quality Lanczos downsample to exact 2x dimensions
            target_2x_w = orig_w * 2
            target_2x_h = orig_h * 2
            return canvas.resize((target_2x_w, target_2x_h), Image.Resampling.LANCZOS)
        return canvas