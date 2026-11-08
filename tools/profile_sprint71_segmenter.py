"""
Detailed profiling of ColorSpatialSegmenter (Sprint 71 baseline).
Breaks down runtime step-by-step and measures cold vs warm starts across resolutions.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from PIL import Image, ImageFilter

from engine.color_spatial_segmenter import ColorSpatialSegmenter
IMG_APPLE_PATH = PROJECT_ROOT / "reports" / "appl_edit_test_49" / "appl_edit_49_original.png"
IMG_FALCON_PATH = PROJECT_ROOT / "reports" / "phoenix_material_lab_65" / "m1_glass_original.png"


def profile_steps(segmenter: ColorSpatialSegmenter, image: Image.Image, target_color: str, spatial_hint: str | None = None) -> dict[str, float]:
    """Profile individual internal steps of segment()."""
    w, h = image.size
    img_rgb = image.convert("RGB") if image.mode != "RGB" else image
    img_arr = np.array(img_rgb, dtype=np.uint8)

    timings = {}

    # Step 1: Color alias resolution
    t0 = time.perf_counter()
    c_clean = target_color.strip().lower() if target_color else None
    norm_color = segmenter.COLOR_ALIASES.get(c_clean, c_clean) if c_clean else None
    timings["step1_alias_resolution_ms"] = (time.perf_counter() - t0) * 1000.0

    # Step 2: RGB to HSV
    t0 = time.perf_counter()
    h_arr, s_arr, v_arr = segmenter.rgb_to_hsv_fast(img_arr)
    timings["step2_rgb_to_hsv_ms"] = (time.perf_counter() - t0) * 1000.0

    # Step 3: Color mask & photometric dominance
    t0 = time.perf_counter()
    spec = segmenter.COLOR_RANGES[norm_color]
    h_mask = np.zeros((h, w), dtype=bool)
    for h_low, h_high in spec["h_ranges"]:
        h_mask |= (h_arr >= h_low) & (h_arr <= h_high)
    s_mask = np.ones((h, w), dtype=bool)
    if "s_min" in spec: s_mask &= (s_arr >= spec["s_min"])
    if "s_max" in spec: s_mask &= (s_arr <= spec["s_max"])
    v_mask = np.ones((h, w), dtype=bool)
    if "v_min" in spec: v_mask &= (v_arr >= spec["v_min"])
    if "v_max" in spec: v_mask &= (v_arr <= spec["v_max"])
    binary_mask = h_mask & s_mask & v_mask

    dom = spec.get("photometric_dom")
    if dom:
        r_chan = img_arr[..., 0].astype(np.float32)
        g_chan = img_arr[..., 1].astype(np.float32)
        b_chan = img_arr[..., 2].astype(np.float32)
        if dom == "red":
            binary_mask &= (r_chan > g_chan * 1.15) & (r_chan > b_chan * 1.15)
        elif dom == "green":
            binary_mask &= (g_chan > r_chan * 1.10) & (g_chan > b_chan * 1.10)
    timings["step3_color_mask_dom_ms"] = (time.perf_counter() - t0) * 1000.0

    # Step 4: Spatial hint / window
    t0 = time.perf_counter()
    spatial_mask = np.ones((h, w), dtype=bool)
    if spatial_hint:
        sh = spatial_hint.lower()
        if "center" in sh or "mitte" in sh:
            spatial_mask[:int(h * 0.15), :] = False
            spatial_mask[int(h * 0.85):, :] = False
            spatial_mask[:, :int(w * 0.15)] = False
            spatial_mask[:, int(w * 0.85):] = False
    binary_mask &= spatial_mask
    timings["step4_spatial_mask_ms"] = (time.perf_counter() - t0) * 1000.0

    # Step 5: Morphological cleanup (PIL MaxFilter/MinFilter)
    t0 = time.perf_counter()
    mask_pil = Image.fromarray((binary_mask.astype(np.uint8) * 255))
    t_conv1 = time.perf_counter()
    closed = mask_pil.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    opened = closed.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    clean_arr = np.array(opened) > 128
    timings["step5_morphology_filters_ms"] = (time.perf_counter() - t0) * 1000.0

    # Step 6: Connected component BFS
    t0 = time.perf_counter()
    final_arr = segmenter._filter_connected_components_fast(clean_arr, point_prompt=None)
    timings["step6_connected_components_ms"] = (time.perf_counter() - t0) * 1000.0

    # Step 7: Edge snapping
    t0 = time.perf_counter()
    if final_arr.any():
        final_arr = segmenter._snap_to_edges_fast(img_arr, final_arr)
    timings["step7_edge_snapping_ms"] = (time.perf_counter() - t0) * 1000.0

    # Step 8: Stats & hash
    t0 = time.perf_counter()
    active_count = int(np.sum(final_arr))
    coverage = float(active_count / (w * h))
    mask_result = Image.fromarray((final_arr.astype(np.uint8) * 255), mode="L")
    mask_bytes = mask_result.tobytes()
    det_hash = hashlib.sha256(mask_bytes).hexdigest()
    timings["step8_stats_and_hash_ms"] = (time.perf_counter() - t0) * 1000.0

    # Step 9: Overlay generation
    t0 = time.perf_counter()
    overlay_result = segmenter._create_overlay(img_rgb, final_arr, (47, 128, 237, 120))
    timings["step9_overlay_generation_ms"] = (time.perf_counter() - t0) * 1000.0

    # Step 10: Comparison grid (Lanczos resizes)
    t0 = time.perf_counter()
    grid_result = segmenter._create_comparison_grid(img_rgb, overlay_result, mask_result, "Status", coverage)
    timings["step10_comparison_grid_ms"] = (time.perf_counter() - t0) * 1000.0

    total_profiled = sum(timings.values())
    timings["total_profiled_ms"] = total_profiled
    return timings


def main():
    print("=" * 60)
    print("SPRINT 72: ROOT CAUSE ANALYSIS & PROFILING (Sprint 71 Segmenter)")
    print("=" * 60)

    segmenter = ColorSpatialSegmenter()
    apple_img = Image.open(IMG_APPLE_PATH).convert("RGB")
    falcon_img = Image.open(IMG_FALCON_PATH).convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)

    # 1. Cold start vs Warm start
    print("\n--- 1. Cold Start vs Warm Start (Apple 512x512) ---")
    t_cold_0 = time.perf_counter()
    res_cold = segmenter.segment(apple_img, target_color="red")
    t_cold = (time.perf_counter() - t_cold_0) * 1000.0
    print(f"Cold Start Latency: {t_cold:.2f} ms (reported by obj: {res_cold.elapsed_ms:.2f} ms)")

    warm_runs = []
    for _ in range(20):
        t0 = time.perf_counter()
        res = segmenter.segment(apple_img, target_color="red")
        warm_runs.append((time.perf_counter() - t0) * 1000.0)
    mean_warm = float(np.mean(warm_runs))
    min_warm = float(np.min(warm_runs))
    max_warm = float(np.max(warm_runs))
    print(f"Warm Start (20 runs): Mean = {mean_warm:.2f} ms, Min = {min_warm:.2f} ms, Max = {max_warm:.2f} ms")

    # 2. Detailed step breakdown
    print("\n--- 2. Step Breakdown (Apple 512x512) ---")
    step_times = profile_steps(segmenter, apple_img, target_color="red")
    for step, ms in step_times.items():
        pct = (ms / step_times["total_profiled_ms"]) * 100.0 if step != "total_profiled_ms" else 100.0
        print(f"  {step:32s}: {ms:7.2f} ms ({pct:5.1f} %)")

    # 3. Resolution scaling (512x512, 768x768, 1024x1024)
    print("\n--- 3. Resolution Scaling (Sprint 71 Baseline) ---")
    res_bench = {}
    for res in [512, 768, 1024]:
        scaled_img = apple_img.resize((res, res), Image.Resampling.BILINEAR)
        runs = []
        for _ in range(5):
            t0 = time.perf_counter()
            segmenter.segment(scaled_img, target_color="red")
            runs.append((time.perf_counter() - t0) * 1000.0)
        mean_res = float(np.mean(runs))
        res_bench[f"{res}x{res}"] = {
            "resolution": f"{res}x{res}",
            "pixels": res * res,
            "mean_ms": round(mean_res, 2),
            "min_ms": round(float(np.min(runs)), 2),
            "max_ms": round(float(np.max(runs)), 2),
        }
        print(f"  {res:4d}x{res:4d} ({res*res:9,d} px): {mean_res:7.2f} ms")

    # Save initial profiling results
    output_dir = PROJECT_ROOT / "reports" / "sprint_72_segmenter_optimization"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "root_cause_analysis.json", "w", encoding="utf-8") as f:
        json.dump({
            "sprint": "SPRINT_72",
            "phase": "URSACHENANALYSE",
            "cold_start_ms": round(t_cold, 2),
            "warm_start_mean_ms": round(mean_warm, 2),
            "warm_start_min_ms": round(min_warm, 2),
            "warm_start_max_ms": round(max_warm, 2),
            "step_breakdown": {k: round(v, 2) for k, v in step_times.items()},
            "resolution_scaling": res_bench,
        }, f, indent=2)

    print(f"\nProfiling saved to: {output_dir / 'root_cause_analysis.json'}")


if __name__ == "__main__":
    main()
