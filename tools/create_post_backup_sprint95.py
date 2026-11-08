"""
HK NPU STUDIO – Phoenix Architecture
Sprint 95: Create POST-Backup on Drive D:
Directory: D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_95_HYBRID_SEGMENTATION_20261104\\POST\\
"""

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path("C:/SnapdragonAI").resolve()
BACKUP_ROOT = Path("D:/HK_NPU_STUDIO_BACKUPS/SPRINT_95_HYBRID_SEGMENTATION_20261104/POST").resolve()

FILES_TO_BACKUP = [
    # Core Sprint 95 files
    "engine/phoenix_hybrid_segmenter.py",
    "engine/color_spatial_segmenter.py",
    "engine/prompt_intent_parser.py",
    "engine/backends/mobilesam_qnn_adapter.py",
    "engine/backends/sd15_qnn_inpainting_adapter.py",
    "controllers/prompt_edit_controller.py",
    "widgets/phoenix/inpainting_canvas.py",
    "widgets/phoenix/views/inpainting_view.py",
    "widgets/phoenix/views/image_lab_view.py",
    # Tools and validation
    "tools/create_pre_backup_sprint95.py",
    "tools/create_post_backup_sprint95.py",
    "tools/run_sprint95_hybrid_validation.py",
    # Tests
    "tests/test_phoenix_hybrid_segmenter.py",
    "tests/test_interactive_point_prompting.py",
    # Audit & report & governance
    "reports/sprint_95_hybrid_segmentation/hybrid_segmentation_audit.json",
    "reports/sprint_95_hybrid_segmentation/SPRINT-95-REPORT.md",
    "GOVERNANCE/CHANGELOG.md",
]


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_git_info():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=str(REPO_ROOT), text=True).strip()
    return head, status


def main():
    print("=" * 70)
    print("HK NPU STUDIO – SPRINT 95 POST-BACKUP GENERATION")
    print(f"Target Directory: {BACKUP_ROOT}")
    print("=" * 70)

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    head, status = get_git_info()

    manifest_entries = []
    metadata = {
        "sprint": "SPRINT_95_PHOENIX_HYBRID_SEGMENTATION",
        "backup_type": "POST",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "git_head": head,
        "files": {},
    }

    verified_count = 0

    for rel_path in FILES_TO_BACKUP:
        src = REPO_ROOT / rel_path
        if not src.exists():
            print(f"WARNING: Source file does not exist, skipping: {rel_path}")
            continue

        dst = BACKUP_ROOT / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src, dst)

        src_hash = sha256_file(src)
        dst_hash = sha256_file(dst)

        if src_hash != dst_hash:
            raise RuntimeError(f"Hash mismatch on {rel_path}!\nSrc: {src_hash}\nDst: {dst_hash}")

        manifest_entries.append(f"{dst_hash}  {rel_path}")
        metadata["files"][rel_path] = {
            "sha256": dst_hash,
            "bytes": src.stat().st_size,
        }
        verified_count += 1
        print(f"[OK] {rel_path} -> {dst_hash[:16]}... ({src.stat().st_size} bytes)")

    # Write Manifest
    manifest_file = BACKUP_ROOT / "SHA256_MANIFEST.txt"
    with open(manifest_file, "w", encoding="utf-8") as f:
        f.write("\n".join(manifest_entries) + "\n")

    # Write Metadata
    metadata_file = BACKUP_ROOT / "BACKUP_METADATA.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("-" * 70)
    print(f"POST-Backup verified successfully: {verified_count}/{len(FILES_TO_BACKUP)} files.")
    print(f"Manifest written: {manifest_file}")
    print(f"Metadata written: {metadata_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
