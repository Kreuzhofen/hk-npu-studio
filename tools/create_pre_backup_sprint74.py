"""
HK NPU STUDIO – Sprint 74 Pre-Backup & SHA-256 Verification Script
Backs up all files that could be affected during Sprint 74 to:
D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_74_PROMPT_EDIT_UI_20261103\\PRE
and computes/verifies SHA-256 hashes before any modifications.

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
BACKUP_DIR = Path("D:/HK_NPU_STUDIO_BACKUPS/SPRINT_74_PROMPT_EDIT_UI_20261103/PRE")

FILES_TO_BACKUP = [
    "widgets/phoenix/views/inpainting_view.py",
    "widgets/phoenix/inpainting_canvas.py",
    "widgets/phoenix/views/image_lab_workspace.py",
    "widgets/phoenix/views/image_lab_view.py",
    "controllers/prompt_edit_controller.py",
    "controllers/inpainting_controller.py",
    "controllers/image_to_image_controller.py",
    "engine/prompt_intent_parser.py",
    "engine/color_spatial_segmenter.py",
    "engine/material_priming.py",
    "locales/de_DE.json",
    "locales/en_US.json",
    "tests/test_phoenix_inpainting_ui.py",
    "tests/test_prompt_edit_controller.py",
]


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    print(f"Creating Pre-Backup directory: {BACKUP_DIR}")
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

    manifest_path = BACKUP_DIR / "pre_backup_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest saved to: {manifest_path}")
    if verified:
        print(f"Pre-Backup SUCCESS: All {len(manifest)} files verified with SHA-256.")
    else:
        print("Pre-Backup FAILED verification!")
        raise RuntimeError("Pre-backup hash verification failed.")


if __name__ == "__main__":
    main()
