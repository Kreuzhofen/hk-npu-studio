"""Root Cause Analysis Script for Sprint APP-ACCEPTANCE-51 examining Sprint 50 results."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

REPO_ROOT = Path("C:/SnapdragonAI")
ORIG_PATH = REPO_ROOT / "acceptance48_text_to_image.png"
S50_MASK_PATH = REPO_ROOT / "reports/app_acceptance_50/acceptance50_mask.png"
S50_GOLDEN_PATH = REPO_ROOT / "reports/app_acceptance_50/acceptance50_golden_apple.png"
S50_RUN1_PATH = REPO_ROOT / "reports/app_acceptance_50/acceptance50_golden_apple_run1.png"
S50_RUN2_PATH = REPO_ROOT / "reports/app_acceptance_50/acceptance50_golden_apple_run2.png"

def analyze():
    orig_img = Image.open(ORIG_PATH).convert("RGB")
    orig_np = np.array(orig_img, dtype=np.float32) / 255.0
    hsv_orig = np.array(orig_img.convert("HSV"))
    h, s, v = hsv_orig[..., 0], hsv_orig[..., 1], hsv_orig[..., 2]

    # Ground truth apple body: red pixels with high saturation
    gt_apple = ((h < 25) | (h > 230)) & (s > 50) & (v > 20)
    # Exclude table
    table_mask = (v > 130) & (s < 80)
    gt_apple = gt_apple & ~table_mask
    gt_count = int(np.sum(gt_apple))
    y_gt, x_gt = np.where(gt_apple)
    gt_bbox = (int(x_gt.min()), int(y_gt.min()), int(x_gt.max()), int(y_gt.max()))

    # S50 Mask analysis
    mask_img = Image.open(S50_MASK_PATH).convert("L")
    mask_np = np.array(mask_img, dtype=np.uint8)
    mask_active = mask_np > 0
    mask_core = mask_np >= 128
    mask_count = int(np.sum(mask_active))
    core_count = int(np.sum(mask_core))

    y_m, x_m = np.where(mask_active)
    mask_bbox = (int(x_m.min()), int(y_m.min()), int(x_m.max()), int(y_m.max()))

    # Overlap / IoU between ground truth apple and mask
    intersection = np.sum(gt_apple & mask_core)
    union = np.sum(gt_apple | mask_core)
    mask_apple_iou = intersection / union

    # Mask bleeding outside apple
    mask_outside_apple = mask_core & ~gt_apple
    outside_count = int(np.sum(mask_outside_apple))

    # Apple missed by mask
    apple_missed = gt_apple & ~mask_core
    missed_count = int(np.sum(apple_missed))

    print("=== SPRINT 50 MASK MEASUREMENTS ===")
    print(f"Ground truth apple pixels: {gt_count}")
    print(f"Ground truth apple bbox: [x1={gt_bbox[0]}, y1={gt_bbox[1]}, x2={gt_bbox[2]}, y2={gt_bbox[3]}] (W={gt_bbox[2]-gt_bbox[0]+1}, H={gt_bbox[3]-gt_bbox[1]+1})")
    print(f"S50 Mask active pixels (>0): {mask_count}")
    print(f"S50 Mask core pixels (>=128): {core_count}")
    print(f"S50 Mask bbox: [x1={mask_bbox[0]}, y1={mask_bbox[1]}, x2={mask_bbox[2]}, y2={mask_bbox[3]}] (W={mask_bbox[2]-mask_bbox[0]+1}, H={mask_bbox[3]-mask_bbox[1]+1})")
    print(f"Mask vs GT Apple IoU: {mask_apple_iou:.4f}")
    print(f"Mask core pixels outside GT apple (overshoot): {outside_count} ({outside_count/gt_count*100:.2f}%)")
    print(f"GT Apple pixels missed by mask core: {missed_count} ({missed_count/gt_count*100:.2f}%)")

    # Inspect Golden Apple Run 2
    golden_img = Image.open(S50_GOLDEN_PATH).convert("RGB")
    golden_np = np.array(golden_img, dtype=np.uint8)
    diff = np.abs(np.array(orig_img, dtype=np.int16) - np.array(golden_img, dtype=np.int16))
    diff_px = np.any(diff > 0, axis=-1)
    diff_count = int(np.sum(diff_px))
    y_d, x_d = np.where(diff_px)
    diff_bbox = (int(x_d.min()), int(y_d.min()), int(x_d.max()), int(y_d.max())) if len(x_d) > 0 else (0,0,0,0)

    print("\n=== SPRINT 50 RESULT DIFFERENCE MEASUREMENTS ===")
    print(f"Total modified pixels in output: {diff_count}")
    print(f"Difference bounding box: {diff_bbox}")

    # Check Stem region specifically:
    # Stem in original: y < 45, x in [242, 272]
    orig_arr_u8 = np.array(orig_img)
    stem_region = (np.arange(512)[:, None] < 55) & (np.arange(512)[None, :] >= 238) & (np.arange(512)[None, :] <= 275)
    stem_diffs = np.sum(diff_px & stem_region)
    print(f"Modified pixels in stem region (y<55, x in [238, 275]): {stem_diffs}")

    # Golden fruit segmentation in golden apple
    hsv_gold = np.array(golden_img.convert("HSV"))
    hg, sg, vg = hsv_gold[..., 0], hsv_gold[..., 1], hsv_gold[..., 2]
    # In HSV: Hue for yellow is roughly 20-50 (out of 255 in PIL HSV, where 255 = 360 deg, so 20-50 = 28-70 deg)
    yellow_fruit = (hg >= 20) & (hg <= 55) & (sg >= 50) & (vg >= 50)
    red_fruit = ((hg < 15) | (hg > 235)) & (sg >= 60) & (vg >= 50)
    print(f"Yellow fruit pixels in output: {np.sum(yellow_fruit)}")
    print(f"Red residual pixels in output: {np.sum(red_fruit)}")

    # What does the generated fruit look like geometrically?
    # Segment any fruit in golden_img:
    fruit_in_gold = (yellow_fruit | red_fruit | ((hg < 25) & (sg > 40))) & (np.arange(512)[:, None] > 40)
    y_fg, x_fg = np.where(fruit_in_gold)
    if len(x_fg) > 0:
        gold_fruit_bbox = (int(x_fg.min()), int(y_fg.min()), int(x_fg.max()), int(y_fg.max()))
        gold_fruit_cx = float(np.mean(x_fg))
        gold_fruit_cy = float(np.mean(y_fg))
        orig_fruit_cx = float(np.mean(x_gt))
        orig_fruit_cy = float(np.mean(y_gt))
        print(f"Golden apple fruit bbox: {gold_fruit_bbox}")
        print(f"Original fruit centroid: ({orig_fruit_cx:.2f}, {orig_fruit_cy:.2f})")
        print(f"Golden fruit centroid: ({gold_fruit_cx:.2f}, {gold_fruit_cy:.2f})")
        print(f"Centroid shift: dx={gold_fruit_cx - orig_fruit_cx:.2f}, dy={gold_fruit_cy - orig_fruit_cy:.2f}")

        # Compute Shape IoU between original apple and golden apple
        fruit_iou = np.sum(gt_apple & fruit_in_gold) / np.sum(gt_apple | fruit_in_gold)
        print(f"Fruit Shape IoU (Original vs Generated): {fruit_iou:.4f}")

if __name__ == "__main__":
    analyze()
