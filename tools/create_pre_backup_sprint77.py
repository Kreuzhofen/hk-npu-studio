"""
HK NPU STUDIO – Sprint 77 Pre-Backup Generator
Secures relevant files to D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_77_SEMANTIC_MASK_REPAIR_20261103\\PRE
with SHA-256 verification and manifest.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT_DIR = Path(r"C:\SnapdragonAI")
BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_77_SEMANTIC_MASK_REPAIR_20261103\PRE")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    "engine/color_spatial_segmenter.py",
    "engine/prompt_intent_parser.py",
    "controllers/prompt_edit_controller.py",
    "widgets/phoenix/inpainting_canvas.py",
    "widgets/phoenix/views/inpainting_view.py",
    "engine/material_priming.py",
    "tests/test_prompt_edit_ui.py",
    "tests/test_prompt_edit_controller.py",
    "tests/test_prompt_engine_foundation.py",
    "tests/test_phoenix_inpainting_ui.py",
    "reports/sprint_76_visual_audit/SPRINT-76-REPORT.md",
    "SPRINT-76-REPORT.md",
]


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    manifest = {}
    print(f"Creating Sprint 77 Pre-Backup in: {BACKUP_DIR}")
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

    print(f"\nPre-Backup successfully completed. {len(manifest)} files verified.")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    main()
