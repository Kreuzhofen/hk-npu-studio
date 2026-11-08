"""
Sprint 82 PRE-Backup Tool
Secures the files to be modified in Sprint 82 to Drive D: with verified SHA-256 manifest.
Target: D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_82_MATERIAL_REPAIR_20261103\\PRE
"""

import hashlib
import json
import shutil
from pathlib import Path

def create_pre_backup():
    backup_dir = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_82_MATERIAL_REPAIR_20261103\PRE")
    backup_dir.mkdir(parents=True, exist_ok=True)

    files_to_backup = [
        Path("engine/color_spatial_segmenter.py"),
        Path("engine/material_priming.py"),
        Path("controllers/prompt_edit_controller.py"),
        Path("tests/test_prompt_engine_foundation.py"),
        Path("tests/test_prompt_edit_controller.py"),
        Path("tests/test_prompt_edit_ui.py"),
    ]

    manifest = {}
    for src in files_to_backup:
        if not src.exists():
            raise FileNotFoundError(f"Missing required source file for backup: {src}")
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
        print(f"PRE-Backup: {src} -> {sha[:16]}... ({dst.stat().st_size} bytes)")

    manifest_path = backup_dir / "SHA256_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nPRE-Backup successfully created at: {backup_dir}")
    print(f"Manifest written to: {manifest_path}")

if __name__ == "__main__":
    create_pre_backup()
