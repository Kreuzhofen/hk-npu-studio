"""
Sprint 81 Visual Asset Generator
Produces high-resolution analytical visual comparisons for the Sprint 81 Report:
1. Apple Dent Analysis (Original, Mask, Priming, S80 Seed 42 Crater, Healed Seed 43)
2. Glass Pedestal Analysis (Original, S80 Truncated Mask, Hue Analysis, S80 Result)
3. Jacket Regression Card
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def create_apple_panel():
    out_dir = Path("reports/sprint_81_material_quality/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    orig = Image.open("reports/sprint_80_total_validation/images/motif1_apple_1_original.png").convert("RGB")
    mask = Image.open("reports/sprint_80_total_validation/images/motif1_apple_3_binary_mask.png").convert("RGB")
    prime = Image.open("reports/sprint_80_total_validation/images/motif1_apple_4_primed_preview.png").convert("RGB")
    s80_res = Image.open("reports/sprint_80_total_validation/images/motif1_apple_5_htp_result.png").convert("RGB")
    seed43_res = Image.open("scratch/diag_apple/apple_seed43.png").convert("RGB")

    # Crop area of interest: y: 280..360, x: 320..400 (80x80 pixels)
    crop_box = (320, 280, 400, 360)
    c_orig = orig.crop(crop_box).resize((220, 220), Image.Resampling.NEAREST)
    c_mask = mask.crop(crop_box).resize((220, 220), Image.Resampling.NEAREST)
    c_prime = prime.crop(crop_box).resize((220, 220), Image.Resampling.NEAREST)
    c_s80 = s80_res.crop(crop_box).resize((220, 220), Image.Resampling.NEAREST)
    c_s43 = seed43_res.crop(crop_box).resize((220, 220), Image.Resampling.NEAREST)

    # Annotate S80 with red circle around dent
    draw_s80 = ImageDraw.Draw(c_s80)
    # in 80x80 crop, (y=324, x=359) is (39, 44), scaled to 220x220 is (39*220/80, 44*220/80) = (107, 121)
    draw_s80.ellipse([92, 106, 122, 136], outline="#FF3333", width=3)

    # Annotate S43 with green circle around healed area
    draw_s43 = ImageDraw.Draw(c_s43)
    draw_s43.ellipse([92, 106, 122, 136], outline="#00FF66", width=3)

    # 5-panel layout with headers
    panel_w = 220
    panel_h = 220
    header_h = 45
    footer_h = 35
    total_w = panel_w * 5 + 40
    total_h = panel_h + header_h + footer_h + 30

    card = Image.new("RGB", (total_w, total_h), color=(24, 26, 32))
    draw = ImageDraw.Draw(card)

    titles = [
        "1. Original (Rot)",
        "2. Maske (100% solide)",
        "3. Priming (Gold)",
        "4. S80 Seed 42 (Krater)",
        "5. Seed 43 (Geheilt)"
    ]
    subtitles = [
        "Glattes Rot / Keine Delle",
        "Vollst. 255 / Kein Loch",
        "Gleichm. Goldtnung",
        "Min Lum=0.6 (Schwarz)",
        "Min Lum=130.2 (Glatt)"
    ]
    panels = [c_orig, c_mask, c_prime, c_s80, c_s43]

    for i in range(5):
        x = 10 + i * (panel_w + 5)
        y = 10
        # Title
        draw.text((x + 10, y + 8), titles[i], fill=(230, 235, 245))
        # Image
        card.paste(panels[i], (x, y + header_h))
        # Subtitle
        draw.text((x + 10, y + header_h + panel_h + 8), subtitles[i], fill=(160, 175, 195))

    card.save(out_dir / "apple_dent_analysis.png")
    print(f"Saved {out_dir / 'apple_dent_analysis.png'}")

def create_glass_panel():
    out_dir = Path("reports/sprint_81_material_quality/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    orig = Image.open("reports/sprint_80_total_validation/images/motif2_glass_1_original.png").convert("RGB")
    mask = Image.open("reports/sprint_80_total_validation/images/motif2_glass_3_binary_mask.png").convert("RGB")
    prime = Image.open("reports/sprint_80_total_validation/images/motif2_glass_4_primed_preview.png").convert("RGB")
    res = Image.open("reports/sprint_80_total_validation/images/motif2_glass_5_htp_result.png").convert("RGB")

    # Crop pedestal area: y: 320..420, x: 190..310 (120x100)
    crop_box = (190, 320, 310, 420)
    c_orig = orig.crop(crop_box).resize((220, 220), Image.Resampling.NEAREST)
    c_mask = mask.crop(crop_box).resize((220, 220), Image.Resampling.NEAREST)
    c_prime = prime.crop(crop_box).resize((220, 220), Image.Resampling.NEAREST)
    c_res = res.crop(crop_box).resize((220, 220), Image.Resampling.NEAREST)

    # Create Hue heatmap for the pedestal crop
    orig_hsv = np.array(orig.convert("HSV"), dtype=float)
    h_crop = orig_hsv[320:420, 190:310, 0] * (360.0 / 255.0)
    # Heatmap: Hue > 185 in bright magenta/red, Hue <= 185 in green
    heat_rgb = np.zeros((100, 120, 3), dtype=np.uint8)
    for r in range(100):
        for c in range(120):
            hv = h_crop[r, c]
            if hv > 185.0:
                heat_rgb[r, c] = [230, 40, 80]  # Excluded cyan/teal hue
            elif hv >= 65.0:
                heat_rgb[r, c] = [50, 200, 80]  # Captured green hue
            else:
                heat_rgb[r, c] = [40, 40, 50]   # Background
    c_heat = Image.fromarray(heat_rgb).resize((220, 220), Image.Resampling.NEAREST)

    panel_w = 220
    panel_h = 220
    header_h = 45
    footer_h = 35
    total_w = panel_w * 5 + 40
    total_h = panel_h + header_h + footer_h + 30

    card = Image.new("RGB", (total_w, total_h), color=(24, 26, 32))
    draw = ImageDraw.Draw(card)

    titles = [
        "1. Original (Sockel)",
        "2. Hue-Karte (H > 185)",
        "3. S80 Maske (Abbruch)",
        "4. Priming (Truncated)",
        "5. S80 Ergebnis (Cyan)"
    ]
    subtitles = [
        "Trkis Klarglas (y=370..420)",
        "Rot: H > 185 (Abgeschnitten)",
        "Maske endet bei y=369",
        "Sockel unberhrt",
        "Cyan-Glas 100% erhalten"
    ]
    panels = [c_orig, c_heat, c_mask, c_prime, c_res]

    for i in range(5):
        x = 10 + i * (panel_w + 5)
        y = 10
        draw.text((x + 10, y + 8), titles[i], fill=(230, 235, 245))
        card.paste(panels[i], (x, y + header_h))
        draw.text((x + 10, y + header_h + panel_h + 8), subtitles[i], fill=(160, 175, 195))

    card.save(out_dir / "glass_pedestal_analysis.png")
    print(f"Saved {out_dir / 'glass_pedestal_analysis.png'}")

def create_jacket_card():
    out_dir = Path("reports/sprint_81_material_quality/images")
    src = Path("reports/sprint_80_total_validation/images/motif3_jacket_card_5col.png")
    dst = out_dir / "motif3_jacket_regression_5col.png"
    if src.exists():
        im = Image.open(src)
        im.save(dst)
        print(f"Copied {src} -> {dst}")

if __name__ == "__main__":
    create_apple_panel()
    create_glass_panel()
    create_jacket_card()
