"""
Sprint 82 POST-Backup Tool
Secures all modified code, reports, benchmark JSONs, and generated images to Drive D:
Target: D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_82_MATERIAL_REPAIR_20261103\\POST
"""

import hashlib
import json
import shutil
from pathlib import Path

def create_post_backup():
    backup_dir = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_82_MATERIAL_REPAIR_20261103\POST")
    backup_dir.mkdir(parents=True, exist_ok=True)

    files_to_backup = [
        Path("engine/color_spatial_segmenter.py"),
        Path("engine/material_priming.py"),
        Path("controllers/prompt_edit_controller.py"),
        Path("tests/test_prompt_engine_foundation.py"),
        Path("tests/test_prompt_edit_controller.py"),
        Path("tests/test_prompt_edit_ui.py"),
        Path("reports/sprint_82_material_repair/SPRINT-82-REPORT.md"),
        Path("reports/sprint_82_material_repair/apple_seed_matrix.json"),
        Path("reports/sprint_82_material_repair/images/sprint_82_apple_comparison.png"),
        Path("reports/sprint_82_material_repair/images/sprint_82_glass_comparison.png"),
        Path("reports/sprint_82_material_repair/images/sprint_82_master_comparison_grid.png"),
        Path("reports/sprint_82_material_repair/images/motif1_apple_repaired_htp.png"),
        Path("reports/sprint_82_material_repair/images/motif1_apple_repaired_mask.png"),
        Path("reports/sprint_82_material_repair/images/motif1_apple_repaired_overlay.png"),
        Path("reports/sprint_82_material_repair/images/motif1_apple_repaired_primed.png"),
        Path("reports/sprint_82_material_repair/images/motif2_glass_repaired_htp.png"),
        Path("reports/sprint_82_material_repair/images/motif2_glass_repaired_mask.png"),
        Path("reports/sprint_82_material_repair/images/motif2_glass_repaired_overlay.png"),
        Path("reports/sprint_82_material_repair/images/motif2_glass_repaired_primed.png"),
        Path("reports/sprint_82_material_repair/images/apple_seeds/apple_result_seed_42.png"),
        Path("reports/sprint_82_material_repair/images/apple_seeds/apple_result_seed_43.png"),
        Path("reports/sprint_82_material_repair/images/apple_seeds/apple_result_seed_100.png"),
        Path("reports/sprint_82_material_repair/images/apple_seeds/apple_result_seed_777.png"),
        Path("reports/sprint_82_material_repair/images/apple_seeds/apple_result_seed_4901.png"),
        Path("tools/run_sprint82_apple_seed_matrix.py"),
        Path("tools/run_sprint82_glass_repair.py"),
        Path("tools/run_sprint82_apple_repair.py"),
        Path("tools/generate_sprint82_visual_comparisons.py"),
    ]

    manifest = {}
    copied_count = 0
    for src in files_to_backup:
        if not src.exists():
            print(f"Skipping non-existent file: {src}")
            continue
        dst = backup_dir / src
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

        h = hashlib.sha256()
        with open(dst, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        sha = h.hexdigest()
        manifest[str(src).replace("\\", "/")] = {
            "sha256": sha,
            "bytes": dst.stat().st_size,
        }
        copied_count += 1
        print(f"POST-Backup: {src} -> {sha[:16]}... ({dst.stat().st_size} bytes)")

    manifest_path = backup_dir / "SHA256_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nPOST-Backup complete: {copied_count} files saved to {backup_dir}")
    print(f"Manifest written to: {manifest_path}")

if __name__ == "__main__":
    create_post_backup()
