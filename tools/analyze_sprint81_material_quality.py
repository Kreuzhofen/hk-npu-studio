"""
Sprint 81 Analysis Tool: Material Quality Refinement Investigation
HK NPU STUDIO (Phoenix Architecture)

Analyzes:
1. Golden Apple: Dark indented spot analysis (mask, priming, prompt, SD1.5 inpainting).
2. Glass Sculpture: Cyan/green remnants at pedestal/base (inside vs outside mask, transition).
3. Red Jacket: Regression verification.
"""

import sys
import json
from pathlib import Path
import numpy as np
from PIL import Image

def analyze_apple():
    print("=== MOTIF 1: GOLDEN APPLE ANALYSIS ===")
    img_dir = Path("reports/sprint_80_total_validation/images")
    orig_path = img_dir / "motif1_apple_1_original.png"
    mask_path = img_dir / "motif1_apple_3_binary_mask.png"
    prime_path = img_dir / "motif1_apple_4_primed_preview.png"
    res_path = img_dir / "motif1_apple_5_htp_result.png"

    orig = np.array(Image.open(orig_path).convert("RGB"), dtype=np.float32)
    mask = np.array(Image.open(mask_path).convert("L")) > 0
    prime = np.array(Image.open(prime_path).convert("RGB"), dtype=np.float32)
    res = np.array(Image.open(res_path).convert("RGB"), dtype=np.float32)

    # BBox of entire apple mask
    ys, xs = np.where(mask)
    print(f"Apple Mask: {len(ys)} px, y=[{ys.min()}, {ys.max()}], x=[{xs.min()}, {xs.max()}], center=({ys.mean():.1f}, {xs.mean():.1f})")

    # Let's inspect the original apple image:
    # What are the colors and luminance of the original apple?
    lum_orig = 0.299 * orig[..., 0] + 0.587 * orig[..., 1] + 0.114 * orig[..., 2]
    lum_prime = 0.299 * prime[..., 0] + 0.587 * prime[..., 1] + 0.114 * prime[..., 2]
    lum_res = 0.299 * res[..., 0] + 0.587 * res[..., 1] + 0.114 * res[..., 2]

    # Compare luminance in the original apple vs primed vs result
    orig_in_mask = lum_orig[mask]
    prime_in_mask = lum_prime[mask]
    res_in_mask = lum_res[mask]

    print(f"Original Apple in mask luminance: min={orig_in_mask.min():.1f}, mean={orig_in_mask.mean():.1f}, max={orig_in_mask.max():.1f}")
    print(f"Primed Apple in mask luminance:   min={prime_in_mask.min():.1f}, mean={prime_in_mask.mean():.1f}, max={prime_in_mask.max():.1f}")
    print(f"Result Apple in mask luminance:   min={res_in_mask.min():.1f}, mean={res_in_mask.mean():.1f}, max={res_in_mask.max():.1f}")

    # Let's find where the result is significantly darker than the rest of the golden surface
    # Golden surface is typically > 120 luminance. Dark dent is where it dips low.
    # Where is lum_res < 80 inside mask?
    dark_mask = (lum_res < 70) & mask
    if np.any(dark_mask):
        dys, dxs = np.where(dark_mask)
        print(f"Dark spot (<70 lum): {len(dys)} px, y=[{dys.min()}, {dys.max()}], x=[{dxs.min()}, {dxs.max()}], center=({dys.mean():.1f}, {dxs.mean():.1f})")
        # Check original at that dark spot
        print(f"Original at dark spot: lum_mean={lum_orig[dark_mask].mean():.1f}, R={orig[dark_mask, 0].mean():.1f}, G={orig[dark_mask, 1].mean():.1f}, B={orig[dark_mask, 2].mean():.1f}")
        print(f"Primed at dark spot:   lum_mean={lum_prime[dark_mask].mean():.1f}, R={prime[dark_mask, 0].mean():.1f}, G={prime[dark_mask, 1].mean():.1f}, B={prime[dark_mask, 2].mean():.1f}")
        print(f"Result at dark spot:   lum_mean={lum_res[dark_mask].mean():.1f}, R={res[dark_mask, 0].mean():.1f}, G={res[dark_mask, 1].mean():.1f}, B={res[dark_mask, 2].mean():.1f}")

    # Let's check the very darkest cluster (< 50)
    vdark_mask = (lum_res < 45) & mask
    if np.any(vdark_mask):
        vys, vxs = np.where(vdark_mask)
        print(f"Very dark spot (<45 lum): {len(vys)} px, y=[{vys.min()}, {vys.max()}], x=[{vxs.min()}, {vxs.max()}], center=({vys.mean():.1f}, {vxs.mean():.1f})")

    # Let's also check if there is an indentation / shadow in the original apple!
    # Where was the stem and the natural cavity of the apple in the original image?
    # In the original apple, where is the stem or cavity?
    # Let's inspect original around top of apple (ys.min() is 223, ys.max() is 447)
    # y=223 to 260 is top of apple.

