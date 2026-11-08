"""
Sprint 85 Controller Glass Test:
Runs PromptEditController.execute() with Seed 100 on Qualcomm Hexagon NPU.
Checks if the black line is prevented through the controller's full crop-and-pad pipeline.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
import numpy as np

from controllers.prompt_edit_controller import PromptEditController

def test_glass_controller_run():
    out_dir = Path("reports/sprint_85_material_polish/images/glass_controller_tests")
    out_dir.mkdir(parents=True, exist_ok=True)

    input_path = Path("reports/sprint_80_total_validation/images/motif2_glass_1_original.png")
    out_path = out_dir / "motif2_glass_controller_seed_100.png"

    controller = PromptEditController()

    prompt = "Verwandle die Glasskulptur in 24k Gold."

    print("Executing PromptEditController for Glass Sculpture (Seed 100) on Qualcomm Hexagon HTP...")
    t0 = time.perf_counter()
    res = controller.execute(
        input_image_path=input_path,
        prompt=prompt,
        output_path=out_path,
        steps=20,
        seed=100,
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

    lum = 0.299 * res_arr[..., 0] + 0.587 * res_arr[..., 1] + 0.114 * res_arr[..., 2]

    # Seam zone: X in [213, 218], Y in [162, 269]
    seam_slice = (slice(162, 270), slice(213, 219))
    seam_mask = m_arr[seam_slice]
    seam_lum = lum[seam_slice][seam_mask]
    
    print(f"Seam Zone (Controller Crop-and-Pad Run):")
    print(f"  Min Lum: {seam_lum.min():.1f} (was 1.5 in Sprint 82)")
    print(f"  Mean Lum: {seam_lum.mean():.1f}")
    print(f"  Dark pixels (<25): {(seam_lum < 25).sum()} (was 28 in Sprint 82)")
    print(f"  Dark pixels (<40): {(seam_lum < 40).sum()} (was 107 in Sprint 82)")

    # Pedestal
    ped_mask = m_arr & (np.arange(512)[:, None] >= 330) & (np.arange(512)[:, None] <= 387)
    print(f"Pedestal: Mean Lum={lum[ped_mask].mean():.1f}, RGB=[{res_arr[ped_mask][:,0].mean():.1f}, {res_arr[ped_mask][:,1].mean():.1f}, {res_arr[ped_mask][:,2].mean():.1f}]")

if __name__ == "__main__":
    test_glass_controller_run()
