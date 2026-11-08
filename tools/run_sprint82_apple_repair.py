"""
Sprint 82 Apple Official Inpainting Validation
Executes PromptEditController on Motif 1 (Apfel) with the repaired pipeline (English token 'apple', anti-crater negative prompt).
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
import numpy as np

from controllers.prompt_edit_controller import PromptEditController

def run_apple_repair():
    controller = PromptEditController()
    input_path = Path("reports/appl_edit_test_49/appl_edit_49_original.png")
    out_dir = Path("reports/sprint_82_material_repair/images")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "motif1_apple_repaired_htp.png"

    prompt = "Verwandle den Apfel in 24k Gold."

    print(f"Executing PromptEditController for Apple on Qualcomm Hexagon HTP...")
    t0 = time.perf_counter()
    res = controller.execute(
        input_image_path=input_path,
        prompt=prompt,
        output_path=out_path,
        steps=20,
        seed=43,  # Best proven seed from empirical matrix
        cfg_scale=7.5,
    )
    elapsed = time.perf_counter() - t0
    print(f"Execution complete in {elapsed:.2f}s. Success={res.success}")

    if not res.success:
        print(f"ERROR: {res.error_message}")
        return

    orig = Image.open(input_path).convert("RGB")
    result = Image.open(out_path).convert("RGB")
    mask = res.plan.segment_result.mask

    orig_arr = np.array(orig, dtype=float)
    res_arr = np.array(result, dtype=float)
    m_arr = np.array(mask) > 0

    # Outside diff
    unmasked = ~m_arr
    diff_outside = np.max(np.abs(res_arr[unmasked] - orig_arr[unmasked]))
    print(f"Max difference outside mask: {diff_outside:.1f} px (100% bit-exact = {diff_outside == 0})")

    # Region A analysis (y: 310..335, x: 350..370)
    lum = 0.299 * res_arr[..., 0] + 0.587 * res_arr[..., 1] + 0.114 * res_arr[..., 2]
    crop_a = lum[310:335, 350:370]
    min_lum = float(crop_a.min())
    mean_lum = float(crop_a.mean())
    dark_px = int((crop_a < 30).sum())
    print(f"Region A: Min Lum={min_lum:.1f}, Mean Lum={mean_lum:.1f}, Dark pixels (<30)={dark_px}")

    # Save mask and overlay for reporting
    mask.save(out_dir / "motif1_apple_repaired_mask.png")
    res.plan.segment_result.overlay_image.save(out_dir / "motif1_apple_repaired_overlay.png")
    if res.primed_image:
        res.primed_image.save(out_dir / "motif1_apple_repaired_primed.png")

    print(f"Artifacts saved to {out_dir}")

if __name__ == "__main__":
    run_apple_repair()
