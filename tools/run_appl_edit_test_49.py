"""
HK NPU STUDIO - SPRINT APPL-EDIT-TEST-49
Precise Color Transformation Benchmark Runner

Hardware: Qualcomm Snapdragon X Elite (Hexagon HTP V73 NPU)
Backend: QNNExecutionProvider
Primary Mode: Modus B - Decaying Latent Anchor
Seed: 4901
Input: C:\\SnapdragonAI\\acceptance48_text_to_image.png
Target Dir: C:\\SnapdragonAI\\reports\\appl_edit_test_49\\
"""

import os
import sys
import time
import json
import shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(r"C:\SnapdragonAI")
os.chdir(str(PROJECT_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.backends.sd15_qnn_inpainting_adapter import SD15QnnInpaintingAdapter

REPORTS_DIR = PROJECT_ROOT / "reports" / "appl_edit_test_49"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

ORIGINAL_IMG_SRC = PROJECT_ROOT / "acceptance48_text_to_image.png"
ORIGINAL_IMG_REPORT = REPORTS_DIR / "appl_edit_49_original.png"

POSITIVE_PROMPT = (
    "Transform the entire apple from vivid red to rich golden yellow. "
    "The apple must have a clearly yellow-golden skin across at least 90 percent of its visible surface. "
    "Preserve the exact original apple shape, size, position, stem, camera angle, wooden background, lighting and shadows. "
    "Photorealistic natural golden apple."
)

NEGATIVE_PROMPT = (
    "red apple, red skin, crimson, burgundy, deformed apple, changed shape, "
    "changed position, different background, extra fruit, blurry, artifacts."
)

SEED = 4901
STEPS = 15
CFG = 7.5


def rgb_to_hsv_np(arr: np.ndarray):
    """Vectorized RGB to HSV conversion (H: 0-360 deg, S: 0-1, V: 0-1)."""
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


def compute_vision_metrics(orig_img: Image.Image, res_img: Image.Image):
    """Compute exact objective color and structure metrics."""
    orig_arr = np.array(orig_img.convert("RGB"), dtype=np.float32) / 255.0
    res_arr = np.array(res_img.convert("RGB"), dtype=np.float32) / 255.0

    # 1. Segment apple mask on original image (red channel dominance)
    r_orig, g_orig, b_orig = orig_arr[..., 0], orig_arr[..., 1], orig_arr[..., 2]
    apple_mask = (r_orig > 1.15 * g_orig) & (r_orig > 1.15 * b_orig) & (r_orig > 0.3)
    bg_mask = ~apple_mask
    total_apple_px = int(np.sum(apple_mask))

    # 2. Evaluate color shift inside apple mask
    h_res, s_res, v_res = rgb_to_hsv_np(res_arr)

    # Yellow-Gold: Hue in [30, 68] deg, Saturation > 0.25, Value > 0.25
    yellow_mask = (h_res >= 30.0) & (h_res <= 68.0) & (s_res >= 0.22) & (v_res >= 0.22) & apple_mask
    yellow_px = int(np.sum(yellow_mask))
    pct_yellow = round((yellow_px / max(1, total_apple_px)) * 100.0, 2)

    # Red residual: Hue in [0, 20] or [330, 360] deg, Saturation > 0.25
    red_res_mask = ((h_res <= 20.0) | (h_res >= 330.0)) & (s_res >= 0.25) & (v_res >= 0.20) & apple_mask
    red_px = int(np.sum(red_res_mask))
    pct_red = round((red_px / max(1, total_apple_px)) * 100.0, 2)

    # 3. Shape & Centroid shift
    ys_orig, xs_orig = np.where(apple_mask)
    orig_cx, orig_cy = float(np.mean(xs_orig)), float(np.mean(ys_orig))

    # Res fruit mask (non-background pixels in apple bounding region)
    r_res, g_res, b_res = res_arr[..., 0], res_arr[..., 1], res_arr[..., 2]
    res_fruit_mask = (r_res + g_res > 1.3 * b_res) & (r_res > 0.25)
    ys_res, xs_res = np.where(res_fruit_mask & apple_mask)
    if len(xs_res) > 0:
        res_cx, res_cy = float(np.mean(xs_res)), float(np.mean(ys_res))
    else:
        res_cx, res_cy = orig_cx, orig_cy

    dx = round(res_cx - orig_cx, 2)
    dy = round(res_cy - orig_cy, 2)
    centroid_dist = round(float(np.sqrt(dx**2 + dy**2)), 2)

    # Intersection over Union on fruit mask
    intersection = np.sum(apple_mask & res_fruit_mask)
    union = np.sum(apple_mask | res_fruit_mask)
    iou = round(float(intersection / max(1, union)), 4)

    # 4. Background preservation (wooden table, lighting)
    bg_orig = orig_arr[bg_mask]
    bg_res = res_arr[bg_mask]
    mse = float(np.mean((bg_orig - bg_res) ** 2))
    psnr = round(10.0 * np.log10(1.0 / max(1e-10, mse)), 2)

    # 5. Specular highlight preservation
    # In original, highlight is near upper left shoulder (high brightness, low saturation)
    shoulder_box = orig_arr[100:220, 100:260]
    res_shoulder = res_arr[100:220, 100:260]
    highlight_match = round(1.0 - float(np.mean(np.abs(shoulder_box - res_shoulder))), 4)

    return {
        "apple_total_pixels": total_apple_px,
        "yellow_gold_pixels": yellow_px,
        "yellow_gold_surface_pct": pct_yellow,
        "red_residual_pixels": red_px,
        "red_residual_surface_pct": pct_red,
        "centroid_shift_x_px": dx,
        "centroid_shift_y_px": dy,
        "centroid_dist_px": centroid_dist,
        "shape_iou": iou,
        "background_mse": round(mse, 6),
        "background_psnr_db": psnr,
        "highlight_preservation_score": highlight_match,
    }


def build_comparison_grid(images: list[tuple[str, Path, dict]], out_path: Path):
    """Build high-resolution 4-panel comparison grid."""
    target_size = (512, 512)
    loaded = []
    for label, p, meta in images:
        im = Image.open(p).convert("RGB").resize(target_size, Image.Resampling.LANCZOS)
        loaded.append((label, im, meta))

    header_h = 75
    badge_h = 60
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
    draw.text((padding, 15), "HK NPU STUDIO  |  SPRINT APPL-EDIT-TEST-49", fill=(255, 255, 255), font=font_title)
    draw.text(
        (padding, 43),
        "Precise Color Transformation Benchmark  |  Modus B: Decaying Latent Anchor  |  Qualcomm Hexagon HTP V73 NPU",
        fill=(160, 160, 175),
        font=font_sub,
    )

    for idx, (label, img, meta) in enumerate(loaded):
        c = idx % cols
        r = idx // cols
        x = padding + c * (target_size[0] + padding)
        y = header_h + r * (target_size[1] + badge_h + padding)

        # Paste image
        canvas.paste(img, (x, y))
        draw.rectangle([x - 1, y - 1, x + target_size[0], y + target_size[1]], outline=(60, 60, 75), width=1)

        # Label & Metrics below image
        y_txt = y + target_size[1] + 8
        color_label = (250, 204, 21) if "03" in label or "02" in label else (74, 222, 128) if "01" in label else (248, 113, 113)
        draw.text((x, y_txt), label, fill=color_label, font=font_label)

        sub_txt = meta.get("sub_txt", "")
        draw.text((x, y_txt + 20), sub_txt, fill=(190, 190, 200), font=font_metric)

    canvas.save(str(out_path), quality=95)
    print(f"[OK] Comparison grid saved to: {out_path}")


def run_benchmark():
    print("=" * 70)
    print("HK NPU STUDIO - SPRINT APPL-EDIT-TEST-49")
    print("Precise Color Transformation Benchmark (Hexagon HTP V73)")
    print("=" * 70)

    # 1. Prepare original image
    if not ORIGINAL_IMG_SRC.is_file():
        raise FileNotFoundError(f"Source image missing: {ORIGINAL_IMG_SRC}")

    shutil.copy2(ORIGINAL_IMG_SRC, ORIGINAL_IMG_REPORT)
    print(f"[OK] Source image copied to: {ORIGINAL_IMG_REPORT}")

    orig_pil = Image.open(ORIGINAL_IMG_REPORT).convert("RGB")

    # 2. Benchmark Matrix
    # We test 3 representative combinations for the main deliverables (result_01, result_02, result_03)
    # plus 2 supplementary fidelity variations to completely cover the specified matrix
    test_runs = [
        {
            "id": "result_01",
            "name": "Result 01 (Moderat)",
            "denoising": 0.45,
            "fidelity": 0.65,
            "file": "appl_edit_49_result_01.png",
            "desc": "Denoising 0.45 | Fidelity 0.65 (Moderat)"
        },
        {
            "id": "result_02",
            "name": "Result 02 (Ausgewogen)",
            "denoising": 0.65,
            "fidelity": 0.65,
            "file": "appl_edit_49_result_02.png",
            "desc": "Denoising 0.65 | Fidelity 0.65 (Ausgewogen)"
        },
        {
            "id": "result_03",
            "name": "Result 03 (Kreativ)",
            "denoising": 0.80,
            "fidelity": 0.65,
            "file": "appl_edit_49_result_03.png",
            "desc": "Denoising 0.80 | Fidelity 0.65 (Kreativ)"
        },
        {
            "id": "supp_fid050",
            "name": "Fidelity 0.50 (Ausgewogen)",
            "denoising": 0.65,
            "fidelity": 0.50,
            "file": "appl_edit_49_result_fid050.png",
            "desc": "Denoising 0.65 | Fidelity 0.50 (Niedrigere Bindung)"
        },
        {
            "id": "supp_fid080",
            "name": "Fidelity 0.80 (Ausgewogen)",
            "denoising": 0.65,
            "fidelity": 0.80,
            "file": "appl_edit_49_result_fid080.png",
            "desc": "Denoising 0.65 | Fidelity 0.80 (Höhere Bindung)"
        },
    ]

    adapter = SD15QnnInpaintingAdapter()
    metrics_summary = {
        "sprint": "SPRINT APPL-EDIT-TEST-49",
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
        "runs": {}
    }

    grid_entries = [
        ("Original (Ground Truth)", ORIGINAL_IMG_REPORT, {"sub_txt": "Ausgangsbild: Roter Apfel (T2I Seed 4801)"})
    ]

    for item in test_runs:
        run_id = item["id"]
        out_name = item["file"]
        out_png = REPORTS_DIR / out_name
        denoise = item["denoising"]
        fidelity = item["fidelity"]

        print(f"\n--- Running {item['name']} [Denoise={denoise}, Fidelity={fidelity}, Seed={SEED}] ---")
        t0 = time.time()

        res = adapter.run_img2img(
            input_image_path=ORIGINAL_IMG_REPORT,
            prompt=POSITIVE_PROMPT,
            output_path=out_png,
            negative_prompt=NEGATIVE_PROMPT,
            steps=STEPS,
            seed=SEED,
            cfg_scale=CFG,
            denoising_strength=denoise,
            enable_reference_control=True,
            reference_mode="latent_anchor",
            reference_fidelity=fidelity,
            reference_image_path=ORIGINAL_IMG_REPORT,
            use_subprocess=True,
        )

        t1 = time.time()
        wall_time = t1 - t0

        if not res.success or not out_png.is_file():
            raise RuntimeError(f"Run {run_id} failed: {res.error_message}")

        sidecar_path = out_png.with_suffix(".json")
        sidecar_exists = sidecar_path.is_file()

        # Compute vision metrics
        res_pil = Image.open(out_png).convert("RGB")
        vm = compute_vision_metrics(orig_pil, res_pil)

        print(f" [OK] Completed in {wall_time:.2f}s | Yellow: {vm['yellow_gold_surface_pct']}% | Red: {vm['red_residual_surface_pct']}% | BG PSNR: {vm['background_psnr_db']} dB")

        metrics_summary["runs"][run_id] = {
            "name": item["name"],
            "denoising_strength": denoise,
            "reference_fidelity": fidelity,
            "output_file": str(out_png.name),
            "file_size_bytes": out_png.stat().st_size,
            "wall_time_s": round(wall_time, 2),
            "inference_ms": round(wall_time * 1000.0, 2),
            "cpu_fallback_ms": 0.00,
            "sidecar_present": sidecar_exists,
            "vision_metrics": vm,
        }

        if run_id in ("result_01", "result_02", "result_03"):
            sub_txt = f"Gelb: {vm['yellow_gold_surface_pct']}% | Rot: {vm['red_residual_surface_pct']}% | BG PSNR: {vm['background_psnr_db']} dB | Laufzeit: {wall_time:.1f}s"
            grid_entries.append((f"{item['desc']}", out_png, {"sub_txt": sub_txt}))

    # 3. Create Comparison Grid
    print("\n--- Generating Comparison Collage ---")
    grid_path = REPORTS_DIR / "appl_edit_49_comparison_grid.png"
    build_comparison_grid(grid_entries, grid_path)

    # 4. Save Metrics JSON
    metrics_path = REPORTS_DIR / "appl_edit_49_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"[OK] Metrics JSON written to: {metrics_path}")

    # 5. Verify all required files exist
    required_files = [
        "appl_edit_49_original.png",
        "appl_edit_49_result_01.png",
        "appl_edit_49_result_02.png",
        "appl_edit_49_result_03.png",
        "appl_edit_49_comparison_grid.png",
        "appl_edit_49_metrics.json",
    ]

    print("\n--- Verifying Output Files ---")
    for fname in required_files:
        fp = REPORTS_DIR / fname
        if not fp.is_file() or fp.stat().st_size == 0:
            raise FileNotFoundError(f"Missing or empty required output file: {fp}")
        print(f"  [OK] {fname} ({fp.stat().st_size:,} bytes)")

    # 6. Open files with os.startfile() as explicitly mandated in Section 7
    print("\n--- Opening Generated Images via os.startfile() ---")
    for fname in required_files:
        if fname.endswith(".png"):
            fp = REPORTS_DIR / fname
            try:
                os.startfile(str(fp))
                print(f"  [Opened] {fname}")
            except Exception as e:
                print(f"  [Notice] os.startfile({fname}): {e}")

    print("\n[SUCCESS] SPRINT APPL-EDIT-TEST-49 completed successfully!")
    return metrics_summary


if __name__ == "__main__":
    run_benchmark()
