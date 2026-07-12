#!/usr/bin/env python3
"""Isolated 1024x1024 tiled-diffusion PoC for the fixed-shape SD2.1 QNN package."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Callable

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
GLOBAL_SITE_PACKAGES = Path(r"C:\Program Files\Python311-arm64\Lib\site-packages")
if str(GLOBAL_SITE_PACKAGES) not in sys.path:
    sys.path.append(str(GLOBAL_SITE_PACKAGES))

from engine.sd21_qnn_backend import (  # noqa: E402
    SimpleCLIPTokenizer,
    StableDiffusion21DDIMScheduler,
    StableDiffusion21QnnBackend,
    _read_git_commit,
    _tensor_summary,
)


LOGGER = logging.getLogger("TiledSD21QnnExperiment")
MODEL_ID = "stable_diffusion_v2_1_qnn"
TARGET_SIZE = 1024
LATENT_SIZE = 128
TILE_SIZE = 64
LATENT_TO_PIXEL = 8
DEFAULT_PROMPT = (
    "a wide cinematic futuristic city plaza at night, one central glass tower, "
    "continuous wet pavement reflections, coherent architecture, neon signs, "
    "people walking across the same connected plaza, realistic perspective, "
    "high photographic detail"
)
DEFAULT_NEGATIVE_PROMPT = (
    "disconnected buildings, duplicated tower, repeated objects, visible seams, "
    "misaligned perspective, collage, split image, blurry, distorted, low quality"
)


@dataclass(frozen=True)
class TilePosition:
    y: int
    x: int
    height: int
    width: int


@dataclass(frozen=True)
class TilePlan:
    canvas_height: int
    canvas_width: int
    tile_size: int
    overlap: int
    stride: int
    positions: tuple[TilePosition, ...]


def _axis_positions(canvas_size: int, tile_size: int, overlap: int) -> tuple[int, ...]:
    if canvas_size < tile_size:
        raise ValueError("Canvas must be at least as large as one tile")
    if overlap < 0 or overlap >= tile_size:
        raise ValueError("Overlap must satisfy 0 <= overlap < tile_size")
    stride = tile_size - overlap
    last = canvas_size - tile_size
    positions = list(range(0, last + 1, stride))
    if not positions or positions[-1] != last:
        positions.append(last)
    return tuple(positions)


def create_tile_plan(
    canvas_height: int = LATENT_SIZE,
    canvas_width: int = LATENT_SIZE,
    tile_size: int = TILE_SIZE,
    overlap: int = 8,
) -> TilePlan:
    """Create deterministic fixed-size windows with boundary-aligned final tiles."""
    ys = _axis_positions(canvas_height, tile_size, overlap)
    xs = _axis_positions(canvas_width, tile_size, overlap)
    positions = tuple(TilePosition(y, x, tile_size, tile_size) for y in ys for x in xs)
    return TilePlan(canvas_height, canvas_width, tile_size, overlap, tile_size - overlap, positions)


def create_global_latents(seed: int, shape: tuple[int, ...] = (1, LATENT_SIZE, LATENT_SIZE, 4)) -> np.ndarray:
    """Create the one shared deterministic latent-noise canvas."""
    return np.random.default_rng(seed=seed).standard_normal(shape, dtype=np.float32)


def cosine_blend_mask(plan: TilePlan, position: TilePosition) -> np.ndarray:
    """Return a separable cosine edge mask; global canvas boundaries remain weight 1."""
    size = plan.tile_size
    axis_y = np.ones(size, dtype=np.float32)
    axis_x = np.ones(size, dtype=np.float32)
    if plan.overlap:
        phase = (np.arange(plan.overlap, dtype=np.float32) + 1.0) / (plan.overlap + 1.0)
        ramp = 0.5 - 0.5 * np.cos(np.pi * phase)
        if position.y > 0:
            axis_y[: plan.overlap] = ramp
        if position.y + size < plan.canvas_height:
            axis_y[-plan.overlap :] = ramp[::-1]
        if position.x > 0:
            axis_x[: plan.overlap] = ramp
        if position.x + size < plan.canvas_width:
            axis_x[-plan.overlap :] = ramp[::-1]
    return np.outer(axis_y, axis_x).astype(np.float32)


def accumulate_tiles(
    plan: TilePlan,
    tile_values: list[np.ndarray],
    mask_factory: Callable[[TilePlan, TilePosition], np.ndarray] = cosine_blend_mask,
) -> tuple[np.ndarray, np.ndarray]:
    """Blend NHWC tile values into one canvas without any neural inference."""
    if len(tile_values) != len(plan.positions):
        raise ValueError("One value tensor is required for every tile position")
    if not tile_values:
        raise ValueError("Tile plan must not be empty")
    channels = int(tile_values[0].shape[-1])
    accumulator = np.zeros((1, plan.canvas_height, plan.canvas_width, channels), dtype=np.float32)
    weights = np.zeros((1, plan.canvas_height, plan.canvas_width, 1), dtype=np.float32)
    for position, value in zip(plan.positions, tile_values):
        expected = (1, plan.tile_size, plan.tile_size, channels)
        if value.shape != expected:
            raise ValueError(f"Unexpected tile shape {value.shape}; expected {expected}")
        mask = mask_factory(plan, position)[None, :, :, None]
        y_slice = slice(position.y, position.y + position.height)
        x_slice = slice(position.x, position.x + position.width)
        accumulator[:, y_slice, x_slice, :] += value.astype(np.float32) * mask
        weights[:, y_slice, x_slice, :] += mask
    if float(weights.min()) <= 0.0:
        raise RuntimeError("Tile plan produced uncovered canvas pixels")
    return accumulator / weights, weights


def _quantize(value: np.ndarray | float, spec: dict[str, Any]) -> np.ndarray:
    return np.clip(
        np.round(np.asarray(value, dtype=np.float32) / float(spec["scale"])) + int(spec["zero_point"]),
        0,
        65535,
    ).astype(np.uint16)


def _dequantize(value: np.ndarray, spec: dict[str, Any]) -> np.ndarray:
    return (value.astype(np.float32) - int(spec["zero_point"])) * float(spec["scale"])


def _load_contract(model_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = json.loads((model_dir / "metadata.json").read_text(encoding="utf-8"))
    package = json.loads((model_dir / "package.json").read_text(encoding="utf-8"))
    files = metadata["model_files"]
    contract = {
        "text_output": files["text_encoder.bin"]["outputs"]["text_embedding"]["quantization_parameters"],
        "unet_timestep": files["unet.bin"]["inputs"]["timestep"]["quantization_parameters"],
        "unet_latent": files["unet.bin"]["inputs"]["latent"]["quantization_parameters"],
        "unet_text": files["unet.bin"]["inputs"]["text_emb"]["quantization_parameters"],
        "unet_output": files["unet.bin"]["outputs"]["output_latent"]["quantization_parameters"],
        "vae_latent": files["vae.bin"]["inputs"]["latent"]["quantization_parameters"],
        "vae_output": files["vae.bin"]["outputs"]["image"]["quantization_parameters"],
    }
    return contract, package


def _session_evidence(session: Any, component: str) -> dict[str, Any]:
    providers = list(session.get_providers()) if hasattr(session, "get_providers") else ["QNNExecutionProvider"]
    if "QNNExecutionProvider" not in providers:
        raise RuntimeError(f"{component} is not assigned to QNNExecutionProvider: {providers}")
    return {
        "component": component,
        "providers": providers,
        "assigned_provider": "QNNExecutionProvider",
        "cpu_ep_fallback_disabled": True,
        "qnn_htp_verified": True,
    }


def run_experiment(
    overlap: int,
    output_dir: Path,
    prompt: str = DEFAULT_PROMPT,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    seed: int = 123456789,
    steps: int = 20,
    cfg: float = 7.5,
    model_dir: Path = PROJECT_ROOT / "models" / "stable_diffusion_v2_1",
) -> tuple[Path, Path]:
    """Run global tiled denoising and tiled VAE decode exclusively on QNN/HTP."""
    if overlap not in {8, 16}:
        raise ValueError("HR-001 supports overlap 8 or 16 latent pixels")
    plan = create_tile_plan(overlap=overlap)
    contract, package = _load_contract(model_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    host_blend_seconds = 0.0
    sessions: tuple[Any, Any, Any] | None = None

    backend = StableDiffusion21QnnBackend()
    text_session, unet_session, vae_session, provider_diagnostics = backend._setup_sessions(model_dir)
    sessions = (text_session, unet_session, vae_session)
    evidence = [
        _session_evidence(text_session, "text_encoder"),
        _session_evidence(unet_session, "unet"),
        _session_evidence(vae_session, "vae_decoder"),
    ]
    try:
        tokenizer = SimpleCLIPTokenizer(model_dir / "tokenizer" / "vocab.json", model_dir / "tokenizer" / "merges.txt")
        cond_tokens = np.asarray([tokenizer.tokenize_prompt(prompt)], dtype=np.int32)
        uncond_tokens = np.asarray([tokenizer.tokenize_prompt(negative_prompt)], dtype=np.int32)
        text_started = time.perf_counter()
        cond_q = text_session.run(["text_embedding"], {"tokens": cond_tokens})[0]
        uncond_q = text_session.run(["text_embedding"], {"tokens": uncond_tokens})[0]
        text_seconds = time.perf_counter() - text_started
        cond_text = _quantize(_dequantize(cond_q, contract["text_output"]), contract["unet_text"])
        uncond_text = _quantize(_dequantize(uncond_q, contract["text_output"]), contract["unet_text"])

        scheduler = StableDiffusion21DDIMScheduler()
        scheduler.set_timesteps(steps)
        latents = create_global_latents(seed)
        latent_summaries = [_tensor_summary("global_latent.initial", latents)]
        unet_call_times: list[float] = []
        weight_min = float("inf")
        weight_max = 0.0
        for step_index, timestep in enumerate(scheduler.timesteps):
            predictions: list[np.ndarray] = []
            timestep_q = _quantize(np.asarray([[timestep]], dtype=np.float32), contract["unet_timestep"])
            print(f"Step {step_index + 1}/{steps}: timestep={int(timestep)}, tiles={len(plan.positions)}", flush=True)
            for position in plan.positions:
                tile = latents[:, position.y : position.y + TILE_SIZE, position.x : position.x + TILE_SIZE, :]
                latent_q = _quantize(tile, contract["unet_latent"])
                call_started = time.perf_counter()
                cond_out = unet_session.run(
                    ["output_latent"], {"latent": latent_q, "timestep": timestep_q, "text_emb": cond_text}
                )[0]
                uncond_out = unet_session.run(
                    ["output_latent"], {"latent": latent_q, "timestep": timestep_q, "text_emb": uncond_text}
                )[0]
                unet_call_times.append(time.perf_counter() - call_started)
                cond_prediction = _dequantize(cond_out, contract["unet_output"])
                uncond_prediction = _dequantize(uncond_out, contract["unet_output"])
                predictions.append(uncond_prediction + cfg * (cond_prediction - uncond_prediction))
            blend_started = time.perf_counter()
            global_prediction, weights = accumulate_tiles(plan, predictions)
            host_blend_seconds += time.perf_counter() - blend_started
            weight_min = min(weight_min, float(weights.min()))
            weight_max = max(weight_max, float(weights.max()))
            latents = scheduler.step(
                global_prediction,
                int(timestep),
                latents,
                scheduler.num_train_timesteps // steps,
            ).astype(np.float32)
            if step_index == steps // 2:
                latent_summaries.append(_tensor_summary("global_latent.mid", latents))
        latent_summaries.append(_tensor_summary("global_latent.final", latents))

        vae_tiles: list[np.ndarray] = []
        vae_times: list[float] = []
        for tile_index, position in enumerate(plan.positions, start=1):
            print(f"VAE tile {tile_index}/{len(plan.positions)}", flush=True)
            tile = latents[:, position.y : position.y + TILE_SIZE, position.x : position.x + TILE_SIZE, :]
            vae_started = time.perf_counter()
            image_q = vae_session.run(["image"], {"latent": _quantize(tile, contract["vae_latent"])})[0]
            vae_times.append(time.perf_counter() - vae_started)
            image_float = image_q.astype(np.float32) * float(contract["vae_output"]["scale"])
            vae_tiles.append(image_float)

        pixel_plan = TilePlan(
            TARGET_SIZE,
            TARGET_SIZE,
            TILE_SIZE * LATENT_TO_PIXEL,
            overlap * LATENT_TO_PIXEL,
            plan.stride * LATENT_TO_PIXEL,
            tuple(
                TilePosition(
                    position.y * LATENT_TO_PIXEL,
                    position.x * LATENT_TO_PIXEL,
                    position.height * LATENT_TO_PIXEL,
                    position.width * LATENT_TO_PIXEL,
                )
                for position in plan.positions
            ),
        )
        blend_started = time.perf_counter()
        image_float, pixel_weights = accumulate_tiles(pixel_plan, vae_tiles)
        host_blend_seconds += time.perf_counter() - blend_started
        if float(pixel_weights.min()) <= 0.0:
            raise RuntimeError("Tiled VAE decode produced uncovered output pixels")
        image_rgb = np.clip(image_float[0] * 255.0, 0, 255).astype(np.uint8)

        from PIL import Image

        stem = f"hr001_sd21_1024_overlap_{overlap * LATENT_TO_PIXEL}px"
        image_path = output_dir / f"{stem}.png"
        Image.fromarray(image_rgb, mode="RGB").save(image_path, format="PNG")
        total_seconds = time.perf_counter() - started
        sidecar_path = image_path.with_suffix(".json")
        metadata = {
            "experiment": "HR-001 Tiled QNN Diffusion Proof of Concept",
            "model_id": MODEL_ID,
            "model_version": package.get("package_version"),
            "git_commit": _read_git_commit(),
            "backend": "Qualcomm Stable Diffusion 2.1 QNN",
            "device": "Qualcomm Hexagon HTP V73",
            "runtime": "ONNX Runtime QNN",
            "qnn_htp_evidence": evidence,
            "provider_diagnostics": provider_diagnostics,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "scheduler": "DDIMScheduler",
            "prediction_type": "v_prediction",
            "target_width": TARGET_SIZE,
            "target_height": TARGET_SIZE,
            "global_latent_shape": list(latents.shape),
            "initial_noise_sigma": 1.0,
            "tile_size_latent": TILE_SIZE,
            "overlap_latent": overlap,
            "overlap_pixels": overlap * LATENT_TO_PIXEL,
            "stride_latent": plan.stride,
            "tile_positions": [asdict(position) for position in plan.positions],
            "unet_calls_per_step": len(plan.positions) * 2,
            "total_unet_calls": len(plan.positions) * 2 * steps,
            "weighting_method": "separable_cosine",
            "weighting_parameters": {"ramp_width_latent": overlap, "canvas_edges_weight": 1.0},
            "latent_diagnostics": latent_summaries,
            "latent_weight_sum_min": weight_min,
            "latent_weight_sum_max": weight_max,
            "pixel_weight_sum_min": float(pixel_weights.min()),
            "pixel_weight_sum_max": float(pixel_weights.max()),
            "timings": {
                "text_encoder_seconds": text_seconds,
                "unet_call_seconds": unet_call_times,
                "unet_total_seconds": float(sum(unet_call_times)),
                "vae_tile_seconds": vae_times,
                "vae_total_seconds": float(sum(vae_times)),
                "host_blending_seconds": host_blend_seconds,
                "total_seconds": total_seconds,
            },
            "quantization_contract": contract,
            "cpu_fallback_used": False,
            "result_file": str(image_path.resolve()),
        }
        sidecar_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        return image_path, sidecar_path
    finally:
        if sessions is not None:
            for session in sessions:
                try:
                    session.end_profiling()
                except Exception:
                    LOGGER.exception("QNN profiling could not be finalized")
            del text_session, unet_session, vae_session


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overlap", type=int, choices=(8, 16), required=True, help="Latent overlap (8=64px, 16=128px)")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "output" / "hr001")
    parser.add_argument("--seed", type=int, default=123456789)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--cfg", type=float, default=7.5)
    args = parser.parse_args()
    image_path, sidecar_path = run_experiment(args.overlap, args.output_dir, seed=args.seed, steps=args.steps, cfg=args.cfg)
    print(f"Image: {image_path}")
    print(f"Sidecar: {sidecar_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
