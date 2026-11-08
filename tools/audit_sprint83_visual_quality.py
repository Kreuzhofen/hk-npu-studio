"""
Audit script for Sprint 83: Visual Quality and Release Audit.
Read-only analysis across the 3 canonical motifs:
- Motif 1: Apple (Original, Seed 42, Seed 43, seed matrix, crater freedom, highlights, smoothness)
- Motif 2: Glass Sculpture (Pedestal, neck, torso, wings, beak, contour seams, table & room protection)
- Motif 3: Red Jacket (Leather grain, seams, zipper, biological protection, zero leakage)
Pure numpy and PIL implementation without external scientific libraries.
"""

import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

def dilate_mask_pil(mask_bool: np.ndarray, radius: int = 5) -> np.ndarray:
    mask_img = Image.fromarray((mask_bool * 255).astype(np.uint8))
    size = radius * 2 + 1
    dilated = mask_img.filter(ImageFilter.MaxFilter(size=size))
    return np.array(dilated) > 128

def erode_mask_pil(mask_bool: np.ndarray, radius: int = 2) -> np.ndarray:
    mask_img = Image.fromarray((mask_bool * 255).astype(np.uint8))
    size = radius * 2 + 1
    eroded = mask_img.filter(ImageFilter.MinFilter(size=size))
    return np.array(eroded) > 128

def laplacian_filter_pil(img_array: np.ndarray) -> np.ndarray:
    pad = np.pad(img_array, 1, mode='edge')
    lap = -4.0 * img_array + pad[:-2, 1:-1] + pad[2:, 1:-1] + pad[1:-1, :-2] + pad[1:-1, 2:]
    return lap

def analyze_motif1_apple():
    print("=== MOTIF 1: APPLE VISUAL QUALITY ===")
    orig_path = Path("reports/appl_edit_test_49/appl_edit_49_original.png")
    mask_path = Path("reports/sprint_82_material_repair/images/motif1_apple_repaired_mask.png")
    s42_path = Path("reports/sprint_82_material_repair/images/apple_seeds/apple_result_seed_42.png")
    s43_path = Path("reports/sprint_82_material_repair/images/apple_seeds/apple_result_seed_43.png")
    rep_htp_path = Path("reports/sprint_82_material_repair/images/motif1_apple_repaired_htp.png")

    orig = np.array(Image.open(orig_path).convert("RGB"), dtype=np.float32)
    mask = np.array(Image.open(mask_path).convert("L"), dtype=np.uint8) > 128
    s42 = np.array(Image.open(s42_path).convert("RGB"), dtype=np.float32)
    s43 = np.array(Image.open(s43_path).convert("RGB"), dtype=np.float32)
    rep_htp = np.array(Image.open(rep_htp_path).convert("RGB"), dtype=np.float32)

    def lum(rgb):
        return 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]

    lum_orig = lum(orig)
    lum_s42 = lum(s42)
    lum_s43 = lum(s43)
    lum_rep = lum(rep_htp)

    # Region A: [310:335, 350:370]
    reg_a = (slice(310, 335), slice(350, 370))

    print(f"Region A (Former Crater Zone):")
    for name, l in [("Original", lum_orig), ("Seed 42", lum_s42), ("Seed 43", lum_s43), ("Repaired HTP (Seed 43)", lum_rep)]:
        sub = l[reg_a]
        print(f"  {name:25s}: min={sub.min():6.2f}, mean={sub.mean():6.2f}, max={sub.max():6.2f}, pixels<30={(sub < 30).sum():3d}, pixels<60={(sub < 60).sum():3d}")

    # Full mask area statistics
    print(f"\nFull Mask Area ({mask.sum()} px):")
    for name, l, rgb in [("Original", lum_orig, orig), ("Seed 42", lum_s42, s42), ("Seed 43", lum_s43, s43), ("Repaired HTP", lum_rep, rep_htp)]:
        sub_l = l[mask]
        sub_rgb = rgb[mask]
        specular = (sub_l > 200).sum()
        mean_r = sub_rgb[:, 0].mean()
        mean_g = sub_rgb[:, 1].mean()
        mean_b = sub_rgb[:, 2].mean()
        print(f"  {name:25s}: lum_mean={sub_l.mean():6.2f}, lum_std={sub_l.std():6.2f}, spec_px(>200)={specular:5d} ({specular/mask.sum()*100:4.1f}%), Mean RGB=[{mean_r:.1f}, {mean_g:.1f}, {mean_b:.1f}]")

    # Outside mask preservation
    for name, rgb in [("Seed 42", s42), ("Seed 43", s43), ("Repaired HTP", rep_htp)]:
        mask_dil = dilate_mask_pil(mask, radius=6)
        pure_outside = ~mask_dil
        pure_diff = np.abs(rgb[pure_outside] - orig[pure_outside])
        print(f"  Outside Mask ({name:12s}): pure_outside_px={pure_outside.sum()}, max_diff={pure_diff.max():.2f}, mean_diff={pure_diff.mean():.4f}")

    return {
        "s42_reg_a_min": float(lum_s42[reg_a].min()),
        "s43_reg_a_min": float(lum_s43[reg_a].min()),
        "s43_mean_rgb": [float(rep_htp[mask][:, i].mean()) for i in range(3)],
        "outside_pure_diff": float(np.abs(rep_htp[~dilate_mask_pil(mask, radius=6)] - orig[~dilate_mask_pil(mask, radius=6)]).max())
    }

