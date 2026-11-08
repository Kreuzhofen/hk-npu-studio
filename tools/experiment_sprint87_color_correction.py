"""
Experiment script for Sprint 87 color correction:
1. Prototype Black Leather Priming on Motif 3.
2. Prototype Apple Shadow Compensation on Motif 1 with elevated min_val (185, 195, 205).
3. Evaluate colorimetry, RGB, HSV, and contrast.
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from PIL import Image

from engine.material_priming import MaterialPreset, prime_material_chrominance

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

def lum(arr):
    return 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

def test_leather_priming():
    print("\n--- PROTOTYPING BLACK LEATHER PRIMING ---")
    orig_img = Image.open("reports/sprint_80_total_validation/images/motif3_jacket_1_original.png").convert("RGB")
    mask_img = Image.open("reports/sprint_85_material_polish/images/motif3_jacket_polished_mask.png").convert("L")

    # Define candidate black leather preset
    leather_preset = MaterialPreset(
        id="black_leather",
        display_name="Schwarzes Leder",
        hue_deg=0.0,
        sat_min=0.0,
        sat_max=6.0,
        val_multiplier=0.38,
        metallic_contrast=1.05,
        recommended_prompt=(
            "A photorealistic black leather jacket, authentic fine leather grain texture, "
            "subtle specular highlights, professional studio lighting, 8k."
        ),
        negative_prompt="red, crimson, burgundy, wine, red tint, fabric, cloth, cotton, blurry, distorted, cartoon, low quality",
        min_val=35.0,
    )

    # Temporary custom priming function using the preset parameters
    orig_arr = np.array(orig_img, dtype=np.float32)
    mask_arr = np.array(mask_img, dtype=np.float32) / 255.0
    orig_hsv = np.array(orig_img.convert("HSV"), dtype=np.float32)

    h = orig_hsv[:, :, 0]
    s = orig_hsv[:, :, 1]
    v = orig_hsv[:, :, 2]
    v_norm = v / 255.0

    # Desaturate completely to neutral gray/black
    prime_h = np.zeros_like(h)
    norm_comp = (leather_preset.min_val / 255.0) + v_norm * (1.0 - (leather_preset.min_val / 255.0))
    prime_v = np.clip(norm_comp * 255.0 * leather_preset.val_multiplier, 0.0, 255.0)
    prime_s = np.zeros_like(s) # Complete desaturation!

    hsv_primed = np.stack([prime_h, prime_s, prime_v], axis=-1).astype(np.uint8)
    rgb_primed = np.array(Image.fromarray(hsv_primed, mode="HSV").convert("RGB"), dtype=np.float32)

    alpha = mask_arr[:, :, np.newaxis]
    out_arr = orig_arr * (1.0 - alpha) + rgb_primed * alpha
    out_uint8 = np.clip(np.round(out_arr), 0, 255).astype(np.uint8)
    unmasked = mask_arr == 0.0
    out_uint8[unmasked] = np.round(orig_arr[unmasked]).astype(np.uint8)

    primed_jacket = Image.fromarray(out_uint8, mode="RGB")
    out_path = Path("reports/sprint_87_final_color_correction/experiments/prototype_leather_primed.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    primed_jacket.save(out_path)

    # Measure stats of primed jacket inside mask
    m = mask_arr > 0.0
    prim_rgb = out_uint8[m].mean(axis=0)
    prim_lum = lum(out_uint8[m]).mean()
    h_p, s_p, v_p = rgb_to_hsv_np(out_uint8.astype(float))
    prim_sat = s_p[m].mean()
    red_dom = ((out_uint8[..., 0] > out_uint8[..., 1] + 20) & (out_uint8[..., 0] > out_uint8[..., 2] + 20) & m).sum()

    print(f"Primed Jacket: RGB=[{prim_rgb[0]:.1f}, {prim_rgb[1]:.1f}, {prim_rgb[2]:.1f}], Mean L={prim_lum:.1f}, Sat={prim_sat:.3f}")
    print(f"Red dominant pixels in primed jacket: {red_dom} / {m.sum()} ({red_dom/m.sum()*100:.2f}%)")
    print(f"Saved prototype to {out_path}")

def test_apple_min_val():
    print("\n--- PROTOTYPING APPLE MIN_VAL CANDIDATES ---")
    orig_img = Image.open("reports/appl_edit_test_49/appl_edit_49_original.png").convert("RGB")
    mask_img = Image.open("reports/sprint_85_material_polish/images/motif1_apple_polished_mask.png").convert("L")

    candidates = [145.0, 185.0, 195.0, 205.0]
    out_dir = Path("reports/sprint_87_final_color_correction/experiments")
    out_dir.mkdir(parents=True, exist_ok=True)

    for mv in candidates:
        p = MaterialPreset(
            id="24k_gold",
            display_name="24k Gold",
            hue_deg=40.0,
            sat_min=130.0,
            sat_max=220.0,
            val_multiplier=1.05,
            metallic_contrast=1.05,
            recommended_prompt="",
            negative_prompt="",
            min_val=mv,
        )

        orig_arr = np.array(orig_img, dtype=np.float32)
        mask_arr = np.array(mask_img, dtype=np.float32) / 255.0
        orig_hsv = np.array(orig_img.convert("HSV"), dtype=np.float32)

        h = orig_hsv[:, :, 0]
        s = orig_hsv[:, :, 1]
        v = orig_hsv[:, :, 2]
        v_norm = v / 255.0

        target_h = float(p.hue_deg * 255.0 / 360.0)
        prime_h = np.full_like(h, target_h)

        norm_comp = (mv / 255.0) + v_norm * (1.0 - (mv / 255.0))
        prime_v = np.clip(norm_comp * 255.0 * p.val_multiplier, 0.0, 255.0)

        sat_curve = np.sin(np.pi * np.clip(prime_v / 255.0, 0.0, 1.0))
        target_s = p.sat_min + (p.sat_max - p.sat_min) * sat_curve
        prime_s = np.clip(target_s, 0.0, 255.0)

        hsv_primed = np.stack([prime_h, prime_s, prime_v], axis=-1).astype(np.uint8)
        rgb_primed = np.array(Image.fromarray(hsv_primed, mode="HSV").convert("RGB"), dtype=np.float32)

        alpha = mask_arr[:, :, np.newaxis]
        out_arr = orig_arr * (1.0 - alpha) + rgb_primed * alpha
        out_uint8 = np.clip(np.round(out_arr), 0, 255).astype(np.uint8)
        unmasked = mask_arr == 0.0
        out_uint8[unmasked] = np.round(orig_arr[unmasked]).astype(np.uint8)

        primed_apple = Image.fromarray(out_uint8, mode="RGB")
        primed_apple.save(out_dir / f"apple_primed_mv_{int(mv)}.png")

        # Check Zone V (X in [348, 382], Y in [275, 375])
        m = mask_arr > 0.0
        zv = (slice(275, 376), slice(348, 383))
        zv_mask = m[zv]
        l_img = lum(out_uint8.astype(float))
        zv_min = l_img[zv][zv_mask].min()
        zv_mean = l_img[zv][zv_mask].mean()
        lit_box = (slice(280, 381), slice(240, 311))
        lit_mean = l_img[lit_box][m[lit_box]].mean()

        print(f"min_val={mv:5.1f} | Zone V: Min L={zv_min:5.1f}, Mean L={zv_mean:5.1f} | Lit L={lit_mean:5.1f} | Delta={lit_mean - zv_mean:4.1f}")

if __name__ == "__main__":
    test_leather_priming()
    test_apple_min_val()
