"""
Sprint 82 Visual Comparison Asset Generator
Produces high-resolution visual comparison grids and cards for Sprint 82:
1. Apple Comparison (Original, S80 Defect, S82 Repaired, Zoomed Crater Crop)
2. Glass Sculpture Comparison (Original, S80 Mask, S82 Mask, S80 Cyan Pedestal, S82 Gold Pedestal)
3. Master Comparison Grid across all 3 Motifs
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def build_comparisons():
    img_dir = Path("reports/sprint_82_material_repair/images")
    img_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # 1. Apple Comparison Card
    # -------------------------------------------------------------
    orig_apple = Image.open("reports/appl_edit_test_49/appl_edit_49_original.png").convert("RGB")
    s80_apple = Image.open("reports/sprint_80_total_validation/images/motif1_apple_5_htp_result.png").convert("RGB")
    s82_apple = Image.open(img_dir / "motif1_apple_repaired_htp.png").convert("RGB")

    # Zoomed crops of Region A (y: 300..345, x: 340..385)
    crop_box = (340, 300, 385, 345)
    z_orig = orig_apple.crop(crop_box).resize((240, 240), Image.Resampling.NEAREST)
    z_s80 = s80_apple.crop(crop_box).resize((240, 240), Image.Resampling.NEAREST)
    z_s82 = s82_apple.crop(crop_box).resize((240, 240), Image.Resampling.NEAREST)

    # Add red circle on s80 crater
    draw80 = ImageDraw.Draw(z_s80)
    draw80.ellipse([85, 105, 135, 155], outline="#FF2222", width=3)

    # Add green circle on s82 healed surface
    draw82 = ImageDraw.Draw(z_s82)
    draw82.ellipse([85, 105, 135, 155], outline="#00FF66", width=3)

    # 4-panel card
    panel_w = 260
    panel_h = 260
    header_h = 45
    footer_h = 40
    card_w = panel_w * 4 + 30
    card_h = panel_h + header_h + footer_h + 20

    card_apple = Image.new("RGB", (card_w, card_h), (24, 26, 32))
    draw = ImageDraw.Draw(card_apple)

    panels = [
        orig_apple.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
        s80_apple.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
        s82_apple.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
        z_s82.resize((panel_w, panel_h), Image.Resampling.NEAREST),
    ]
    titles = [
        "1. Original (Rot)",
        "2. S80 Ergebnis (Krater)",
        "3. S82 Repariert (Gold)",
        "4. Detailansicht (Geheilt)"
    ]
    subtitles = [
        "Glattes Rot / Keine Delle",
        "Seed 42 / Min Lum=0.6",
        "Seed 43 / Min Lum=54.2 (Glatt)",
        "0 dunkle Pixel (<30) im Zentrum"
    ]

    for i in range(4):
        x = 10 + i * (panel_w + 5)
        y = 10
        draw.text((x + 8, y + 8), titles[i], fill=(230, 235, 245))
        card_apple.paste(panels[i], (x, y + header_h))
        draw.text((x + 8, y + header_h + panel_h + 8), subtitles[i], fill=(160, 175, 195))

    card_apple.save(img_dir / "sprint_82_apple_comparison.png")
    print(f"Saved {img_dir / 'sprint_82_apple_comparison.png'}")

    # -------------------------------------------------------------
    # 2. Glass Sculpture Comparison Card
    # -------------------------------------------------------------
    orig_glass = Image.open("reports/sprint_80_total_validation/images/motif2_glass_1_original.png").convert("RGB")
    s80_mask = Image.open("reports/sprint_80_total_validation/images/motif2_glass_3_binary_mask.png").convert("RGB")
    s82_mask = Image.open(img_dir / "motif2_glass_repaired_mask.png").convert("RGB")
    s80_glass = Image.open("reports/sprint_80_total_validation/images/motif2_glass_5_htp_result.png").convert("RGB")
    s82_glass = Image.open(img_dir / "motif2_glass_repaired_htp.png").convert("RGB")

    # Zoom pedestal crop: y: 320..420, x: 190..310
    crop_ped = (190, 320, 310, 420)
    z_s80_g = s80_glass.crop(crop_ped).resize((panel_w, panel_h), Image.Resampling.NEAREST)
    z_s82_g = s82_glass.crop(crop_ped).resize((panel_w, panel_h), Image.Resampling.NEAREST)

    card_glass = Image.new("RGB", (card_w, card_h), (24, 26, 32))
    draw = ImageDraw.Draw(card_glass)

    panels_g = [
        orig_glass.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
        s80_mask.resize((panel_w, panel_h), Image.Resampling.NEAREST),
        s82_mask.resize((panel_w, panel_h), Image.Resampling.NEAREST),
        z_s82_g,
    ]
    titles_g = [
        "1. Original (Klarglas)",
        "2. S80 Maske (Abbruch y=369)",
        "3. S82 Maske (Verbunden y=387)",
        "4. S82 Sockel-Detail (Gold)"
    ]
    subtitles_g = [
        "Trkis/Cyan Klarglas",
        "12.024 px / Sockel fehlt",
        "14.502 px / Hals berbrckt",
        "RGB=(194,169,100) Reines Gold"
    ]

    for i in range(4):
        x = 10 + i * (panel_w + 5)
        y = 10
        draw.text((x + 8, y + 8), titles_g[i], fill=(230, 235, 245))
        card_glass.paste(panels_g[i], (x, y + header_h))
        draw.text((x + 8, y + header_h + panel_h + 8), subtitles_g[i], fill=(160, 175, 195))

    card_glass.save(img_dir / "sprint_82_glass_comparison.png")
    print(f"Saved {img_dir / 'sprint_82_glass_comparison.png'}")

    # -------------------------------------------------------------
    # 3. Master Comparison Grid (3 Rows x 4 Columns)
    # -------------------------------------------------------------
    jacket_orig = Image.open("reports/sprint_79_red_jacket/images/original_rote_jacke.jpg").convert("RGB")
    jacket_mask = Image.open("reports/sprint_80_total_validation/images/motif3_jacket_3_binary_mask.png").convert("RGB")
    jacket_res = Image.open("reports/sprint_80_total_validation/images/motif3_jacket_5_htp_result.png").convert("RGB")

    grid_w = panel_w * 4 + 30
    grid_h = (panel_h + header_h + footer_h) * 3 + 20
    master_grid = Image.new("RGB", (grid_w, grid_h), (20, 22, 28))
    draw = ImageDraw.Draw(master_grid)

    motifs_data = [
        {
            "name": "Motiv 1: Roter Apfel -> 24k Gold",
            "panels": [
                orig_apple.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
                s80_apple.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
                s82_apple.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
                z_s82.resize((panel_w, panel_h), Image.Resampling.NEAREST),
            ],
            "titles": ["Original", "S80 (Krater Min=0.6)", "S82 (Geheilt Min=54.2)", "Detail (0 Krater-Pixel)"],
        },
        {
            "name": "Motiv 2: Grne Glasskulptur -> 24k Gold",
            "panels": [
                orig_glass.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
                s80_glass.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
                s82_glass.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
                z_s82_g,
            ],
            "titles": ["Original", "S80 (Sockel Cyan)", "S82 (Sockel Gold)", "Detail (Goldener Sockel)"],
        },
        {
            "name": "Motiv 3: Rote Jacke -> Schwarzes Leder (Regression)",
            "panels": [
                jacket_orig.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
                jacket_mask.resize((panel_w, panel_h), Image.Resampling.NEAREST),
                jacket_res.resize((panel_w, panel_h), Image.Resampling.LANCZOS),
                jacket_res.crop((600, 800, 1200, 1400)).resize((panel_w, panel_h), Image.Resampling.LANCZOS),
            ],
            "titles": ["Original (1672x2500)", "Maske (37.11%)", "Ergebnis (Schwarzes Leder)", "Detail (Haut 100% geschtzt)"],
        },
    ]

    row_h = panel_h + header_h + footer_h
    for r_idx, m in enumerate(motifs_data):
        base_y = 10 + r_idx * row_h
        for c_idx in range(4):
            x = 10 + c_idx * (panel_w + 5)
            y = base_y
            draw.text((x + 8, y + 8), m["titles"][c_idx], fill=(230, 235, 245))
            master_grid.paste(m["panels"][c_idx], (x, y + header_h))

    master_grid.save(img_dir / "sprint_82_master_comparison_grid.png")
    print(f"Saved {img_dir / 'sprint_82_master_comparison_grid.png'}")

if __name__ == "__main__":
    build_comparisons()
