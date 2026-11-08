"""
HK NPU STUDIO – Sprint 80 Post-Backup Generator
Secures all modified code, test suites, reports, audit files, and visual evidence to:
D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_80_TOTAL_VALIDATION_20261103\\POST
with SHA-256 verification and manifest.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT_DIR = Path(r"C:\SnapdragonAI")
BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_80_TOTAL_VALIDATION_20261103\POST")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    # Engine & Controller
    "engine/color_spatial_segmenter.py",
    "controllers/prompt_edit_controller.py",
    "engine/prompt_intent_parser.py",
    "engine/material_priming.py",
    "engine/backends/sd15_qnn_inpainting_adapter.py",
    # Verification & Regression Tests
    "tests/test_prompt_engine_foundation.py",
    "tests/test_prompt_edit_controller.py",
    "tests/test_prompt_edit_ui.py",
    # Tools
    "tools/create_pre_backup_sprint80.py",
    "tools/run_sprint80_total_validation.py",
    "tools/create_post_backup_sprint80.py",
    # Reports & JSON Evidence
    "reports/sprint_80_total_validation/SPRINT-80-REPORT.md",
    "SPRINT-80-REPORT.md",
    "reports/sprint_80_total_validation/mask_quality_audit.json",
    "reports/sprint_80_total_validation/workflow_results.json",
    "reports/sprint_80_total_validation/htp_execution_evidence.json",
    "reports/sprint_80_total_validation/test_protocol.json",
    "reports/sprint_80_total_validation/visual_comparison_grid.png",
    # Motif 1 (Apple) Component Images & Card
    "reports/sprint_80_total_validation/images/motif1_apple_1_original.png",
    "reports/sprint_80_total_validation/images/motif1_apple_2_mask_overlay.png",
    "reports/sprint_80_total_validation/images/motif1_apple_3_binary_mask.png",
    "reports/sprint_80_total_validation/images/motif1_apple_4_primed_preview.png",
    "reports/sprint_80_total_validation/images/motif1_apple_5_htp_result.png",
    "reports/sprint_80_total_validation/images/motif1_apple_card_5col.png",
    # Motif 2 (Glass Sculpture) Component Images & Card
    "reports/sprint_80_total_validation/images/motif2_glass_1_original.png",
    "reports/sprint_80_total_validation/images/motif2_glass_2_mask_overlay.png",
    "reports/sprint_80_total_validation/images/motif2_glass_3_binary_mask.png",
    "reports/sprint_80_total_validation/images/motif2_glass_4_primed_preview.png",
    "reports/sprint_80_total_validation/images/motif2_glass_5_htp_result.png",
    "reports/sprint_80_total_validation/images/motif2_glass_card_5col.png",
    # Motif 3 (Jacket) Component Images & Card
    "reports/sprint_80_total_validation/images/motif3_jacket_1_original.png",
    "reports/sprint_80_total_validation/images/motif3_jacket_2_mask_overlay.png",
    "reports/sprint_80_total_validation/images/motif3_jacket_3_binary_mask.png",
    "reports/sprint_80_total_validation/images/motif3_jacket_4_primed_preview.png",
    "reports/sprint_80_total_validation/images/motif3_jacket_5_htp_result.png",
    "reports/sprint_80_total_validation/images/motif3_jacket_card_5col.png",
]


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    manifest = {}
    print(f"Creating Sprint 80 Post-Backup in: {BACKUP_DIR}")
    for rel_path in FILES:
        src = ROOT_DIR / rel_path
        if not src.is_file():
            print(f"WARNING: File not found: {src}")
            continue
        dst = BACKUP_DIR / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        src_hash = sha256_of_file(src)
        dst_hash = sha256_of_file(dst)
        assert src_hash == dst_hash, f"Hash mismatch for {rel_path}"
        manifest[rel_path] = {
            "size_bytes": src.stat().st_size,
            "sha256": src_hash,
            "verified": True,
        }
        print(f"  [OK] {rel_path} -> {src_hash[:16]}... ({src.stat().st_size} bytes)")

    manifest_path = BACKUP_DIR / "SHA256_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nPost-Backup successfully completed. {len(manifest)} files verified.")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    main()
