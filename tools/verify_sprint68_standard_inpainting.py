"""Verify Standard Inpainting with material_preset=None on Qualcomm Hexagon HTP."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\SnapdragonAI")
sys.path.insert(0, str(PROJECT_ROOT))

from controllers.inpainting_controller import InpaintingController
from config import OUTPUT_DIR, TEMP_DIR

M1_ORIGINAL = PROJECT_ROOT / "reports" / "phoenix_material_lab_65" / "m1_glass_original.png"
M1_MASK = PROJECT_ROOT / "reports" / "phoenix_material_lab_65" / "m1_glass_mask.png"
TEST_OUT = TEMP_DIR / "sprint68_std_inpainting_verify.png"

def main():
    print("Testing Standard Inpainting (material_preset=None) on Qualcomm Hexagon HTP...")
    ctrl = InpaintingController(ui_dispatch=lambda cb: cb())
    res = ctrl._run_product_path(
        input_image_path=M1_ORIGINAL,
        mask_image_path=M1_MASK,
        prompt="A modern glass sculpture, photorealistic",
        output_path=TEST_OUT,
        negative_prompt="blurry, deformed",
        steps=7,
        seed=6801,
        cfg_scale=7.5,
        denoising_strength=0.90,
        material_preset=None,
        progress=lambda p, v, d: print(f"  [{v*100:5.1f}%] {p:15}: {d or ''}"),
    )
    if res.success and TEST_OUT.is_file():
        print(f"[SUCCESS] Standard Inpainting executed successfully: {TEST_OUT.name} ({TEST_OUT.stat().st_size} bytes)")
        TEST_OUT.unlink(missing_ok=True)
        TEST_OUT.with_suffix(".json").unlink(missing_ok=True)
        return True
    else:
        print(f"[FAIL] Standard Inpainting failed: {res.error_message}")
        return False

if __name__ == "__main__":
    if not main():
        sys.exit(1)
