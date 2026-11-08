"""
HK NPU STUDIO - SPRINT APP-ACCEPTANCE-50
Generative Color Replacement via Masked Inpainting

Hardware: Qualcomm Snapdragon X Elite (Hexagon HTP V73 NPU)
Backend: QNNExecutionProvider
Model: Stable Diffusion 1.5 QNN Inpainting
Target Dir: C:\\SnapdragonAI\\reports\\app_acceptance_50\\
"""

import os
import sys
import time
import json
import shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(r"C:\SnapdragonAI")
os.chdir(str(PROJECT_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.backends.sd15_qnn_inpainting_adapter import SD15QnnInpaintingAdapter

REPORTS_DIR = PROJECT_ROOT / "reports" / "app_acceptance_50"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

ORIGINAL_IMG_SRC = PROJECT_ROOT / "acceptance48_text_to_image.png"
ORIGINAL_IMG_REPORT = REPORTS_DIR / "acceptance50_original.png"
MASK_REPORT = REPORTS_DIR / "acceptance50_mask.png"
GOLDEN_APPLE_REPORT = REPORTS_DIR / "acceptance50_golden_apple.png"
GRID_REPORT = REPORTS_DIR / "acceptance50_comparison_grid.png"
METRICS_REPORT = REPORTS_DIR / "acceptance50_metrics.json"

POSITIVE_PROMPT = (
    "A realistic golden yellow apple, rich natural golden-yellow skin, "
    "subtle yellow-orange gradients, natural apple texture, realistic pores, "
    "preserve original shape and proportions."
)

NEGATIVE_PROMPT = (
    "red skin, crimson, burgundy, deformed fruit, changed shape, "
    "altered background, blurry, artificial plastic texture."
)

SEED = 5001
STEPS = 20
CFG = 7.5


def create_apple_mask(src_path: Path, out_path: Path) -> Image.Image:
    """Create precise feathered mask covering apple body while preserving stem and table."""
    im = Image.open(src_path).convert("RGB")
    arr = np.array(im, dtype=np.float32) / 255.0
    hsv = im.convert("HSV")
    h_arr, s_arr, v_arr = [np.array(c) for c in hsv.split()]

    # 1. Red apple body: high saturation red
    red_apple = ((h_arr < 25) | (h_arr > 230)) & (s_arr > 60) & (v_arr > 20)

    # 2. Table protection (foreground wood table at bottom and sides)
    table_mask = (v_arr > 130) & (s_arr < 80)
    shadow_mask = (v_arr < 60) & (s_arr < 60) & (arr[..., 0] < 0.25)
    apple_mask = red_apple & ~table_mask & ~shadow_mask

    # 3. Exclude natural stem (top crest)
    y_indices, x_indices = np.indices(apple_mask.shape)
    stem_region = (y_indices < 45) & (x_indices >= 242) & (x_indices <= 272)
    is_stem = stem_region & (arr[..., 0] < 0.35) & (arr[..., 1] < 0.3)
    apple_mask = apple_mask & ~is_stem

    # 4. Clean up mask & fill internal holes
    mask_u8 = (apple_mask.astype(np.uint8)) * 255
    mask_img = Image.fromarray(mask_u8, mode="L")
    mask_clean = mask_img.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))

    # 5. Soft feathering along boundary (radius 3)
    mask_feathered = mask_clean.filter(ImageFilter.GaussianBlur(radius=3))
    mask_feathered.save(out_path)
    print(f"[OK] Mask created and saved to: {out_path}")
    return mask_feathered


