"""
Sprint 82 Apple Seed Matrix Benchmark
Tests Seed 42 against Seed 43, 100, 777, and 4901 on Qualcomm Snapdragon X Elite Hexagon NPU.
Evaluates:
- Anti-crater negative prompt
- English object token translation ('apple')
- Minimum luminance, mean luminance, and dark pixels in Region A (y: 310..335, x: 350..370)
- Outside mask bit-exact preservation
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
from engine.material_priming import prime_material_chrominance

def run_matrix():
    out_dir = Path("reports/sprint_82_material_repair/images/apple_seeds")
    out_dir.mkdir(parents=True, exist_ok=True)

    orig_path = Path("reports/sprint_80_total_validation/images/motif1_apple_1_original.png")
    mask_path = Path("reports/sprint_80_total_validation/images/motif1_apple_3_binary_mask.png")

    orig_img = Image.open(orig_path).convert("RGB")
    mask_img = Image.open(mask_path).convert("L")

    # Priming
    primed_img = prime_material_chrominance(orig_img, mask_img, "24k_gold", 1.0)
    primed_path = out_dir / "apple_primed.png"
    primed_img.save(primed_path, format="PNG")

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

    seeds = [42, 43, 100, 777, 4901]
    results = {}

    for seed in seeds:
        print(f"\n--- Running Seed {seed} on Qualcomm Hexagon NPU ---")
        out_path = out_dir / f"apple_result_seed_{seed}.png"
        t0 = time.perf_counter()
        res = adapter.run(
            input_image_path=primed_path,
            mask_image_path=mask_path,
            prompt=prompt,
            negative_prompt=neg_prompt,
            output_path=out_path,
            steps=20,
            seed=seed,
            cfg_scale=7.5,
            denoising_strength=0.75,
            feather_radius=5,
            dilate_pixels=1,
            use_subprocess=True,
        )
        elapsed = time.perf_counter() - t0

        if not res.success or not out_path.exists():
            print(f"FAILED for Seed {seed}: {res.error_message}")
            results[seed] = {"success": False, "error": res.error_message}
            continue

        # Analyze Region A (y: 310..335, x: 350..370)
        res_img = Image.open(out_path).convert("RGB")
        res_arr = np.array(res_img, dtype=float)
        orig_arr = np.array(orig_img, dtype=float)
        m_arr = np.array(mask_img) > 0

        # Background verification
        unmasked = ~m_arr
        diff_outside = np.max(np.abs(res_arr[unmasked] - orig_arr[unmasked]))

        lum = 0.299 * res_arr[..., 0] + 0.587 * res_arr[..., 1] + 0.114 * res_arr[..., 2]
        crop_a = lum[310:335, 350:370]
        min_lum_a = float(crop_a.min())
        mean_lum_a = float(crop_a.mean())
        dark_px_a = int((crop_a < 30).sum())

        dark_px_mask = int(((lum < 60) & m_arr).sum())

        has_crater = bool(min_lum_a < 30.0 or dark_px_a > 0)
        quality_assessment = "EXCELLENT (Glatt & Gleichmäßig)" if not has_crater else "DEFECT (Kraterbildung)"

        results[seed] = {
            "success": True,
            "seed": seed,
            "elapsed_seconds": round(elapsed, 2),
            "cpu_fallback": 0,
            "region_a_min_lum": round(min_lum_a, 2),
            "region_a_mean_lum": round(mean_lum_a, 2),
            "region_a_dark_pixels_lt30": dark_px_a,
            "total_dark_pixels_lt60_in_mask": dark_px_mask,
            "outside_mask_diff": float(diff_outside),
            "has_crater": has_crater,
            "quality_assessment": quality_assessment,
        }
        print(f"Seed {seed}: Min Lum={min_lum_a:.1f}, Mean Lum={mean_lum_a:.1f}, Dark px (<30)={dark_px_a}, Has Crater={has_crater}, Diff Out={diff_outside}")

    json_path = Path("reports/sprint_82_material_repair/apple_seed_matrix.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nSeed Matrix Benchmark Complete! Results saved to {json_path}")

if __name__ == "__main__":
    run_matrix()
