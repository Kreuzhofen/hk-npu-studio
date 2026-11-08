"""Precision Mask Builder and Verification for Sprint APP-ACCEPTANCE-56."""
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI")
os.chdir(str(REPO_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from PIL import Image

from widgets.phoenix.inpainting_canvas import PhoenixInpaintingCanvas
from widgets.phoenix.theme import PHOENIX_THEME

REPORTS_DIR = Path("reports/app_acceptance_56")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

SRC_ORIGINAL = Path("reports/app_acceptance_54/acceptance54_original.png")
DST_ORIGINAL = REPORTS_DIR / "acceptance56_original.png"
MASK_OUT = REPORTS_DIR / "acceptance56_mask.png"
OVERLAY_OUT = REPORTS_DIR / "acceptance56_mask_overlay.png"
ZOOM_OVERLAY_OUT = REPORTS_DIR / "acceptance56_zoom_overlay.png"

def create_mask_overlay(source: Image.Image, mask: Image.Image) -> Image.Image:
    """Create semi-transparent canvas mask overlay using Phoenix theme accent."""
    composite = source.convert("RGBA")
    accent = PHOENIX_THEME.accent.lstrip("#")
    color = tuple(int(accent[i:i + 2], 16) for i in (0, 2, 4))
    alpha = mask.point(lambda v: round(v * 0.45))
    overlay = Image.new("RGBA", source.size, (*color, 0))
    overlay.putalpha(alpha)
    return Image.alpha_composite(composite, overlay).convert("RGB")

def main():
    if not SRC_ORIGINAL.is_file():
        raise FileNotFoundError(f"Source image missing: {SRC_ORIGINAL}")

    # Copy original to sprint 56 folder
    shutil.copy2(SRC_ORIGINAL, DST_ORIGINAL)
    print(f"Copied original to: {DST_ORIGINAL}")

    with Image.open(DST_ORIGINAL) as opened:
        source_img = opened.convert("RGB")
    w, h = source_img.size

    mask = Image.new("L", (w, h), 0)

    # Precision brush strokes:
    # Brush size: 18 px (well within 16-24 px requirement)
    # Hardness: 0.70 (within 60-80% requirement)
    brush_size = 18
    hardness = 0.70

    # 1. Main axis of the decorative ornament:
    PhoenixInpaintingCanvas.paint_mask(mask, (679, 375), (673, 470), brush_size=brush_size, hardness=hardness)
    # 2. Secondary interior fill:
    PhoenixInpaintingCanvas.paint_mask(mask, (674, 395), (670, 465), brush_size=16, hardness=hardness)
    # 3. Clean separation from the right-side tablecloth:
    PhoenixInpaintingCanvas.paint_mask(mask, (690, 370), (690, 475), brush_size=10, hardness=1.0, erase=True)

    m_arr = np.array(mask)
    img_arr = np.array(source_img)

    # Measure mask composition:
    active = m_arr > 10
    total_masked = np.sum(active)
    ys, xs = np.where(active)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    print(f"Mask active pixels (>10): {total_masked}")
    print(f"Mask BBox: {bbox} (width: {bbox[2]-bbox[0]+1}, height: {bbox[3]-bbox[1]+1})")

    masked_r = img_arr[active, 0]
    masked_g = img_arr[active, 1]
    masked_b = img_arr[active, 2]

    # White tablecloth / background pixels: R>225, G>225, B>225
    is_env = (masked_r > 225) & (masked_g > 225) & (masked_b > 225)
    env_pixels = np.sum(is_env)
    env_pct = float(env_pixels / total_masked * 100.0)
    obj_pct = 100.0 - env_pct

    print(f"Composition: Object = {obj_pct:.2f}%, Environment = {env_pct:.2f}%")

    mask.save(MASK_OUT, format="PNG")
    print(f"Saved binary mask: {MASK_OUT}")

    overlay = create_mask_overlay(source_img, mask)
    overlay.save(OVERLAY_OUT, format="PNG")
    print(f"Saved mask overlay: {OVERLAY_OUT}")

    # Zoom in around the target object (X: 630..730, Y: 340..510)
    zoom_box = (630, 340, 730, 510)
    zoom = overlay.crop(zoom_box).resize((400, 680), Image.Resampling.NEAREST)
    zoom.save(ZOOM_OVERLAY_OUT, format="PNG")
    print(f"Saved zoomed overlay: {ZOOM_OVERLAY_OUT}")

    return obj_pct >= 90.0 and env_pct <= 10.0

if __name__ == "__main__":
    import sys
    ok = main()
    sys.exit(0 if ok else 1)
