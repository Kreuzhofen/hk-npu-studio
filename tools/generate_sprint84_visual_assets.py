"""
Generate Sprint 84 Diagnostic Visual Assets:
1. Apple Artifact Zoom Panel (Core shadow zone X:330..400, Y:260..380)
2. Glass Sculpture Artifact Zoom Panel (Black seam line X:190..250, Y:150..280)
3. Master Diagnostic Grid
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def make_apple_zoom():
    out_dir = Path("reports/sprint_84_material_artifact_audit/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    orig = Image.open("reports/appl_edit_test_49/appl_edit_49_original.png").convert("RGB")
    prim = Image.open("reports/sprint_82_material_repair/images/motif1_apple_repaired_primed.png").convert("RGB")
    s42  = Image.open("reports/sprint_82_material_repair/images/apple_seeds/apple_result_seed_42.png").convert("RGB")
    rep  = Image.open("reports/sprint_82_material_repair/images/motif1_apple_repaired_htp.png").convert("RGB")

    # Crop box: X in [330, 400], Y in [260, 380] -> 70x120 px, scale by 3x -> 210x360 px
    box = (330, 260, 400, 380)
    w, h = 210, 360

    c_orig = orig.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_prim = prim.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_s42  = s42.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_rep  = rep.crop(box).resize((w, h), Image.Resampling.NEAREST)

    pad = 12
    header_h = 45
    total_w = 4 * w + 5 * pad
    total_h = header_h + h + 2 * pad + 60

    canvas = Image.new("RGB", (total_w, total_h), (24, 26, 30))
    draw = ImageDraw.Draw(canvas)

    panels = [
        ("1. Original (Rot)", c_orig, "Realer Kernschatten (L=47.3)", (200, 100, 100)),
        ("2. Priming-Vorschau", c_prim, "Schatten in HSV vererbt (L=114.3)", (220, 180, 80)),
        ("3. Seed 42 Matrix", c_s42, "Lokale Vertiefung (L=73.5)", (220, 140, 60)),
        ("4. HTP Repariert (S43)", c_rep, "Dunkle Senkrechte Zone (L=84.1)", (240, 80, 80)),
    ]

    for i, (title, img, sub, color) in enumerate(panels):
        x = pad + i * (w + pad)
        y = header_h + pad
        draw.text((x + 5, 12), title, fill=(230, 235, 240))
        canvas.paste(img, (x, y))
        draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
        # Highlight vertical center line
        cx = x + int((360 - 330) * 3)
        draw.line([(cx, y), (cx, y + h)], fill=(255, 50, 50), width=1)
        draw.text((x + 5, y + h + 10), sub, fill=color)

    out_path = out_dir / "apple_artifact_crop_comparison.png"
    canvas.save(out_path, quality=95)
    print(f"Apple zoom saved to {out_path}")

def make_glass_zoom():
    out_dir = Path("reports/sprint_84_material_artifact_audit/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    orig = Image.open("reports/sprint_80_total_validation/images/motif2_glass_1_original.png").convert("RGB")
    mask = Image.open("reports/sprint_82_material_repair/images/motif2_glass_repaired_mask.png").convert("RGB")
    prim = Image.open("reports/sprint_82_material_repair/images/motif2_glass_repaired_primed.png").convert("RGB")
    rep  = Image.open("reports/sprint_82_material_repair/images/motif2_glass_repaired_htp.png").convert("RGB")

    # Crop box: X in [195, 255], Y in [155, 275] -> 60x120 px, scale by 3x -> 180x360 px
    box = (195, 155, 255, 275)
    w, h = 180, 360

    c_orig = orig.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_mask = mask.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_prim = prim.crop(box).resize((w, h), Image.Resampling.NEAREST)
    c_rep  = rep.crop(box).resize((w, h), Image.Resampling.NEAREST)

    pad = 12
    header_h = 45
    total_w = 4 * w + 5 * pad
    total_h = header_h + h + 2 * pad + 60

    canvas = Image.new("RGB", (total_w, total_h), (24, 26, 30))
    draw = ImageDraw.Draw(canvas)

    panels = [
        ("1. Original (Glas)", c_orig, "Sanfte Flanke (L=100.5)", (100, 180, 160)),
        ("2. Semantische Maske", c_mask, "100% homogen aktiv (Kein Spalt)", (200, 200, 200)),
        ("3. Priming-Vorschau", c_prim, "Homogenes Gold (L=83.2)", (220, 180, 80)),
        ("4. HTP Repariert", c_rep, "Schwarze Nahtlinie (L=1.5..10.8)", (255, 60, 60)),
    ]

    for i, (title, img, sub, color) in enumerate(panels):
        x = pad + i * (w + pad)
        y = header_h + pad
        draw.text((x + 5, 12), title, fill=(230, 235, 240))
        canvas.paste(img, (x, y))
        draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
        # Highlight vertical seam coordinate X=215
        cx = x + int((215 - 195) * 3)
        draw.line([(cx, y), (cx, y + h)], fill=(255, 40, 40), width=1)
        draw.text((x + 5, y + h + 10), sub, fill=color)

    out_path = out_dir / "glass_artifact_crop_comparison.png"
    canvas.save(out_path, quality=95)
    print(f"Glass zoom saved to {out_path}")

def make_diagnostic_overview():
    out_dir = Path("reports/sprint_84_material_artifact_audit/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    app_img = Image.open(out_dir / "apple_artifact_crop_comparison.png")
    gla_img = Image.open(out_dir / "glass_artifact_crop_comparison.png")

    w = max(app_img.width, gla_img.width)
    total_h = app_img.height + gla_img.height + 80

    canvas = Image.new("RGB", (w, total_h), (18, 20, 24))
    draw = ImageDraw.Draw(canvas)

    draw.rectangle([10, 10, w - 10, 50], fill=(30, 36, 46))
    draw.text((25, 20), "SPRINT 84: DIAGNOSTISCHES ARTEFAKT-AUDIT (APFEL & GLASSKULPTUR)", fill=(240, 245, 250))

    canvas.paste(app_img, (0, 60))
    canvas.paste(gla_img, ((w - gla_img.width) // 2, 60 + app_img.height + 10))

    out_path = out_dir / "sprint_84_diagnostic_overview.png"
    canvas.save(out_path, quality=95)
    print(f"Diagnostic overview saved to {out_path}")

    # Copy to brain artifact directory
    brain_dir = Path(r"C:\Users\holge\.gemini\antigravity-cli\brain\c991b454-d253-4b5d-9ce4-469780cc4864\images")
    if brain_dir.exists():
        canvas.save(brain_dir / "sprint_84_diagnostic_overview.png")
        app_img.save(brain_dir / "apple_artifact_crop_comparison.png")
        gla_img.save(brain_dir / "glass_artifact_crop_comparison.png")
        print(f"Copied visual assets to brain directory {brain_dir}")

if __name__ == "__main__":
    make_apple_zoom()
    make_glass_zoom()
    make_diagnostic_overview()
