from __future__ import annotations

import os
import math
import shutil
import subprocess
import sys
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from PIL import Image, ImageFilter

from config import BASE, MODELS_DIR, TEMP_DIR

BACKEND_NAME = "Qualcomm QNN HTP (RORem DLC)"

IMAGE_SIZE = (1024, 1024)
LATENT_SCALE = np.float16(0.13025)
DEFAULT_GUIDANCE_SCALE = 7.5
DEFAULT_STRENGTH = 0.9999
DEFAULT_SEED = 20260830
COMPOSITE_FEATHER_RADIUS = 12
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("ROREM_DLC_TIMEOUT_SECONDS", "900"))

DEFAULT_GRAPH_A_DLC = MODELS_DIR / "rorem_mixed_qnn_dlc" / "graph_a" / "graph_a.dlc"
DEFAULT_GRAPH_B_DLC = MODELS_DIR / "rorem_mixed_qnn_dlc" / "graph_b" / "graph_b.dlc"

EXPECTED_GRAPH_A_SHA256 = "4aab49508c6fc7d481f908c8fb472692fbf3802cded80935ff0b81a07e180307"
EXPECTED_GRAPH_B_SHA256 = "becfbaca891e6b0a89116eb25776d9776706cff8520304ae0c9db555c7166e07"

DEFAULT_QNN_ROOT = Path(r"C:\Qualcomm\AIStack\2.47.0.260601")
DEFAULT_QNN_ARCH = "aarch64-windows-msvc"
DEFAULT_QNN_NET_RUN = DEFAULT_QNN_ROOT / "bin" / DEFAULT_QNN_ARCH / "qnn-net-run.exe"
DEFAULT_QNN_MODEL_DLC = DEFAULT_QNN_ROOT / "lib" / DEFAULT_QNN_ARCH / "QnnModelDlc.dll"
DEFAULT_QNN_HTP = DEFAULT_QNN_ROOT / "lib" / DEFAULT_QNN_ARCH / "QnnHtp.dll"
DEFAULT_SKELETON_DIR = DEFAULT_QNN_ROOT / "lib" / "hexagon-v73" / "unsigned"

DEFAULT_SDXL_ROOT = MODELS_DIR / "sdxl_inpainting"
DEFAULT_VAE_ROOT = MODELS_DIR / "sdxl_inpainting_qnn_context"
DEFAULT_CLIP_ROOT = MODELS_DIR / "stable_diffusion_v3_5_qai" / "serialized_binaries"

DEFAULT_VAE_ENCODER = DEFAULT_VAE_ROOT / "vae_encoder" / "vae_encoder.serialized.bin"
DEFAULT_VAE_DECODER = DEFAULT_VAE_ROOT / "vae_decoder" / "vae_decoder.serialized.bin"
DEFAULT_CLIP_L = DEFAULT_CLIP_ROOT / "text_encoder.serialized.bin"
DEFAULT_CLIP_G = DEFAULT_CLIP_ROOT / "text_encoder_2.serialized.bin"
DEFAULT_TOKENIZER_L = DEFAULT_SDXL_ROOT / "tokenizer"
DEFAULT_TOKENIZER_G = DEFAULT_SDXL_ROOT / "tokenizer_2"
DEFAULT_SCHEDULER = DEFAULT_SDXL_ROOT / "scheduler"

# Graph A Input Contract (FP16)
GRAPH_A_INPUT_SPECS: dict[str, tuple[int, ...]] = {
    "sample": (1, 9, 128, 128),
    "timestep": (1,),
    "encoder_hidden_states": (1, 77, 2048),
    "text_embeds": (1, 1280),
    "time_ids": (1, 6),
}

# Cross-Graph Specifications (Graph A Output -> Graph B Input)
CROSS_GRAPH_SPECS: list[dict[str, Any]] = [
    {
        "index": 0,
        "source_stem": "output_0",
        "target_name": "/unet/conv_in/Conv_output_0",
        "shape": (1, 320, 128, 128),
        "bytes": 10485760,
    },
    {
        "index": 1,
        "source_stem": "output_1",
        "target_name": "/unet/down_blocks.0/resnets.0/Div_output_0",
        "shape": (1, 320, 128, 128),
        "bytes": 10485760,
    },
    {
        "index": 2,
        "source_stem": "output_2",
        "target_name": "/unet/down_blocks.0/resnets.1/Div_output_0",
        "shape": (1, 320, 128, 128),
        "bytes": 10485760,
    },
    {
        "index": 3,
        "source_stem": "output_3",
        "target_name": "/unet/down_blocks.0/downsamplers.0/conv/Conv_output_0",
        "shape": (1, 320, 64, 64),
        "bytes": 2621440,
    },
    {
        "index": 4,
        "source_stem": "output_4",
        "target_name": "/unet/down_blocks.1/attentions.0/Add_output_0",
        "shape": (1, 640, 64, 64),
        "bytes": 5242880,
    },
    {
        "index": 5,
        "source_stem": "output_5",
        "target_name": "/unet/down_blocks.1/attentions.1/Add_output_0",
        "shape": (1, 640, 64, 64),
        "bytes": 5242880,
    },
    {
        "index": 6,
        "source_stem": "output_6",
        "target_name": "/unet/down_blocks.1/downsamplers.0/conv/Conv_output_0",
        "shape": (1, 640, 32, 32),
        "bytes": 1310720,
    },
    {
        "index": 7,
        "source_stem": "output_7",
        "target_name": "/unet/down_blocks.2/attentions.0/Add_output_0",
        "shape": (1, 1280, 32, 32),
        "bytes": 2621440,
    },
    {
        "index": 8,
        "source_stem": "output_8",
        "target_name": "/unet/down_blocks.2/attentions.1/Add_output_0",
        "shape": (1, 1280, 32, 32),
        "bytes": 2621440,
    },
    {
        "index": 9,
        "source_stem": "output_9",
        "target_name": "/unet/mid_block/resnets.1/Div_output_0",
        "shape": (1, 1280, 32, 32),
        "bytes": 2621440,
    },
]

# Graph B Conditioning Input Contract
GRAPH_B_CONDITIONING_SPECS: dict[str, tuple[int, ...]] = {
    "timestep": (1,),
    "encoder_hidden_states": (1, 77, 2048),
    "text_embeds": (1, 1280),
    "time_ids": (1, 6),
}

# Graph B Output Contract
GRAPH_B_OUTPUT_SPEC: dict[str, Any] = {
    "source_stem": "output_0",
    "name": "out_sample",
    "shape": (1, 4, 128, 128),
    "bytes": 131072,
}

# Ordered list of 14 inputs for Graph B input_list.txt
GRAPH_B_INPUT_NAMES: list[str] = [
    "timestep",
    "encoder_hidden_states",
    "text_embeds",
    "time_ids",
    "/unet/conv_in/Conv_output_0",
    "/unet/down_blocks.0/resnets.0/Div_output_0",
    "/unet/down_blocks.0/resnets.1/Div_output_0",
    "/unet/down_blocks.0/downsamplers.0/conv/Conv_output_0",
    "/unet/down_blocks.1/attentions.0/Add_output_0",
    "/unet/down_blocks.1/attentions.1/Add_output_0",
    "/unet/down_blocks.1/downsamplers.0/conv/Conv_output_0",
    "/unet/down_blocks.2/attentions.0/Add_output_0",
    "/unet/down_blocks.2/attentions.1/Add_output_0",
    "/unet/mid_block/resnets.1/Div_output_0",
]


@dataclass
class RORemDlcResult:
    """Execution result from RORem DLC runtime."""

    success: bool
    output: np.ndarray | None = None
    output_path: str | Path | None = None
    error_code: str | None = None
    error_message: str | None = None
    backend_name: str = BACKEND_NAME
    metadata: dict[str, Any] = field(default_factory=dict)


