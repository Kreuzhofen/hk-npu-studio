"""
HK NPU STUDIO – Phoenix Architecture
Sprint 97: Create POST-Backup and SHA-256 Manifest on Drive D:

Backs up all modified and validated files to:
D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_97_HYBRID_SEGMENTATION_REPAIR_20261104\\POST\\
"""

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI")
BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_97_HYBRID_SEGMENTATION_REPAIR_20261104\POST")

FILES_TO_BACKUP = [
    "engine/color_spatial_segmenter.py",
    "engine/phoenix_hybrid_segmenter.py",
    "engine/backends/mobilesam_qnn_adapter.py",
    "controllers/prompt_edit_controller.py",
    "tests/test_phoenix_hybrid_segmenter.py",
    "tools/run_sprint97_hybrid_repair_validation.py",
    "config.py",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    print(f"Creating POST-Backup in {BACKUP_DIR}...")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).decode().strip()
    manifest_lines = []
    manifest_dict = {}

    for rel_path in FILES_TO_BACKUP:
        src = REPO_ROOT / rel_path
        dst = BACKUP_DIR / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src, dst)
        h_src = sha256_file(src)
        h_dst = sha256_file(dst)
        assert h_src == h_dst, f"Checksum mismatch for {rel_path}: {h_src} != {h_dst}"

        manifest_lines.append(f"{h_src}  {rel_path}")
        manifest_dict[rel_path] = {
            "sha256": h_src,
            "size_bytes": src.stat().st_size,
        }
        print(f"  Backed up {rel_path}: {h_src[:16]}... OK")

    # Write manifest
    manifest_path = BACKUP_DIR / "SHA256_MANIFEST.txt"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    # Write metadata
    metadata = {
        "sprint": "SPRINT_97_HYBRID_SEGMENTATION_REPAIR_20261104",
        "stage": "POST",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "git_head": git_head,
        "files_count": len(FILES_TO_BACKUP),
        "files": manifest_dict,
    }
    meta_path = BACKUP_DIR / "BACKUP_METADATA.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\nPOST-Backup successfully created with {len(FILES_TO_BACKUP)} files.")
    print(f"Git HEAD: {git_head}")


if __name__ == "__main__":
    main()
