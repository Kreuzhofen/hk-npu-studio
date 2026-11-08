"""Precision Mask Generator and Visualizer for Sprint APP-ACCEPTANCE-51."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

REPO_ROOT = Path("C:/SnapdragonAI")
ORIG_PATH = REPO_ROOT / "acceptance48_text_to_image.png"

def create_precision_mask(orig_path: Path):
    im = Image.open(orig_path).convert("RGB")
    arr = np.array(im, dtype=float)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    # Spatial gating to the true apple component (around center X=358, Y=320)
    # The true apple is entirely contained within X in [250, 460], Y in [200, 430]
    spatial_gate = (np.arange(512)[None, :] >= 250) & (np.arange(512)[None, :] <= 460) & \
                   (np.arange(512)[:, None] >= 200) & (np.arange(512)[:, None] <= 430)

    # 1. Red fruit surface:
    # High red difference from green and blue
    diff = r - np.maximum(g, b)
    is_red_fruit = (diff > 30.0) & (r > 60.0) & spatial_gate

    # 2. Specular highlights inside the apple:
    # Highlights may be bright whitish/yellowish (e.g. r>180, g>140, b>120) inside the fruit bounds
    is_highlight = (r > 160.0) & (g > 120.0) & (b > 100.0) & spatial_gate & \
                   (np.arange(512)[None, :] >= 280) & (np.arange(512)[None, :] <= 360) & \
                   (np.arange(512)[:, None] >= 240) & (np.arange(512)[:, None] <= 330)

    raw_apple = is_red_fruit | is_highlight

    # 3. Fill holes inside the apple using PIL Max/Min filters
    raw_img = Image.fromarray((raw_apple.astype(np.uint8) * 255), mode="L")
    # Morphological Close
    closed_img = raw_img.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))
    closed_np = np.array(closed_img) > 128

    # 4. Exclude Stem and Stalk:
    # Stem is at X in [350, 372], Y in [180, 226] and top dimple pixels
    is_stem_zone = (np.arange(512)[None, :] >= 348) & (np.arange(512)[None, :] <= 374) & \
                   (np.arange(512)[:, None] >= 180) & (np.arange(512)[:, None] <= 226)
    # Also dark stalk pixels in crest indentation (lum < 50)
    crest_stalk = (np.arange(512)[None, :] >= 352) & (np.arange(512)[None, :] <= 370) & \
                  (np.arange(512)[:, None] >= 210) & (np.arange(512)[:, None] <= 235) & \
                  (np.mean(arr, axis=-1) < 55.0)

    # 5. Exclude Wooden Table surface and contact shadow:
    # Table below y=412 where surface is horizontal wood
    is_table_zone = (np.arange(512)[:, None] >= 418) & (arr[:,:,1] > arr[:,:,0] * 0.75)

    final_mask_np = closed_np & ~is_stem_zone & ~crest_stalk & ~is_table_zone

    # Morphological clean
    clean_img = Image.fromarray((final_mask_np.astype(np.uint8) * 255), mode="L")
    clean_img = clean_img.filter(ImageFilter.MedianFilter(3))

    # Apply soft Gaussian feathering (radius 2) for seamless edge blending
    feathered = clean_img.filter(ImageFilter.GaussianBlur(radius=2))

    # Measurements
    f_arr = np.array(feathered)
    active_px = int(np.sum(f_arr > 0))
    core_px = int(np.sum(f_arr >= 128))
    ys, xs = np.where(f_arr > 0)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    cx, cy = float(np.mean(xs)), float(np.mean(ys))

    print("=== PRECISION MASK CREATED ===")
    print(f"Active pixels (>0): {active_px} ({active_px/(512*512)*100:.2f}% of image)")
    print(f"Core pixels (>=128): {core_px} ({core_px/(512*512)*100:.2f}% of image)")
    print(f"Bounding Box: X=[{bbox[0]}, {bbox[2]}], Y=[{bbox[1]}, {bbox[3]}] (W={bbox[2]-bbox[0]+1}, H={bbox[3]-bbox[1]+1})")
    print(f"Centroid: ({cx:.2f}, {cy:.2f})")

    # Generate Overlay
    orig_rgba = im.convert("RGBA")
    overlay = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    # Semi-transparent magenta/cyan overlay where mask > 0
    f_norm = f_arr.astype(float) / 255.0
    overlay_arr = np.zeros((512, 512, 4), dtype=np.uint8)
    # Bright cyan/turquoise color (0, 230, 255) with alpha proportional to mask
    overlay_arr[..., 0] = 0
    overlay_arr[..., 1] = 230
    overlay_arr[..., 2] = 255
    overlay_arr[..., 3] = (f_norm * 140).astype(np.uint8) # semi-transparent

    overlay_img = Image.fromarray(overlay_arr, mode="RGBA")
    composite_overlay = Image.alpha_composite(orig_rgba, overlay_img).convert("RGB")

    return feathered, composite_overlay

if __name__ == "__main__":
    mask, overlay = create_precision_mask(ORIG_PATH)
    mask.save("reports/app_acceptance_50/test_precision_mask.png")
    overlay.save("reports/app_acceptance_50/test_precision_overlay.png")
    print("Saved test_precision_mask.png and test_precision_overlay.png")
