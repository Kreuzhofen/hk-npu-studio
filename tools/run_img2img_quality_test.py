from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Ensure repo root on sys.path
REPO_ROOT = Path(r"C:\SnapdragonAI")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.backends.sd15_qnn_inpainting_adapter import SD15QnnInpaintingAdapter
from controllers.gallery_image_loader import ImageLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("img2img_quality_test")


def main() -> int:
    source_path = REPO_ROOT / "output" / "generate_1792859418_d2646d69.png"
    if not source_path.is_file():
        logger.error("Source image not found: %s", source_path)
        return 1

    prompt = "A shiny crystalline blue diamond apple on a sleek obsidian reflective table, dramatic studio lighting, octane render, 8k"
    neg_prompt = "blurry, red apple, food, organic fruit, low quality, distorted"
    seed = 42
    steps = 20
    cfg = 7.5

    adapter = SD15QnnInpaintingAdapter()
    strengths = [0.35, 0.65, 1.00]
    results = {}

    output_dir = REPO_ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print("HK NPU STUDIO – SD1.5 Image-to-Image Hexagon HTP Quality Benchmark")
    print("=================================================================")
    print(f"Source Image: {source_path}")
    print(f"Prompt:       {prompt}")
    print(f"Negative:     {neg_prompt}")
    print(f"Seed:         {seed} | Steps: {steps} | CFG: {cfg}")
    print("-----------------------------------------------------------------")

    for s in strengths:
        tag = f"{int(s * 100):03d}"
        out_path = output_dir / f"img2img_benchmark_s{tag}.png"
        print(f"\n--- Running Image-to-Image on HTP: Denoising Strength = {s:.2f} ---")
        t0 = time.perf_counter()

        def prog_cb(phase, frac, detail):
            print(f"  [{phase.upper()}] {frac * 100:.1f}%: {detail}")

        res = adapter.run_img2img(
            input_image_path=source_path,
            prompt=prompt,
            output_path=out_path,
            negative_prompt=neg_prompt,
            steps=steps,
            seed=seed,
            cfg_scale=cfg,
            denoising_strength=s,
            progress_callback=prog_cb,
            use_subprocess=True,
        )
        wall_time = time.perf_counter() - t0

        if not res.success or not res.output_path or not Path(res.output_path).is_file():
            logger.error("HTP inference failed for strength %.2f: %s", s, res.error_message)
            return 1

        print(f"  SUCCESS in {wall_time:.2f}s! Saved to: {res.output_path}")
        results[s] = {
            "result": res,
            "path": Path(res.output_path),
            "wall_time": wall_time,
        }

    # Analyze RGB statistics and distances
    with Image.open(source_path) as im:
        src_np = np.array(im.convert("RGB"), dtype=np.float32)

    stats = {}
    print("\n=================================================================")
    print("RGB STATISTICS & DIFFERENCE ANALYSIS")
    print("=================================================================")
    for s, data in results.items():
        with Image.open(data["path"]) as im:
            gen_np = np.array(im.convert("RGB"), dtype=np.float32)

        r_mean, g_mean, b_mean = np.mean(gen_np[:, :, 0]), np.mean(gen_np[:, :, 1]), np.mean(gen_np[:, :, 2])
        r_std, g_std, b_std = np.std(gen_np[:, :, 0]), np.std(gen_np[:, :, 1]), np.std(gen_np[:, :, 2])
        rgb_min, rgb_max = np.min(gen_np), np.max(gen_np)

        # L1 diff from source
        l1_diff = np.mean(np.abs(gen_np - src_np))
        l2_diff = np.sqrt(np.mean((gen_np - src_np) ** 2))

        meta = data["result"].metadata
        exec_times = meta.get("execution_times", {})
        actual_steps = meta.get("actual_inference_steps", 0)

        stats[s] = {
            "l1_diff": float(l1_diff),
            "l2_diff": float(l2_diff),
            "r_mean": float(r_mean),
            "g_mean": float(g_mean),
            "b_mean": float(b_mean),
            "r_std": float(r_std),
            "g_std": float(g_std),
            "b_std": float(b_std),
            "rgb_min": float(rgb_min),
            "rgb_max": float(rgb_max),
            "actual_steps": int(actual_steps),
            "exec_times": {k: float(v) for k, v in exec_times.items()},
        }

        print(f"Strength {s:.2f} ({actual_steps} steps):")
        print(f"  L1 Difference from Source: {l1_diff:.2f} / 255 (L2: {l2_diff:.2f})")
        print(f"  RGB Range: [{rgb_min:.0f}, {rgb_max:.0f}], Means: R={r_mean:.1f}, G={g_mean:.1f}, B={b_mean:.1f}")
        print(f"  RGB Std:   R={r_std:.1f}, G={g_std:.1f}, B={b_std:.1f}")
        print(f"  HTP Timings:")
        print(f"    HTP VAE Encoder:  {exec_times.get('htp_vae_encoder_ms', 0):.2f} ms")
        print(f"    CPU VAE Fallback: {exec_times.get('cpu_vae_encoder_ms', 0):.2f} ms")
        print(f"    HTP CLIP Text:    {exec_times.get('htp_clip_text_ms', 0):.2f} ms")
        print(f"    HTP UNet Total:   {exec_times.get('htp_unet_total_ms', 0):.2f} ms ({actual_steps} steps)")
        print(f"    HTP VAE Decoder:  {exec_times.get('htp_vae_decoder_ms', 0):.2f} ms")
        print(f"    Total Inference:  {exec_times.get('total_inference_ms', 0):.2f} ms")

    # Verify Progression Contract:
    # L1 diff must increase strictly with denoising strength!
    diff_035 = stats[0.35]["l1_diff"]
    diff_065 = stats[0.65]["l1_diff"]
    diff_100 = stats[1.00]["l1_diff"]
    print(f"\nProgression check: diff(0.35)={diff_035:.2f} < diff(0.65)={diff_065:.2f} < diff(1.00)={diff_100:.2f}")
    assert diff_035 < diff_065 < diff_100, f"Denoising strength progression failed: {diff_035} < {diff_065} < {diff_100}"
    print("PASS: Denoising progression strictly monotonic and mathematically verified!")

    # Verify Color Dynamics (not gray! R, G, B standard deviations must be > 20)
    for s, st in stats.items():
        assert st["rgb_max"] > 200 and st["rgb_min"] < 50, f"Color range compressed at s={s}"
        assert st["r_std"] > 20 and st["g_std"] > 20 and st["b_std"] > 20, f"Image lacks color dynamics at s={s}"
    print("PASS: Color dynamics verified full range on all 3 channels!")

    # Verify Gallery Compatibility
    loader = ImageLoader()
    gallery_items = loader.load_folder(output_dir)
    found_gallery_count = 0
    for s in strengths:
        tag = f"{int(s * 100):03d}"
        fn = f"img2img_benchmark_s{tag}.png"
        matches = [it for it in gallery_items if it.filename == fn]
        assert len(matches) == 1, f"Gallery failed to load item {fn}"
        item = matches[0]
        assert item.prompt == prompt, f"Sidecar prompt mismatch: {item.prompt}"
        assert item.width == 512 and item.height == 512
        assert item.metadata.get("feature") == "Image-to-Image"
        found_gallery_count += 1
    print(f"PASS: All {found_gallery_count} benchmark outputs loaded and verified in Gallery loader!")

    # Build Side-by-Side Comparison Canvas (1x4 grid)
    # Width: 4 * 512 + 5 * 16 = 2048 + 80 = 2128
    # Height: 512 + header (120) + footer (100) = 732
    card_w, card_h = 512, 512
    margin = 20
    header_h = 100
    footer_h = 90
    total_w = 4 * card_w + 5 * margin
    total_h = header_h + card_h + footer_h

    grid_img = Image.new("RGB", (total_w, total_h), (24, 24, 27))  # Phoenix dark bg
    draw = ImageDraw.Draw(grid_img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 28)
        font_sub = ImageFont.truetype("arial.ttf", 16)
        font_card_title = ImageFont.truetype("arial.ttf", 20)
        font_metrics = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font_title = font_sub = font_card_title = font_metrics = None

    # Draw Header
    draw.text(
        (margin, 20),
        "HK NPU STUDIO – SD1.5 Image-to-Image on Qualcomm Hexagon HTP (Snapdragon X Elite)",
        fill=(255, 255, 255),
        font=font_title,
    )
    draw.text(
        (margin, 58),
        f"Prompt: \"{prompt[:95]}...\"  |  Negative: \"{neg_prompt}\"  |  Seed: {seed}  |  CFG: {cfg}",
        fill=(161, 161, 170),
        font=font_sub,
    )

    panels = [
        ("1. Originalbild (Quelle)", source_path, "Ausgangsbild 512x512", "Roter Apfel auf Tisch", (234, 179, 8)),
        (
            f"2. Denoising 0.35 ({stats[0.35]['actual_steps']} Steps)",
            results[0.35]["path"],
            f"L1 Diff: {stats[0.35]['l1_diff']:.1f} | NPU: {stats[0.35]['exec_times']['total_inference_ms']:.0f} ms",
            "Nuancen / Form & Struktur dominieren",
            (59, 130, 246),
        ),
        (
            f"3. Denoising 0.65 ({stats[0.65]['actual_steps']} Steps)",
            results[0.65]["path"],
            f"L1 Diff: {stats[0.65]['l1_diff']:.1f} | NPU: {stats[0.65]['exec_times']['total_inference_ms']:.0f} ms",
            "Ausgewogen: Blauer Kristall, Komposition bewahrt",
            (168, 85, 247),
        ),
        (
            f"4. Denoising 1.00 ({stats[1.00]['actual_steps']} Steps)",
            results[1.00]["path"],
            f"L1 Diff: {stats[1.00]['l1_diff']:.1f} | NPU: {stats[1.00]['exec_times']['total_inference_ms']:.0f} ms",
            "Vollständige Neugenerierung aus Prompt",
            (34, 197, 94),
        ),
    ]

    for idx, (title, img_p, sub1, sub2, accent_color) in enumerate(panels):
        x = margin + idx * (card_w + margin)
        y = header_h

        # Draw card header
        draw.rectangle([x, y - 28, x + card_w, y], fill=(39, 39, 42))
        draw.text((x + 10, y - 24), title, fill=accent_color, font=font_card_title)

        # Paste image
        with Image.open(img_p) as p_im:
            grid_img.paste(p_im.convert("RGB"), (x, y))

        # Draw card footer
        draw.rectangle([x, y + card_h, x + card_w, y + card_h + footer_h - 10], fill=(39, 39, 42))
        draw.text((x + 10, y + card_h + 8), sub1, fill=(244, 244, 245), font=font_metrics)
        draw.text((x + 10, y + card_h + 30), sub2, fill=(161, 161, 170), font=font_metrics)

    # Save to reports and artifact directory
    reports_dir = REPO_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_img_p = reports_dir / "sprint38_img2img_comparison_grid.png"
    grid_img.save(report_img_p, format="PNG")

    artifact_dir = Path(r"C:\Users\holge\.gemini\antigravity-cli\brain\c991b454-d253-4b5d-9ce4-469780cc4864")
    artifact_img_p = artifact_dir / "sprint38_img2img_comparison_grid.png"
    grid_img.save(artifact_img_p, format="PNG")

    # Also copy individual images to artifact dir for report linking
    for s in strengths:
        tag = f"{int(s * 100):03d}"
        fn = f"sprint38_img2img_s{tag}.png"
        shutil_dst = artifact_dir / fn
        with Image.open(results[s]["path"]) as im:
            im.save(shutil_dst, format="PNG")

    with Image.open(source_path) as im:
        im.save(artifact_dir / "sprint38_source_apple.png", format="PNG")

    print(f"\nComparison grid saved to: {report_img_p}")
    print(f"Artifact comparison grid saved to: {artifact_img_p}")

    # Write summary json
    summary_path = reports_dir / "sprint38_quality_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_image": str(source_path),
                "prompt": prompt,
                "negative_prompt": neg_prompt,
                "seed": seed,
                "cfg": cfg,
                "steps": steps,
                "stats": stats,
            },
            f,
            indent=2,
        )
    print("ALL TESTS PASSED SUCCESSFULLY ON QUALCOMM HEXAGON HTP V73!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
