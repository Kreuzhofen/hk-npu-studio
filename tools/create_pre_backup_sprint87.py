"""
Create PRE Backup for Sprint 87 on Drive D:
Destination: D:\HK_NPU_STUDIO_BACKUPS\SPRINT_87_FINAL_COLOR_CORRECTION_20261104\PRE\
Computes and verifies SHA-256 checksums for all backed up files.
"""

import hashlib
import json
import shutil
from pathlib import Path

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def create_pre_backup():
    src_root = Path("C:/SnapdragonAI")
    dst_root = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_87_FINAL_COLOR_CORRECTION_20261104\PRE")
    dst_root.mkdir(parents=True, exist_ok=True)

    files_to_backup = [
        "engine/material_priming.py",
        "controllers/prompt_edit_controller.py",
        "engine/color_spatial_segmenter.py",
        "engine/prompt_intent_parser.py",
        "tests/test_prompt_engine_foundation.py",
        "tests/test_prompt_edit_controller.py",
        "tests/test_prompt_edit_ui.py",
        "reports/sprint_86_visual_release_acceptance/SPRINT-86-REPORT.md",
        "reports/sprint_86_visual_release_acceptance/release_acceptance_metrics.json",
    ]

    manifest = {}
    verified = True

    print(f"Creating PRE Backup at: {dst_root}")
    for rel_path in files_to_backup:
        src_path = src_root / rel_path
        if not src_path.exists():
            print(f"ERROR: Target file does not exist: {src_path}")
            verified = False
            continue

        dst_path = dst_root / rel_path
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)

        src_hash = compute_sha256(src_path)
        dst_hash = compute_sha256(dst_path)

        if src_hash != dst_hash:
            print(f"ERROR: SHA-256 mismatch for {rel_path}!")
            verified = False
        else:
            print(f"OK [VERIFIED]: {rel_path} ({dst_path.stat().st_size} bytes, SHA-256={dst_hash[:12]}...)")

        manifest[rel_path] = {
            "sha256": dst_hash,
            "bytes": dst_path.stat().st_size,
            "verified": src_hash == dst_hash
        }

    manifest_path = dst_root / "SHA256_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest written to {manifest_path}")
    if verified and len(manifest) == len(files_to_backup):
        print("ALL PRE-BACKUP FILES VERIFIED SUCCESSFULLY!")
    else:
        print("PRE-BACKUP VERIFICATION FAILED!")
        raise RuntimeError("Pre-backup verification failed. Hard stop.")

if __name__ == "__main__":
    create_pre_backup()
