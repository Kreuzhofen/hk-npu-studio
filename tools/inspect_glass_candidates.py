"""
Visual inspection of candidate seeds on glass sculpture:
Compare Seed 42 (base vs enhanced neg), Seed 100, Seed 777.
"""

from pathlib import Path
import numpy as np
from PIL import Image

def inspect_glass_candidates():
    mask = np.array(Image.open("reports/sprint_82_material_repair/images/motif2_glass_repaired_mask.png").convert("L")) > 128
    
    seeds = ["seed_42_base_neg", "seed_42_enh_neg", "seed_100_enh_neg"]
    
    # Sub-components:
    # 1. Beak & Head (Y: 117..165)
    head_mask = mask & (np.arange(512)[:, None] >= 117) & (np.arange(512)[:, None] <= 165)
    # 2. Seam Zone (X: 213..218, Y: 162..269)
    seam_slice = (slice(162, 270), slice(213, 219))
    seam_mask = mask[seam_slice]
    # 3. Pedestal / Base (Y: 330..387)
    ped_mask = mask & (np.arange(512)[:, None] >= 330) & (np.arange(512)[:, None] <= 387)

    print("Detailed Component Inspection of Glass Candidates:")
    for s in seeds:
        p = f"reports/sprint_85_material_polish/images/glass_seeds/glass_result_{s}.png"
        arr = np.array(Image.open(p).convert("RGB"), dtype=float)
        lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
        
        h_lum = lum[head_mask].mean()
        s_lum = lum[seam_slice][seam_mask].mean()
        s_min = lum[seam_slice][seam_mask].min()
        p_lum = lum[ped_mask].mean()
        p_rgb = arr[ped_mask].mean(axis=0)
        
        print(f"\nCandidate: {s}")
        print(f"  Head & Beak Mean L: {h_lum:.1f}")
        print(f"  Seam Zone: Mean L={s_lum:.1f}, Min L={s_min:.1f}, px<30={(lum[seam_slice][seam_mask] < 30).sum()}")
        print(f"  Pedestal Mean L: {p_lum:.1f}, RGB=[{p_rgb[0]:.1f}, {p_rgb[1]:.1f}, {p_rgb[2]:.1f}]")
        print(f"  Overall Mask: Mean L={lum[mask].mean():.1f}, Std={lum[mask].std():.1f}")

if __name__ == "__main__":
    inspect_glass_candidates()
