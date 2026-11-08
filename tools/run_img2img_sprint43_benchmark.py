"""
Sprint 43 Quality Benchmark Suite: Reference Image Control (Canny QNN vs Latent Anchor).
Executes systematic empirical comparisons on Qualcomm Hexagon HTP V73.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
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
from engine.controlnet_canny_backend import canny_edge_detector

# Windows Memory query via psapi
class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.wintypes.DWORD),
        ("PageFaultCount", ctypes.wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]

def get_process_memory_mb() -> tuple[float, float]:
    try:
        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
            return (pmc.WorkingSetSize / (1024 * 1024), pmc.PeakWorkingSetSize / (1024 * 1024))
    except Exception:
        pass
    return (0.0, 0.0)

def compute_edge_iou(img1_path: Path, img2_path: Path) -> float:
    try:
        e1 = canny_edge_detector(str(img1_path), low_threshold=15, high_threshold=45) > 0
        e2 = canny_edge_detector(str(img2_path), low_threshold=15, high_threshold=45) > 0
        intersection = np.logical_and(e1, e2).sum()
        union = np.logical_or(e1, e2).sum()
        return float(intersection / union) if union > 0 else 1.0
    except Exception:
        return 0.0

def compute_l1_drift(img1_path: Path, img2_path: Path) -> float:
    try:
        with Image.open(img1_path) as im1, Image.open(img2_path) as im2:
            arr1 = np.array(im1.convert("RGB").resize((512, 512)), dtype=np.float32)
            arr2 = np.array(im2.convert("RGB").resize((512, 512)), dtype=np.float32)
        return float(np.mean(np.abs(arr1 - arr2)))
    except Exception:
        return 0.0

def create_horizontal_grid(title: str, images: list[tuple[str, Path]], output_path: Path):
    cell_w, cell_h = 280, 280
    header_h = 36
    n = len(images)
    grid = Image.new("RGB", (n * cell_w, cell_h + header_h), (24, 26, 32))
    draw = ImageDraw.Draw(grid)

    for i, (label, p) in enumerate(images):
        if p.is_file():
            with Image.open(p) as img:
                thumb = img.convert("RGB").resize((cell_w, cell_h), Image.Resampling.LANCZOS)
                grid.paste(thumb, (i * cell_w, header_h))
        # Draw label
        draw.text((i * cell_w + 10, 10), label, fill=(235, 235, 240))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    grid.save(output_path, format="PNG")
    print(f"Saved visual grid: {output_path.name}", flush=True)

def main():
    print("==================================================================", flush=True)
    print("  SPRINT 43: REFERENCE CONTROL QUALITY BENCHMARK (HTP NPU)        ", flush=True)
    print("==================================================================", flush=True)

    results_dir = REPO_ROOT / "reports" / "sprint43_results"
    results_dir.mkdir(parents=True, exist_ok=True)
    sources_dir = results_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    # 1. Prepare standardized 512x512 golden sources
    raw_motifs = {
        "objects": {
            "src": REPO_ROOT / "output" / "generate_1792859418_d2646d69.png",
            "prompt": "a futuristic metallic apple with blue glowing circuits, polished chrome, 8k, photorealistic",
            "seed": 4201,
            "title": "Gegenstände & Stillleben (Apfel)",
        },
        "landscapes": {
            "src": REPO_ROOT / "output" / "smoke_sd21_1792768376_94abe6b7.png",
            "prompt": "a vibrant autumn mountain valley with golden yellow trees and warm sunset light, 8k, scenic",
            "seed": 4202,
            "title": "Landschaften (Gebirge)",
        },
        "portraits": {
            "src": REPO_ROOT / "output" / "generate_1792859244_1137524_input.png",
            "prompt": "a glowing neon cybernetic warrior portrait, synthwave aesthetic, 8k",
            "seed": 4203,
            "title": "Porträts & Gesichter (Krieger)",
        },
        "architecture": {
            "src": REPO_ROOT / "output" / "generate_a2879a4e.png",
            "prompt": "a futuristic gothic cyberpunk cathedral illuminated by violet neon lights, towering spires, 8k",
            "seed": 4204,
            "title": "Architektur & Geometrie (Kathedrale)",
        },
    }

    motif_sources = {}
    for m_key, m_info in raw_motifs.items():
        s_path = sources_dir / f"motif_{m_key}.png"
        with Image.open(m_info["src"]) as opened:
            rgb_512 = opened.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
            rgb_512.save(s_path, format="PNG")
        motif_sources[m_key] = s_path
        print(f"Prepared standardized source for {m_key}: {s_path.name}", flush=True)

    adapter = SD15QnnInpaintingAdapter()
    benchmark_database = []

    # 2. Benchmark Parameters
    denoising_levels = [0.45, 0.65, 0.80]
    fidelity_levels = [0.25, 0.50, 0.75, 1.00]
    steps = 15  # Optimal convergence for Euler scheduler on HTP

    # Total planned runs:
    # Per motif:
    # 1 Baseline (denoising 0.65, no ref)
    # Denoising sweep: 3 denoising * 2 modes (at fidelity 0.75) = 6 runs
    # Fidelity sweep: 3 additional fidelities (0.25, 0.50, 1.00) * 2 modes (at denoising 0.65) = 6 runs
    # Total per motif = 1 + 6 + 6 = 13 runs.
    # Total across 4 motifs = 52 runs!

    run_counter = 0
    total_runs = len(raw_motifs) * 13

    for m_key, m_info in raw_motifs.items():
        src_path = motif_sources[m_key]
        prompt = m_info["prompt"]
        seed = m_info["seed"]
        title = m_info["title"]
        print(f"\n==================================================================", flush=True)
        print(f"  MOTIF: {title.upper()}", flush=True)
        print(f"==================================================================", flush=True)

        motif_runs = {}

        # Run 0: Baseline (No Reference Control, Sweet Spot Denoising 0.65)
        run_counter += 1
        base_name = f"{m_key}_baseline_s065"
        base_out = results_dir / f"{base_name}.png"
        print(f"[{run_counter}/{total_runs}] Running Baseline (No Ref) for {m_key}...", flush=True)
        t0 = time.perf_counter()
        res_base = adapter.run_img2img(
            input_image_path=src_path,
            prompt=prompt,
            output_path=base_out,
            steps=steps,
            seed=seed,
            denoising_strength=0.65,
            enable_reference_control=False,
        )
        t_wall = time.perf_counter() - t0
        mem_rss, mem_peak = get_process_memory_mb()
        edge_iou = compute_edge_iou(src_path, base_out)
        l1_drift = compute_l1_drift(src_path, base_out)

        meta_base = {
            "motif": m_key,
            "title": title,
            "configuration": "Baseline (No Ref)",
            "mode": "none",
            "denoising_strength": 0.65,
            "reference_fidelity": 0.0,
            "seed": seed,
            "steps": steps,
            "actual_inference_steps": res_base.metadata.get("actual_inference_steps", 10),
            "output_path": str(base_out),
            "wall_clock_seconds": t_wall,
            "execution_times": res_base.metadata.get("execution_times", {}),
            "memory_rss_mb": mem_rss,
            "memory_peak_mb": mem_peak,
            "edge_iou": edge_iou,
            "l1_drift": l1_drift,
        }
        benchmark_database.append(meta_base)
        motif_runs["baseline_s065"] = base_out

        # Denoising Sweep across 0.45, 0.65, 0.80 at Fidelity 0.75
        for d in denoising_levels:
            for mode_key, mode_name in [("canny_qnn", "Canny QNN"), ("latent_anchor", "Latent Anchor")]:
                run_counter += 1
                cfg_name = f"{m_key}_{mode_key}_d{int(d*100)}_f75"
                out_p = results_dir / f"{cfg_name}.png"
                print(f"[{run_counter}/{total_runs}] Running {mode_name} | Denoising={d:.2f} | Fidelity=0.75 | {m_key}...", flush=True)
                t0 = time.perf_counter()
                res = adapter.run_img2img(
                    input_image_path=src_path,
                    prompt=prompt,
                    output_path=out_p,
                    steps=steps,
                    seed=seed,
                    denoising_strength=d,
                    enable_reference_control=True,
                    reference_mode=mode_key,
                    reference_fidelity=0.75,
                )
                t_wall = time.perf_counter() - t0
                mem_rss, mem_peak = get_process_memory_mb()
                edge_iou = compute_edge_iou(src_path, out_p)
                l1_drift = compute_l1_drift(src_path, out_p)

                meta = {
                    "motif": m_key,
                    "title": title,
                    "configuration": f"{mode_name} (d={d:.2f}, f=0.75)",
                    "mode": mode_key,
                    "denoising_strength": d,
                    "reference_fidelity": 0.75,
                    "seed": seed,
                    "steps": steps,
                    "actual_inference_steps": res.metadata.get("actual_inference_steps", 10),
                    "output_path": str(out_p),
                    "wall_clock_seconds": t_wall,
                    "execution_times": res.metadata.get("execution_times", {}),
                    "memory_rss_mb": mem_rss,
                    "memory_peak_mb": mem_peak,
                    "edge_iou": edge_iou,
                    "l1_drift": l1_drift,
                }
                benchmark_database.append(meta)
                motif_runs[f"{mode_key}_d{int(d*100)}_f75"] = out_p

        # Reference Fidelity Sweep across 0.25, 0.50, 1.00 at Denoising 0.65
        for f in [0.25, 0.50, 1.00]:
            for mode_key, mode_name in [("canny_qnn", "Canny QNN"), ("latent_anchor", "Latent Anchor")]:
                run_counter += 1
                cfg_name = f"{m_key}_{mode_key}_d65_f{int(f*100)}"
                out_p = results_dir / f"{cfg_name}.png"
                print(f"[{run_counter}/{total_runs}] Running {mode_name} | Denoising=0.65 | Fidelity={f:.2f} | {m_key}...", flush=True)
                t0 = time.perf_counter()
                res = adapter.run_img2img(
                    input_image_path=src_path,
                    prompt=prompt,
                    output_path=out_p,
                    steps=steps,
                    seed=seed,
                    denoising_strength=0.65,
                    enable_reference_control=True,
                    reference_mode=mode_key,
                    reference_fidelity=f,
                )
                t_wall = time.perf_counter() - t0
                mem_rss, mem_peak = get_process_memory_mb()
                edge_iou = compute_edge_iou(src_path, out_p)
                l1_drift = compute_l1_drift(src_path, out_p)

                meta = {
                    "motif": m_key,
                    "title": title,
                    "configuration": f"{mode_name} (d=0.65, f={f:.2f})",
                    "mode": mode_key,
                    "denoising_strength": 0.65,
                    "reference_fidelity": f,
                    "seed": seed,
                    "steps": steps,
                    "actual_inference_steps": res.metadata.get("actual_inference_steps", 10),
                    "output_path": str(out_p),
                    "wall_clock_seconds": t_wall,
                    "execution_times": res.metadata.get("execution_times", {}),
                    "memory_rss_mb": mem_rss,
                    "memory_peak_mb": mem_peak,
                    "edge_iou": edge_iou,
                    "l1_drift": l1_drift,
                }
                benchmark_database.append(meta)
                motif_runs[f"{mode_key}_d65_f{int(f*100)}"] = out_p

        # 3. Build Visual Comparison Grids for this motif
        # Grid 1: Denoising progression (Original, Baseline, Canny 0.45/0.65/0.80, Anchor 0.45/0.65/0.80)
        grid_denoise = [
            ("Original", src_path),
            ("Baseline (No Ref)", motif_runs["baseline_s065"]),
            ("Canny (d=0.45)", motif_runs["canny_qnn_d45_f75"]),
            ("Anchor (d=0.45)", motif_runs["latent_anchor_d45_f75"]),
            ("Canny (d=0.65)", motif_runs["canny_qnn_d65_f75"]),
            ("Anchor (d=0.65)", motif_runs["latent_anchor_d65_f75"]),
            ("Canny (d=0.80)", motif_runs["canny_qnn_d80_f75"]),
            ("Anchor (d=0.80)", motif_runs["latent_anchor_d80_f75"]),
        ]
        create_horizontal_grid(
            f"{title} - Denoising Sweep",
            grid_denoise,
            results_dir / f"sprint43_{m_key}_denoising_sweep.png",
        )

        # Grid 2: Reference Fidelity progression (Original, Canny 0.25..1.00, Anchor 0.25..1.00)
        grid_fidelity = [
            ("Original", src_path),
            ("Canny (f=0.25)", motif_runs["canny_qnn_d65_f25"]),
            ("Anchor (f=0.25)", motif_runs["latent_anchor_d65_f25"]),
            ("Canny (f=0.50)", motif_runs["canny_qnn_d65_f50"]),
            ("Anchor (f=0.50)", motif_runs["latent_anchor_d65_f50"]),
            ("Canny (f=0.75)", motif_runs["canny_qnn_d65_f75"]),
            ("Anchor (f=0.75)", motif_runs["latent_anchor_d65_f75"]),
            ("Canny (f=1.00)", motif_runs["canny_qnn_d65_f100"]),
            ("Anchor (f=1.00)", motif_runs["latent_anchor_d65_f100"]),
        ]
        create_horizontal_grid(
            f"{title} - Fidelity Sweep",
            grid_fidelity,
            results_dir / f"sprint43_{m_key}_fidelity_sweep.png",
        )

    # 4. Save entire benchmark database
    db_path = results_dir / "sprint43_benchmark_metrics.json"
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_database, f, indent=2)
    print(f"\nAll {len(benchmark_database)} benchmark runs saved to: {db_path}", flush=True)

    # 5. Build Master Cross-Motif Comparison Grid (4 Rows x 6 Columns)
    # Rows: Objects, Landscapes, Portraits, Architecture
    # Cols: Original, Baseline (0.65), Canny (d=0.65, f=0.75), Anchor (d=0.65, f=0.75), Canny (d=0.80, f=0.75), Anchor (d=0.80, f=0.75)
    cell_w, cell_h = 260, 260
    header_h = 32
    col_labels = [
        "1. Original-Quelle",
        "2. Baseline (Kein Ref)",
        "3. Modus A: Canny (0.65/0.75)",
        "4. Modus B: Anchor (0.65/0.75)",
        "5. Modus A: Canny (0.80/0.75)",
        "6. Modus B: Anchor (0.80/0.75)",
    ]
    master_grid = Image.new("RGB", (len(col_labels) * cell_w, 4 * cell_h + header_h), (20, 22, 28))
    draw_m = ImageDraw.Draw(master_grid)

    for c, lbl in enumerate(col_labels):
        draw_m.text((c * cell_w + 10, 8), lbl, fill=(235, 235, 240))

    row_keys = ["objects", "landscapes", "portraits", "architecture"]
    for r, m_key in enumerate(row_keys):
        y_top = header_h + r * cell_h
        row_files = [
            motif_sources[m_key],
            results_dir / f"{m_key}_baseline_s065.png",
            results_dir / f"{m_key}_canny_qnn_d65_f75.png",
            results_dir / f"{m_key}_latent_anchor_d65_f75.png",
            results_dir / f"{m_key}_canny_qnn_d80_f75.png",
            results_dir / f"{m_key}_latent_anchor_d80_f75.png",
        ]
        for c, p in enumerate(row_files):
            if p.is_file():
                with Image.open(p) as im:
                    thumb = im.convert("RGB").resize((cell_w, cell_h), Image.Resampling.LANCZOS)
                    master_grid.paste(thumb, (c * cell_w, y_top))

    master_path = results_dir / "sprint43_master_comparison.png"
    master_grid.save(master_path, format="PNG")
    print(f"Master comparison grid generated: {master_path}", flush=True)

    print("\n==================================================================", flush=True)
    print("  SPRINT 43 BENCHMARK SUITE COMPLETED SUCCESSFULLY ON HTP!         ", flush=True)
    print("==================================================================", flush=True)

if __name__ == "__main__":
    main()
