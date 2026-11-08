"""
Sprint 86 - Visual Release Acceptance Audit Script
Performs deep pixel, colorimetric, and visual inspection of all 3 canonical motifs
from Sprint 85:
1. Motif 1 (Apfel): Luminance profiles, shadow vs lit flank, chromaticity, residual shadow analysis.
2. Motif 2 (Glass): Column-by-column scan for vertical lines, structure vs artifact comparison with original, pedestal/neck/wing review.
3. Motif 3 (Jacket): Complete colorimetric audit (RGB, HSV, Saturation, Red-dominance ratio) to evaluate "schwarzes Leder" prompt fulfillment.
"""

import json
from pathlib import Path
import numpy as np
from PIL import Image

def rgb_to_hsv_np(arr):
    """Normalized HSV from [0, 255] RGB numpy array."""
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
    # where deltac != 0
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

def audit():
    report_data = {}
    base_dir = Path("reports/sprint_85_material_polish/images")

    # =========================================================================
    # 1. MOTIF 1: APFEL
    # =========================================================================
    print("--- AUDITING MOTIF 1: APFEL ---")
    orig_m1 = np.array(Image.open("reports/appl_edit_test_49/appl_edit_49_original.png").convert("RGB"), dtype=float)
    prim_m1 = np.array(Image.open(base_dir / "motif1_apple_polished_primed.png").convert("RGB"), dtype=float)
    res_m1 = np.array(Image.open(base_dir / "motif1_apple_polished_htp.png").convert("RGB"), dtype=float)
    mask_m1 = np.array(Image.open(base_dir / "motif1_apple_polished_mask.png")) > 0

    l_orig_m1 = lum(orig_m1)
    l_prim_m1 = lum(prim_m1)
    l_res_m1 = lum(res_m1)

    # Lit side (left flank): X in [240, 310], Y in [280, 380]
    lit_box = (slice(280, 381), slice(240, 311))
    lit_mask = mask_m1[lit_box]
    lit_rgb = res_m1[lit_box][lit_mask].mean(axis=0)
    lit_lum = l_res_m1[lit_box][lit_mask].mean()

    # Shadow side (right flank Zone V): X in [348, 382], Y in [275, 375]
    zone_v = (slice(275, 376), slice(348, 383))
    v_mask = mask_m1[zone_v]
    v_rgb_orig = orig_m1[zone_v][v_mask].mean(axis=0)
    v_rgb_prim = prim_m1[zone_v][v_mask].mean(axis=0)
    v_rgb_res = res_m1[zone_v][v_mask].mean(axis=0)
    v_lum_orig = l_orig_m1[zone_v][v_mask].mean()
    v_lum_prim = l_prim_m1[zone_v][v_mask].mean()
    v_lum_res = l_res_m1[zone_v][v_mask].mean()
    v_lum_min = l_res_m1[zone_v][v_mask].min()

    # Overall masked apple stats
    apple_rgb = res_m1[mask_m1].mean(axis=0)
    apple_lum = l_res_m1[mask_m1].mean()
    h_res_m1, s_res_m1, v_res_m1 = rgb_to_hsv_np(res_m1)
    v_hue = h_res_m1[zone_v][v_mask].mean()
    v_sat = s_res_m1[zone_v][v_mask].mean()
    lit_hue = h_res_m1[lit_box][lit_mask].mean()
    lit_sat = s_res_m1[lit_box][lit_mask].mean()

    # Contrast ratio between lit side and shadow side
    contrast_ratio = lit_lum / max(v_lum_res, 1e-5)

    print(f"Apple Lit Side: Mean L={lit_lum:.1f}, RGB=[{lit_rgb[0]:.1f}, {lit_rgb[1]:.1f}, {lit_rgb[2]:.1f}], Hue={lit_hue:.1f}deg, Sat={lit_sat:.2f}")
    print(f"Apple Zone V:   Mean L={v_lum_res:.1f}, Min L={v_lum_min:.1f}, RGB=[{v_rgb_res[0]:.1f}, {v_rgb_res[1]:.1f}, {v_rgb_res[2]:.1f}], Hue={v_hue:.1f}deg, Sat={v_sat:.2f}")
    print(f"Contrast Ratio (Lit / Shadow): {contrast_ratio:.2f}")

    report_data["motif1_apple"] = {
        "lit_side_mean_lum": round(lit_lum, 2),
        "lit_side_mean_rgb": [round(float(x), 1) for x in lit_rgb],
        "lit_side_mean_hue_deg": round(lit_hue, 1),
        "lit_side_mean_sat": round(lit_sat, 2),
        "zone_v_orig_mean_lum": round(v_lum_orig, 2),
        "zone_v_prim_mean_lum": round(v_lum_prim, 2),
        "zone_v_res_mean_lum": round(v_lum_res, 2),
        "zone_v_res_min_lum": round(v_lum_min, 2),
        "zone_v_mean_rgb": [round(float(x), 1) for x in v_rgb_res],
        "zone_v_mean_hue_deg": round(v_hue, 1),
        "zone_v_mean_sat": round(v_sat, 2),
        "contrast_ratio_lit_to_shadow": round(contrast_ratio, 2),
        "total_apple_mean_lum": round(apple_lum, 2),
        "total_apple_mean_rgb": [round(float(x), 1) for x in apple_rgb],
    }

    # =========================================================================
    # 2. MOTIF 2: GLASSKULPTUR
    # =========================================================================
    print("\n--- AUDITING MOTIF 2: GLASSKULPTUR ---")
    orig_m2 = np.array(Image.open("reports/sprint_80_total_validation/images/motif2_glass_1_original.png").convert("RGB"), dtype=float)
    res_m2 = np.array(Image.open(base_dir / "motif2_glass_polished_htp.png").convert("RGB"), dtype=float)
    mask_m2 = np.array(Image.open(base_dir / "motif2_glass_polished_mask.png")) > 0

    l_orig_m2 = lum(orig_m2)
    l_res_m2 = lum(res_m2)

    # Scan column-by-column across wing and body (X in [190, 240], Y in [160, 270])
    seam_col_lums_orig = []
    seam_col_lums_res = []
    cols = list(range(195, 235))
    y_slice = slice(162, 270)

    for c in cols:
        col_mask = mask_m2[y_slice, c]
        if col_mask.sum() > 0:
            seam_col_lums_orig.append((c, float(l_orig_m2[y_slice, c][col_mask].mean()), float(l_orig_m2[y_slice, c][col_mask].min())))
            seam_col_lums_res.append((c, float(l_res_m2[y_slice, c][col_mask].mean()), float(l_res_m2[y_slice, c][col_mask].min())))

    # Inspect specific seam coordinate X=215, Y in [162, 269]
    seam_slice = (slice(162, 270), slice(213, 219))
    seam_mask = mask_m2[seam_slice]
    seam_lum_orig = float(l_orig_m2[seam_slice][seam_mask].mean())
    seam_lum_res = float(l_res_m2[seam_slice][seam_mask].mean())
    seam_min_res = float(l_res_m2[seam_slice][seam_mask].min())
    seam_rgb_res = res_m2[seam_slice][seam_mask].mean(axis=0)

    # Inspect Pedestal (Y in [330, 387])
    ped_mask = mask_m2 & (np.arange(512)[:, None] >= 330) & (np.arange(512)[:, None] <= 387)
    ped_rgb = res_m2[ped_mask].mean(axis=0)
    ped_lum = float(l_res_m2[ped_mask].mean())

    # Inspect Neck/Head (Y in [100, 160])
    head_mask = mask_m2 & (np.arange(512)[:, None] >= 100) & (np.arange(512)[:, None] <= 160)
    head_rgb = res_m2[head_mask].mean(axis=0)
    head_lum = float(l_res_m2[head_mask].mean())

    # Outside mask check
    outside_mask = ~mask_m2
    diff_outside_max = float(np.max(np.abs(res_m2[outside_mask] - orig_m2[outside_mask])))
    diff_table = float(np.max(np.abs(res_m2[420:, :] - orig_m2[420:, :])))

    print(f"Glass Seam (X=215): Orig Mean L={seam_lum_orig:.1f}, Res Mean L={seam_lum_res:.1f}, Min L={seam_min_res:.1f}")
    print(f"Glass Pedestal: Mean L={ped_lum:.1f}, RGB=[{ped_rgb[0]:.1f}, {ped_rgb[1]:.1f}, {ped_rgb[2]:.1f}]")
    print(f"Glass Head/Neck: Mean L={head_lum:.1f}, RGB=[{head_rgb[0]:.1f}, {head_rgb[1]:.1f}, {head_rgb[2]:.1f}]")
    print(f"Outside Max Diff: {diff_outside_max:.4f}, Table Max Diff: {diff_table:.4f}")

    report_data["motif2_glass"] = {
        "seam_orig_mean_lum": round(seam_lum_orig, 2),
        "seam_res_mean_lum": round(seam_lum_res, 2),
        "seam_res_min_lum": round(seam_min_res, 2),
        "seam_mean_rgb": [round(float(x), 1) for x in seam_rgb_res],
        "pedestal_mean_lum": round(ped_lum, 2),
        "pedestal_mean_rgb": [round(float(x), 1) for x in ped_rgb],
        "head_mean_lum": round(head_lum, 2),
        "head_mean_rgb": [round(float(x), 1) for x in head_rgb],
        "outside_max_diff": diff_outside_max,
        "table_max_diff": diff_table,
    }

    # =========================================================================
    # 3. MOTIF 3: ROTE JACKE
    # =========================================================================
    print("\n--- AUDITING MOTIF 3: ROTE JACKE ---")
    orig_m3 = np.array(Image.open("reports/sprint_80_total_validation/images/motif3_jacket_1_original.png").convert("RGB"), dtype=float)
    res_m3 = np.array(Image.open(base_dir / "motif3_jacket_polished_htp.png").convert("RGB"), dtype=float)
    mask_m3 = np.array(Image.open(base_dir / "motif3_jacket_polished_mask.png")) > 0

    l_orig_m3 = lum(orig_m3)
    l_res_m3 = lum(res_m3)

    orig_jacket_rgb = orig_m3[mask_m3].mean(axis=0)
    res_jacket_rgb = res_m3[mask_m3].mean(axis=0)
    orig_jacket_lum = float(l_orig_m3[mask_m3].mean())
    res_jacket_lum = float(l_res_m3[mask_m3].mean())

    h_orig_m3, s_orig_m3, v_orig_m3 = rgb_to_hsv_np(orig_m3)
    h_res_m3, s_res_m3, v_res_m3 = rgb_to_hsv_np(res_m3)

    orig_jacket_hue = float(h_orig_m3[mask_m3].mean())
    orig_jacket_sat = float(s_orig_m3[mask_m3].mean())
    res_jacket_hue = float(h_res_m3[mask_m3].mean())
    res_jacket_sat = float(s_res_m3[mask_m3].mean())

    # Red dominance analysis: pixels where R > G + 20 and R > B + 20
    red_dominant_orig = ((orig_m3[..., 0] > orig_m3[..., 1] + 20) & (orig_m3[..., 0] > orig_m3[..., 2] + 20)) & mask_m3
    red_dominant_res = ((res_m3[..., 0] > res_m3[..., 1] + 20) & (res_m3[..., 0] > res_m3[..., 2] + 20)) & mask_m3

    total_jacket_px = int(mask_m3.sum())
    red_px_orig = int(red_dominant_orig.sum())
    red_px_res = int(red_dominant_res.sum())
    red_ratio_orig = red_px_orig / total_jacket_px
    red_ratio_res = red_px_res / total_jacket_px

    # Blackness check: For true black leather, expect R, G, B < 60, Saturation < 0.25
    black_pixels = ((res_m3[..., 0] < 60) & (res_m3[..., 1] < 60) & (res_m3[..., 2] < 60)) & mask_m3
    black_ratio = float(black_pixels.sum()) / total_jacket_px

    # Biological tissue protection check (Face/Hair: Y < 516)
    face_mask = np.zeros(orig_m3.shape[:2], dtype=bool)
    face_mask[:516, :] = True
    face_diff = float(np.max(np.abs(res_m3[face_mask] - orig_m3[face_mask])))
    face_overlap = int((mask_m3 & face_mask).sum())

    # Hand protection check (right hand around bottom left X in [250, 420], Y in [1700, 2100])
    hand_box = (slice(1700, 2100), slice(250, 420))
    hand_overlap = int(mask_m3[hand_box].sum())

    # Zipper / Seam detail check (central line around X in [800, 880], Y in [1000, 1800])
    zipper_box = (slice(1000, 1800), slice(800, 880))
    zipper_diff = float(np.mean(np.abs(res_m3[zipper_box] - orig_m3[zipper_box])))

    outside_jacket = ~mask_m3
    outside_jacket_diff = float(np.max(np.abs(res_m3[outside_jacket] - orig_m3[outside_jacket])))

    print(f"Jacket Original RGB: [{orig_jacket_rgb[0]:.1f}, {orig_jacket_rgb[1]:.1f}, {orig_jacket_rgb[2]:.1f}], Mean L={orig_jacket_lum:.1f}, Sat={orig_jacket_sat:.2f}")
    print(f"Jacket Result RGB:   [{res_jacket_rgb[0]:.1f}, {res_jacket_rgb[1]:.1f}, {res_jacket_rgb[2]:.1f}], Mean L={res_jacket_lum:.1f}, Sat={res_jacket_sat:.2f}")
    print(f"Red Dominance Ratio: Orig={red_ratio_orig*100:.1f}%, Res={red_ratio_res*100:.1f}%")
    print(f"True Black Ratio (RGB<60): {black_ratio*100:.1f}%")
    print(f"Face Overlap: {face_overlap} px, Face Diff: {face_diff:.4f}")
    print(f"Outside Jacket Max Diff: {outside_jacket_diff:.4f}")

    report_data["motif3_jacket"] = {
        "orig_rgb": [round(float(x), 1) for x in orig_jacket_rgb],
        "orig_lum": round(orig_jacket_lum, 2),
        "orig_sat": round(orig_jacket_sat, 2),
        "res_rgb": [round(float(x), 1) for x in res_jacket_rgb],
        "res_lum": round(res_jacket_lum, 2),
        "res_sat": round(res_jacket_sat, 2),
        "red_dominance_orig_percent": round(red_ratio_orig * 100, 2),
        "red_dominance_res_percent": round(red_ratio_res * 100, 2),
        "black_ratio_percent": round(black_ratio * 100, 2),
        "face_overlap_pixels": face_overlap,
        "face_max_diff": face_diff,
        "outside_max_diff": outside_jacket_diff,
        "zipper_mean_delta": round(zipper_diff, 2),
    }

    # Save metrics JSON
    out_json = Path("reports/sprint_86_visual_release_acceptance/release_acceptance_metrics.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"\nAudit complete. Metrics saved to {out_json}")

if __name__ == "__main__":
    audit()
