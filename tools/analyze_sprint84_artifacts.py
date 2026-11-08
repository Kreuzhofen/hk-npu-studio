"""
Visual artifact inspection script for Sprint 84:
Pinpoints the dark vertical zone in Apple and the dark line/area in Glass Sculpture.
Outputs detailed pixel statistics, coordinates, and comparisons.
"""

from pathlib import Path
import numpy as np
from PIL import Image

def lum(arr):
    return 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

def inspect_apple_artifacts():
    print("==================================================")
    print("DETAILED PIXEL AUDIT: MOTIF 1 (APFEL)")
    print("==================================================")
    
    orig = np.array(Image.open("reports/appl_edit_test_49/appl_edit_49_original.png").convert("RGB"), dtype=np.float32)
    prim = np.array(Image.open("reports/sprint_82_material_repair/images/motif1_apple_repaired_primed.png").convert("RGB"), dtype=np.float32)
    s42  = np.array(Image.open("reports/sprint_82_material_repair/images/apple_seeds/apple_result_seed_42.png").convert("RGB"), dtype=np.float32)
    s43  = np.array(Image.open("reports/sprint_82_material_repair/images/apple_seeds/apple_result_seed_43.png").convert("RGB"), dtype=np.float32)
    rep  = np.array(Image.open("reports/sprint_82_material_repair/images/motif1_apple_repaired_htp.png").convert("RGB"), dtype=np.float32)
    mask = np.array(Image.open("reports/sprint_82_material_repair/images/motif1_apple_repaired_mask.png").convert("L")) > 128

    l_orig = lum(orig)
    l_prim = lum(prim)
    l_s42 = lum(s42)
    l_s43 = lum(s43)
    l_rep = lum(rep)

    y_mid_slice = slice(280, 360)
    print(f"\n--- Horizontal Luminance Cross-Section (averaged across y=280..360) ---")
    print(f"{'X':3s} | {'Orig L':7s} | {'Prim L':7s} | {'S42 L':7s} | {'S43 L':7s} | {'Rep L':7s}")
    for x in range(250, 420, 5):
        m_col = mask[y_mid_slice, x]
        if m_col.sum() == 0:
            continue
        print(f"{x:3d} | {l_orig[y_mid_slice, x].mean():7.1f} | {l_prim[y_mid_slice, x].mean():7.1f} | {l_s42[y_mid_slice, x].mean():7.1f} | {l_s43[y_mid_slice, x].mean():7.1f} | {l_rep[y_mid_slice, x].mean():7.1f}")

    v_zone = (slice(280, 370), slice(350, 375))
    v_mask = mask[v_zone]

    print(f"\n--- Zone V (Dark Vertical Zone: X=350..375, Y=280..370, {v_mask.sum()} px) ---")
    for name, l, arr in [("Original Red Apple", l_orig, orig), 
                         ("Primed Preview", l_prim, prim), 
                         ("Seed 42 (Matrix)", l_s42, s42), 
                         ("Seed 43 (Matrix)", l_s43, s43), 
                         ("Repaired HTP Result", l_rep, rep)]:
        sub_l = l[v_zone][v_mask]
        sub_rgb = arr[v_zone][v_mask]
        print(f"  {name:22s}: Mean L={sub_l.mean():5.1f}, Min L={sub_l.min():5.1f}, Max L={sub_l.max():5.1f}, Mean RGB=[{sub_rgb[:,0].mean():5.1f}, {sub_rgb[:,1].mean():5.1f}, {sub_rgb[:,2].mean():5.1f}]")

    stem_zone = (slice(223, 270), slice(300, 325))
    stem_mask = mask[stem_zone]
    print(f"\n--- Zone S (Stem / Inflow Crease: X=300..325, Y=223..270, {stem_mask.sum()} px) ---")
    for name, l, arr in [("Original Red Apple", l_orig, orig), 
                         ("Primed Preview", l_prim, prim), 
                         ("Seed 42 (Matrix)", l_s42, s42), 
                         ("Seed 43 (Matrix)", l_s43, s43), 
                         ("Repaired HTP Result", l_rep, rep)]:
        sub_l = l[stem_zone][stem_mask]
        sub_rgb = arr[stem_zone][stem_mask]
        print(f"  {name:22s}: Mean L={sub_l.mean():5.1f}, Min L={sub_l.min():5.1f}, Max L={sub_l.max():5.1f}, Mean RGB=[{sub_rgb[:,0].mean():5.1f}, {sub_rgb[:,1].mean():5.1f}, {sub_rgb[:,2].mean():5.1f}]")

