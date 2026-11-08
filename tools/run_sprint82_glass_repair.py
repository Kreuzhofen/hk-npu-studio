"""
Sprint 82 Glass Sculpture Inpainting Validation
Executes prompt editing on the glass sculpture with the repaired continuous mask on Qualcomm Hexagon NPU.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
import numpy as np

from controllers.prompt_edit_controller import PromptEditController

def run_glass_repair():
    controller = PromptEditController()
    input_path = Path("reports/sprint_80_total_validation/images/motif2_glass_1_original.png")
    out_dir = Path("reports/sprint_82_material_repair/images")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "motif2_glass_repaired_htp.png"

    prompt = "Verwandle die Glasskulptur in 24k Gold."

    print(f"Executing PromptEditController for Glass Sculpture on Qualcomm Hexagon HTP...")
    t0 = time.perf_counter()
    res = controller.execute(
        input_image_path=input_path,
        prompt=prompt,
        output_path=out_path,
        steps=20,
        seed=42,
        cfg_scale=7.5,
    )
    elapsed = time.perf_counter() - t0
    print(f"Execution complete in {elapsed:.2f}s. Success={res.success}")

    if not res.success:
        print(f"ERROR: {res.error_message}")
        return

    # Analyze result
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

    # Check cyan/green remaining inside mask
    res_hsv = np.array(result.convert("HSV"), dtype=float)
    h = res_hsv[..., 0] * (360.0 / 255.0)
    s = res_hsv[..., 1] / 255.0
    v = res_hsv[..., 2] / 255.0
    cg_inside = ((h >= 50) & (h <= 180) & (s >= 0.20) & (v >= 0.20)) & m_arr
    print(f"Cyan/green pixels inside mask after inpainting: {cg_inside.sum()} px")

    # Save mask and overlay for reporting
    mask.save(out_dir / "motif2_glass_repaired_mask.png")
    res.plan.segment_result.overlay_image.save(out_dir / "motif2_glass_repaired_overlay.png")
    if res.primed_image:
        res.primed_image.save(out_dir / "motif2_glass_repaired_primed.png")

    print(f"Artifacts saved to {out_dir}")

if __name__ == "__main__":
    run_glass_repair()
