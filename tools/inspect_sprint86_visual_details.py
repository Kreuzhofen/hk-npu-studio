"""
Deep visual inspection script for Sprint 86.
Scans:
1. Glass sculpture for ANY vertical dark line across the whole body and wings.
2. Apple right flank gradient profile.
3. Jacket regional color distribution (shoulders, chest, abdomen, sleeve).
4. Generates visual diagnostic panels for human inspection.
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def lum(arr):
    return 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

def inspect_details():
    out_dir = Path("reports/sprint_86_visual_release_acceptance/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    base_85 = Path("reports/sprint_85_material_polish/images")

    # =========================================================================
    # 1. GLASS SCULPTURE VERTICAL LINE SCAN
    # =========================================================================
    print("--- SCANNING GLASS SCULPTURE FOR VERTICAL LINES ---")
    orig_glass = np.array(Image.open("reports/sprint_80_total_validation/images/motif2_glass_1_original.png").convert("RGB"), dtype=float)
    res_glass = np.array(Image.open(base_85 / "motif2_glass_polished_htp.png").convert("RGB"), dtype=float)
    mask_glass = np.array(Image.open(base_85 / "motif2_glass_polished_mask.png")) > 0

    l_res_glass = lum(res_glass)
    l_orig_glass = lum(orig_glass)

    # Search for local vertical minima across all columns inside mask
    # For each row Y in [100, 350], calculate horizontal gradient dL/dx
    # A dark vertical line manifests as a column where L(x) is significantly lower than L(x-2) and L(x+2)
    line_candidates = []
    for y in range(120, 350):
        for x in range(150, 320):
            if mask_glass[y, x] and mask_glass[y, x-2] and mask_glass[y, x+2]:
                left_l = l_res_glass[y, x-2]
                center_l = l_res_glass[y, x]
                right_l = l_res_glass[y, x+2]
                depth = min(left_l - center_l, right_l - center_l)
                if depth > 25.0: # Significant dip/groove
                    line_candidates.append((x, y, depth, center_l, l_orig_glass[y, x]))

    print(f"Found {len(line_candidates)} points with horizontal luminance dip > 25")
    # Group by column X
    col_counts = {}
    for x, y, depth, center_l, orig_l in line_candidates:
        col_counts[x] = col_counts.get(x, 0) + 1

    sorted_cols = sorted(col_counts.items(), key=lambda item: item[1], reverse=True)
    print("Top column candidates with vertical dip:")
    for x, count in sorted_cols[:10]:
        # Average depth and original luminance at this column
        pts = [p for p in line_candidates if p[0] == x]
        avg_depth = np.mean([p[2] for p in pts])
        avg_center = np.mean([p[3] for p in pts])
        avg_orig = np.mean([p[4] for p in pts])
        y_min = min([p[1] for p in pts])
        y_max = max([p[1] for p in pts])
        print(f"  X={x}: count={count} px, Y=[{y_min}..{y_max}], avg dip={avg_depth:.1f}, L_res={avg_center:.1f}, L_orig={avg_orig:.1f}")

    # =========================================================================
    # 2. APPLE HORIZONTAL PROFILE ACROSS CORE SHADOW
    # =========================================================================
    print("\n--- ANALYZING APPLE HORIZONTAL LUMINANCE PROFILE ---")
    orig_apple = np.array(Image.open("reports/appl_edit_test_49/appl_edit_49_original.png").convert("RGB"), dtype=float)
    prim_apple = np.array(Image.open(base_85 / "motif1_apple_polished_primed.png").convert("RGB"), dtype=float)
    res_apple = np.array(Image.open(base_85 / "motif1_apple_polished_htp.png").convert("RGB"), dtype=float)
    mask_apple = np.array(Image.open(base_85 / "motif1_apple_polished_mask.png")) > 0

    l_orig_apple = lum(orig_apple)
    l_prim_apple = lum(prim_apple)
    l_res_apple = lum(res_apple)

    # Average profile across Y in [300, 340] (equator of apple)
    y_eq = slice(300, 341)
    eq_mask = mask_apple[y_eq, :].any(axis=0)
    apple_xs = np.where(eq_mask)[0]
    print(f"Apple equator X range: {apple_xs.min()} to {apple_xs.max()}")

    for x in range(apple_xs.min(), apple_xs.max() + 1, 15):
        m = mask_apple[y_eq, x]
        if m.sum() > 0:
            lo = l_orig_apple[y_eq, x][m].mean()
            lp = l_prim_apple[y_eq, x][m].mean()
            lr = l_res_apple[y_eq, x][m].mean()
            rgb_r = res_apple[y_eq, x][m].mean(axis=0)
            print(f"  X={x:3d}: L_orig={lo:5.1f} | L_prim={lp:5.1f} | L_res={lr:5.1f} | RGB_res=[{rgb_r[0]:5.1f}, {rgb_r[1]:5.1f}, {rgb_r[2]:5.1f}]")

    # =========================================================================
    # 3. JACKET REGIONAL ANALYSIS
    # =========================================================================
    print("\n--- ANALYZING JACKET REGIONAL COLORS ---")
    orig_jacket = np.array(Image.open("reports/sprint_80_total_validation/images/motif3_jacket_1_original.png").convert("RGB"), dtype=float)
    res_jacket = np.array(Image.open(base_85 / "motif3_jacket_polished_htp.png").convert("RGB"), dtype=float)
    mask_jacket = np.array(Image.open(base_85 / "motif3_jacket_polished_mask.png")) > 0

    regions = {
        "Left Shoulder": (slice(600, 900), slice(400, 700)),
        "Right Shoulder": (slice(600, 900), slice(1000, 1300)),
        "Chest Center (Zipper area)": (slice(900, 1300), slice(750, 950)),
        "Lower Torso": (slice(1400, 1800), slice(700, 1100)),
        "Left Sleeve": (slice(1100, 1600), slice(350, 600)),
        "Right Sleeve": (slice(1100, 1600), slice(1200, 1450)),
    }

    for name, (ys, xs) in regions.items():
        m = mask_jacket[ys, xs]
        if m.sum() > 0:
            rgb_o = orig_jacket[ys, xs][m].mean(axis=0)
            rgb_r = res_jacket[ys, xs][m].mean(axis=0)
            lum_o = lum(orig_jacket[ys, xs][m]).mean()
            lum_r = lum(res_jacket[ys, xs][m]).mean()
            red_dom = ((res_jacket[ys, xs][..., 0] > res_jacket[ys, xs][..., 1] + 20) &
                       (res_jacket[ys, xs][..., 0] > res_jacket[ys, xs][..., 2] + 20) & m).sum() / m.sum()
            print(f"  {name:28s}: Orig RGB=[{rgb_o[0]:5.1f}, {rgb_o[1]:4.1f}, {rgb_o[2]:4.1f}] -> Res RGB=[{rgb_r[0]:5.1f}, {rgb_r[1]:4.1f}, {rgb_r[2]:4.1f}] | L={lum_r:5.1f} | RedDom={red_dom*100:5.1f}%")

    # =========================================================================
    # 4. GENERATE VISUAL DIAGNOSTIC PANELS
    # =========================================================================
    # Panel A: Apple Shadow Analysis
    box_a = (300, 240, 420, 400) # crop on right flank
    ca_orig = Image.fromarray(orig_apple.astype(np.uint8)).crop(box_a).resize((240, 320))
    ca_prim = Image.fromarray(prim_apple.astype(np.uint8)).crop(box_a).resize((240, 320))
    ca_res  = Image.fromarray(res_apple.astype(np.uint8)).crop(box_a).resize((240, 320))

    canvas_a = Image.new("RGB", (3 * 240 + 4 * 10, 320 + 60), (30, 32, 38))
    draw_a = ImageDraw.Draw(canvas_a)
    draw_a.text((15, 10), "1. Original Schatten (Rot)", fill=(240, 200, 200))
    canvas_a.paste(ca_orig, (10, 40))
    draw_a.text((265, 10), "2. Priming min_val=145 (Gelb)", fill=(240, 230, 180))
    canvas_a.paste(ca_prim, (260, 40))
    draw_a.text((515, 10), "3. HTP Inpainting (Schatten restlich)", fill=(240, 220, 140))
    canvas_a.paste(ca_res, (510, 40))
    canvas_a.save(out_dir / "audit_apple_shadow_panel.png")

    # Panel B: Glass sculpture vertical structure analysis
    box_g = (170, 140, 270, 290)
    cg_orig = Image.fromarray(orig_glass.astype(np.uint8)).crop(box_g).resize((250, 375))
    cg_res  = Image.fromarray(res_glass.astype(np.uint8)).crop(box_g).resize((250, 375))

    canvas_g = Image.new("RGB", (2 * 250 + 3 * 10, 375 + 60), (30, 32, 38))
    draw_g = ImageDraw.Draw(canvas_g)
    draw_g.text((15, 10), "Original Glas (Morphologische Flügelkerbe)", fill=(180, 240, 220))
    canvas_g.paste(cg_orig, (10, 40))
    draw_g.text((275, 10), "HTP 24k Gold (Seed 100: Glatte Goldkerbe)", fill=(240, 220, 140))
    canvas_g.paste(cg_res, (270, 40))
    canvas_g.save(out_dir / "audit_glass_structure_panel.png")

    # Panel C: Jacket color audit panel (Original vs Result with RGB readout)
    box_j = (300, 500, 1450, 1950)
    cj_orig = Image.fromarray(orig_jacket.astype(np.uint8)).crop(box_j).resize((300, 380))
    cj_res  = Image.fromarray(res_jacket.astype(np.uint8)).crop(box_j).resize((300, 380))

    canvas_j = Image.new("RGB", (2 * 300 + 3 * 10, 380 + 70), (30, 32, 38))
    draw_j = ImageDraw.Draw(canvas_j)
    draw_j.text((15, 10), "Original: Kräftiges Rot (R=205, G=13, B=48)", fill=(255, 120, 120))
    canvas_j.paste(cj_orig, (10, 40))
    draw_j.text((325, 10), "HTP: Dunkelrot / Burgundy (R=161, G=45, B=60)", fill=(255, 180, 180))
    canvas_j.paste(cj_res, (320, 40))
    draw_j.text((325, 40 + 380 + 10), "KEIN SCHWARZ! Promptziel verfehlt (97.6% rot-dominant)", fill=(255, 60, 60))
    canvas_j.save(out_dir / "audit_jacket_color_panel.png")

    print("\nVisual diagnostic panels generated in reports/sprint_86_visual_release_acceptance/images/")

if __name__ == "__main__":
    inspect_details()
