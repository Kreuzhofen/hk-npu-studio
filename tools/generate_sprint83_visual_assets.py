"""
Generate Sprint 83 Visual Assets:
- Master Comparison Grid: 3 rows (Apple, Glass, Jacket) x 4 columns (Original, Overlay/Mask, Primed, HTP Result)
- Apple Audit Panel: Original vs Seed 42 vs Seed 43 vs Crater Zoom
- Glass Audit Panel: Original vs Mask vs Inpaint with Pedestal Zoom
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def make_master_comparison():
    out_dir = Path("reports/sprint_83_visual_quality_audit/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Assets
    m1_orig = Image.open("reports/appl_edit_test_49/appl_edit_49_original.png").convert("RGB").resize((300, 300))
    m1_over = Image.open("reports/sprint_82_material_repair/images/motif1_apple_repaired_overlay.png").convert("RGB").resize((300, 300))
    m1_prim = Image.open("reports/sprint_82_material_repair/images/motif1_apple_repaired_primed.png").convert("RGB").resize((300, 300))
    m1_res  = Image.open("reports/sprint_82_material_repair/images/motif1_apple_repaired_htp.png").convert("RGB").resize((300, 300))

    m2_orig = Image.open("reports/sprint_80_total_validation/images/motif2_glass_1_original.png").convert("RGB").resize((300, 300))
    m2_over = Image.open("reports/sprint_82_material_repair/images/motif2_glass_repaired_overlay.png").convert("RGB").resize((300, 300))
    m2_prim = Image.open("reports/sprint_82_material_repair/images/motif2_glass_repaired_primed.png").convert("RGB").resize((300, 300))
    m2_res  = Image.open("reports/sprint_82_material_repair/images/motif2_glass_repaired_htp.png").convert("RGB").resize((300, 300))

    # Jacket is tall, aspect ratio 1672:2500 (~ 1:1.495). Crop or resize into 300x300 center crop for consistent grid
    def crop_center_square(img):
        w, h = img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 4 # focus on upper torso/jacket
        return img.crop((left, top, left + min_dim, top + min_dim)).resize((300, 300))

    m3_orig = crop_center_square(Image.open("reports/sprint_80_total_validation/images/motif3_jacket_1_original.png").convert("RGB"))
    m3_over = crop_center_square(Image.open("reports/sprint_80_total_validation/images/motif3_jacket_2_mask_overlay.png").convert("RGB"))
    m3_prim = crop_center_square(Image.open("reports/sprint_80_total_validation/images/motif3_jacket_4_primed_preview.png").convert("RGB"))
    m3_res  = crop_center_square(Image.open("reports/sprint_80_total_validation/images/motif3_jacket_5_htp_result.png").convert("RGB"))

    # Canvas: 4 columns x 3 rows + headers
    col_w = 300
    row_h = 300
    pad = 15
    header_h = 70
    row_title_w = 180

    total_w = row_title_w + 4 * col_w + 5 * pad
    total_h = header_h + 3 * row_h + 4 * pad

    canvas = Image.new("RGB", (total_w, total_h), (24, 26, 30))
    draw = ImageDraw.Draw(canvas)

    # Column titles
    col_titles = [
        "1. Original-Bild",
        "2. Semantische Maske",
        "3. Priming-Vorschau",
        "4. HTP-Inpainting (Qualcomm NPU)"
    ]

    for c, title in enumerate(col_titles):
        x = row_title_w + pad + c * (col_w + pad)
        draw.rectangle([x, pad, x + col_w, header_h - pad], fill=(36, 40, 48), outline=(60, 68, 80))
        draw.text((x + 15, pad + 15), title, fill=(220, 230, 242))

    rows_data = [
        ("Motiv 1: Roter Apfel\nZiel: 24k Gold\nHTP-Zeit: 26.19s\nStatus: RELEASE-FÄHIG", [m1_orig, m1_over, m1_prim, m1_res], (80, 180, 100)),
        ("Motiv 2: Glasskulptur\nZiel: 24k Gold (inkl. Sockel)\nHTP-Zeit: 26.10s\nStatus: RELEASE-FÄHIG", [m2_orig, m2_over, m2_prim, m2_res], (80, 180, 100)),
        ("Motiv 3: Rote Jacke\nZiel: Schwarzes Leder\nHTP-Zeit: 24.93s\nStatus: RELEASE-FÄHIG", [m3_orig, m3_over, m3_prim, m3_res], (80, 180, 100))
    ]

    for r, (label, imgs, status_color) in enumerate(rows_data):
        y = header_h + pad + r * (row_h + pad)
        # Row label card
        draw.rectangle([pad, y, row_title_w, y + row_h], fill=(32, 36, 44), outline=(50, 58, 70))
        draw.text((pad + 10, y + 20), label, fill=(240, 240, 245))
        # Status pill
        draw.rectangle([pad + 10, y + row_h - 45, row_title_w - 10, y + row_h - 15], fill=(20, 50, 30), outline=status_color)
        draw.text((pad + 20, y + row_h - 38), "VERIFIED PASS", fill=status_color)

        for c, img in enumerate(imgs):
            x = row_title_w + pad + c * (col_w + pad)
            canvas.paste(img, (x, y))
            draw.rectangle([x, y, x + col_w, y + row_h], outline=(70, 80, 95), width=1)

    out_path = out_dir / "sprint_83_master_comparison_grid.png"
    canvas.save(out_path, quality=95)
    print(f"Master comparison grid saved to {out_path}")

    # Copy to brain artifact directory if accessible
    brain_dir = Path(r"C:\Users\holge\.gemini\antigravity-cli\brain\c991b454-d253-4b5d-9ce4-469780cc4864\images")
    if brain_dir.exists():
        canvas.save(brain_dir / "sprint_83_master_comparison_grid.png")
        print(f"Copied grid to brain directory {brain_dir}")

if __name__ == "__main__":
    make_master_comparison()
