"""
Test Sprint 87 NPU Candidates using controller.execute:
1. Test Black Leather Priming on Hexagon NPU (Motif 3)
2. Test Apple with min_val=195.0 on Hexagon NPU (Motif 1) across Seeds 42, 43, 100, 777
"""

import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from PIL import Image

from controllers.prompt_edit_controller import PromptEditController
from engine.material_priming import MaterialPreset, prime_material_chrominance

def lum(arr):
    return 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

def rgb_to_hsv_np(arr):
    r = arr[..., 0] / 255.0
    g = arr[..., 1] / 255.0
    b = arr[..., 2] / 255.0
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    v = maxc
    deltac = maxc - minc
    s = np.zeros_like(v)
    non_zero = maxc != 0
    s[non_zero] = deltac[non_zero] / maxc[non_zero]
    h = np.zeros_like(v)
    idx_r = (maxc == r) & (deltac != 0)
    idx_g = (maxc == g) & (deltac != 0)
    idx_b = (maxc == b) & (deltac != 0)
    h[idx_r] = ((g[idx_r] - b[idx_r]) / deltac[idx_r]) % 6.0
    h[idx_g] = ((b[idx_g] - r[idx_g]) / deltac[idx_g]) + 2.0
    h[idx_b] = ((r[idx_b] - g[idx_b]) / deltac[idx_b]) + 4.0
    h = (h * 60.0) % 360.0
    return h, s, v