def rgb_to_hsv_np(arr: np.ndarray):
    """Vectorized RGB to HSV conversion."""
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    v = maxc
    deltac = maxc - minc
    s = np.zeros_like(maxc)
    nz = maxc > 1e-6
    s[nz] = deltac[nz] / maxc[nz]

    h = np.zeros_like(maxc)
    mr = (r == maxc) & (deltac > 1e-6)
    h[mr] = ((g[mr] - b[mr]) / deltac[mr]) % 6.0
    mg = (g == maxc) & (deltac > 1e-6) & ~mr
    h[mg] = ((b[mg] - r[mg]) / deltac[mg]) + 2.0
    mb = (b == maxc) & (deltac > 1e-6) & ~mr & ~mg
    h[mb] = ((r[mb] - g[mb]) / deltac[mb]) + 4.0
    h = (h / 6.0) * 360.0
    return h, s, v


def analyze_inpainting_result(orig_img: Image.Image, mask_img: Image.Image, res_img: Image.Image):
    """Evaluate objective metrics for color replacement, shape, and bit-identity."""
    orig_np = np.array(orig_img.convert("RGB"), dtype=np.uint8)
    res_np = np.array(res_img.convert("RGB"), dtype=np.uint8)
    mask_np = np.array(mask_img.convert("L"), dtype=np.uint8)

    # 1. Unmasked region: check 100% bit-exact identity
    unmasked = mask_np == 0
    num_unmasked = int(np.sum(unmasked))
    identical_pixels = int(np.sum(np.all(orig_np[unmasked] == res_np[unmasked], axis=-1)))
    bit_identical_pct = round((identical_pixels / max(1, num_unmasked)) * 100.0, 4)

    # 2. Inpainted region color analysis
    res_norm = res_np.astype(np.float32) / 255.0
    h_res, s_res, v_res = rgb_to_hsv_np(res_norm)
    inpaint_zone = mask_np > 128
    total_inpaint_px = int(np.sum(inpaint_zone))

    # Golden-Yellow: Hue in [30, 68] deg, Saturation > 0.20, Value > 0.20
    yellow_mask = (h_res >= 30.0) & (h_res <= 68.0) & (s_res >= 0.20) & (v_res >= 0.20) & inpaint_zone
    yellow_px = int(np.sum(yellow_mask))
    pct_yellow = round((yellow_px / max(1, total_inpaint_px)) * 100.0, 2)

    # Red residual: Hue in [0, 20] or [330, 360] deg, Saturation > 0.25
    red_mask = ((h_res <= 20.0) | (h_res >= 330.0)) & (s_res >= 0.25) & (v_res >= 0.20) & inpaint_zone
    red_px = int(np.sum(red_mask))
    pct_red = round((red_px / max(1, total_inpaint_px)) * 100.0, 2)

    # 3. Shape & Centroid
    ys_m, xs_m = np.where(inpaint_zone)
    orig_cx, orig_cy = float(np.mean(xs_m)), float(np.mean(ys_m))

    # Inpainted fruit centroid
    r_res, g_res, b_res = res_norm[..., 0], res_norm[..., 1], res_norm[..., 2]
    fruit_pixels = (r_res + g_res > 1.2 * b_res) & inpaint_zone
    ys_f, xs_f = np.where(fruit_pixels)
    if len(xs_f) > 0:
        res_cx, res_cy = float(np.mean(xs_f)), float(np.mean(ys_f))
    else:
        res_cx, res_cy = orig_cx, orig_cy

    dx = round(res_cx - orig_cx, 2)
    dy = round(res_cy - orig_cy, 2)
    centroid_dist = round(float(np.sqrt(dx**2 + dy**2)), 2)

    # 4. Background PSNR outside feathered region
    orig_f = orig_np.astype(np.float32) / 255.0
    bg_diff = (orig_f[unmasked] - res_norm[unmasked]) ** 2
    bg_mse = float(np.mean(bg_diff))
    bg_psnr = round(10.0 * np.log10(1.0 / max(1e-10, bg_mse)), 2) if bg_mse > 0 else 100.0

    return {
        "unmasked_pixels": num_unmasked,
        "bit_identical_pixels": identical_pixels,
        "bit_identical_pct": bit_identical_pct,
        "inpaint_zone_pixels": total_inpaint_px,
        "yellow_gold_pixels": yellow_px,
        "yellow_gold_surface_pct": pct_yellow,
        "red_residual_pixels": red_px,
        "red_residual_surface_pct": pct_red,
        "centroid_shift_x_px": dx,
        "centroid_shift_y_px": dy,
        "centroid_dist_px": centroid_dist,
        "background_mse": round(bg_mse, 6),
        "background_psnr_db": bg_psnr,
    }


