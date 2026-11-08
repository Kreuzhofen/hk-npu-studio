"""
Test and benchmark optimized ColorSpatialSegmenter against Sprint 71 baseline.
Verifies latency, determinism, and test case compliance.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.color_spatial_segmenter import ColorSpatialSegmenter, SegmentResult

# Optimized implementations:
def dilate_3x3_np(arr: np.ndarray) -> np.ndarray:
    p = np.pad(arr, 1, mode="edge")
    h, w = arr.shape
    res = p[1:h+1, 1:w+1].copy()
    res |= p[0:h, 1:w+1]
    res |= p[2:h+2, 1:w+1]
    res |= p[1:h+1, 0:w]
    res |= p[1:h+1, 2:w+2]
    res |= p[0:h, 0:w]
    res |= p[0:h, 2:w+2]
    res |= p[2:h+2, 0:w]
    res |= p[2:h+2, 2:w+2]
    return res

def erode_3x3_np(arr: np.ndarray) -> np.ndarray:
    return ~dilate_3x3_np(~arr)

def morph_close_open_fast(binary_mask: np.ndarray) -> np.ndarray:
    # Closing (Max5 then Min5) = 2 dilations, 2 erosions
    closed = dilate_3x3_np(dilate_3x3_np(binary_mask))
    closed = erode_3x3_np(erode_3x3_np(closed))
    # Opening (Min3 then Max3) = 1 erosion, 1 dilation
    opened = erode_3x3_np(closed)
    clean_arr = dilate_3x3_np(opened)
    return clean_arr

def snap_to_edges_optimized(rgb_arr: np.ndarray, mask_arr: np.ndarray) -> np.ndarray:
    # Exact float grayscale matching original
    gray = (0.299 * rgb_arr[..., 0] + 0.587 * rgb_arr[..., 1] + 0.114 * rgb_arr[..., 2]).astype(np.float32)
    gx = np.zeros_like(gray)
    gy = np.zeros_like(gray)
    gx[:, 1:-1] = np.abs(gray[:, 2:] - gray[:, :-2]) * 0.5
    gy[1:-1, :] = np.abs(gray[2:, :] - gray[:-2, :]) * 0.5
    strong_edge = (gx * gx + gy * gy) > 1600.0  # Exact match for hypot > 40.0
    dilated = dilate_3x3_np(mask_arr)
    return mask_arr | (dilated & ~strong_edge)


def main():
    print("Verifying morphology exact match on real Apple image...")
    apple_img = Image.open(PROJECT_ROOT / "reports" / "appl_edit_test_49" / "appl_edit_49_original.png")
    seg = ColorSpatialSegmenter()

    w, h = apple_img.size
    img_arr = np.array(apple_img, dtype=np.uint8)
    h_arr, s_arr, v_arr = seg.rgb_to_hsv_fast(img_arr)
    spec = seg.COLOR_RANGES["red"]
    h_mask = (h_arr <= 16.0) | (h_arr >= 344.0)
    s_mask = s_arr >= spec["s_min"]
    v_mask = v_arr >= spec["v_min"]
    b_mask = h_mask & s_mask & v_mask
    r_chan = img_arr[..., 0].astype(np.float32)
    g_chan = img_arr[..., 1].astype(np.float32)
    b_chan = img_arr[..., 2].astype(np.float32)
    b_mask &= (r_chan > g_chan * 1.15) & (r_chan > b_chan * 1.15)

    # PIL version
    t0 = time.perf_counter()
    mask_pil = Image.fromarray((b_mask.astype(np.uint8) * 255))
    closed = mask_pil.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    opened = closed.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    clean_pil = np.array(opened) > 128
    t_pil = (time.perf_counter() - t0) * 1000.0

    # NumPy version
    t0 = time.perf_counter()
    clean_np = morph_close_open_fast(b_mask)
    t_np = (time.perf_counter() - t0) * 1000.0

    print(f"PIL Morphology Time:   {t_pil:.2f} ms")
    print(f"NumPy Morphology Time: {t_np:.2f} ms")
    print(f"Exact match on real Apple: {np.array_equal(clean_pil, clean_np)}")
    print(f"Speedup: {t_pil / t_np:.1f}x")

    # Edge snapping
    t0 = time.perf_counter()
    snap_orig = seg._snap_to_edges_fast(img_arr, clean_pil)
    t_snap_orig = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    snap_new = snap_to_edges_optimized(img_arr, clean_np)
    t_snap_new = (time.perf_counter() - t0) * 1000.0

    print(f"\nOriginal Edge Snap Time:  {t_snap_orig:.2f} ms")
    print(f"Optimized Edge Snap Time: {t_snap_new:.2f} ms")
    print(f"Exact match on Edge Snap: {np.array_equal(snap_orig, snap_new)}")
    print(f"Speedup: {t_snap_orig / t_snap_new:.1f}x")


if __name__ == "__main__":
    main()
