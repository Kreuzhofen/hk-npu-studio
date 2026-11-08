"""
HK NPU STUDIO – Sprint 73 Post-Backup & SHA-256 Verification Script
Backs up all key components, tests, and deliverables to:
D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_73_CONTROLLER_INTEGRATION_20261103\\POST
and computes/verifies SHA-256 hashes.

Created by Senior Software Engineer (Antigravity / Gemini)
Chief Software Architect: ChatGPT
Product Owner: Holger Kreuzhofen
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT_DIR = Path("C:/SnapdragonAI")
BACKUP_DIR = Path("D:/HK_NPU_STUDIO_BACKUPS/SPRINT_73_CONTROLLER_INTEGRATION_20261103/POST")

FILES_TO_BACKUP = [
    "controllers/prompt_edit_controller.py",
    "controllers/inpainting_controller.py",
    "controllers/image_to_image_controller.py",
    "engine/prompt_intent_parser.py",
    "engine/color_spatial_segmenter.py",
    "engine/material_priming.py",
    "tests/test_prompt_edit_controller.py",
    "tests/test_prompt_engine_foundation.py",
    "tools/run_sprint73_htp_validation.py",
    "reports/sprint_73_controller_integration/routing_results.json",
    "reports/sprint_73_controller_integration/pipeline_metrics.json",
    "reports/sprint_73_controller_integration/htp_execution_evidence.json",
    "reports/sprint_73_controller_integration/visual_comparison_grid.png",
    "reports/sprint_73_controller_integration/images/motif1_apple_5_htp_result.png",
    "reports/sprint_73_controller_integration/images/motif2_glass_5_htp_result.png",
    "reports/sprint_73_controller_integration/images/motif3_jacket_5_htp_result.png",
    "reports/sprint_73_controller_integration/images/motif1_apple_card_5col.png",
    "reports/sprint_73_controller_integration/images/motif2_glass_card_5col.png",
    "reports/sprint_73_controller_integration/images/motif3_jacket_card_5col.png",
    "reports/sprint_73_controller_integration/SPRINT-73-REPORT.md",
]


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    print(f"Creating Post-Backup directory: {BACKUP_DIR}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {}
    verified = True

    for rel_str in FILES_TO_BACKUP:
        src = ROOT_DIR / rel_str
        dst = BACKUP_DIR / rel_str

        if not src.exists():
            print(f"ERROR: Source file missing: {src}")
            verified = False
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

        src_hash = sha256_of_file(src)
        dst_hash = sha256_of_file(dst)

        if src_hash != dst_hash:
            print(f"ERROR: Hash mismatch for {rel_str}!")
            verified = False
        else:
            print(f"OK [SHA-256 Verified]: {rel_str} -> {src_hash[:16]}...")

        manifest[rel_str] = {
            "sha256": src_hash,
            "size_bytes": src.stat().st_size,
        }

    manifest_path = BACKUP_DIR / "post_backup_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest saved to: {manifest_path}")
    if verified:
        print(f"Post-Backup SUCCESS: All {len(manifest)} files verified with SHA-256.")
    else:
        print("Post-Backup FAILED verification!")
        raise RuntimeError("Post-backup hash verification failed.")


if __name__ == "__main__":
    main()
