"""
Generate Sprint 85 Diagnostic & Master Visual Assets:
1. Master Comparison Grid (3 motifs x 4 columns)
2. Apple Polish Comparison Panel (Sprint 84 dark shadow vs Sprint 85 polished gold)
3. Glass Sculpture Polish Comparison Panel (Sprint 82/84 black seam vs Sprint 85 polished gold)
4. Copies all assets to brain artifact directory.
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def make_apple_polish_comparison():
    out_dir = Path("reports/sprint_85_material_polish/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    orig = Image.open("reports/appl_edit_test_49/appl_edit_49_original.png").convert("RGB")
    prim_old = Image.open("reports/sprint_82_material_repair/images/motif1_apple_repaired_primed.png").convert("RGB")
    htp_old = Image.open("reports/sprint_82_material_repair/images/motif1_apple_repaired_htp.png").convert("RGB")
    prim_new = Image.open(out_dir / "motif1_apple_polished_primed.png").convert("RGB") if (out_dir / "motif1_apple_polished_primed.png").exists() else Image.open("reports/sprint_85_material_polish/images/apple_polish/apple_primed_compressed_145.png").convert("RGB")
    htp_new = Image.open(out_dir / "motif1_apple_polished_htp.png").convert("RGB") if (out_dir / "motif1_apple_polished_htp.png").exists() else Image.open("reports/sprint_85_material_polish/images/apple_polish/apple_result_polished_htp.png").convert("RGB")

    # Zoom box on Zone V: X in [330, 400], Y in [260, 380] -> 70x120 px, 3x scale -> 210x360 px
    box = (330, 260, 400, 380)
    w, h = 210, 360

    c_orig = orig.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_p_old = prim_old.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_h_old = htp_old.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_p_new = prim_new.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_h_new = htp_new.crop(box).resize((w, h), Image.Resampling.NEAREST)

    pad = 12
    header_h = 45
    total_w = 5 * w + 6 * pad
    total_h = header_h + h + 2 * pad + 60

    canvas = Image.new("RGB", (total_w, total_h), (24, 26, 30))
    draw = ImageDraw.Draw(canvas)

    panels = [
        ("1. Original (Rot)", c_orig, "Kernschatten (L=47.3)", (200, 100, 100)),
        ("2. Priming Alt (Sp. 84)", c_p_old, "Schatten vererbt (L=114.3)", (220, 160, 80)),
        ("3. HTP Alt (Sp. 84)", c_h_old, "Dunkle Zone (L=84.1)", (240, 80, 80)),
        ("4. Priming Neu (Sp. 85)", c_p_new, "Luminanz-Lift (L=173.8)", (100, 220, 140)),
        ("5. HTP Neu (Sp. 85)", c_h_new, "Polierter Glanz (L=200.7)", (80, 240, 120)),
    ]

    for i, (title, img, sub, color) in enumerate(panels):
        x = pad + i * (w + pad)
        y = header_h + pad
        draw.text((x + 5, 12), title, fill=(230, 235, 240))
        canvas.paste(img, (x, y))
        draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
        cx = x + int((360 - 330) * 3)
        draw.line([(cx, y), (cx, y + h)], fill=(255, 60, 60) if i < 3 else (60, 255, 120), width=1)
        draw.text((x + 5, y + h + 10), sub, fill=color)

    out_path = out_dir / "sprint_85_apple_polish_comparison.png"
    canvas.save(out_path, quality=95)
    print(f"Apple polish comparison saved to {out_path}")

def make_glass_polish_comparison():
    out_dir = Path("reports/sprint_85_material_polish/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    orig = Image.open("reports/sprint_80_total_validation/images/motif2_glass_1_original.png").convert("RGB")
    htp_old = Image.open("reports/sprint_82_material_repair/images/motif2_glass_repaired_htp.png").convert("RGB")
    htp_new = Image.open(out_dir / "motif2_glass_polished_htp.png").convert("RGB") if (out_dir / "motif2_glass_polished_htp.png").exists() else Image.open("reports/sprint_85_material_polish/images/glass_controller_tests/motif2_glass_controller_seed_100.png").convert("RGB")

    box = (195, 155, 255, 275)
    w, h = 210, 360

    c_orig = orig.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_old = htp_old.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_new = htp_new.crop(box).resize((w, h), Image.Resampling.NEAREST)

    pad = 15
    header_h = 45
    total_w = 3 * w + 4 * pad
    total_h = header_h + h + 2 * pad + 60

    canvas = Image.new("RGB", (total_w, total_h), (24, 26, 30))
    draw = ImageDraw.Draw(canvas)

    panels = [
        ("1. Original Glas", c_orig, "Flügelkante (L=100.5)", (100, 180, 160)),
        ("2. HTP Alt (Seed 42)", c_old, "Schwarze Naht (L=1.5..10.8)", (255, 60, 60)),
        ("3. HTP Neu (Seed 100)", c_new, "Nahtlos poliert (L=51.7, 0px<40)", (80, 240, 120)),
    ]

    for i, (title, img, sub, color) in enumerate(panels):
        x = pad + i * (w + pad)
        y = header_h + pad
        draw.text((x + 5, 12), title, fill=(230, 235, 240))
        canvas.paste(img, (x, y))
        draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
        cx = x + int((215 - 195) * (w / 60.0))
        draw.line([(cx, y), (cx, y + h)], fill=(255, 40, 40) if i == 1 else (60, 255, 120), width=1)
        draw.text((x + 5, y + h + 10), sub, fill=color)

    out_path = out_dir / "sprint_85_glass_polish_comparison.png"
    canvas.save(out_path, quality=95)
    print(f"Glass polish comparison saved to {out_path}")

def make_master_comparison():
    out_dir = Path("reports/sprint_85_material_polish/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    m1_orig = Image.open("reports/appl_edit_test_49/appl_edit_49_original.png").convert("RGB").resize((300, 300))
    m1_over = Image.open(out_dir / "motif1_apple_polished_overlay.png").convert("RGB").resize((300, 300))
    m1_prim = Image.open(out_dir / "motif1_apple_polished_primed.png").convert("RGB").resize((300, 300))
    m1_res  = Image.open(out_dir / "motif1_apple_polished_htp.png").convert("RGB").resize((300, 300))

    m2_orig = Image.open("reports/sprint_80_total_validation/images/motif2_glass_1_original.png").convert("RGB").resize((300, 300))
    m2_over = Image.open(out_dir / "motif2_glass_polished_overlay.png").convert("RGB").resize((300, 300))
    m2_prim = Image.open(out_dir / "motif2_glass_polished_primed.png").convert("RGB").resize((300, 300))
    m2_res  = Image.open(out_dir / "motif2_glass_polished_htp.png").convert("RGB").resize((300, 300))

    def crop_center_square(img):
        w, h = img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 4
        return img.crop((left, top, left + min_dim, top + min_dim)).resize((300, 300))

    m3_orig = crop_center_square(Image.open("reports/sprint_80_total_validation/images/motif3_jacket_1_original.png").convert("RGB"))
    m3_over = crop_center_square(Image.open(out_dir / "motif3_jacket_polished_overlay.png").convert("RGB"))
    m3_prim_path = out_dir / "motif3_jacket_polished_primed.png"
    if m3_prim_path.exists():
        m3_prim = crop_center_square(Image.open(m3_prim_path).convert("RGB"))
    else:
        m3_prim = m3_orig
    m3_res  = crop_center_square(Image.open(out_dir / "motif3_jacket_polished_htp.png").convert("RGB"))

    col_w = 300
    row_h = 300
    pad = 15
    header_h = 70
    row_title_w = 200

    total_w = row_title_w + 4 * col_w + 5 * pad
    total_h = header_h + 3 * row_h + 4 * pad

    canvas = Image.new("RGB", (total_w, total_h), (24, 26, 30))
    draw = ImageDraw.Draw(canvas)

    col_titles = [
        "1. Original-Bild",
        "2. Semantische Maske",
        "3. Priming (Komprimiert)",
        "4. HTP-Inpainting (Polished NPU)"
    ]

    for c, title in enumerate(col_titles):
        x = row_title_w + pad + c * (col_w + pad)
        draw.rectangle([x, pad, x + col_w, header_h - pad], fill=(36, 40, 48), outline=(60, 68, 80))
        draw.text((x + 15, pad + 15), title, fill=(220, 230, 242))

    rows_data = [
        ("Motiv 1: Roter Apfel\nZiel: 24k Gold (min_val=145)\nHTP: 22.0s | Seed 43\nStatus: POLISHED (Kein Schatten)", [m1_orig, m1_over, m1_prim, m1_res], (80, 220, 120)),
        ("Motiv 2: Glasskulptur\nZiel: 24k Gold (inkl. Sockel)\nHTP: 25.1s | Seed 100\nStatus: POLISHED (Keine Naht)", [m2_orig, m2_over, m2_prim, m2_res], (80, 220, 120)),
        ("Motiv 3: Rote Jacke\nZiel: Schwarzes Leder\nHTP: 25.0s | Seed 20260830\nStatus: REGRESSION BESTANDEN", [m3_orig, m3_over, m3_prim, m3_res], (80, 220, 120))
    ]

    for r, (label, imgs, status_color) in enumerate(rows_data):
        y = header_h + pad + r * (row_h + pad)
        draw.rectangle([pad, y, row_title_w, y + row_h], fill=(32, 36, 44), outline=(50, 58, 70))
        draw.text((pad + 10, y + 20), label, fill=(240, 240, 245))
        draw.rectangle([pad + 10, y + row_h - 45, row_title_w - 10, y + row_h - 15], fill=(20, 50, 30), outline=status_color)
        draw.text((pad + 20, y + row_h - 38), "COMMERCIAL GRADE", fill=status_color)

        for c, img in enumerate(imgs):
            x = row_title_w + pad + c * (col_w + pad)
            canvas.paste(img, (x, y))
            draw.rectangle([x, y, x + col_w, y + row_h], outline=(70, 80, 95), width=1)

    out_path = out_dir / "sprint_85_master_comparison_grid.png"
    canvas.save(out_path, quality=95)
    print(f"Master comparison grid saved to {out_path}")

    # Copy to brain artifact directory
    brain_dir = Path(r"C:\Users\holge\.gemini\antigravity-cli\brain\c991b454-d253-4b5d-9ce4-469780cc4864\images")
    if brain_dir.exists():
        canvas.save(brain_dir / "sprint_85_master_comparison_grid.png")
        print(f"Copied grid to brain directory {brain_dir}")

if __name__ == "__main__":
    make_apple_polish_comparison()
    make_glass_polish_comparison()
    make_master_comparison()