def analyze_glass():
    print("\n=== MOTIF 2: GLASS SCULPTURE ANALYSIS ===")
    img_dir = Path("reports/sprint_80_total_validation/images")
    orig_path = img_dir / "motif2_glass_1_original.png"
    mask_path = img_dir / "motif2_glass_3_binary_mask.png"
    prime_path = img_dir / "motif2_glass_4_primed_preview.png"
    res_path = img_dir / "motif2_glass_5_htp_result.png"

    orig = np.array(Image.open(orig_path).convert("RGB"), dtype=np.float32)
    mask = np.array(Image.open(mask_path).convert("L")) > 0
    prime = np.array(Image.open(prime_path).convert("RGB"), dtype=np.float32)
    res = np.array(Image.open(res_path).convert("RGB"), dtype=np.float32)

    ys, xs = np.where(mask)
    print(f"Glass Sculpture Mask: {len(ys)} px, y=[{ys.min()}, {ys.max()}], x=[{xs.min()}, {xs.max()}], center=({ys.mean():.1f}, {xs.mean():.1f})")

    # In Sprint 80, the mask covers y=[117, 369], x=[205, 285].
    # Where is the pedestal/base (Sockel) of the glass sculpture?
    # Look at bottom of sculpture: y around 320 to 370 or beyond!
    # Let's check original colors in the pedestal region (y: 300 to 400, x: 180 to 320)
    # Cyan/green colors have Hue around 120-190 deg (or G > R + 15, B > R + 10)
    # Let's inspect original image for cyan/green pixels:
    orig_hsv = np.array(Image.open(orig_path).convert("HSV"))
    h = orig_hsv[..., 0] # 0-255 corresponds to 0-360 deg. Green is ~85 (120 deg), Cyan is ~128 (180 deg)
    s = orig_hsv[..., 1]
    v = orig_hsv[..., 2]

    # Cyan/green in HSV: h between 60 and 150, s > 40, v > 40
    cyan_green = (h >= 50) & (h <= 160) & (s >= 35) & (v >= 35)
    print(f"Total cyan/green pixels in original image: {cyan_green.sum()}")

    # How many of these cyan/green pixels are inside the mask vs outside the mask?
    cg_inside_mask = cyan_green & mask
    cg_outside_mask = cyan_green & (~mask)
    print(f"Cyan/green pixels INSIDE mask:  {cg_inside_mask.sum()}")
    print(f"Cyan/green pixels OUTSIDE mask: {cg_outside_mask.sum()}")

    # Where are the cyan/green pixels outside the mask?
    if cg_outside_mask.sum() > 0:
        cys, cxs = np.where(cg_outside_mask)
        print(f"Cyan/green OUTSIDE mask bbox: y=[{cys.min()}, {cys.max()}], x=[{cxs.min()}, {cxs.max()}], center=({cys.mean():.1f}, {cxs.mean():.1f})")
        # Focus on the pedestal/base region: y >= 300
        cg_base_outside = cg_outside_mask & (np.arange(512)[:, None] >= 300)
        print(f"Cyan/green OUTSIDE mask at base (y >= 300): {cg_base_outside.sum()} px")
        if cg_base_outside.sum() > 0:
            bys, bxs = np.where(cg_base_outside)
            print(f"Base cyan/green outside bbox: y=[{bys.min()}, {bys.max()}], x=[{bxs.min()}, {bxs.max()}]")

    # Now let's examine the RESULT image (res):
    res_hsv = np.array(Image.open(res_path).convert("HSV"))
    res_h = res_hsv[..., 0]
    res_s = res_hsv[..., 1]
    res_v = res_hsv[..., 2]

    res_cyan_green = (res_h >= 50) & (res_h <= 160) & (res_s >= 35) & (res_v >= 35)
    print(f"\nTotal cyan/green in RESULT image: {res_cyan_green.sum()}")
    print(f"Result cyan/green INSIDE mask:  {(res_cyan_green & mask).sum()} px")
    print(f"Result cyan/green OUTSIDE mask: {(res_cyan_green & (~mask)).sum()} px")

    # If any cyan/green is inside mask in result, where is it?
    if (res_cyan_green & mask).sum() > 0:
        rys, rxs = np.where(res_cyan_green & mask)
        print(f"Result cyan/green INSIDE mask bbox: y=[{rys.min()}, {rys.max()}], x=[{rxs.min()}, {rxs.max()}]")

if __name__ == "__main__":
    analyze_apple()
    analyze_glass()
