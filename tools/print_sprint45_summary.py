import json
from pathlib import Path

data = json.loads(Path("reports/sprint45_results/sprint45_portrait_metrics.json").read_text(encoding="utf-8"))

print(f"{'Label':<35} | {'D':<4} | {'L1':<6} | {'FaceL1':<6} | {'SSIM':<6} | {'EdgeIoU':<7} | {'TexVar':<7} | {'DeltaE':<6} | {'Time':<5}")
print("-" * 98)
for d in data:
    m = d["metrics"]
    label = d["label"]
    d_val = d["denoising"]
    l1 = m["l1_drift"]
    fl1 = m["face_l1_drift"]
    ssim = m["ssim"]
    eiou = m["edge_iou"]
    tex = m["laplacian_texture_variance"]
    de = m["delta_e_color_drift"]
    sec = d["total_seconds"]
    print(f"{label:<35} | {d_val:<4.2f} | {l1:<6.2f} | {fl1:<6.2f} | {ssim:<6.4f} | {eiou:<7.4f} | {tex:<7.1f} | {de:<6.2f} | {sec:<5.1f}")