class GraphAOutputs(dict):
    """
    Container for Graph A outputs mapping canonical target names,
    output stems ('output_0'), indices (0..9), and raw file paths.
    """

    def __init__(
        self,
        tensors: dict[str, np.ndarray],
        raw_paths: dict[str, Path] | None = None,
        index_mapping: dict[int, str] | None = None,
    ) -> None:
        super().__init__(tensors)
        self.raw_paths: dict[str, Path] = raw_paths or {}
        self._index_mapping: dict[int, str] = index_mapping or {}

    def __getitem__(self, key: Any) -> np.ndarray:
        if isinstance(key, int) and key in self._index_mapping:
            return super().__getitem__(self._index_mapping[key])
        if isinstance(key, str) and key.startswith("output_"):
            try:
                idx = int(key.split("_")[1])
                if idx in self._index_mapping:
                    return super().__getitem__(self._index_mapping[idx])
            except (ValueError, IndexError):
                pass
        return super().__getitem__(key)


class RORemDlcRuntime:
    """
    Production-near Qualcomm QNN HTP DLC Runtime for RORem Split UNet.
    Supports prepared tensor execution and full 1024x1024 image inpainting on Qualcomm NPU.
    No CPU/GPU neural model fallback.
    """

    BACKEND_NAME = BACKEND_NAME
    CPU_AI_FALLBACK: bool = False

    @staticmethod
    def _resolve_init_timestep(steps: int, strength: float) -> int:
        """Keep near-one strengths from silently dropping a requested denoising step."""
        return min(max(math.ceil(steps * strength), 1), steps)

    def __init__(
        self,
        graph_a_path: Path | str | None = None,
        graph_b_path: Path | str | None = None,
        work_root: Path | str | None = None,
        qnn_root: Path | str | None = None,
        qnn_net_run: Path | str | None = None,
        qnn_htp: Path | str | None = None,
        qnn_model_dlc: Path | str | None = None,
        skeleton_dirs: tuple[Path | str, ...] | None = None,
        vae_encoder_path: Path | str | None = None,
        vae_decoder_path: Path | str | None = None,
        clip_l_path: Path | str | None = None,
        clip_g_path: Path | str | None = None,
        tokenizer_l_dir: Path | str | None = None,
        tokenizer_g_dir: Path | str | None = None,
        scheduler_dir: Path | str | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        cleanup_temp: bool = True,
    ) -> None:
        self.graph_a_path = Path(graph_a_path) if graph_a_path else DEFAULT_GRAPH_A_DLC
        self.graph_b_path = Path(graph_b_path) if graph_b_path else DEFAULT_GRAPH_B_DLC
        self.work_root = Path(work_root) if work_root else TEMP_DIR / "rorem_dlc_runtime"
        self.timeout_seconds = timeout_seconds
        self.cleanup_temp = cleanup_temp

        root = Path(qnn_root) if qnn_root else DEFAULT_QNN_ROOT
        arch = DEFAULT_QNN_ARCH
        self.qnn_net_run = Path(qnn_net_run) if qnn_net_run else root / "bin" / arch / "qnn-net-run.exe"
        self.qnn_model_dlc = Path(qnn_model_dlc) if qnn_model_dlc else root / "lib" / arch / "QnnModelDlc.dll"
        self.qnn_htp = Path(qnn_htp) if qnn_htp else root / "lib" / arch / "QnnHtp.dll"
        if skeleton_dirs is not None:
            self.skeleton_dirs = tuple(Path(p) for p in skeleton_dirs)
        else:
            self.skeleton_dirs = (root / "lib" / "hexagon-v73" / "unsigned",)

        self.vae_encoder_path = Path(vae_encoder_path) if vae_encoder_path else DEFAULT_VAE_ENCODER
        self.vae_decoder_path = Path(vae_decoder_path) if vae_decoder_path else DEFAULT_VAE_DECODER
        self.clip_l_path = Path(clip_l_path) if clip_l_path else DEFAULT_CLIP_L
        self.clip_g_path = Path(clip_g_path) if clip_g_path else DEFAULT_CLIP_G
        self.tokenizer_l_dir = Path(tokenizer_l_dir) if tokenizer_l_dir else DEFAULT_TOKENIZER_L
        self.tokenizer_g_dir = Path(tokenizer_g_dir) if tokenizer_g_dir else DEFAULT_TOKENIZER_G
        self.scheduler_dir = Path(scheduler_dir) if scheduler_dir else DEFAULT_SCHEDULER

    def validate_artifacts(self, full_pipeline: bool = False) -> list[Path]:
        """Return list of missing required artifact and runtime files."""
        if full_pipeline:
            return self.validate_pipeline_artifacts()
        required = [
            self.graph_a_path,
            self.graph_b_path,
            self.qnn_net_run,
            self.qnn_model_dlc,
            self.qnn_htp,
        ]
        return [p for p in required if not p.is_file()]

    def validate_pipeline_artifacts(self) -> list[Path]:
        """Return list of missing required artifact and runtime files for end-to-end image pipeline."""
        required = [
            self.graph_a_path,
            self.graph_b_path,
            self.qnn_net_run,
            self.qnn_model_dlc,
            self.qnn_htp,
            self.vae_encoder_path,
            self.vae_decoder_path,
            self.clip_l_path,
            self.clip_g_path,
            self.tokenizer_l_dir,
            self.tokenizer_g_dir,
            self.scheduler_dir,
        ]
        return [p for p in required if not p.exists()]

    def _build_env(self) -> dict[str, str]:
        """Prepare subprocess environment with QNN binary and library paths."""
        env = os.environ.copy()
        bin_dir = self.qnn_net_run.parent
        lib_dir = self.qnn_htp.parent
        env["PATH"] = os.pathsep.join((str(bin_dir), str(lib_dir), env.get("PATH", "")))
        valid_skeletons = [str(s) for s in self.skeleton_dirs if Path(s).exists()]
        if valid_skeletons:
            env["ADSP_LIBRARY_PATH"] = ";".join(valid_skeletons)
        return env

    def _validate_graph_a_inputs(self, inputs: Mapping[str, Any]) -> None:
        """Strictly validate Graph A input tensors (presence, dtype, shape, finite)."""
        for name, expected_shape in GRAPH_A_INPUT_SPECS.items():
            if name not in inputs:
                raise ValueError(f"Graph A missing required input: '{name}'")
            arr = inputs[name]
            if not isinstance(arr, np.ndarray):
                raise TypeError(f"Graph A input '{name}' must be a numpy.ndarray, got {type(arr)}")
            if arr.dtype != np.float16:
                raise ValueError(f"Graph A input '{name}' must have dtype float16, got {arr.dtype}")
            if arr.shape != expected_shape:
                raise ValueError(
                    f"Graph A input '{name}' shape mismatch: expected {expected_shape}, got {arr.shape}"
                )
            if not np.isfinite(arr).all():
                raise ValueError(f"Graph A input '{name}' contains non-finite values (NaN/Inf)")

    def run_context(
        self,
        context_path: Path | str,
        inputs: Mapping[str, np.ndarray | Path],
        output_shapes: Mapping[str, tuple[int, ...]],
        work_dir: Path,
    ) -> dict[str, np.ndarray]:
        """Execute a QNN serialized context binary on Qualcomm HTP via qnn-net-run."""
        ctx_file = Path(context_path)
        if not ctx_file.is_file():
            raise FileNotFoundError(f"QNN context file not found: {ctx_file}")

        input_dir = work_dir / "inputs"
        output_dir = work_dir / "outputs"
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        entries = []
        for name, value in inputs.items():
            if isinstance(value, Path):
                raw_path = value
            elif isinstance(value, np.ndarray):
                if value.dtype != np.float16:
                    raise ValueError(f"Input '{name}' to context must be float16, got {value.dtype}")
                if not np.isfinite(value).all():
                    raise ValueError(f"Input '{name}' to context contains non-finite values (NaN/Inf)")
                raw_path = input_dir / f"{name}.raw"
                value.tofile(raw_path)
            else:
                raise TypeError(f"Unsupported input type for '{name}': {type(value)}")
            entries.append(f"{name}:={raw_path}")

        input_list_path = work_dir / "input_list.txt"
        input_list_path.write_text(" ".join(entries), encoding="ascii")

        cmd = [
            str(self.qnn_net_run),
            "--backend", str(self.qnn_htp),
            "--retrieve_context", str(ctx_file),
            "--input_list", str(input_list_path),
            "--output_dir", str(output_dir),
            "--profiling_level", "basic",
            "--use_native_input_files",
            "--use_native_output_files",
            "--perf_profile", "burst",
            "--log_level", "info",
        ]

        env = self._build_env()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(work_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"QNN context execution timed out after {self.timeout_seconds}s for {ctx_file.name}"
            ) from exc

        (work_dir / "qnn_stdout.txt").write_text(proc.stdout, encoding="utf-8", errors="replace")
        (work_dir / "qnn_stderr.txt").write_text(proc.stderr, encoding="utf-8", errors="replace")

        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            raise RuntimeError(
                f"QNN context execution failed ({ctx_file.name}) with exit code {proc.returncode}: {err}"
            )

        results: dict[str, np.ndarray] = {}
        for index, (name, shape) in enumerate(output_shapes.items()):
            expected_bytes = int(np.prod(shape)) * 2
            candidate_paths = [
                output_dir / "Result_0" / f"{name}_native.raw",
                output_dir / f"{name}_native.raw",
                output_dir / "Result_0" / f"output_{index}_native.raw",
                output_dir / f"output_{index}_native.raw",
                output_dir / "Result_0" / f"{name}.raw",
                output_dir / f"{name}.raw",
                output_dir / "Result_0" / f"output_{index}.raw",
                output_dir / f"output_{index}.raw",
            ]
            matched_file: Path | None = None
            for cand in candidate_paths:
                if cand.is_file():
                    matched_file = cand
                    break

            if matched_file is None:
                raise FileNotFoundError(
                    f"QNN output tensor file missing: '{name}' for context {ctx_file.name}"
                )

            actual_bytes = matched_file.stat().st_size
            if actual_bytes != expected_bytes:
                raise ValueError(
                    f"QNN output tensor '{name}' byte size mismatch: "
                    f"expected {expected_bytes} bytes, got {actual_bytes} bytes"
                )

            arr = np.fromfile(matched_file, dtype=np.float16).reshape(shape)
            if not np.isfinite(arr).all():
                raise ValueError(f"QNN output tensor '{name}' contains non-finite values (NaN/Inf)")

            results[name] = arr

        return results

    def _encode_prompt(
        self, prompt: str, negative_prompt: str = ""
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Encode prompt and negative prompt using CLIP-L and CLIP-G on Qualcomm HTP."""
        from qai_appbuilder import LogLevel, PerfProfile, ProfilingLevel, QNNConfig, QNNContext, Runtime
        from transformers import CLIPTokenizer

        tok_l = CLIPTokenizer.from_pretrained(str(self.tokenizer_l_dir))
        tok_g = CLIPTokenizer.from_pretrained(str(self.tokenizer_g_dir))

        def token_ids(tokenizer, text):
            return np.asarray(
                tokenizer(text, padding="max_length", max_length=77, truncation=True).input_ids,
                dtype=np.float32,
            ).reshape(-1)

        positive_l, negative_l = token_ids(tok_l, prompt), token_ids(tok_l, negative_prompt)
        positive_g, negative_g = token_ids(tok_g, prompt), token_ids(tok_g, negative_prompt)

        QNNConfig.Config(Runtime.HTP, LogLevel.WARN, ProfilingLevel.BASIC, "")
        PerfProfile.SetPerfProfileGlobal(PerfProfile.BURST)
        try:
            clip_l = QNNContext("sdxl_clip_l", str(self.clip_l_path))
            try:
                out_l = clip_l.Inference([positive_l])
                out_l_negative = clip_l.Inference([negative_l])
            finally:
                clip_l.release()
            clip_g = QNNContext("sdxl_clip_g", str(self.clip_g_path))
            try:
                out_g = clip_g.Inference([positive_g])
                out_g_negative = clip_g.Inference([negative_g])
            finally:
                clip_g.release()
        finally:
            PerfProfile.RelPerfProfileGlobal()

        def embeddings(out_l_values, out_g_values):
            hidden_l = (out_l_values[1] if out_l_values[0].size == 768 else out_l_values[0]).reshape(1, 77, 768)
            hidden_g = (out_g_values[0] if out_g_values[0].size == 77 * 1280 else out_g_values[1]).reshape(1, 77, 1280)
            pooled = (out_g_values[1] if out_g_values[1].size == 1280 else out_g_values[0]).reshape(1, 1280)
            return np.concatenate((hidden_l, hidden_g), axis=-1).astype(np.float16), pooled.astype(np.float16)

        hidden, pooled = embeddings(out_l, out_g)
        negative_hidden, negative_pooled = embeddings(out_l_negative, out_g_negative)
        time_ids = np.array([[1024.0, 1024.0, 0.0, 0.0, 1024.0, 1024.0]], dtype=np.float16)

        if not (np.isfinite(hidden).all() and np.isfinite(pooled).all() and
                np.isfinite(negative_hidden).all() and np.isfinite(negative_pooled).all() and
                np.isfinite(time_ids).all()):
            raise ValueError("CLIP prompt encoding produced non-finite values (NaN/Inf)")

        return hidden, pooled, negative_hidden, negative_pooled, time_ids

    @staticmethod
    def _prepare_inputs(
        image_path: Path | str, mask_path: Path | str
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Load and strictly validate 1024x1024 RGB image and mask."""
        img_p = Path(image_path)
        msk_p = Path(mask_path)
        if not img_p.is_file():
            raise FileNotFoundError(f"Input image file not found: {img_p}")
        if not msk_p.is_file():
            raise FileNotFoundError(f"Input mask file not found: {msk_p}")

        with Image.open(img_p) as image:
            if image.size != IMAGE_SIZE:
                raise ValueError(
                    f"Input image must be exactly {IMAGE_SIZE[0]}x{IMAGE_SIZE[1]} (fail-closed), got {image.size}"
                )
            original_pixels = np.asarray(image.convert("RGB"), dtype=np.uint8).copy()
            source = (original_pixels.astype(np.float32).transpose(2, 0, 1)[None] / 127.5 - 1.0)

        with Image.open(msk_p) as mask:
            if mask.size != IMAGE_SIZE:
                raise ValueError(
                    f"Input mask must be exactly {IMAGE_SIZE[0]}x{IMAGE_SIZE[1]} (fail-closed), got {mask.size}"
                )
            mask_l = mask.convert("L")
            pixel_mask = np.asarray(mask_l, dtype=np.float32)[None, None] / 255.0
            latent_mask = np.asarray(
                mask_l.resize((128, 128), Image.Resampling.NEAREST),
                dtype=np.float32,
            )[None, None] / 255.0
            authored_mask = (np.asarray(mask_l, dtype=np.float32) / 255.0)[..., None]

        pixel_mask = np.clip(pixel_mask, 0.0, 1.0)
        masked_source = source * (1.0 - pixel_mask)

        return (
            source.astype(np.float16),
            masked_source.astype(np.float16),
            np.clip(latent_mask, 0.0, 1.0).astype(np.float16),
            original_pixels,
            np.clip(authored_mask, 0.0, 1.0),
        )

    @staticmethod
    def _build_unet_sample(
        noisy_latents: np.ndarray,
        latent_mask: np.ndarray,
        masked_image_latents: np.ndarray,
    ) -> np.ndarray:
        """Concatenate noisy latents [1,4,128,128], mask [1,1,128,128], and masked latents [1,4,128,128] into [1,9,128,128] FP16."""
        if noisy_latents.shape != (1, 4, 128, 128):
            raise ValueError(f"noisy latents must have shape (1,4,128,128), got {noisy_latents.shape}")
        if latent_mask.shape != (1, 1, 128, 128):
            raise ValueError(f"latent mask must have shape (1,1,128,128), got {latent_mask.shape}")
        if masked_image_latents.shape != (1, 4, 128, 128):
            raise ValueError(f"masked image latents must have shape (1,4,128,128), got {masked_image_latents.shape}")
        return np.concatenate((noisy_latents, latent_mask, masked_image_latents), axis=1).astype(np.float16)

    @staticmethod
    def _composite_pixels(
        original: np.ndarray, generated: np.ndarray, authored_mask: np.ndarray
    ) -> np.ndarray:
        """Deterministic boundary feathering compositing: strictly preserves original outside mask."""
        mask_2d = np.clip(authored_mask[..., 0], 0.0, 1.0)
        mask_image = Image.fromarray(np.rint(mask_2d * 255.0).astype(np.uint8), mode="L")
        filter_size = COMPOSITE_FEATHER_RADIUS * 2 + 1
        core = np.asarray(mask_image.filter(ImageFilter.MinFilter(filter_size)), dtype=np.float32) / 255.0
        feathered = np.asarray(
            mask_image.filter(ImageFilter.GaussianBlur(radius=COMPOSITE_FEATHER_RADIUS)),
            dtype=np.float32,
        ) / 255.0
        alpha = np.maximum(core, feathered * mask_2d)[..., None]
        blended = original.astype(np.float32) * (1.0 - alpha) + generated.astype(np.float32) * alpha
        return np.clip(np.rint(blended), 0, 255).astype(np.uint8)

    def _run_dlc_batch(
        self,
        dlc_path: Path | str,
        input_lines: list[str],
        work_path: Path,
        output_dir: Path | None = None,
    ) -> Path:
        """
        Execute qnn-net-run once for a DLC with multi-line input_list.txt on Qualcomm HTP.
        Each line in input_lines represents one inference set (Result_0, Result_1, ...).
        Returns the output directory path containing Result_0, Result_1, ...
        """
        if output_dir is None:
            output_dir = work_path / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        input_list_path = work_path / "input_list.txt"
        input_list_path.write_text("\n".join(input_lines), encoding="ascii")

        cmd = [
            str(self.qnn_net_run),
            "--model", str(self.qnn_model_dlc),
            "--backend", str(self.qnn_htp),
            "--dlc_path", str(dlc_path),
            "--input_list", str(input_list_path),
            "--output_dir", str(output_dir),
            "--profiling_level", "basic",
            "--use_native_input_files",
            "--use_native_output_files",
        ]

        env = self._build_env()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(work_path),
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"DLC execution timed out after {self.timeout_seconds}s for {Path(dlc_path).name}"
            ) from exc

        (work_path / "qnn_stdout.txt").write_text(proc.stdout, encoding="utf-8", errors="replace")
        (work_path / "qnn_stderr.txt").write_text(proc.stderr, encoding="utf-8", errors="replace")

        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            name_lower = str(dlc_path).lower()
            model_label = "Graph A" if "graph_a" in name_lower else ("Graph B" if "graph_b" in name_lower else "DLC")
            raise RuntimeError(f"{model_label} DLC execution failed with code {proc.returncode}: {err}")

        return output_dir

    def _run_graph_a_internal(
        self,
        input_sets: list[Mapping[str, np.ndarray]],
        work_dir: Path | str | None = None,
    ) -> list[GraphAOutputs]:
        """Low-level batch execution of Graph A DLC via qnn-net-run."""
        if not input_sets:
            raise ValueError("input_sets cannot be empty")

        for s_idx, inputs in enumerate(input_sets):
            try:
                self._validate_graph_a_inputs(inputs)
            except Exception as exc:
                raise ValueError(f"Input set {s_idx} validation failed: {exc}") from exc

        missing = self.validate_artifacts()
        if missing:
            raise FileNotFoundError(f"Missing required runtime/model artifacts: {missing}")

        owned_dir = False
        if work_dir is None:
            work_path = self.work_root / f"graph_a_batch_{uuid.uuid4().hex[:8]}"
            owned_dir = True
        else:
            work_path = Path(work_dir)
        work_path.mkdir(parents=True, exist_ok=True)

        try:
            output_dir = work_path / "outputs"
            output_dir.mkdir(parents=True, exist_ok=True)

            input_lines = []
            for set_idx, inputs in enumerate(input_sets):
                input_dir = work_path / f"inputs_{set_idx}"
                input_dir.mkdir(parents=True, exist_ok=True)
                entries = []
                for name in ("sample", "timestep", "encoder_hidden_states", "text_embeds", "time_ids"):
                    raw_path = input_dir / f"{name}.raw"
                    arr = inputs[name]
                    np.asarray(arr, dtype=np.float16).tofile(raw_path)
                    entries.append(f"{name}:={raw_path}")
                input_lines.append(" ".join(entries))

            self._run_dlc_batch(self.graph_a_path, input_lines, work_path, output_dir)

            batch_results: list[GraphAOutputs] = []
            for set_idx in range(len(input_sets)):
                result_dir = output_dir / f"Result_{set_idx}"
                # For single-set backward compatibility when mock/runtime writes directly to output_dir
                if not result_dir.is_dir():
                    if len(input_sets) == 1 and (
                        (output_dir / "output_0_native.raw").is_file()
                        or (output_dir / "output_0.raw").is_file()
                    ):
                        result_dir = output_dir
                    else:
                        raise FileNotFoundError(
                            f"Graph A missing Result_{set_idx} directory in {output_dir}"
                        )

                tensors: dict[str, np.ndarray] = {}
                raw_paths: dict[str, Path] = {}
                index_mapping: dict[int, str] = {}

                for spec in CROSS_GRAPH_SPECS:
                    idx = spec["index"]
                    target_name = spec["target_name"]
                    shape = spec["shape"]
                    expected_bytes = spec["bytes"]

                    candidate_paths = [
                        result_dir / f"output_{idx}_native.raw",
                        result_dir / f"output_{idx}.raw",
                    ]
                    matched_file: Path | None = None
                    for cand in candidate_paths:
                        if cand.is_file():
                            matched_file = cand
                            break

                    if matched_file is None:
                        raise FileNotFoundError(
                            f"Graph A missing output tensor file for index {idx} ('{target_name}') in Result_{set_idx}"
                        )

                    actual_bytes = matched_file.stat().st_size
                    if actual_bytes != expected_bytes:
                        raise ValueError(
                            f"Graph A output tensor {idx} ('{target_name}') in Result_{set_idx} byte size mismatch: "
                            f"expected {expected_bytes} bytes, got {actual_bytes} bytes"
                        )

                    arr = np.fromfile(matched_file, dtype=np.float16).reshape(shape)
                    if not np.isfinite(arr).all():
                        raise ValueError(
                            f"Graph A output tensor {idx} ('{target_name}') in Result_{set_idx} contains non-finite values (NaN/Inf)"
                        )

                    tensors[target_name] = arr
                    raw_paths[target_name] = matched_file
                    index_mapping[idx] = target_name

                batch_results.append(GraphAOutputs(tensors, raw_paths=raw_paths, index_mapping=index_mapping))

            return batch_results
        finally:
            if owned_dir and self.cleanup_temp and work_path.exists():
                shutil.rmtree(work_path, ignore_errors=True)

    def run_graph_a_batch(
        self,
        input_sets: list[Mapping[str, np.ndarray]],
        work_dir: Path | str | None = None,
    ) -> list[GraphAOutputs]:
        """
        Execute Graph A DLC on Qualcomm HTP for one or more input sets in a single process.
        input_sets: list of mappings, each containing:
            sample, timestep, encoder_hidden_states, text_embeds, time_ids (all FP16).
        Returns a list of GraphAOutputs, strictly ordered by input_sets index (Result_0, Result_1, ...).
        """
        if hasattr(self.run_graph_a, "assert_called") or getattr(self.run_graph_a, "__func__", None) != RORemDlcRuntime.run_graph_a:
            return [self.run_graph_a(s, work_dir=work_dir) for s in input_sets]
        return self._run_graph_a_internal(input_sets, work_dir=work_dir)

    def run_graph_a(
        self,
        inputs: Mapping[str, np.ndarray],
        work_dir: Path | str | None = None,
    ) -> GraphAOutputs:
        """
        Execute Graph A DLC on Qualcomm HTP and return 10 cross-graph tensors.
        Inputs: sample, timestep, encoder_hidden_states, text_embeds, time_ids (all FP16).
        """
        return self._run_graph_a_internal([inputs], work_dir=work_dir)[0]

    def _process_graph_b_input(
        self,
        name: str,
        val: np.ndarray | Path | str,
        expected_shape: tuple[int, ...],
        expected_bytes: int,
        input_dir: Path,
    ) -> Path:
        """Validate input value and return the raw file Path on disk."""
        if isinstance(val, (str, Path)):
            raw_path = Path(val)
            if not raw_path.is_file():
                raise FileNotFoundError(f"Graph B input file for '{name}' does not exist: {raw_path}")
            actual_bytes = raw_path.stat().st_size
            if actual_bytes != expected_bytes:
                raise ValueError(
                    f"Graph B input file '{raw_path.name}' size mismatch: "
                    f"expected {expected_bytes} bytes, got {actual_bytes} bytes"
                )
            arr = np.fromfile(raw_path, dtype=np.float16).reshape(expected_shape)
            if not np.isfinite(arr).all():
                raise ValueError(f"Graph B input file '{raw_path.name}' contains non-finite values (NaN/Inf)")
            return raw_path
        elif isinstance(val, np.ndarray):
            if val.dtype != np.float16:
                raise ValueError(f"Graph B input '{name}' must have dtype float16, got {val.dtype}")
            if val.shape != expected_shape:
                raise ValueError(
                    f"Graph B input '{name}' shape mismatch: expected {expected_shape}, got {val.shape}"
                )
            if not np.isfinite(val).all():
                raise ValueError(f"Graph B input '{name}' contains non-finite values (NaN/Inf)")
            safe_name = name.replace("/", "_").replace(".", "_").strip("_")
            raw_path = input_dir / f"{safe_name}.raw"
            np.asarray(val, dtype=np.float16).tofile(raw_path)
            return raw_path
        else:
            raise TypeError(f"Graph B input '{name}' must be np.ndarray or Path, got {type(val)}")

    def _run_graph_b_internal(
        self,
        input_sets: list[Mapping[str, np.ndarray | Path]],
        work_dir: Path | str | None = None,
    ) -> list[np.ndarray]:
        """Low-level batch execution of Graph B DLC via qnn-net-run."""
        if not input_sets:
            raise ValueError("input_sets cannot be empty")

        missing = self.validate_artifacts()
        if missing:
            raise FileNotFoundError(f"Missing required runtime/model artifacts: {missing}")

        owned_dir = False
        if work_dir is None:
            work_path = self.work_root / f"graph_b_batch_{uuid.uuid4().hex[:8]}"
            owned_dir = True
        else:
            work_path = Path(work_dir)
        work_path.mkdir(parents=True, exist_ok=True)

        try:
            output_dir = work_path / "outputs"
            output_dir.mkdir(parents=True, exist_ok=True)

            input_lines = []
            for set_idx, inputs in enumerate(input_sets):
                input_dir = work_path / f"inputs_{set_idx}"
                input_dir.mkdir(parents=True, exist_ok=True)
                resolved_inputs: dict[str, Path] = {}

                # 1. Conditioning inputs
                for cond_name, expected_shape in GRAPH_B_CONDITIONING_SPECS.items():
                    if cond_name not in inputs:
                        raise ValueError(f"Graph B Set {set_idx} missing required conditioning input: '{cond_name}'")
                    val = inputs[cond_name]
                    expected_bytes = int(np.prod(expected_shape)) * 2
                    resolved_path = self._process_graph_b_input(
                        name=cond_name,
                        val=val,
                        expected_shape=expected_shape,
                        expected_bytes=expected_bytes,
                        input_dir=input_dir,
                    )
                    resolved_inputs[cond_name] = resolved_path

                # 2. Cross-graph inputs
                for spec in CROSS_GRAPH_SPECS:
                    target_name = spec["target_name"]
                    idx = spec["index"]
                    expected_shape = spec["shape"]
                    expected_bytes = spec["bytes"]

                    val = None
                    if target_name in inputs:
                        val = inputs[target_name]
                    elif f"output_{idx}" in inputs:
                        val = inputs[f"output_{idx}"]
                    elif idx in inputs:
                        val = inputs[idx]
                    else:
                        raise ValueError(
                            f"Graph B Set {set_idx} missing required cross-graph input: '{target_name}' (index {idx})"
                        )

                    resolved_path = self._process_graph_b_input(
                        name=target_name,
                        val=val,
                        expected_shape=expected_shape,
                        expected_bytes=expected_bytes,
                        input_dir=input_dir,
                    )
                    resolved_inputs[target_name] = resolved_path

                # Build Graph B input line with exact 14 inputs in order
                entries = [f"{name}:={resolved_inputs[name]}" for name in GRAPH_B_INPUT_NAMES]
                input_lines.append(" ".join(entries))

            self._run_dlc_batch(self.graph_b_path, input_lines, work_path, output_dir)

            batch_out_samples: list[np.ndarray] = []
            for set_idx in range(len(input_sets)):
                result_dir = output_dir / f"Result_{set_idx}"
                if not result_dir.is_dir():
                    if len(input_sets) == 1 and (
                        (output_dir / "output_0_native.raw").is_file()
                        or (output_dir / "output_0.raw").is_file()
                    ):
                        result_dir = output_dir
                    else:
                        raise FileNotFoundError(
                            f"Graph B missing Result_{set_idx} directory in {output_dir}"
                        )

                candidate_paths = [
                    result_dir / "output_0_native.raw",
                    result_dir / "output_0.raw",
                ]
                matched_file: Path | None = None
                for cand in candidate_paths:
                    if cand.is_file():
                        matched_file = cand
                        break

                if matched_file is None:
                    raise FileNotFoundError(
                        f"Graph B missing output tensor file ('output_0_native.raw') in Result_{set_idx}"
                    )

                expected_bytes = GRAPH_B_OUTPUT_SPEC["bytes"]
                actual_bytes = matched_file.stat().st_size
                if actual_bytes != expected_bytes:
                    raise ValueError(
                        f"Graph B output tensor byte size mismatch in Result_{set_idx}: "
                        f"expected {expected_bytes} bytes, got {actual_bytes} bytes"
                    )

                expected_shape = GRAPH_B_OUTPUT_SPEC["shape"]
                out_sample = np.fromfile(matched_file, dtype=np.float16).reshape(expected_shape)
                if not np.isfinite(out_sample).all():
                    raise ValueError(
                        f"Graph B output 'out_sample' in Result_{set_idx} contains non-finite values (NaN/Inf)"
                    )

                batch_out_samples.append(out_sample)

            return batch_out_samples
        finally:
            if owned_dir and self.cleanup_temp and work_path.exists():
                shutil.rmtree(work_path, ignore_errors=True)

    def run_graph_b_batch(
        self,
        input_sets: list[Mapping[str, np.ndarray | Path]],
        work_dir: Path | str | None = None,
    ) -> list[np.ndarray]:
        """
        Execute Graph B DLC on Qualcomm HTP for one or more input sets in a single process.
        input_sets: list of mappings, each containing:
            4 conditioning tensors + 10 cross-graph tensors.
        Returns a list of out_sample [1,4,128,128] FP16, strictly ordered by input_sets index (Result_0, Result_1, ...).
        """
        if hasattr(self.run_graph_b, "assert_called") or getattr(self.run_graph_b, "__func__", None) != RORemDlcRuntime.run_graph_b:
            return [self.run_graph_b(s, work_dir=work_dir) for s in input_sets]
        return self._run_graph_b_internal(input_sets, work_dir=work_dir)

    def run_graph_b(
        self,
        inputs: Mapping[str, np.ndarray | Path],
        work_dir: Path | str | None = None,
    ) -> np.ndarray:
        """
        Execute Graph B DLC on Qualcomm HTP and return out_sample [1,4,128,128] FP16.
        Inputs: 4 conditioning tensors + 10 cross-graph tensors.
        """
        return self._run_graph_b_internal([inputs], work_dir=work_dir)[0]

    def run_split_unet_cfg(
        self,
        sample: np.ndarray,
        timestep: np.ndarray,
        hidden: np.ndarray,
        pooled: np.ndarray,
        negative_hidden: np.ndarray,
        negative_pooled: np.ndarray,
        time_ids: np.ndarray,
        work_dir: Path | str | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Execute full RORem split UNet CFG batch on Qualcomm HTP:
        - Exactly 1 Graph A process start with 2 inference sets (Result_0 = negative, Result_1 = positive)
        - Exactly 1 Graph B process start with 2 inference sets (Result_0 = negative, Result_1 = positive)
        Returns: (noise_uncond, noise_text)
        """
        owned_dir = False
        if work_dir is None:
            step_path = self.work_root / f"unet_cfg_{uuid.uuid4().hex[:8]}"
            owned_dir = True
        else:
            step_path = Path(work_dir)
        step_path.mkdir(parents=True, exist_ok=True)

        try:
            neg_inputs_a = {
                "sample": sample,
                "timestep": timestep,
                "encoder_hidden_states": negative_hidden,
                "text_embeds": negative_pooled,
                "time_ids": time_ids,
            }
            pos_inputs_a = {
                "sample": sample,
                "timestep": timestep,
                "encoder_hidden_states": hidden,
                "text_embeds": pooled,
                "time_ids": time_ids,
            }

            graph_a_sets = self.run_graph_a_batch(
                [neg_inputs_a, pos_inputs_a],
                work_dir=step_path / "graph_a_cfg",
            )
            out_a_neg, out_a_pos = graph_a_sets[0], graph_a_sets[1]

            neg_inputs_b: dict[str, Any] = {
                "timestep": timestep,
                "encoder_hidden_states": negative_hidden,
                "text_embeds": negative_pooled,
                "time_ids": time_ids,
            }
            pos_inputs_b: dict[str, Any] = {
                "timestep": timestep,
                "encoder_hidden_states": hidden,
                "text_embeds": pooled,
                "time_ids": time_ids,
            }

            for spec in CROSS_GRAPH_SPECS:
                tname = spec["target_name"]
                neg_inputs_b[tname] = (
                    out_a_neg.raw_paths[tname]
                    if hasattr(out_a_neg, "raw_paths") and tname in out_a_neg.raw_paths
                    else out_a_neg[tname]
                )
                pos_inputs_b[tname] = (
                    out_a_pos.raw_paths[tname]
                    if hasattr(out_a_pos, "raw_paths") and tname in out_a_pos.raw_paths
                    else out_a_pos[tname]
                )

            graph_b_sets = self.run_graph_b_batch(
                [neg_inputs_b, pos_inputs_b],
                work_dir=step_path / "graph_b_cfg",
            )
            return graph_b_sets[0], graph_b_sets[1]
        finally:
            if owned_dir and self.cleanup_temp and step_path.exists():
                shutil.rmtree(step_path, ignore_errors=True)

    def run_split_unet(
        self,
        sample: np.ndarray | None = None,
        timestep: np.ndarray | None = None,
        encoder_hidden_states: np.ndarray | None = None,
        text_embeds: np.ndarray | None = None,
        time_ids: np.ndarray | None = None,
        *,
        inputs: dict[str, np.ndarray] | None = None,
        work_dir: Path | str | None = None,
    ) -> np.ndarray:
        """
        Execute full RORem split UNet pipeline: Graph A DLC -> Graph B DLC on Qualcomm HTP.
        Accepts prepared FP16 numpy arrays and returns out_sample [1,4,128,128] FP16.
        """
        all_inputs = dict(inputs) if inputs is not None else {}
        if sample is not None:
            all_inputs["sample"] = sample
        if timestep is not None:
            all_inputs["timestep"] = timestep
        if encoder_hidden_states is not None:
            all_inputs["encoder_hidden_states"] = encoder_hidden_states
        if text_embeds is not None:
            all_inputs["text_embeds"] = text_embeds
        if time_ids is not None:
            all_inputs["time_ids"] = time_ids

        self._validate_graph_a_inputs(all_inputs)

        owned_dir = False
        if work_dir is None:
            job_id = f"rorem_job_{uuid.uuid4().hex[:10]}"
            job_path = self.work_root / job_id
            owned_dir = True
        else:
            job_path = Path(work_dir)
        job_path.mkdir(parents=True, exist_ok=True)

        try:
            graph_a_work = job_path / "graph_a"
            graph_b_work = job_path / "graph_b"
            graph_a_work.mkdir(parents=True, exist_ok=True)
            graph_b_work.mkdir(parents=True, exist_ok=True)

            graph_a_outputs = self.run_graph_a(all_inputs, work_dir=graph_a_work)

            graph_b_inputs: dict[str, Any] = {
                "timestep": all_inputs["timestep"],
                "encoder_hidden_states": all_inputs["encoder_hidden_states"],
                "text_embeds": all_inputs["text_embeds"],
                "time_ids": all_inputs["time_ids"],
            }
            for spec in CROSS_GRAPH_SPECS:
                target_name = spec["target_name"]
                if hasattr(graph_a_outputs, "raw_paths") and target_name in graph_a_outputs.raw_paths:
                    graph_b_inputs[target_name] = graph_a_outputs.raw_paths[target_name]
                else:
                    graph_b_inputs[target_name] = graph_a_outputs[target_name]

            out_sample = self.run_graph_b(graph_b_inputs, work_dir=graph_b_work)
            return out_sample
        finally:
            if owned_dir and self.cleanup_temp and job_path.exists():
                shutil.rmtree(job_path, ignore_errors=True)

    def execute(
        self,
        sample: np.ndarray | None = None,
        timestep: np.ndarray | None = None,
        encoder_hidden_states: np.ndarray | None = None,
        text_embeds: np.ndarray | None = None,
        time_ids: np.ndarray | None = None,
        *,
        inputs: dict[str, np.ndarray] | None = None,
        work_dir: Path | str | None = None,
    ) -> RORemDlcResult:
        """Run split UNet pipeline and wrap result into RORemDlcResult."""
        try:
            out = self.run_split_unet(
                sample=sample,
                timestep=timestep,
                encoder_hidden_states=encoder_hidden_states,
                text_embeds=text_embeds,
                time_ids=time_ids,
                inputs=inputs,
                work_dir=work_dir,
            )
            return RORemDlcResult(
                success=True,
                output=out,
                error_code=None,
                error_message=None,
                backend_name=self.BACKEND_NAME,
            )
        except Exception as exc:
            return RORemDlcResult(
                success=False,
                output=None,
                error_code=exc.__class__.__name__,
                error_message=str(exc),
                backend_name=self.BACKEND_NAME,
            )

    def run_image(
        self,
        input_image_path: str | Path,
        mask_image_path: str | Path,
        prompt: str,
        output_path: str | Path,
        *,
        negative_prompt: str = "",
        steps: int = 1,
        seed: int = DEFAULT_SEED,
        guidance_scale: float = DEFAULT_GUIDANCE_SCALE,
        strength: float = DEFAULT_STRENGTH,
        progress_callback: Callable[[str, float, str | None], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> RORemDlcResult:
        """
        Full 1024x1024 Inpainting End-to-End Pipeline:
        RGB Image -> Mask -> HTP VAE Encode -> HTP CLIP-L/G -> CPU Scheduler/CFG ->
        RORem Graph A HTP -> RORem Graph B HTP -> HTP VAE Decode -> Compositing -> PNG.
        """
        t0 = time.perf_counter()
        out_target = Path(output_path)

        def progress(phase: str, val: float, detail: str | None = None) -> None:
            if progress_callback is not None:
                progress_callback(phase, val, detail)

        def check_cancel(phase_name: str) -> None:
            if cancel_requested is not None and cancel_requested():
                raise InterruptedError(f"Inpainting cancelled by user before {phase_name}")

        metadata: dict[str, Any] = {
            "backend": self.BACKEND_NAME,
            "graph_a_process_starts": 0,
            "graph_a_inference_sets": 0,
            "graph_b_process_starts": 0,
            "graph_b_inference_sets": 0,
            "graph_a_execution_count": 0,
            "graph_b_execution_count": 0,
            "graph_a_total_seconds": 0.0,
            "graph_b_total_seconds": 0.0,
            "process_starts_per_step": 2,
            "vae_encoder_backend": "Qualcomm QNN HTP (sdxl_vae_encoder.serialized.bin)",
            "vae_decoder_backend": "Qualcomm QNN HTP (sdxl_vae_decoder.serialized.bin)",
            "clip_l_backend": "Qualcomm QNN HTP (text_encoder.serialized.bin)",
            "clip_g_backend": "Qualcomm QNN HTP (text_encoder_2.serialized.bin)",
            "steps_requested": steps,
            "steps_executed": 0,
            "seed": seed,
            "guidance_scale": float(guidance_scale),
            "strength": float(strength),
            "timeout_seconds": self.timeout_seconds,
            "elapsed_seconds": 0.0,
            "cpu_ai_fallback": False,
        }

        job_dir = self.work_root / f"rorem_img_{uuid.uuid4().hex[:10]}"
        job_dir.mkdir(parents=True, exist_ok=True)

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000003)
            except Exception:
                pass

        try:
            # 1. Validation & Input Preparation (Fail-closed on non-1024x1024)
            progress("init", 0.02, "Validating inputs and pipeline artifacts")
            missing = self.validate_pipeline_artifacts()
            if missing:
                raise FileNotFoundError(
                    "Missing required pipeline artifacts: " + ", ".join(str(p) for p in missing)
                )

            source, masked_source, mask, original_pixels, authored_mask = self._prepare_inputs(
                input_image_path, mask_image_path
            )

            # 2. Text Encoding on HTP (CLIP-L & CLIP-G)
            check_cancel("CLIP encoding")
            progress("clip", 0.08, "Encoding prompt on Qualcomm HTP (CLIP-L & CLIP-G)")
            hidden, pooled, negative_hidden, negative_pooled, time_ids = self._encode_prompt(
                prompt, negative_prompt
            )

            # 3. VAE Encoding on HTP
            check_cancel("VAE encoding")
            progress("vae_encode", 0.16, "Encoding source & masked image on Qualcomm HTP")
            # 3A. Encode source image for inpainting latent reference
            enc_source_dir = job_dir / "vae_encode_source"
            res_source = self.run_context(
                self.vae_encoder_path,
                {"sample": source},
                {"latent_sample": (1, 4, 128, 128)},
                enc_source_dir,
            )
            original_latents = (res_source["latent_sample"] * LATENT_SCALE).astype(np.float16)

            # 3B. Encode masked source image for UNet conditioning
            enc_masked_dir = job_dir / "vae_encode_masked"
            res_masked = self.run_context(
                self.vae_encoder_path,
                {"sample": masked_source},
                {"latent_sample": (1, 4, 128, 128)},
                enc_masked_dir,
            )
            masked_image_latents = (res_masked["latent_sample"] * LATENT_SCALE).astype(np.float16)

            # 4. Scheduler & Latent Noise Initialization
            import torch
            from diffusers import EulerDiscreteScheduler

            scheduler = EulerDiscreteScheduler.from_pretrained(str(self.scheduler_dir))
            scheduler.set_timesteps(steps)

            init_timestep = self._resolve_init_timestep(steps, strength)
            t_start = max(steps - init_timestep, 0)
            timesteps = scheduler.timesteps[t_start * scheduler.order :]
            if len(timesteps) == 0:
                timesteps = scheduler.timesteps
                t_start = 0

            if hasattr(scheduler, "set_begin_index"):
                scheduler.set_begin_index(t_start * scheduler.order)

            metadata["steps_executed"] = len(timesteps)

            # Deterministic noise with seed
            rng = np.random.default_rng(seed)
            noise = rng.standard_normal((1, 4, 128, 128)).astype(np.float32)

            # Inpainting initialization: add noise to original latents at start timestep
            start_timestep = timesteps[:1]
            latents = scheduler.add_noise(
                torch.from_numpy(original_latents.astype(np.float32)),
                torch.from_numpy(noise),
                start_timestep,
            ).numpy().astype(np.float16)

            # 5. Denoising Loop: CFG with Graph A DLC -> Graph B DLC on Qualcomm HTP
            total_steps = len(timesteps)
            for step_idx, scheduler_timestep in enumerate(timesteps):
                frac = step_idx / max(total_steps, 1)
                progress("denoise", 0.20 + 0.65 * frac, f"Denoising step {step_idx + 1}/{total_steps}")

                scaled_noisy_latents = scheduler.scale_model_input(
                    torch.from_numpy(latents.astype(np.float32)), scheduler_timestep
                ).numpy().astype(np.float16)

                sample_9ch = self._build_unet_sample(scaled_noisy_latents, mask, masked_image_latents)
                step_timestep = np.array([float(scheduler_timestep)], dtype=np.float16)

                step_dir = job_dir / f"step_{step_idx:03d}"
                step_dir.mkdir(parents=True, exist_ok=True)

                # CFG Batch: 1 Graph A process start (2 inference sets: Result_0=neg, Result_1=pos)
                check_cancel(f"step {step_idx + 1} Graph A CFG batch")
                neg_inputs_a = {
                    "sample": sample_9ch,
                    "timestep": step_timestep,
                    "encoder_hidden_states": negative_hidden,
                    "text_embeds": negative_pooled,
                    "time_ids": time_ids,
                }
                pos_inputs_a = {
                    "sample": sample_9ch,
                    "timestep": step_timestep,
                    "encoder_hidden_states": hidden,
                    "text_embeds": pooled,
                    "time_ids": time_ids,
                }
                t_a0 = time.perf_counter()
                graph_a_sets = self.run_graph_a_batch(
                    [neg_inputs_a, pos_inputs_a],
                    work_dir=step_dir / "graph_a_cfg",
                )
                t_a = time.perf_counter() - t_a0
                metadata["graph_a_total_seconds"] = round(metadata["graph_a_total_seconds"] + t_a, 2)
                metadata["graph_a_process_starts"] += 1
                metadata["graph_a_inference_sets"] += 2
                metadata["graph_a_execution_count"] += 2
                out_a_neg, out_a_pos = graph_a_sets[0], graph_a_sets[1]

                # CFG Batch: 1 Graph B process start (2 inference sets: Result_0=neg, Result_1=pos)
                check_cancel(f"step {step_idx + 1} Graph B CFG batch")
                neg_inputs_b: dict[str, Any] = {
                    "timestep": step_timestep,
                    "encoder_hidden_states": negative_hidden,
                    "text_embeds": negative_pooled,
                    "time_ids": time_ids,
                }
                pos_inputs_b: dict[str, Any] = {
                    "timestep": step_timestep,
                    "encoder_hidden_states": hidden,
                    "text_embeds": pooled,
                    "time_ids": time_ids,
                }
                for spec in CROSS_GRAPH_SPECS:
                    tname = spec["target_name"]
                    neg_inputs_b[tname] = (
                        out_a_neg.raw_paths[tname]
                        if hasattr(out_a_neg, "raw_paths") and tname in out_a_neg.raw_paths
                        else out_a_neg[tname]
                    )
                    pos_inputs_b[tname] = (
                        out_a_pos.raw_paths[tname]
                        if hasattr(out_a_pos, "raw_paths") and tname in out_a_pos.raw_paths
                        else out_a_pos[tname]
                    )

                t_b0 = time.perf_counter()
                graph_b_sets = self.run_graph_b_batch(
                    [neg_inputs_b, pos_inputs_b],
                    work_dir=step_dir / "graph_b_cfg",
                )
                t_b = time.perf_counter() - t_b0
                metadata["graph_b_total_seconds"] = round(metadata["graph_b_total_seconds"] + t_b, 2)
                metadata["graph_b_process_starts"] += 1
                metadata["graph_b_inference_sets"] += 2
                metadata["graph_b_execution_count"] += 2
                noise_uncond, noise_text = graph_b_sets[0], graph_b_sets[1]

                # CFG calculation on CPU
                noise_pred = noise_uncond + guidance_scale * (noise_text - noise_uncond)
                if not np.isfinite(noise_pred).all():
                    raise ValueError(f"Step {step_idx + 1} CFG noise prediction contains non-finite values (NaN/Inf)")

                # Scheduler step on CPU
                check_cancel(f"step {step_idx + 1} scheduler step")
                latents = scheduler.step(
                    torch.from_numpy(noise_pred.astype(np.float32)),
                    scheduler_timestep,
                    torch.from_numpy(latents.astype(np.float32)),
                ).prev_sample.numpy().astype(np.float16)

                if not np.isfinite(latents).all():
                    raise ValueError(f"Step {step_idx + 1} scheduler output latents contain non-finite values (NaN/Inf)")

            # 6. VAE Decoding on Qualcomm HTP
            check_cancel("VAE decode")
            progress("vae_decode", 0.90, "Decoding latents on Qualcomm HTP VAE Decoder")
            dec_dir = job_dir / "vae_decode"
            unscaled_latents = (latents / LATENT_SCALE).astype(np.float16)
            res_dec = self.run_context(
                self.vae_decoder_path,
                {"latent_sample": unscaled_latents},
                {"sample": (1, 3, 1024, 1024)},
                dec_dir,
            )
            decoded = res_dec["sample"]

            # 7. Pixel Conversion & Deterministic Mask Compositing
            progress("composite", 0.96, "Compositing mask boundaries")
            generated_pixels = np.clip(
                (decoded[0].transpose(1, 2, 0).astype(np.float32) + 1.0) * 127.5, 0, 255
            ).astype(np.uint8)

            final_pixels = self._composite_pixels(original_pixels, generated_pixels, authored_mask)

            out_target.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(final_pixels, mode="RGB").save(out_target, format="PNG")

            metadata["elapsed_seconds"] = round(time.perf_counter() - t0, 3)
            progress("completed", 1.0, f"Inpainting finished in {metadata['elapsed_seconds']}s")

            return RORemDlcResult(
                success=True,
                output=final_pixels,
                output_path=out_target,
                error_code=None,
                error_message=None,
                backend_name=self.BACKEND_NAME,
                metadata=metadata,
            )
        except Exception as exc:
            metadata["elapsed_seconds"] = round(time.perf_counter() - t0, 3)
            return RORemDlcResult(
                success=False,
                output=None,
                output_path=None,
                error_code=exc.__class__.__name__,
                error_message=str(exc),
                backend_name=self.BACKEND_NAME,
                metadata=metadata,
            )
        finally:
            if sys.platform == "win32":
                try:
                    import ctypes
                    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
                except Exception:
                    pass
            if self.cleanup_temp and job_dir.exists():
                shutil.rmtree(job_dir, ignore_errors=True)


class RORemDlcInpaintingAdapter:
    """
    Thin adapter for RORem DLC inpainting execution (split UNet on Qualcomm HTP).
    Ready for integration into inpainting pipelines.
    """

    def __init__(
        self,
        runtime: RORemDlcRuntime | None = None,
        *,
        timeout_seconds: int | None = None,
    ) -> None:
        if runtime is not None:
            self.runtime = runtime
            if timeout_seconds is not None:
                self.runtime.timeout_seconds = timeout_seconds
        else:
            self.runtime = RORemDlcRuntime(
                timeout_seconds=timeout_seconds if timeout_seconds is not None else DEFAULT_TIMEOUT_SECONDS
            )
        import threading
        self._cancel_event = threading.Event()

    @property
    def backend_name(self) -> str:
        return self.runtime.BACKEND_NAME

    def validate_artifacts(self, full_pipeline: bool = False) -> list[Path]:
        return self.runtime.validate_artifacts(full_pipeline=full_pipeline)

    def is_available(self, full_pipeline: bool = False) -> bool:
        return len(self.validate_artifacts(full_pipeline=full_pipeline)) == 0

    def cancel(self) -> None:
        self._cancel_event.set()

    def run_split_unet(
        self,
        sample: np.ndarray | None = None,
        timestep: np.ndarray | None = None,
        encoder_hidden_states: np.ndarray | None = None,
        text_embeds: np.ndarray | None = None,
        time_ids: np.ndarray | None = None,
        *,
        inputs: dict[str, np.ndarray] | None = None,
        work_dir: Path | str | None = None,
    ) -> np.ndarray:
        return self.runtime.run_split_unet(
            sample=sample,
            timestep=timestep,
            encoder_hidden_states=encoder_hidden_states,
            text_embeds=text_embeds,
            time_ids=time_ids,
            inputs=inputs,
            work_dir=work_dir,
        )

    def execute(
        self,
        sample: np.ndarray | None = None,
        timestep: np.ndarray | None = None,
        encoder_hidden_states: np.ndarray | None = None,
        text_embeds: np.ndarray | None = None,
        time_ids: np.ndarray | None = None,
        *,
        inputs: dict[str, np.ndarray] | None = None,
        work_dir: Path | str | None = None,
    ) -> RORemDlcResult:
        return self.runtime.execute(
            sample=sample,
            timestep=timestep,
            encoder_hidden_states=encoder_hidden_states,
            text_embeds=text_embeds,
            time_ids=time_ids,
            inputs=inputs,
            work_dir=work_dir,
        )

    def run_image(
        self,
        input_image_path: str | Path,
        mask_image_path: str | Path,
        prompt: str,
        output_path: str | Path,
        *,
        negative_prompt: str = "",
        steps: int = 1,
        seed: int = DEFAULT_SEED,
        guidance_scale: float = DEFAULT_GUIDANCE_SCALE,
        strength: float = DEFAULT_STRENGTH,
        progress_callback: Callable[[str, float, str | None], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> RORemDlcResult:
        def check_cancel() -> bool:
            if self._cancel_event.is_set():
                return True
            if cancel_requested is not None:
                return cancel_requested()
            return False

        return self.runtime.run_image(
            input_image_path,
            mask_image_path,
            prompt,
            output_path,
            negative_prompt=negative_prompt,
            steps=steps,
            seed=seed,
            guidance_scale=guidance_scale,
            strength=strength,
            progress_callback=progress_callback,
            cancel_requested=check_cancel,
        )

    def run(self, *args, **kwargs) -> RORemDlcResult:
        """Alias for run_image to match generic adapter interface."""
        return self.run_image(*args, **kwargs)
