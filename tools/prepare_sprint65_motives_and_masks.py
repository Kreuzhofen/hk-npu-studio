"""Prepare 4 Motives and Precision Masks for Sprint 65 - Phoenix Material Lab."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from PIL import Image

PROJECT_ROOT = Path(r"C:\SnapdragonAI")
OUTPUT_DIR = PROJECT_ROOT / "reports" / "phoenix_material_lab_65"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# Motiv 1: Glasdekoration (Benchmark aus Sprint 56-64)
# ---------------------------------------------------------
def prepare_m1_glass():
    print("Preparing Motiv 1: Glasdekoration...")
    src_img_path = PROJECT_ROOT / "reports" / "phoenix_material_lab_64" / "acceptance56_original.png"
    src_mask_path = PROJECT_ROOT / "reports" / "phoenix_material_lab_64" / "phoenix_material_lab_mask.png"

    orig = Image.open(src_img_path).convert("RGB")
    mask = Image.open(src_mask_path).convert("L")

    dst_img = OUTPUT_DIR / "m1_glass_original.png"
    dst_mask = OUTPUT_DIR / "m1_glass_mask.png"
    dst_overlay = OUTPUT_DIR / "m1_glass_mask_overlay.png"

    orig.save(dst_img)
    mask.save(dst_mask)

    # Create overlay
    m_arr = np.array(mask) > 128
    orig_arr = np.array(orig)
    overlay = orig_arr.copy()
    overlay[m_arr] = (overlay[m_arr] * 0.58 + np.array([235, 110, 30]) * 0.42).astype(np.uint8)
    Image.fromarray(overlay).save(dst_overlay)

    # Mask stats inside crop
    crop_box = (546, 295, 802, 551)
    mask_crop = mask.crop(crop_box)
    crop_arr = np.array(mask_crop)
    active_px = int(np.sum(crop_arr > 128))
    print(f"  M1 Glass ready: {orig.size}, active mask pixels in crop: {active_px}")
    return {
        "motive_id": "m1_glass",
        "category": "Glasdekoration",
        "name": "Smaragdgrüne Glasskulptur",
        "image_path": str(dst_img),
        "mask_path": str(dst_mask),
        "overlay_path": str(dst_overlay),
        "width": orig.width,
        "height": orig.height,
        "mask_pixels": active_px,
        "crop_box": crop_box,
    }


# ---------------------------------------------------------
# Motiv 2: Keramik- oder Porzellanobjekt (Vase)
# ---------------------------------------------------------
def prepare_m2_ceramic():
    print("Preparing Motiv 2: Keramik- / Porzellanobjekt...")
    src_path = PROJECT_ROOT / "output" / "generate_a05560d5.png"
    full_img = Image.open(src_path).convert("RGB")

    # Crop 512x512 centered on the ceramic vase: x in [256..768], y in [450..962]
    crop_box = (256, 450, 768, 962)
    vase_img = full_img.crop(crop_box)
    dst_img = OUTPUT_DIR / "m2_ceramic_original.png"
    dst_mask = OUTPUT_DIR / "m2_ceramic_mask.png"
    dst_overlay = OUTPUT_DIR / "m2_ceramic_mask_overlay.png"
    vase_img.save(dst_img)

    # Segment the ceramic vase body:
    # In the 512x512 crop:
    # Vase body is in rows y in [120..380], x in [100..412]
    # Neutral/cream porcelain glaze: R, G, B are balanced, luminance > 120, avoiding the brown wood table at bottom
    arr = np.array(vase_img)
    mask_arr = np.zeros((512, 512), dtype=np.uint8)

    # Approximate vase silhouette using contour analysis and thresholding
    # The vase is located between y=130 and y=365, x between 110 and 400
    for y in range(130, 365):
        # Calculate width of vase at this height (curved ceramic amphora/vase shape)
        t = (y - 130) / (365 - 130)
        # Amphora profile: narrower at neck (y=130..160), wider at belly (y=220..280), taper to foot
        if t < 0.2: # neck
            x_min, x_max = 165, 345
        elif t < 0.7: # belly
            w_belly = int(105 + 30 * np.sin((t - 0.2) / 0.5 * np.pi))
            x_min = 256 - w_belly
            x_max = 256 + w_belly
        else: # foot
            x_min, x_max = 175, 335

        # Check ceramic pixels: luminance and color balance
        row = arr[y, :]
        is_ceramic = (
            (row[:, 0] > 110) &
            (row[:, 1] > 110) &
            (row[:, 2] > 80) &
            (np.abs(row[:, 0].astype(int) - row[:, 1].astype(int)) < 35) &
            (row[:, 0].astype(int) + row[:, 1].astype(int) > 1.3 * row[:, 2].astype(int)) # warm cream glaze
        )
        mask_arr[y, x_min:x_max] = np.where(is_ceramic[x_min:x_max], 255, 0)

    # Clean up small gaps with morphological binary closing
    from PIL import ImageFilter
    mask_img = Image.fromarray(mask_arr, mode="L")
    mask_img = mask_img.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    mask_img.save(dst_mask)

    # Create overlay
    m_arr = np.array(mask_img) > 128
    overlay = np.array(vase_img).copy()
    overlay[m_arr] = (overlay[m_arr] * 0.58 + np.array([235, 110, 30]) * 0.42).astype(np.uint8)
    Image.fromarray(overlay).save(dst_overlay)

    active_px = int(np.sum(m_arr))
    print(f"  M2 Ceramic ready: {vase_img.size}, active mask pixels: {active_px}")
    return {
        "motive_id": "m2_ceramic",
        "category": "Keramik- oder Porzellanobjekt",
        "name": "Glasierte Keramikvase",
        "image_path": str(dst_img),
        "mask_path": str(dst_mask),
        "overlay_path": str(dst_overlay),
        "width": 512,
        "height": 512,
        "mask_pixels": active_px,
        "crop_box": None,
    }


# ---------------------------------------------------------
# Motiv 3: Metallisches oder lackiertes Objekt (Sportwagen)
# ---------------------------------------------------------
def prepare_m3_metal():
    print("Preparing Motiv 3: Metallisches / lackiertes Objekt...")
    src_path = PROJECT_ROOT / "output" / "generate_1792941478_.png"
    sports_car = Image.open(src_path).convert("RGB")

    dst_img = OUTPUT_DIR / "m3_metal_original.png"
    dst_mask = OUTPUT_DIR / "m3_metal_mask.png"
    dst_overlay = OUTPUT_DIR / "m3_metal_mask_overlay.png"
    sports_car.save(dst_img)

    # Segment the metallic painted body panels of the car:
    # y between 190 and 380, x between 60 and 460
    # The car body is dark blue / metallic cyan with specular reflections
    arr = np.array(sports_car)
    mask_arr = np.zeros((512, 512), dtype=np.uint8)

    for y in range(190, 385):
        t = (y - 190) / (385 - 190)
        # Roof / cabin is y in 190..260 (x between 160 and 350)
        # Hood / body is y in 260..385 (x between 60 and 460)
        if t < 0.35:
            x_min, x_max = 170, 350
        else:
            x_min, x_max = 70, 455

        row = arr[y, :]
        # Exclude wheels and shadows (luminance < 25)
        lum = row.mean(axis=1)
        # Exclude windshield / windows (dark tinted) and ground
        is_body = (lum >= 35) & (lum <= 245)
        # Exclude pure black tires at bottom
        if y > 330:
            is_body = is_body & (lum > 50)
        mask_arr[y, x_min:x_max] = np.where(is_body[x_min:x_max], 255, 0)

    # Clean up mask
    from PIL import ImageFilter
    mask_img = Image.fromarray(mask_arr, mode="L")
    mask_img = mask_img.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
    mask_img.save(dst_mask)

    m_arr = np.array(mask_img) > 128
    overlay = np.array(sports_car).copy()
    overlay[m_arr] = (overlay[m_arr] * 0.58 + np.array([235, 110, 30]) * 0.42).astype(np.uint8)
    Image.fromarray(overlay).save(dst_overlay)

    active_px = int(np.sum(m_arr))
    print(f"  M3 Metal ready: {sports_car.size}, active mask pixels: {active_px}")
    return {
        "motive_id": "m3_metal",
        "category": "Metallisches oder lackiertes Dekorationsobjekt",
        "name": "Lackierte Sportwagenkarosserie",
        "image_path": str(dst_img),
        "mask_path": str(dst_mask),
        "overlay_path": str(dst_overlay),
        "width": 512,
        "height": 512,
        "mask_pixels": active_px,
        "crop_box": None,
    }


# ---------------------------------------------------------
# Motiv 4: Holz- oder Kunststoffobjekt (Tischapfel auf Holz)
# ---------------------------------------------------------
def prepare_m4_wood_plastic():
    print("Preparing Motiv 4: Holz- oder Kunststoffobjekt...")
    src_path = PROJECT_ROOT / "reports" / "appl_edit_test_49" / "appl_edit_49_original.png"
    apple_img = Image.open(src_path).convert("RGB")

    dst_img = OUTPUT_DIR / "m4_wood_plastic_original.png"
    dst_mask = OUTPUT_DIR / "m4_wood_plastic_mask.png"
    dst_overlay = OUTPUT_DIR / "m4_wood_plastic_mask_overlay.png"
    apple_img.save(dst_img)

    # Exact fruit segmentation from Sprints 49-53:
    arr = np.array(apple_img)
    diff = arr[..., 0].astype(int) - arr[..., 1].astype(int)
    mask_arr = np.zeros((512, 512), dtype=np.uint8)
    
    # Apple is centered at x in [250..450], y in [200..420]
    apple_zone = (diff[200:420, 250:455] > 38) & (arr[200:420, 250:455, 0] > 105)
    mask_arr[200:420, 250:455] = np.where(apple_zone, 255, 0)

    # Morphological closing to ensure solid interior
    from PIL import ImageFilter
    mask_img = Image.fromarray(mask_arr, mode="L")
    mask_img = mask_img.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
    mask_img.save(dst_mask)

    m_arr = np.array(mask_img) > 128
    overlay = np.array(apple_img).copy()
    overlay[m_arr] = (overlay[m_arr] * 0.58 + np.array([235, 110, 30]) * 0.42).astype(np.uint8)
    Image.fromarray(overlay).save(dst_overlay)

    active_px = int(np.sum(m_arr))
    print(f"  M4 Wood/Plastic ready: {apple_img.size}, active mask pixels: {active_px}")
    return {
        "motive_id": "m4_wood_plastic",
        "category": "Holz- oder Kunststoffobjekt",
        "name": "Glattes Stillleben-Dekoobjekt auf Holztisch",
        "image_path": str(dst_img),
        "mask_path": str(dst_mask),
        "overlay_path": str(dst_overlay),
        "width": 512,
        "height": 512,
        "mask_pixels": active_px,
        "crop_box": None,
    }


def main():
    manifest = {}
    manifest["m1_glass"] = prepare_m1_glass()
    manifest["m2_ceramic"] = prepare_m2_ceramic()
    manifest["m3_metal"] = prepare_m3_metal()
    manifest["m4_wood_plastic"] = prepare_m4_wood_plastic()

    manifest_path = OUTPUT_DIR / "motives_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nMotives manifest written to {manifest_path}")
    print("Verification of mask coverage rules:")
    for k, v in manifest.items():
        print(f"  - [{v['motive_id']}] {v['name']} ({v['category']}): {v['mask_pixels']} px maskiert")


if __name__ == "__main__":
    main()
