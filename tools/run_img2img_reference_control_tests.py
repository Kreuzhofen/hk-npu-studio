"""
Sprint 42 Comprehensive HTP Empirical Verification Suite for Reference Image Control.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from engine.backends.sd15_qnn_inpainting_adapter import SD15QnnInpaintingAdapter

def create_comparison_row(title: str, images: list[tuple[str, Path]], output_path: Path):
    """Combine input and result images horizontally with labels."""
    cell_w, cell_h = 320, 320
    header_h = 40
    n = len(images)
    grid = Image.new("RGB", (n * cell_w, cell_h + header_h), (20, 22, 28))
    draw = ImageDraw.Draw(grid)

    for i, (label, p) in enumerate(images):
        if p.is_file():
            with Image.open(p) as img:
                thumb = img.convert("RGB").resize((cell_w, cell_h), Image.Resampling.LANCZOS)
                grid.paste(thumb, (i * cell_w, header_h))
        # Draw header label
        draw.text((i * cell_w + 12, 12), label, fill=(230, 230, 235))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    grid.save(output_path, format="PNG")
    print(f"Saved visual comparison row: {output_path}")

def main():
    print("=================================================================")
    print("  SPRINT 42: REFERENCE IMAGE CONTROL EMPIRICAL HTP VERIFICATION  ")
    print("=================================================================")

    adapter = SD15QnnInpaintingAdapter()
    results_dir = REPO_ROOT / "reports" / "sprint42_results"
    results_dir.mkdir(parents=True, exist_ok=True)

    img_object = REPO_ROOT / "output" / "generate_1792859418_d2646d69.png"
    img_landscape = REPO_ROOT / "output" / "smoke_sd21_1792768376_94abe6b7.png"
    img_portrait = REPO_ROOT / "output" / "generate_1792859244_1137524_input.png"

    all_benchmarks = []

    # -------------------------------------------------------------
    # Test 1: Architectures & Objects (Apple on table)
    # -------------------------------------------------------------
    print("\n--- Test 1: Objects (Apple) @ Denoising 0.65 ---")
    prompt_obj = "a futuristic metallic apple with blue glowing circuits, 8k, photorealistic"
    
    # 1A. Baseline (No ref control)
    p_obj_base = results_dir / "obj_baseline_s065.png"
    res_obj_base = adapter.run_img2img(
        input_image_path=img_object,
        prompt=prompt_obj,
        output_path=p_obj_base,
        steps=12,
        seed=101,
        denoising_strength=0.65,
        enable_reference_control=False,
    )
    assert res_obj_base.success, f"Failed: {res_obj_base.error_message}"
    all_benchmarks.append(("Object Baseline (No Ref)", res_obj_base.metadata))

    # 1B. Modus A: Contour (Canny QNN)
    p_obj_canny = results_dir / "obj_canny_s065.png"
    res_obj_canny = adapter.run_img2img(
        input_image_path=img_object,
        prompt=prompt_obj,
        output_path=p_obj_canny,
        steps=12,
        seed=101,
        denoising_strength=0.65,
        enable_reference_control=True,
        reference_mode="canny_qnn",
        reference_fidelity=0.75,
    )
    assert res_obj_canny.success, f"Failed: {res_obj_canny.error_message}"
    all_benchmarks.append(("Object Canny QNN", res_obj_canny.metadata))

    # 1C. Modus B: Structure (Latent Anchor)
    p_obj_anchor = results_dir / "obj_anchor_s065.png"
    res_obj_anchor = adapter.run_img2img(
        input_image_path=img_object,
        prompt=prompt_obj,
        output_path=p_obj_anchor,
        steps=12,
        seed=101,
        denoising_strength=0.65,
        enable_reference_control=True,
        reference_mode="latent_anchor",
        reference_fidelity=0.75,
    )
    assert res_obj_anchor.success, f"Failed: {res_obj_anchor.error_message}"
    all_benchmarks.append(("Object Latent Anchor", res_obj_anchor.metadata))

    create_comparison_row(
        "Objects Comparison",
        [
            ("Original", img_object),
            ("Baseline (No Ref)", p_obj_base),
            ("Modus A: Canny QNN (0.75)", p_obj_canny),
            ("Modus B: Latent Anchor (0.75)", p_obj_anchor),
        ],
        results_dir / "sprint42_comparison_objects.png"
    )

    # -------------------------------------------------------------
    # Test 2: Landscapes @ Denoising 0.80 (Creative Preset)
    # -------------------------------------------------------------
    print("\n--- Test 2: Landscapes @ Denoising 0.80 (Creative) ---")
    prompt_land = "a vibrant autumn mountain valley with golden trees and orange sunset light, 8k"

    p_land_base = results_dir / "land_baseline_s080.png"
    res_land_base = adapter.run_img2img(
        input_image_path=img_landscape,
        prompt=prompt_land,
        output_path=p_land_base,
        steps=12,
        seed=202,
        denoising_strength=0.80,
        enable_reference_control=False,
    )
    assert res_land_base.success, f"Failed: {res_land_base.error_message}"
    all_benchmarks.append(("Landscape Baseline (No Ref)", res_land_base.metadata))

    p_land_canny = results_dir / "land_canny_s080.png"
    res_land_canny = adapter.run_img2img(
        input_image_path=img_landscape,
        prompt=prompt_land,
        output_path=p_land_canny,
        steps=12,
        seed=202,
        denoising_strength=0.80,
        enable_reference_control=True,
        reference_mode="canny_qnn",
        reference_fidelity=0.75,
    )
    assert res_land_canny.success, f"Failed: {res_land_canny.error_message}"
    all_benchmarks.append(("Landscape Canny QNN", res_land_canny.metadata))

    p_land_anchor = results_dir / "land_anchor_s080.png"
    res_land_anchor = adapter.run_img2img(
        input_image_path=img_landscape,
        prompt=prompt_land,
        output_path=p_land_anchor,
        steps=12,
        seed=202,
        denoising_strength=0.80,
        enable_reference_control=True,
        reference_mode="latent_anchor",
        reference_fidelity=0.75,
    )
    assert res_land_anchor.success, f"Failed: {res_land_anchor.error_message}"
    all_benchmarks.append(("Landscape Latent Anchor", res_land_anchor.metadata))

    create_comparison_row(
        "Landscapes Comparison",
        [
            ("Original", img_landscape),
            ("Baseline (No Ref)", p_land_base),
            ("Modus A: Canny QNN (0.75)", p_land_canny),
            ("Modus B: Latent Anchor (0.75)", p_land_anchor),
        ],
        results_dir / "sprint42_comparison_landscapes.png"
    )

    # -------------------------------------------------------------
    # Test 3: Portrait Silhouettes @ Denoising 0.65 and 0.80
    # -------------------------------------------------------------
    print("\n--- Test 3: Portrait Silhouettes @ Denoising 0.65 & 0.80 ---")
    prompt_port = "a glowing neon cybernetic warrior portrait, synthwave aesthetic, 8k"

    p_port_canny_065 = results_dir / "port_canny_s065.png"
    res_port_canny_065 = adapter.run_img2img(
        input_image_path=img_portrait,
        prompt=prompt_port,
        output_path=p_port_canny_065,
        steps=12,
        seed=303,
        denoising_strength=0.65,
        enable_reference_control=True,
        reference_mode="canny_qnn",
        reference_fidelity=0.75,
    )
    assert res_port_canny_065.success

    p_port_anchor_065 = results_dir / "port_anchor_s065.png"
    res_port_anchor_065 = adapter.run_img2img(
        input_image_path=img_portrait,
        prompt=prompt_port,
        output_path=p_port_anchor_065,
        steps=12,
        seed=303,
        denoising_strength=0.65,
        enable_reference_control=True,
        reference_mode="latent_anchor",
        reference_fidelity=0.75,
    )
    assert res_port_anchor_065.success

    p_port_canny_080 = results_dir / "port_canny_s080.png"
    res_port_canny_080 = adapter.run_img2img(
        input_image_path=img_portrait,
        prompt=prompt_port,
        output_path=p_port_canny_080,
        steps=12,
        seed=303,
        denoising_strength=0.80,
        enable_reference_control=True,
        reference_mode="canny_qnn",
        reference_fidelity=0.75,
    )
    assert res_port_canny_080.success

    create_comparison_row(
        "Portrait Silhouettes Comparison",
        [
            ("Original", img_portrait),
            ("Canny QNN (s=0.65)", p_port_canny_065),
            ("Latent Anchor (s=0.65)", p_port_anchor_065),
            ("Canny QNN (s=0.80)", p_port_canny_080),
        ],
        results_dir / "sprint42_comparison_portrait.png"
    )

    # -------------------------------------------------------------
    # Test 4: Seed Reproducibility Verification
    # -------------------------------------------------------------
    print("\n--- Test 4: Seed Reproducibility ---")
    p_rep1 = results_dir / "reproducibility_run1.png"
    p_rep2 = results_dir / "reproducibility_run2.png"

    res_rep1 = adapter.run_img2img(
        input_image_path=img_object,
        prompt=prompt_obj,
        output_path=p_rep1,
        steps=10,
        seed=4242,
        denoising_strength=0.65,
        enable_reference_control=True,
        reference_mode="canny_qnn",
        reference_fidelity=0.75,
    )
    res_rep2 = adapter.run_img2img(
        input_image_path=img_object,
        prompt=prompt_obj,
        output_path=p_rep2,
        steps=10,
        seed=4242,
        denoising_strength=0.65,
        enable_reference_control=True,
        reference_mode="canny_qnn",
        reference_fidelity=0.75,
    )

    arr1 = np.array(Image.open(p_rep1))
    arr2 = np.array(Image.open(p_rep2))
    max_diff = int(np.max(np.abs(arr1.astype(np.int32) - arr2.astype(np.int32))))
    print(f"Seed Reproducibility Maximum Absolute Difference: {max_diff}")
    assert max_diff == 0, f"Reproducibility failed: max_diff={max_diff} > 0"
    print("Seed Reproducibility: 100% BIT-IDENTICAL VERIFIED!")

    # Summary benchmark file
    summary_path = results_dir / "sprint42_benchmarks.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_benchmarks, f, indent=2)

    print("\n=============================================================")
    print("  ALL EMPIRICAL TESTS PASSED SUCCESSFULLY ON QUALCOMM HTP!  ")
    print("=============================================================")

if __name__ == "__main__":
    main()