def inspect_glass_artifacts():
    print("\n==================================================")
    print("DETAILED PIXEL AUDIT: MOTIF 2 (GLASS SCULPTURE)")
    print("==================================================")
    orig = np.array(Image.open("reports/sprint_80_total_validation/images/motif2_glass_1_original.png").convert("RGB"), dtype=np.float32)
    prim = np.array(Image.open("reports/sprint_82_material_repair/images/motif2_glass_repaired_primed.png").convert("RGB"), dtype=np.float32)
    rep  = np.array(Image.open("reports/sprint_82_material_repair/images/motif2_glass_repaired_htp.png").convert("RGB"), dtype=np.float32)
    mask = np.array(Image.open("reports/sprint_82_material_repair/images/motif2_glass_repaired_mask.png").convert("L")) > 128
    
    l_orig = lum(orig)
    l_prim = lum(prim)
    l_rep = lum(rep)

    fold_zone = (slice(260, 275), slice(200, 230))
    fold_mask = mask[fold_zone]
    print(f"\n--- Zone G1 (Torso / Wing Fold: X=200..230, Y=260..275, {fold_mask.sum()} px) ---")
    for name, l, arr in [("Original Glass", l_orig, orig), 
                         ("Primed Preview", l_prim, prim), 
                         ("Repaired HTP Result", l_rep, rep)]:
        sub_l = l[fold_zone][fold_mask]
        sub_rgb = arr[fold_zone][fold_mask]
        print(f"  {name:22s}: Mean L={sub_l.mean():5.1f}, Min L={sub_l.min():5.1f}, Max L={sub_l.max():5.1f}, Mean RGB=[{sub_rgb[:,0].mean():5.1f}, {sub_rgb[:,1].mean():5.1f}, {sub_rgb[:,2].mean():5.1f}]")

    neck_zone = (slice(165, 185), slice(210, 240))
    neck_mask = mask[neck_zone]
    print(f"\n--- Zone G2 (Neck Shadow: X=210..240, Y=165..185, {neck_mask.sum()} px) ---")
    for name, l, arr in [("Original Glass", l_orig, orig), 
                         ("Primed Preview", l_prim, prim), 
                         ("Repaired HTP Result", l_rep, rep)]:
        sub_l = l[neck_zone][neck_mask]
        sub_rgb = arr[neck_zone][neck_mask]
        print(f"  {name:22s}: Mean L={sub_l.mean():5.1f}, Min L={sub_l.min():5.1f}, Max L={sub_l.max():5.1f}, Mean RGB=[{sub_rgb[:,0].mean():5.1f}, {sub_rgb[:,1].mean():5.1f}, {sub_rgb[:,2].mean():5.1f}]")

    ped_zone = (slice(325, 345), slice(210, 270))
    ped_mask = mask[ped_zone]
    print(f"\n--- Zone G3 (Pedestal Transition / Waist: X=210..270, Y=325..345, {ped_mask.sum()} px) ---")
    for name, l, arr in [("Original Glass", l_orig, orig), 
                         ("Primed Preview", l_prim, prim), 
                         ("Repaired HTP Result", l_rep, rep)]:
        sub_l = l[ped_zone][ped_mask]
        sub_rgb = arr[ped_zone][ped_mask]
        print(f"  {name:22s}: Mean L={sub_l.mean():5.1f}, Min L={sub_l.min():5.1f}, Max L={sub_l.max():5.1f}, Mean RGB=[{sub_rgb[:,0].mean():5.1f}, {sub_rgb[:,1].mean():5.1f}, {sub_rgb[:,2].mean():5.1f}]")

    from PIL import ImageFilter
    m_img = Image.fromarray((mask * 255).astype(np.uint8))
    m_dil = np.array(m_img.filter(ImageFilter.MaxFilter(size=5))) > 128
    m_ero = np.array(m_img.filter(ImageFilter.MinFilter(size=5))) > 128
    boundary = m_dil & ~m_ero
    print(f"\n--- Boundary Contour Transition ({boundary.sum()} px) ---")
    b_rep_l = l_rep[boundary]
    b_orig_l = l_orig[boundary]
    print(f"  Boundary Repaired Lum: Mean={b_rep_l.mean():.1f}, Min={b_rep_l.min():.1f}, <30px={(b_rep_l < 30).sum()}")
    print(f"  Boundary Original Lum: Mean={b_orig_l.mean():.1f}, Min={b_orig_l.min():.1f}")

if __name__ == "__main__":
    inspect_apple_artifacts()
    inspect_glass_artifacts()
