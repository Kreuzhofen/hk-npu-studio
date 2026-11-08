"""
Sprint 85 PRE-Backup Script:
Backs up relevant source and test files to D:\HK_NPU_STUDIO_BACKUPS\SPRINT_85_MATERIAL_POLISH_20261103\PRE\
and verifies SHA-256 hashes.
"""

import hashlib
import json
import shutil
from pathlib import Path

FILES_TO_BACKUP = [
    "engine/material_priming.py",
    "controllers/prompt_edit_controller.py",
    "engine/color_spatial_segmenter.py",
    "engine/prompt_intent_parser.py",
    "tests/test_prompt_engine_foundation.py",
    "tests/test_prompt_edit_controller.py",
    "tests/test_prompt_edit_ui.py",
    "reports/sprint_84_material_artifact_audit/SPRINT-84-REPORT.md",
]

def create_pre_backup():
    base_dir = Path("C:/SnapdragonAI")
    dest_dir = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_85_MATERIAL_POLISH_20261103\PRE")
    dest_dir.mkdir(parents=True, exist_ok=True)

    manifest = {}

    print(f"Creating SPRINT 85 PRE-Backup at: {dest_dir}")
    for rel_path in FILES_TO_BACKUP:
        src = base_dir / rel_path
        if not src.exists():
            print(f"WARNING: File not found: {src}")
            continue
        
        dst = dest_dir / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

        data = dst.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        manifest[rel_path] = {
            "sha256": sha256,
            "bytes": len(data)
        }
        print(f"  Backed up: {rel_path} ({len(data)} bytes, sha256={sha256[:12]}...)")

    manifest_path = dest_dir / "SHA256_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest written to: {manifest_path}")

    # Verify manifest
    verified = 0
    for rel_path, meta in manifest.items():
        dst_file = dest_dir / rel_path
        actual_hash = hashlib.sha256(dst_file.read_bytes()).hexdigest()
        if actual_hash == meta["sha256"]:
            verified += 1
        else:
            print(f"ERROR: Hash mismatch on {rel_path}")

    print(f"Verification complete: {verified}/{len(manifest)} files verified on Drive D:.")

if __name__ == "__main__":
    create_pre_backup()
