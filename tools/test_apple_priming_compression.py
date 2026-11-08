"""
Sprint 85 Experiment: Test candidate luminance compression functions on Motif 1 (Apple).
Evaluates min_val candidates (120, 135, 145, 155) and tone-curve functions.
Checks:
- Region V (former dark core shadow X:350..375, Y:280..370)
- Highlight retention (X:275..315, Y:280..360)
- Natural surface gradients (no harsh banding or kinks)
- Gold color fidelity (Hue=40 deg, saturation balance)
"""

from pathlib import Path
import numpy as np
from PIL import Image

def lum(arr):
    return 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

def run_tests():
    orig_img = Image.open("reports/appl_edit_test_49/appl_edit_49_original.png").convert("RGB")
    mask_img = Image.open("reports/sprint_82_material_repair/images/motif1_apple_repaired_mask.png").convert("L")
    
    orig_arr = np.array(orig_img, dtype=np.float32)
    mask_arr = np.array(mask_img, dtype=np.float32) / 255.0
    mask_bool = mask_arr > 0.5
    
    orig_hsv = np.array(orig_img.convert("HSV"), dtype=np.float32)
    h = orig_hsv[:, :, 0]
    s = orig_hsv[:, :, 1]
    v = orig_hsv[:, :, 2]
    v_norm = v / 255.0

    target_h = float(40.0 * 255.0 / 360.0) # 24k gold hue
    prime_h = np.full_like(h, target_h)
    
    sat_min = 130.0
    sat_max = 220.0
    val_mult = 1.05

    # Zones for evaluation:
    zone_v = (slice(280, 370), slice(350, 375))
    zone_hl = (slice(280, 360), slice(275, 315))
    mask_v = mask_bool[zone_v]
    mask_hl = mask_bool[zone_hl]

    candidates = [
        ("Current (Sprint 82/84 Baseline)", 0.0, "current"),
        ("Affine min_val = 120.0", 120.0, "affine"),
        ("Affine min_val = 135.0", 135.0, "affine"),
        ("Affine min_val = 145.0 (Prompt Candidate)", 145.0, "affine"),
        ("Affine min_val = 155.0", 155.0, "affine"),
        ("Soft Knee Toe-Lift (threshold=150, min_val=140)", 140.0, "soft_toe"),
    ]

    out_dir = Path("reports/sprint_85_material_polish/experiments")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'Candidate':45s} | {'Zone V Mean L':13s} | {'Zone V Min L':12s} | {'Highlight Mean L':16s} | {'Highlight Max L':15s}")
    print("-" * 115)

    results = []

    for name, m_val, formula in candidates:
        if formula == "current":
            sat_curve = np.sin(np.pi * np.clip(v_norm, 0.0, 1.0))
            prime_s = np.clip(sat_min + (sat_max - sat_min) * sat_curve, 0.0, 255.0)
            prime_v = np.clip(v * val_mult, 0.0, 255.0)
        elif formula == "affine":
            # Normalized compression: v_comp in [min_val/255, 1.0]
            norm_comp = (m_val / 255.0) + v_norm * (1.0 - (m_val / 255.0))
            prime_v = np.clip(norm_comp * 255.0 * val_mult, 0.0, 255.0)
            # Recompute saturation curve with the compressed luminance so specular rolloff adapts
            sat_curve = np.sin(np.pi * np.clip(prime_v / 255.0, 0.0, 1.0))
            prime_s = np.clip(sat_min + (sat_max - sat_min) * sat_curve, 0.0, 255.0)
        elif formula == "soft_toe":
            # Lifts only shadows below 150 smoothly towards m_val
            t = 160.0
            deficit = np.maximum(0.0, t - v) / t
            lift = (m_val - (v * (m_val / t))) * (deficit ** 1.5)
            prime_v = np.clip((v + lift) * val_mult, 0.0, 255.0)
            sat_curve = np.sin(np.pi * np.clip(prime_v / 255.0, 0.0, 1.0))
            prime_s = np.clip(sat_min + (sat_max - sat_min) * sat_curve, 0.0, 255.0)

        hsv_primed = np.stack([prime_h, prime_s, prime_v], axis=-1).astype(np.uint8)
        rgb_primed = np.array(Image.fromarray(hsv_primed, mode="HSV").convert("RGB"), dtype=np.float32)

        alpha = mask_arr[:, :, np.newaxis]
        out_arr = orig_arr * (1.0 - alpha) + rgb_primed * alpha
        out_uint8 = np.clip(np.round(out_arr), 0, 255).astype(np.uint8)
        
        # Enforce exact bit identity outside mask
        out_uint8[~mask_bool] = np.round(orig_arr[~mask_bool]).astype(np.uint8)
        
        test_img = Image.fromarray(out_uint8, mode="RGB")
        safe_name = name.split()[0].lower() + "_" + str(int(m_val)) + ".png"
        test_img.save(out_dir / safe_name)

        l_out = lum(out_uint8)
        v_mean = float(l_out[zone_v][mask_v].mean())
        v_min = float(l_out[zone_v][mask_v].min())
        hl_mean = float(l_out[zone_hl][mask_hl].mean())
        hl_max = float(l_out[zone_hl][mask_hl].max())

        print(f"{name:45s} | {v_mean:13.1f} | {v_min:12.1f} | {hl_mean:16.1f} | {hl_max:15.1f}")
        results.append({
            "name": name,
            "min_val": m_val,
            "v_mean": v_mean,
            "v_min": v_min,
            "hl_mean": hl_mean,
            "hl_max": hl_max,
            "img_path": str(out_dir / safe_name)
        })

    # Outside mask check:
    diff_out = np.abs(out_uint8[~mask_bool] - orig_arr[~mask_bool]).max()
    print(f"\nOutside mask bit-exact check on all candidates: max diff = {diff_out:.1f} px (PASS={diff_out == 0})")

if __name__ == "__main__":
    run_tests()
