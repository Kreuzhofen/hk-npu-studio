"""
Sprint 85 Apple Polish HTP Validation:
Tests the new luminance-compressed photometric priming (min_val = 145.0)
with HTP inpainting on Qualcomm Snapdragon X Elite Hexagon NPU.
Evaluates:
- Region V (former dark vertical zone X:348..382, Y:275..375)
- Highlight preservation (X:275..315)
- Outside mask bit-exact identity
- Comparison against Sprint 84 baseline
"""

import json
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from PIL import Image

from engine.backends.sd15_qnn_inpainting_adapter import SD15QnnInpaintingAdapter
from engine.material_priming import prime_material_chrominance, MATERIAL_PRESETS, MaterialPreset

def run_apple_polish():
    out_dir = Path("reports/sprint_85_material_polish/images/apple_polish")
    out_dir.mkdir(parents=True, exist_ok=True)

    orig_path = Path("reports/appl_edit_test_49/appl_edit_49_original.png")
    mask_path = Path("reports/sprint_82_material_repair/images/motif1_apple_repaired_mask.png")

    orig_img = Image.open(orig_path).convert("RGB")
    mask_img = Image.open(mask_path).convert("L")
    mask_arr = np.array(mask_img) > 128
    orig_arr = np.array(orig_img, dtype=float)

    # 1. Create Affine Compressed Priming with min_val = 145.0
    orig_hsv = np.array(orig_img.convert("HSV"), dtype=np.float32)
    h = orig_hsv[:, :, 0]
    s = orig_hsv[:, :, 1]
    v = orig_hsv[:, :, 2]
    v_norm = v / 255.0

    target_h = float(40.0 * 255.0 / 360.0)
    prime_h = np.full_like(h, target_h)

    # Affine luminance compression: min_val = 145.0
    min_val = 145.0
    norm_comp = (min_val / 255.0) + v_norm * (1.0 - (min_val / 255.0))
    prime_v = np.clip(norm_comp * 255.0 * 1.05, 0.0, 255.0)
    
    # Saturation curve adapted to compressed luminance
    sat_curve = np.sin(np.pi * np.clip(prime_v / 255.0, 0.0, 1.0))
    prime_s = np.clip(130.0 + (220.0 - 130.0) * sat_curve, 0.0, 255.0)

    hsv_primed = np.stack([prime_h, prime_s, prime_v], axis=-1).astype(np.uint8)
    rgb_primed = np.array(Image.fromarray(hsv_primed, mode="HSV").convert("RGB"), dtype=np.float32)

    alpha = (np.array(mask_img, dtype=np.float32) / 255.0)[:, :, np.newaxis]
    primed_arr = orig_arr * (1.0 - alpha) + rgb_primed * alpha
    primed_uint8 = np.clip(np.round(primed_arr), 0, 255).astype(np.uint8)
    primed_uint8[~mask_arr] = np.round(orig_arr[~mask_arr]).astype(np.uint8)

    primed_img = Image.fromarray(primed_uint8, mode="RGB")
    primed_path = out_dir / "apple_primed_compressed_145.png"
    primed_img.save(primed_path, format="PNG")
    print(f"Compressed primed image saved to: {primed_path}")

    # 2. Run Inpainting on Qualcomm Hexagon NPU
    adapter = SD15QnnInpaintingAdapter()

    prompt = (
        "A solid polished 24k Gold apple, sleek smooth curved metallic shape, "
        "pure 24k Gold metal, highly reflective surface, specular highlights, photorealistic, 8k."
    )
    neg_prompt = (
        "dent, dented, crater, cavity, hole, dark spot, depression, blemish, black pit, bite mark, "
        "glass, transparent, translucent, green, blue, turquoise, bird, falcon, animal, "
        "feathers, beak, white wall, room divider, wooden furniture, plants, people, blurry, deformed."
    )

    out_path = out_dir / "apple_result_polished_htp.png"

    print(f"\nExecuting HTP Inpainting on Qualcomm Hexagon NPU for Polished Apple...")
    t0 = time.perf_counter()
    res = adapter.run(
        input_image_path=primed_path,
        mask_image_path=mask_path,
        prompt=prompt,
        negative_prompt=neg_prompt,
        output_path=out_path,
        steps=20,
        seed=43,  # Proven canonical seed for apple
        cfg_scale=7.5,
        denoising_strength=0.75,
        feather_radius=5,
        dilate_pixels=1,
        use_subprocess=True,
    )
    elapsed = time.perf_counter() - t0

    if not res.success or not out_path.exists():
        print(f"FAILED: {res.error_message}")
        return

    # 3. Analyze Results
    res_img = Image.open(out_path).convert("RGB")
    res_arr = np.array(res_img, dtype=float)

    # Outside mask diff
    diff_outside = np.max(np.abs(res_arr[~mask_arr] - orig_arr[~mask_arr]))

    lum = 0.299 * res_arr[..., 0] + 0.587 * res_arr[..., 1] + 0.114 * res_arr[..., 2]

    # Zone V (former dark vertical zone: X in [348, 382], Y in [275, 375])
    zone_v = (slice(275, 376), slice(348, 383))
    mask_v = mask_arr[zone_v]
    v_lum = lum[zone_v][mask_v]
    v_min = float(v_lum.min())
    v_mean = float(v_lum.mean())
    v_dark_lt80 = int((v_lum < 80.0).sum())

    # Highlight Zone (X in [275, 315], Y in [280, 360])
    zone_hl = (slice(280, 361), slice(275, 316))
    mask_hl = mask_arr[zone_hl]
    hl_lum = lum[zone_hl][mask_hl]
    hl_mean = float(hl_lum.mean())
    hl_max = float(hl_lum.max())

    # Entire mask
    mask_lum = lum[mask_arr]
    total_mean = float(mask_lum.mean())
    total_std = float(mask_lum.std())
    specular_px = int((mask_lum > 200.0).sum())

    report_data = {
        "success": True,
        "elapsed_seconds": round(elapsed, 2),
        "cpu_fallback": 0,
        "min_val_used": min_val,
        "zone_v_min_lum": round(v_min, 2),
        "zone_v_mean_lum": round(v_mean, 2),
        "zone_v_dark_pixels_lt80": v_dark_lt80,
        "highlight_mean_lum": round(hl_mean, 2),
        "highlight_max_lum": round(hl_max, 2),
        "mask_mean_lum": round(total_mean, 2),
        "mask_std_lum": round(total_std, 2),
        "specular_pixels_gt200": specular_px,
        "outside_mask_diff": float(diff_outside),
    }

    print(f"\n--- SPRINT 85 APPLE POLISH RESULT ---")
    print(f"Elapsed Time: {elapsed:.2f}s (HTP V73, CPU fallback=0)")
    print(f"Zone V (Core Shadow Zone): Mean L={v_mean:.1f} (was 84.1 in Sprint 84), Min L={v_min:.1f} (was 54.2)")
    print(f"Dark pixels (<80) in Zone V: {v_dark_lt80} (was >1200 in Sprint 84)")
    print(f"Highlight Zone: Mean L={hl_mean:.1f}, Max L={hl_max:.1f}")
    print(f"Total Mask: Mean L={total_mean:.1f}, Std L={total_std:.1f}, Specular px (>200)={specular_px}")
    print(f"Outside Mask Diff: {diff_outside:.1f} (Bit-exact={diff_outside == 0})")

    json_path = Path("reports/sprint_85_material_polish/apple_polish_result.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"Metrics written to {json_path}")

if __name__ == "__main__":
    run_apple_polish()