def analyze_motif2_glass():
    print("\n=== MOTIF 2: GLASS SCULPTURE VISUAL QUALITY ===")
    orig_path = Path("reports/sprint_80_total_validation/images/motif2_glass_1_original.png")
    mask_path = Path("reports/sprint_82_material_repair/images/motif2_glass_repaired_mask.png")
    rep_htp_path = Path("reports/sprint_82_material_repair/images/motif2_glass_repaired_htp.png")

    orig = np.array(Image.open(orig_path).convert("RGB"), dtype=np.float32)
    mask = np.array(Image.open(mask_path).convert("L"), dtype=np.uint8) > 128
    rep = np.array(Image.open(rep_htp_path).convert("RGB"), dtype=np.float32)

    parts = {
        "Head & Beak (y:117-165)": (mask & (np.arange(512)[:, None] >= 117) & (np.arange(512)[:, None] <= 165)),
        "Neck & Torso (y:166-329)": (mask & (np.arange(512)[:, None] >= 166) & (np.arange(512)[:, None] <= 329)),
        "Pedestal / Base (y:330-387)": (mask & (np.arange(512)[:, None] >= 330) & (np.arange(512)[:, None] <= 387)),
        "Base Row 360-387": (mask & (np.arange(512)[:, None] >= 360) & (np.arange(512)[:, None] <= 387))
    }

    for pname, pmask in parts.items():
        count = pmask.sum()
        if count == 0:
            continue
        orig_rgb = orig[pmask].mean(axis=0)
        rep_rgb = rep[pmask].mean(axis=0)
        print(f"  {pname:28s}: {count:5d} px | Orig RGB=[{orig_rgb[0]:5.1f}, {orig_rgb[1]:5.1f}, {orig_rgb[2]:5.1f}] -> Repaired RGB=[{rep_rgb[0]:5.1f}, {rep_rgb[1]:5.1f}, {rep_rgb[2]:5.1f}]")

    # Perimeter audit
    perimeter = dilate_mask_pil(mask, radius=2) & ~erode_mask_pil(mask, radius=2)
    peri_rgb = rep[perimeter]
    peri_lum = 0.299 * peri_rgb[:, 0] + 0.587 * peri_rgb[:, 1] + 0.114 * peri_rgb[:, 2]
    black_seam_px = (peri_lum < 25.0).sum()
    print(f"\n  Perimeter Seam Audit ({perimeter.sum()} px):")
    print(f"    Min Lum on boundary: {peri_lum.min():.2f}, Mean Lum: {peri_lum.mean():.2f}")
    print(f"    Dark seam pixels (<25 lum): {black_seam_px} ({black_seam_px/perimeter.sum()*100:.2f}%)")

    # Table protection: y >= 420
    table_mask = np.zeros((512, 512), dtype=bool)
    table_mask[420:, :] = True
    table_diff = np.abs(rep[table_mask] - orig[table_mask])
    print(f"\n  Table Preservation (y >= 420, {table_mask.sum()} px):")
    print(f"    Max Diff: {table_diff.max():.2f}, Mean Diff: {table_diff.mean():.4f}")

    # Room divider protection: x in [390, 430], y in [100, 300]
    divider_mask = np.zeros((512, 512), dtype=bool)
    divider_mask[100:300, 390:430] = True
    divider_diff = np.abs(rep[divider_mask] - orig[divider_mask])
    print(f"  Room Divider Preservation (x:390-430, y:100-300, {divider_mask.sum()} px):")
    print(f"    Max Diff: {divider_diff.max():.2f}, Mean Diff: {divider_diff.mean():.4f}")

    # Pure outside mask preservation
    pure_outside = ~dilate_mask_pil(mask, radius=6)
    pure_diff = np.abs(rep[pure_outside] - orig[pure_outside])
    print(f"  Pure Outside Mask Preservation ({pure_outside.sum()} px):")
    print(f"    Max Diff: {pure_diff.max():.2f}, Mean Diff: {pure_diff.mean():.4f}")

    return {
        "pedestal_px": int(parts["Pedestal / Base (y:330-387)"].sum()),
        "pedestal_rep_rgb": [float(x) for x in rep[parts["Pedestal / Base (y:330-387)"]].mean(axis=0)],
        "table_max_diff": float(table_diff.max()),
        "divider_max_diff": float(divider_diff.max()),
        "pure_outside_max_diff": float(pure_diff.max()),
        "black_seam_px": int(black_seam_px)
    }

