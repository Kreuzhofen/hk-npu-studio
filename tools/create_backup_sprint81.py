"""
Sprint 81 Backup Script
Saves Sprint 81 report, tools, diagnostics, and images to Drive D: with verified SHA-256 manifest.
"""

import hashlib
import json
import shutil
from pathlib import Path

def run_backup():
    backup_root = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_81_MATERIAL_QUALITY_20261103")
    backup_root.mkdir(parents=True, exist_ok=True)

    files_to_backup = [
        Path("reports/sprint_81_material_quality/SPRINT-81-REPORT.md"),
        Path("reports/sprint_81_material_quality/images/apple_dent_analysis.png"),
        Path("reports/sprint_81_material_quality/images/glass_pedestal_analysis.png"),
        Path("reports/sprint_81_material_quality/images/motif3_jacket_regression_5col.png"),
        Path("tools/analyze_sprint81_material_quality.py"),
        Path("tools/generate_sprint81_visual_assets.py"),
        Path("tools/create_backup_sprint81.py"),
        Path("scratch/diag_apple/apple_seed43.png"),
    ]

    manifest = {}
    copied_count = 0

    for src in files_to_backup:
        if src.exists():
            rel = src
            dst = backup_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

            h = hashlib.sha256()
            with open(dst, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            sha = h.hexdigest()
            manifest[str(rel).replace("\\", "/")] = {
                "sha256": sha,
                "bytes": dst.stat().st_size,
            }
            copied_count += 1
            print(f"Backed up: {rel} ({sha[:16]}...)")

    manifest_path = backup_root / "SHA256_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nBackup complete: {copied_count} files saved to {backup_root}")
    print(f"Manifest written to: {manifest_path}")

if __name__ == "__main__":
    run_backup()
