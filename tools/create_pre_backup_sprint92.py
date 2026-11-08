"""
HK NPU STUDIO – Sprint 92: Interactive Point-Prompting
Tool: Create PRE-Backup on Drive D: with SHA-256 verification.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import time

REPO_ROOT = Path(r"C:\SnapdragonAI")
PRE_BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_92_POINT_PROMPTING_20261104\PRE")

TARGET_FILES = [
    "engine/color_spatial_segmenter.py",
    "controllers/prompt_edit_controller.py",
    "widgets/phoenix/inpainting_canvas.py",
    "widgets/phoenix/views/inpainting_view.py",
    "locales/de_DE.json",
    "locales/en_US.json",
]


def sha256_of_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    print(f"=== SPRINT 92: PRE-BACKUP TO {PRE_BACKUP_DIR} ===")
    PRE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    manifest_lines = []
    metadata = {
        "sprint": "SPRINT_92_POINT_PROMPTING",
        "phase": "PRE",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "git_head": "8784a43f5b7666f1007292393c6ea947b5cdd788",
        "files": {},
    }

    verified_count = 0

    for rel_path in TARGET_FILES:
        src = REPO_ROOT / rel_path
        if not src.is_file():
            raise FileNotFoundError(f"Source file not found: {src}")

        src_hash = sha256_of_file(src)
        dst = PRE_BACKUP_DIR / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

        dst_hash = sha256_of_file(dst)
        if src_hash != dst_hash:
            raise ValueError(f"Hash mismatch for {rel_path}!\nSRC: {src_hash}\nDST: {dst_hash}")

        manifest_lines.append(f"{src_hash}  {rel_path}")
        metadata["files"][rel_path] = {
            "sha256": src_hash,
            "bytes": src.stat().st_size,
        }
        verified_count += 1
        print(f"  [OK] {rel_path} ({src.stat().st_size} bytes, SHA-256: {src_hash[:12]}...)")

    manifest_path = PRE_BACKUP_DIR / "SHA256_MANIFEST.txt"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    meta_path = PRE_BACKUP_DIR / "BACKUP_METADATA.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\nPRE-Backup completed: {verified_count}/{len(TARGET_FILES)} files verified bit-identically.")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    main()