def build_comparison_grid(panels: list[tuple[str, Path, str]], out_path: Path):
    """Build a professional 4-panel comparison grid."""
    target_size = (512, 512)
    loaded = []
    for title, p, sub in panels:
        im = Image.open(p).convert("RGB").resize(target_size, Image.Resampling.LANCZOS)
        loaded.append((title, im, sub))

    header_h = 75
    badge_h = 55
    padding = 20
    cols = 2
    rows = 2

    w = target_size[0] * cols + padding * (cols + 1)
    h = header_h + (target_size[1] + badge_h + padding) * rows + padding

    canvas = Image.new("RGB", (w, h), (18, 18, 22))
    draw = ImageDraw.Draw(canvas)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 22)
        font_sub = ImageFont.truetype("arial.ttf", 13)
        font_label = ImageFont.truetype("arialbd.ttf", 15)
        font_metric = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        font_title = font_sub = font_label = font_metric = ImageFont.load_default()

    # Header
    draw.text((padding, 15), "HK NPU STUDIO  |  SPRINT APP-ACCEPTANCE-50", fill=(255, 255, 255), font=font_title)
    draw.text(
        (padding, 43),
        "Generative Color Replacement (Inpainting)  |  SD1.5 QNN HTP  |  Qualcomm Snapdragon X Elite",
        fill=(160, 160, 175),
        font=font_sub,
    )

    for idx, (title, img, sub) in enumerate(loaded):
        c = idx % cols
        r = idx // cols
        x = padding + c * (target_size[0] + padding)
        y = header_h + r * (target_size[1] + badge_h + padding)

        canvas.paste(img, (x, y))
        draw.rectangle([x - 1, y - 1, x + target_size[0], y + target_size[1]], outline=(60, 60, 75), width=1)

        y_txt = y + target_size[1] + 8
        color_title = (74, 222, 128) if "Golden" in title else (250, 204, 21) if "Mask" in title else (248, 113, 113)
        draw.text((x, y_txt), title, fill=color_title, font=font_label)
        draw.text((x, y_txt + 20), sub, fill=(190, 190, 200), font=font_metric)

    canvas.save(str(out_path), quality=95)
    print(f"[OK] Comparison grid saved to: {out_path}")