def analyze_motif3_jacket():
    print("\n=== MOTIF 3: RED JACKET VISUAL QUALITY ===")
    orig_path = Path("reports/sprint_80_total_validation/images/motif3_jacket_1_original.png")
    mask_path = Path("reports/sprint_80_total_validation/images/motif3_jacket_3_binary_mask.png")
    rep_htp_path = Path("reports/sprint_80_total_validation/images/motif3_jacket_5_htp_result.png")

    orig = np.array(Image.open(orig_path).convert("RGB"), dtype=np.float32)
    mask = np.array(Image.open(mask_path).convert("L"), dtype=np.uint8) > 128
    rep = np.array(Image.open(rep_htp_path).convert("RGB"), dtype=np.float32)

    H, W, _ = orig.shape
    print(f"  Dimensions: {W}x{H}")
    print(f"  Mask Pixels: {mask.sum()} ({mask.sum()/(H*W)*100:.2f}%)")

    inpaint_orig = orig[mask]
    inpaint_rep = rep[mask]
    print(f"  Inpainted Jacket RGB: Orig Mean=[{inpaint_orig[:,0].mean():.1f}, {inpaint_orig[:,1].mean():.1f}, {inpaint_orig[:,2].mean():.1f}] -> Leather Mean=[{inpaint_rep[:,0].mean():.1f}, {inpaint_rep[:,1].mean():.1f}, {inpaint_rep[:,2].mean():.1f}]")

    lum_rep = 0.299 * rep[:, :, 0] + 0.587 * rep[:, :, 1] + 0.114 * rep[:, :, 2]
    lum_orig = 0.299 * orig[:, :, 0] + 0.587 * orig[:, :, 1] + 0.114 * orig[:, :, 2]
    lap_rep = np.abs(laplacian_filter_pil(lum_rep))
    lap_orig = np.abs(laplacian_filter_pil(lum_orig))
    print(f"  Leather Texture High-Freq Energy (Laplacian mean in mask): {lap_rep[mask].mean():.2f} (Orig: {lap_orig[mask].mean():.2f})")

    # Biological tissue zones (Strict protection):
    face_zone = np.zeros((H, W), dtype=bool)
    face_zone[:516, :] = True
    face_mask_overlap = (mask & face_zone).sum()
    face_diff = np.abs(rep[face_zone] - orig[face_zone])

    print(f"\n  Biological & Anatomical Protection:")
    print(f"    Face & Hair (y < 516, {face_zone.sum()} px):")
    print(f"      Mask Overlap: {face_mask_overlap} px (STRICT ZERO)")
    print(f"      Max Pixel Diff: {face_diff.max():.2f}, Mean Diff: {face_diff.mean():.6f}")

    pure_outside = ~dilate_mask_pil(mask, radius=8)
    pure_diff = np.abs(rep[pure_outside] - orig[pure_outside])
    print(f"    Pure Non-Jacket Area ({pure_outside.sum()} px, {pure_outside.sum()/(H*W)*100:.1f}%):")
    print(f"      Max Pixel Diff: {pure_diff.max():.2f}, Mean Diff: {pure_diff.mean():.6f}")

    return {
        "mask_px": int(mask.sum()),
        "face_mask_overlap": int(face_mask_overlap),
        "face_max_diff": float(face_diff.max()),
        "pure_outside_max_diff": float(pure_diff.max()),
        "orig_jacket_rgb": [float(x) for x in inpaint_orig.mean(axis=0)],
        "leather_jacket_rgb": [float(x) for x in inpaint_rep.mean(axis=0)]
    }

if __name__ == "__main__":
    m1 = analyze_motif1_apple()
    m2 = analyze_motif2_glass()
    m3 = analyze_motif3_jacket()

    audit_summary = {
        "sprint": "SPRINT_83",
        "motif1_apple": m1,
        "motif2_glass": m2,
        "motif3_jacket": m3,
        "overall_status": "AUDIT_COMPLETE"
    }

    out_file = Path("reports/sprint_83_visual_quality_audit/visual_quality_metrics.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)
    print(f"\nMetrics written to {out_file}")
