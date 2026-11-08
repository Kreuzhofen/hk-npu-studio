"""
Generate Sprint 86 Master Audit Card:
Combines all 3 motifs with honest visual acceptance verdicts, key metrics, and prompt targets.
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def make_master_audit_card():
    out_dir = Path("reports/sprint_86_visual_release_acceptance/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    base_85 = Path("reports/sprint_85_material_polish/images")

    # Images for Row 1: Apple
    m1_orig = Image.open("reports/appl_edit_test_49/appl_edit_49_original.png").convert("RGB").resize((260, 260))
    m1_prim = Image.open(base_85 / "motif1_apple_polished_primed.png").convert("RGB").resize((260, 260))
    m1_res  = Image.open(base_85 / "motif1_apple_polished_htp.png").convert("RGB").resize((260, 260))

    # Images for Row 2: Glass
    m2_orig = Image.open("reports/sprint_80_total_validation/images/motif2_glass_1_original.png").convert("RGB").resize((260, 260))
    m2_prim = Image.open(base_85 / "motif2_glass_polished_primed.png").convert("RGB").resize((260, 260))
    m2_res  = Image.open(base_85 / "motif2_glass_polished_htp.png").convert("RGB").resize((260, 260))

    # Images for Row 3: Jacket
    def crop_square(img):
        w, h = img.size
        dim = min(w, h)
        left = (w - dim) // 2
        top = (h - dim) // 4
        return img.crop((left, top, left + dim, top + dim)).resize((260, 260))

    m3_orig = crop_square(Image.open("reports/sprint_80_total_validation/images/motif3_jacket_1_original.png").convert("RGB"))
    m3_over = crop_square(Image.open(base_85 / "motif3_jacket_polished_overlay.png").convert("RGB"))
    m3_res  = crop_square(Image.open(base_85 / "motif3_jacket_polished_htp.png").convert("RGB"))

    col_w = 260
    row_h = 260
    info_w = 340
    pad = 12
    header_h = 50

    total_w = info_w + 3 * col_w + 4 * pad
    total_h = header_h + 3 * row_h + 4 * pad

    canvas = Image.new("RGB", (total_w, total_h), (22, 24, 28))
    draw = ImageDraw.Draw(canvas)

    # Column titles
    col_titles = ["1. Original-Bild", "2. Maske / Priming", "3. HTP Inpainting (NPU)"]
    for c, title in enumerate(col_titles):
        x = info_w + pad + c * (col_w + pad)
        draw.rectangle([x, pad, x + col_w, header_h - pad], fill=(34, 38, 46), outline=(60, 68, 80))
        draw.text((x + 20, pad + 10), title, fill=(220, 230, 240))

    draw.rectangle([pad, pad, info_w, header_h - pad], fill=(30, 34, 42), outline=(60, 68, 80))
    draw.text((pad + 15, pad + 10), "SPRINT 86: VISUAL ACCEPTANCE", fill=(255, 200, 100))

    rows = [
        {
            "name": "MOTIV 1: APFEL (24k Gold)",
            "prompt": "Verwandle den Apfel in 24k Gold.",
            "metrics": "Lit L=201.3 | Zone V L=148.8 (Min=87.7)\n0 Px < 80 | Kontrastverhaeltnis: 1.35x\nHintergrund Diff: 0.0000",
            "finding": "Schattenband bei X=353 noch deutlich\nsichtbar (L=95.8 vs 215). Wirkt wie\nDelle in der Goldkugel.",
            "verdict": "ABLEHNUNG (SCHATTEN RESTLICH)",
            "color": (240, 140, 40),
            "imgs": [m1_orig, m1_prim, m1_res]
        },
        {
            "name": "MOTIV 2: GLASSKULPTUR (24k Gold)",
            "prompt": "Verwandle die Glasskulptur in 24k Gold.",
            "metrics": "Naht X=215 L=156.0 (Min=141.3, 0 Px<40)\nSockel L=195.7, RGB=[227, 195, 119]\nTable & Background Diff: 0.0000",
            "finding": "Seed-42-Riss komplett behoben.\nVertiefung bei X=230 ist natuerliche\nmorphologische Fluegelkerbe.",
            "verdict": "FREIGEGEBEN (VOLLSTAENDIG)",
            "color": (60, 220, 100),
            "imgs": [m2_orig, m2_prim, m2_res]
        },
        {
            "name": "MOTIV 3: ROTE JACKE (Schwarzes Leder)",
            "prompt": "Mache die rote Jacke zu schwarzem Leder.",
            "metrics": "Mean RGB=[161, 45, 60] (WEINROT!)\nRot-Dominanz: 97.6% | Schwarz (RGB<60): 4.5%\nHautschutz: 100% (0 Px Diff)",
            "finding": "Promptziel komplett verfehlt!\nKein Priming -> UNet behaelt Rot.\nJacke ist dunkelrot, nicht schwarz.",
            "verdict": "ABGELEHNT (KEIN SCHWARZ)",
            "color": (240, 60, 60),
            "imgs": [m3_orig, m3_over, m3_res]
        }
    ]

    for r, row in enumerate(rows):
        y = header_h + pad + r * (row_h + pad)

        # Info Box
        draw.rectangle([pad, y, info_w, y + row_h], fill=(28, 32, 40), outline=(50, 58, 70))
        draw.text((pad + 12, y + 12), row["name"], fill=(255, 255, 255))
        draw.text((pad + 12, y + 35), f"Prompt: {row['prompt']}", fill=(180, 190, 205))
        draw.text((pad + 12, y + 65), row["metrics"], fill=(160, 175, 190))
        draw.text((pad + 12, y + 125), row["finding"], fill=(220, 210, 160))

        # Verdict Badge
        draw.rectangle([pad + 10, y + row_h - 45, info_w - 10, y + row_h - 12], fill=(20, 22, 28), outline=row["color"], width=2)
        draw.text((pad + 20, y + row_h - 35), row["verdict"], fill=row["color"])

        # Paste Images
        for c, img in enumerate(row["imgs"]):
            x = info_w + pad + c * (col_w + pad)
            canvas.paste(img, (x, y))
            draw.rectangle([x, y, x + col_w, y + row_h], outline=(60, 68, 80), width=1)

    out_file = out_dir / "sprint_86_master_audit_card.png"
    canvas.save(out_file, quality=95)
    print(f"Master audit card saved to {out_file}")

    brain_dir = Path(r"C:\Users\holge\.gemini\antigravity-cli\brain\c991b454-d253-4b5d-9ce4-469780cc4864\images")
    if brain_dir.exists():
        canvas.save(brain_dir / "sprint_86_master_audit_card.png")
        print(f"Copied to brain images directory {brain_dir}")

if __name__ == "__main__":
    make_master_audit_card()
