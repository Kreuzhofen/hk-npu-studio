"""
Analyze Sprint 43 Benchmark Database and generate statistics for report.
"""
import json
from pathlib import Path

db = json.load(open("reports/sprint43_results/sprint43_benchmark_metrics.json", "r", encoding="utf-8"))
print(f"Total runs in database: {len(db)}")

cpu_fallbacks = [x["execution_times"].get("cpu_vae_encoder_ms", 0.0) for x in db]
print(f"Max CPU Fallback across all runs: {max(cpu_fallbacks):.2f} ms")

canny_runs = [x for x in db if x["mode"] == "canny_qnn"]
anchor_runs = [x for x in db if x["mode"] == "latent_anchor"]
base_runs = [x for x in db if x["mode"] == "none"]

def avg(vals): return sum(vals) / len(vals) if vals else 0.0

print("\n--- HTP LATENCY SUMMARY (Average across all motifs & steps) ---")
print(f"Canny QNN ({len(canny_runs)} runs):")
print(f"  VAE Enc:    {avg([x['execution_times']['htp_vae_encoder_ms'] for x in canny_runs]):.1f} ms")
print(f"  ControlNet: {avg([x['execution_times']['htp_controlnet_total_ms'] for x in canny_runs]):.1f} ms")
print(f"  UNet Total: {avg([x['execution_times']['htp_unet_total_ms'] for x in canny_runs]):.1f} ms")
print(f"  UNet/step:  {avg([x['execution_times']['htp_unet_step_avg_ms'] for x in canny_runs]):.1f} ms")
print(f"  VAE Dec:    {avg([x['execution_times']['htp_vae_decoder_ms'] for x in canny_runs]):.1f} ms")
print(f"  Total HTP:  {avg([x['execution_times']['total_inference_ms'] for x in canny_runs]):.1f} ms")

print(f"\nLatent Anchor ({len(anchor_runs)} runs):")
print(f"  VAE Enc:    {avg([x['execution_times']['htp_vae_encoder_ms'] for x in anchor_runs]):.1f} ms")
print(f"  ControlNet: 0.0 ms (No extra model)")
print(f"  UNet Total: {avg([x['execution_times']['htp_unet_total_ms'] for x in anchor_runs]):.1f} ms")
print(f"  UNet/step:  {avg([x['execution_times']['htp_unet_step_avg_ms'] for x in anchor_runs]):.1f} ms")
print(f"  VAE Dec:    {avg([x['execution_times']['htp_vae_decoder_ms'] for x in anchor_runs]):.1f} ms")
print(f"  Total HTP:  {avg([x['execution_times']['total_inference_ms'] for x in anchor_runs]):.1f} ms")

print("\n--- QUALITY METRICS (Silhouette Preservation & L1 Drift) ---")
print("Edge IoU (Silhouette preservation, higher is closer to original contours):")
print(f"  Baseline (No Ref): {avg([x['edge_iou'] for x in base_runs]):.4f}")
print(f"  Latent Anchor:     {avg([x['edge_iou'] for x in anchor_runs]):.4f}")
print(f"  Canny QNN:         {avg([x['edge_iou'] for x in canny_runs]):.4f}")

print("\nL1 Drift (Mean absolute pixel difference from original, lower is closer to original colors/pixels):")
print(f"  Baseline (No Ref): {avg([x['l1_drift'] for x in base_runs]):.2f}")
print(f"  Canny QNN:         {avg([x['l1_drift'] for x in canny_runs]):.2f}")
print(f"  Latent Anchor:     {avg([x['l1_drift'] for x in anchor_runs]):.2f}")

print("\n--- BY MOTIF BREAKDOWN ---")
for m in ["objects", "landscapes", "portraits", "architecture"]:
    m_base = [x for x in base_runs if x["motif"] == m]
    m_canny = [x for x in canny_runs if x["motif"] == m]
    m_anchor = [x for x in anchor_runs if x["motif"] == m]
    print(f"\nMotif: {m.upper()}")
    print(f"  Edge IoU -> Baseline: {avg([x['edge_iou'] for x in m_base]):.4f} | Anchor: {avg([x['edge_iou'] for x in m_anchor]):.4f} | Canny: {avg([x['edge_iou'] for x in m_canny]):.4f}")
    print(f"  L1 Drift -> Baseline: {avg([x['l1_drift'] for x in m_base]):.2f} | Canny: {avg([x['l1_drift'] for x in m_canny]):.2f} | Anchor: {avg([x['l1_drift'] for x in m_anchor]):.2f}")
    print(f"  Avg Latency -> Canny: {avg([x['execution_times']['total_inference_ms'] for x in m_canny]):.1f} ms | Anchor: {avg([x['execution_times']['total_inference_ms'] for x in m_anchor]):.1f} ms")

print("\n--- BY DENOISING LEVEL BREAKDOWN (at fidelity=0.75) ---")
for d in [0.45, 0.65, 0.80]:
    d_canny = [x for x in canny_runs if abs(x["denoising_strength"] - d) < 0.01 and abs(x["reference_fidelity"] - 0.75) < 0.01]
    d_anchor = [x for x in anchor_runs if abs(x["denoising_strength"] - d) < 0.01 and abs(x["reference_fidelity"] - 0.75) < 0.01]
    print(f"Denoising {d:.2f}:")
    print(f"  Canny IoU: {avg([x['edge_iou'] for x in d_canny]):.4f} | Anchor IoU: {avg([x['edge_iou'] for x in d_anchor]):.4f}")
    print(f"  Canny L1:  {avg([x['l1_drift'] for x in d_canny]):.2f} | Anchor L1:  {avg([x['l1_drift'] for x in d_anchor]):.2f}")
    print(f"  Canny HTP: {avg([x['execution_times']['total_inference_ms'] for x in d_canny]):.1f} ms | Anchor HTP: {avg([x['execution_times']['total_inference_ms'] for x in d_anchor]):.1f} ms")

print("\n--- BY FIDELITY LEVEL BREAKDOWN (at denoising=0.65) ---")
for f in [0.25, 0.50, 0.75, 1.00]:
    f_canny = [x for x in canny_runs if abs(x["reference_fidelity"] - f) < 0.01 and abs(x["denoising_strength"] - 0.65) < 0.01]
    f_anchor = [x for x in anchor_runs if abs(x["reference_fidelity"] - f) < 0.01 and abs(x["denoising_strength"] - 0.65) < 0.01]
    print(f"Fidelity {f:.2f}:")
    print(f"  Canny IoU: {avg([x['edge_iou'] for x in f_canny]):.4f} | Anchor IoU: {avg([x['edge_iou'] for x in f_anchor]):.4f}")
    print(f"  Canny L1:  {avg([x['l1_drift'] for x in f_canny]):.2f} | Anchor L1:  {avg([x['l1_drift'] for x in f_anchor]):.2f}")