def run_tests():
    controller = PromptEditController()
    out_dir = Path("reports/sprint_87_final_color_correction/experiments")
    out_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # A. JACKET TEST
    # -------------------------------------------------------------
    print("\n=======================================================")
    print("TESTING MOTIF 3 (JACKET) ON QUALCOMM HEXAGON NPU")
    print("=======================================================")

    orig_j_path = Path("reports/sprint_80_total_validation/images/motif3_jacket_1_original.png")
    mask_j_path = Path("reports/sprint_85_material_polish/images/motif3_jacket_polished_mask.png")
    orig_j_img = Image.open(orig_j_path).convert("RGB")
    mask_j_img = Image.open(mask_j_path).convert("L")

    # Generate desaturated and darkened primed jacket
    orig_j_arr = np.array(orig_j_img, dtype=np.float32)
    mask_j_arr = np.array(mask_j_img, dtype=np.float32) / 255.0
    orig_j_hsv = np.array(orig_j_img.convert("HSV"), dtype=np.float32)

    v = orig_j_hsv[:, :, 2]
    v_norm = v / 255.0
    norm_comp = (30.0 / 255.0) + v_norm * (1.0 - (30.0 / 255.0))
    prime_v = np.clip(norm_comp * 255.0 * 0.28, 0.0, 255.0)
    prime_h = np.zeros_like(v)
    prime_s = np.zeros_like(v)

    hsv_primed = np.stack([prime_h, prime_s, prime_v], axis=-1).astype(np.uint8)
    rgb_primed = np.array(Image.fromarray(hsv_primed, mode="HSV").convert("RGB"), dtype=np.float32)

    alpha = mask_j_arr[:, :, np.newaxis]
    primed_j_arr = orig_j_arr * (1.0 - alpha) + rgb_primed * alpha
    primed_j_uint8 = np.clip(np.round(primed_j_arr), 0, 255).astype(np.uint8)
    unmasked = mask_j_arr == 0.0
    primed_j_uint8[unmasked] = np.round(orig_j_arr[unmasked]).astype(np.uint8)

    primed_j_img = Image.fromarray(primed_j_uint8, mode="RGB")
    primed_j_save = out_dir / "motif3_jacket_primed_black.png"
    primed_j_img.save(primed_j_save)

    jacket_out = out_dir / "motif3_jacket_htp_black_leather.png"
    prompt_j = "A photorealistic black leather jacket, authentic fine leather grain texture, subtle specular highlights, professional studio lighting, 8k."
    neg_j = "red, crimson, burgundy, wine, red tint, fabric, cloth, cotton, blurry, distorted, cartoon, low quality"

    t0 = time.perf_counter()
    res_backend = controller.inpainting_controller._run_product_path(
        input_image_path=primed_j_save,
        mask_image_path=mask_j_path,
        prompt=prompt_j,
        output_path=jacket_out,
        negative_prompt=neg_j,
        steps=20,
        seed=20260830,
        cfg_scale=7.5,
        denoising_strength=0.80,
        feather_radius=5,
        dilate_pixels=1,
        progress=lambda stage, pct, msg: None,
    )
    el_j = time.perf_counter() - t0
    print(f"Jacket HTP inpaint completed in {el_j:.2f}s (Success={res_backend.success})")

    res_j_img = Image.open(jacket_out).convert("RGB")
    res_j_arr = np.array(res_j_img, dtype=float)
    m_j = mask_j_arr > 0.0
    j_rgb = res_j_arr[m_j].mean(axis=0)
    j_lum = float(lum(res_j_arr[m_j]).mean())
    h_j, s_j, v_j = rgb_to_hsv_np(res_j_arr)
    j_sat = float(s_j[m_j].mean())

    red_dom_j = ((res_j_arr[..., 0] > res_j_arr[..., 1] + 20) &
                 (res_j_arr[..., 0] > res_j_arr[..., 2] + 20) & m_j).sum()
    red_ratio_j = red_dom_j / m_j.sum()
    black_px = ((res_j_arr[..., 0] < 60) & (res_j_arr[..., 1] < 60) & (res_j_arr[..., 2] < 60) & m_j).sum()
    black_ratio = black_px / m_j.sum()

    face_diff = float(np.max(np.abs(res_j_arr[:516, :] - orig_j_arr[:516, :])))
    outside_diff = float(np.max(np.abs(res_j_arr[unmasked] - orig_j_arr[unmasked])))

    print(f"Jacket Result RGB: [{j_rgb[0]:.1f}, {j_rgb[1]:.1f}, {j_rgb[2]:.1f}], Mean L={j_lum:.1f}, Sat={j_sat:.3f}")
    print(f"Red Dominance: {red_ratio_j*100:.2f}% (was 97.64% in Sp.86!)")
    print(f"True Black (RGB<60): {black_ratio*100:.2f}% (was 4.46% in Sp.86!)")
    print(f"Face Diff: {face_diff:.4f}, Outside Diff: {outside_diff:.4f}")

    # -------------------------------------------------------------
    # B. APPLE TEST
    # -------------------------------------------------------------
    print("\n=======================================================")
    print("TESTING MOTIF 1 (APPLE min_val=195.0) ON QUALCOMM HEXAGON NPU")
    print("=======================================================")

    orig_a_path = Path("reports/appl_edit_test_49/appl_edit_49_original.png")
    mask_a_path = Path("reports/sprint_85_material_polish/images/motif1_apple_polished_mask.png")
    orig_a_img = Image.open(orig_a_path).convert("RGB")
    mask_a_img = Image.open(mask_a_path).convert("L")

    orig_a_arr = np.array(orig_a_img, dtype=np.float32)
    mask_a_arr = np.array(mask_a_img, dtype=np.float32) / 255.0
    orig_a_hsv = np.array(orig_a_img.convert("HSV"), dtype=np.float32)

    v_a = orig_a_hsv[:, :, 2]
    v_norm_a = v_a / 255.0
    norm_comp_a = (195.0 / 255.0) + v_norm_a * (1.0 - (195.0 / 255.0))
    prime_v_a = np.clip(norm_comp_a * 255.0 * 1.05, 0.0, 255.0)

    prime_h_a = np.full_like(v_a, float(40.0 * 255.0 / 360.0))
    sat_curve_a = np.sin(np.pi * np.clip(prime_v_a / 255.0, 0.0, 1.0))
    prime_s_a = np.clip(130.0 + (220.0 - 130.0) * sat_curve_a, 0.0, 255.0)

    hsv_primed_a = np.stack([prime_h_a, prime_s_a, prime_v_a], axis=-1).astype(np.uint8)
    rgb_primed_a = np.array(Image.fromarray(hsv_primed_a, mode="HSV").convert("RGB"), dtype=np.float32)

    alpha_a = mask_a_arr[:, :, np.newaxis]
    primed_a_arr = orig_a_arr * (1.0 - alpha_a) + rgb_primed_a * alpha_a
    primed_a_uint8 = np.clip(np.round(primed_a_arr), 0, 255).astype(np.uint8)
    unmasked_a = mask_a_arr == 0.0
    primed_a_uint8[unmasked_a] = np.round(orig_a_arr[unmasked_a]).astype(np.uint8)

    primed_a_img = Image.fromarray(primed_a_uint8, mode="RGB")
    primed_a_save = out_dir / "motif1_apple_primed_mv195.png"
    primed_a_img.save(primed_a_save)

    apple_seeds = [43, 42, 100, 777]
    prompt_a = (
        "A solid polished 24k gold apple, sleek smooth curved metallic shape, "
        "pure 24k yellow gold metal, highly reflective surface, specular highlights, photorealistic, 8k."
    )
    neg_a = (
        "seam, black line, dark slit, crease, shadow line, border line, gap, crack, rift, "
        "dent, dented, crater, cavity, hole, dark spot, depression, blemish, black pit, bite mark, "
        "glass, transparent, translucent, green, blue, turquoise, blurry, deformed"
    )

    apple_results = {}
    for s in apple_seeds:
        out_a_p = out_dir / f"motif1_apple_htp_mv195_seed_{s}.png"
        t0 = time.perf_counter()
        res_backend_a = controller.inpainting_controller._run_product_path(
            input_image_path=primed_a_save,
            mask_image_path=mask_a_path,
            prompt=prompt_a,
            output_path=out_a_p,
            negative_prompt=neg_a,
            steps=20,
            seed=s,
            cfg_scale=7.5,
            denoising_strength=0.75,
            feather_radius=5,
            dilate_pixels=1,
            progress=lambda stage, pct, msg: None,
        )
        el_a = time.perf_counter() - t0

        res_a_img = Image.open(out_a_p).convert("RGB")
        res_a_arr = np.array(res_a_img, dtype=float)
        l_res_a = lum(res_a_arr)

        y_eq = slice(300, 341)
        m_a = mask_a_arr > 0.0
        val_353 = l_res_a[y_eq, 353][m_a[y_eq, 353]].mean()
        val_300 = l_res_a[y_eq, 300][m_a[y_eq, 300]].mean()

        zv = (slice(275, 376), slice(348, 383))
        zv_min = l_res_a[zv][m_a[zv]].min()
        zv_mean = l_res_a[zv][m_a[zv]].mean()
        zv_lt80 = int((l_res_a[zv][m_a[zv]] < 80.0).sum())

        outside_diff_a = float(np.max(np.abs(res_a_arr[unmasked_a] - orig_a_arr[unmasked_a])))

        apple_results[s] = {
            "elapsed_s": round(el_a, 2),
            "zone_v_min_lum": round(zv_min, 1),
            "zone_v_mean_lum": round(zv_mean, 1),
            "zone_v_dark_lt80": zv_lt80,
            "x353_lum": round(val_353, 1),
            "x300_lum": round(val_300, 1),
            "contrast_ratio": round(float(val_300) / max(float(val_353), 1e-5), 2),
            "outside_diff": outside_diff_a,
        }
        print(f"Apple Seed {s:3d} ({el_a:.1f}s): Zone V Mean L={zv_mean:.1f}, Min L={zv_min:.1f}, X=353 L={val_353:.1f} (vs X=300 L={val_300:.1f}) | Contrast={apple_results[s]['contrast_ratio']} | Diff Outside={outside_diff_a:.4f}")

    with open(out_dir / "npu_candidate_results.json", "w", encoding="utf-8") as f:
        json.dump({"jacket": {"mean_rgb": [round(float(x), 1) for x in j_rgb], "mean_lum": round(j_lum, 1), "sat": round(j_sat, 3), "red_ratio": round(red_ratio_j, 4), "black_ratio": round(black_ratio, 4)}, "apple_seeds": apple_results}, f, indent=2)
    print("\nCandidate testing complete! Saved to npu_candidate_results.json")

if __name__ == "__main__":
    run_tests()
