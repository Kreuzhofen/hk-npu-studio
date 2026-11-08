"""
HK NPU STUDIO – Sprint 74 Post-Backup Generator
Creates post-modification backup on Drive D: with cryptographic SHA-256 manifest.
Location: D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_74_PROMPT_EDIT_UI_20261103\\POST
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT_DIR = Path(r"C:\SnapdragonAI")
BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_74_PROMPT_EDIT_UI_20261103\POST")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    # Modified files
    "widgets/phoenix/inpainting_canvas.py",
    "widgets/phoenix/views/inpainting_view.py",
    "locales/de_DE.json",
    "locales/en_US.json",
    # Newly created files
    "tests/test_prompt_edit_ui.py",
    "tools/run_sprint74_ui_workflow_validation.py",
    "SPRINT-74-REPORT.md",
    "reports/sprint_74_prompt_edit_ui/SPRINT-74-REPORT.md",
    "reports/sprint_74_prompt_edit_ui/ui_test_results.json",
    "reports/sprint_74_prompt_edit_ui/workflow_results.json",
    "reports/sprint_74_prompt_edit_ui/htp_execution_evidence.json",
    "reports/sprint_74_prompt_edit_ui/visual_comparison_grid.png",
    # Pre-existing core components
    "controllers/prompt_edit_controller.py",
    "engine/prompt_intent_parser.py",
    "engine/color_spatial_segmenter.py",
]


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    manifest = {}
    print(f"Creating Sprint 74 Post-Backup in: {BACKUP_DIR}")
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

    print(f"Post-Backup successfully completed. {len(manifest)} files verified.")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    main()