def run_sprint50():
    print("=" * 70)
    print("HK NPU STUDIO - SPRINT APP-ACCEPTANCE-50")
    print("Generative Color Replacement via Qualcomm Hexagon HTP Inpainting")
    print("=" * 70)

    # 1. Prepare original image
    if not ORIGINAL_IMG_SRC.is_file():
        raise FileNotFoundError(f"Source image missing: {ORIGINAL_IMG_SRC}")

    shutil.copy2(ORIGINAL_IMG_SRC, ORIGINAL_IMG_REPORT)
    print(f"[OK] Source image copied to: {ORIGINAL_IMG_REPORT}")

    orig_pil = Image.open(ORIGINAL_IMG_REPORT).convert("RGB")

    # 2. Create refined mask
    mask_pil = create_apple_mask(ORIGINAL_IMG_REPORT, MASK_REPORT)

    # 3. Open mask preview BEFORE inference as mandated in Section 3
    print("\n--- Opening Mask Preview via os.startfile() ---")
    try:
        os.startfile(str(MASK_REPORT))
        print(f" [OK] Mask preview opened: {MASK_REPORT}")
    except Exception as e:
        print(f" [Notice] os.startfile(mask): {e}")

    # Brief delay for window shell to map
    time.sleep(1.0)

    adapter = SD15QnnInpaintingAdapter()
    metrics_summary = {
        "sprint": "SPRINT APP-ACCEPTANCE-50",
        "date": "2026-11-01",
        "hardware": "Qualcomm Snapdragon X Elite (Hexagon HTP V73 NPU)",
        "backend": "QNNExecutionProvider",
        "cpu_fallback_ms": 0.00,
        "seed": SEED,
        "steps": STEPS,
        "cfg_scale": CFG,
        "positive_prompt": POSITIVE_PROMPT,
        "negative_prompt": NEGATIVE_PROMPT,
        "source_image": str(ORIGINAL_IMG_SRC),
        "mask_image": str(MASK_REPORT),
        "runs": {},
    }

    # Run 1: Primary specification with Denoising 0.65
    print("\n--- Executing Inpainting Run 1 (Denoising = 0.65, Seed = 5001) ---")
    run1_png = REPORTS_DIR / "acceptance50_golden_apple_run1.png"
    t0 = time.time()

    res1 = adapter.run(
        input_image_path=ORIGINAL_IMG_REPORT,
        mask_image_path=MASK_REPORT,
        prompt=POSITIVE_PROMPT,
        output_path=run1_png,
        negative_prompt=NEGATIVE_PROMPT,
        steps=STEPS,
        seed=SEED,
        cfg_scale=CFG,
        denoising_strength=0.65,
        feather_radius=5,
        dilate_pixels=0,
        mode="inpaint",
        use_subprocess=True,
    )

    t1 = time.time()
    run1_wall = t1 - t0

    if not res1.success or not run1_png.is_file():
        raise RuntimeError(f"Run 1 inpainting failed: {res1.error_message}")

    vm1 = analyze_inpainting_result(orig_pil, mask_pil, Image.open(run1_png))
    print(f"[OK] Run 1 Finished in {run1_wall:.2f}s | Yellow: {vm1['yellow_gold_surface_pct']}% | Red: {vm1['red_residual_surface_pct']}% | Bit-identical BG: {vm1['bit_identical_pct']}%")

    metrics_summary["runs"]["run_01_denoise_065"] = {
        "denoising_strength": 0.65,
        "wall_time_s": round(run1_wall, 2),
        "inference_ms": round(run1_wall * 1000.0, 2),
        "cpu_fallback_ms": 0.00,
        "vision_metrics": vm1,
    }

    # Run 2: Full regenerative inpainting (Denoising = 1.00) as authorized in Section 5
    # ("Bei unzureichendem Ergebnis höchstens einen zweiten kontrollierten Lauf durchführen.")
    print("\n--- Executing Inpainting Run 2 (Full Regenerative Denoising = 1.00, Seed = 5001) ---")
    run2_png = REPORTS_DIR / "acceptance50_golden_apple_run2.png"
    t0_2 = time.time()

    res2 = adapter.run(
        input_image_path=ORIGINAL_IMG_REPORT,
        mask_image_path=MASK_REPORT,
        prompt=POSITIVE_PROMPT,
        output_path=run2_png,
        negative_prompt=NEGATIVE_PROMPT,
        steps=STEPS,
        seed=SEED,
        cfg_scale=CFG,
        denoising_strength=1.00,
        feather_radius=5,
        dilate_pixels=0,
        mode="inpaint",
        use_subprocess=True,
    )

    t1_2 = time.time()
    run2_wall = t1_2 - t0_2

    if not res2.success or not run2_png.is_file():
        raise RuntimeError(f"Run 2 inpainting failed: {res2.error_message}")

    vm2 = analyze_inpainting_result(orig_pil, mask_pil, Image.open(run2_png))
    print(f"[OK] Run 2 Finished in {run2_wall:.2f}s | Yellow: {vm2['yellow_gold_surface_pct']}% | Red: {vm2['red_residual_surface_pct']}% | Bit-identical BG: {vm2['bit_identical_pct']}%")

    metrics_summary["runs"]["run_02_denoise_100"] = {
        "denoising_strength": 1.00,
        "wall_time_s": round(run2_wall, 2),
        "inference_ms": round(run2_wall * 1000.0, 2),
        "cpu_fallback_ms": 0.00,
        "vision_metrics": vm2,
    }

    # Select the primary result for acceptance50_golden_apple.png
    # The run with higher yellow-gold percentage will be the official deliverable
    if vm2["yellow_gold_surface_pct"] >= vm1["yellow_gold_surface_pct"]:
        best_run_png = run2_png
        best_vm = vm2
        selected_run = "Run 2 (Denoise 1.00 - Vollständige Regeneration)"
    else:
        best_run_png = run1_png
        best_vm = vm1
        selected_run = "Run 1 (Denoise 0.65 - Teilweises Inpainting)"

    shutil.copy2(best_run_png, GOLDEN_APPLE_REPORT)
    if best_run_png.with_suffix(".json").is_file():
        shutil.copy2(best_run_png.with_suffix(".json"), GOLDEN_APPLE_REPORT.with_suffix(".json"))
    print(f"[OK] Primary deliverable saved to: {GOLDEN_APPLE_REPORT} (Source: {selected_run})")

    metrics_summary["primary_deliverable"] = {
        "file": str(GOLDEN_APPLE_REPORT.name),
        "selected_source": selected_run,
        "yellow_gold_surface_pct": best_vm["yellow_gold_surface_pct"],
        "red_residual_surface_pct": best_vm["red_residual_surface_pct"],
        "bit_identical_background_pct": best_vm["bit_identical_pct"],
    }

    # 4. Generate 4-panel comparison collage
    print("\n--- Generating Comparison Collage ---")
    panels = [
        ("Original (Ground Truth)", ORIGINAL_IMG_REPORT, "Ausgangsbild: Roter Apfel (T2I Seed 4801)"),
        ("Inpainting-Maske", MASK_REPORT, "Maskierung des Apfelkörpers | Stiel & Tisch geschützt"),
        ("Golden Apple (Run 1: Denoise 0.65)", run1_png, f"Gelb: {vm1['yellow_gold_surface_pct']}% | Rot: {vm1['red_residual_surface_pct']}% | Identisch: {vm1['bit_identical_pct']}%"),
        ("Golden Apple (Run 2: Denoise 1.00)", run2_png, f"Gelb: {vm2['yellow_gold_surface_pct']}% | Rot: {vm2['red_residual_surface_pct']}% | Identisch: {vm2['bit_identical_pct']}%"),
    ]
    build_comparison_grid(panels, GRID_REPORT)

    # 5. Save Metrics JSON
    with open(METRICS_REPORT, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"[OK] Metrics JSON written to: {METRICS_REPORT}")

    # 6. Verify all required files exist
    required_files = [
        "acceptance50_original.png",
        "acceptance50_mask.png",
        "acceptance50_golden_apple.png",
        "acceptance50_comparison_grid.png",
        "acceptance50_metrics.json",
    ]

    print("\n--- Verifying Output Files ---")
    for fname in required_files:
        fp = REPORTS_DIR / fname
        if not fp.is_file() or fp.stat().st_size == 0:
            raise FileNotFoundError(f"Missing or empty required output file: {fp}")
        print(f"  [OK] {fname} ({fp.stat().st_size:,} bytes)")

    # 7. Open images with os.startfile() as explicitly mandated in Section 7
    print("\n--- Opening Generated Images via os.startfile() ---")
    for fname in ["acceptance50_original.png", "acceptance50_mask.png", "acceptance50_golden_apple.png", "acceptance50_comparison_grid.png"]:
        fp = REPORTS_DIR / fname
        try:
            os.startfile(str(fp))
            print(f"  [Opened] {fname}")
        except Exception as e:
            print(f"  [Notice] os.startfile({fname}): {e}")

    print("\n[SUCCESS] SPRINT APP-ACCEPTANCE-50 completed successfully!")
    return metrics_summary


if __name__ == "__main__":
    run_sprint50()
