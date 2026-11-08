#!/usr/bin/env python3
"""
HK NPU STUDIO - RC4 STARTUP FIX POST-BACKUP
Target: D:\\HK_NPU_STUDIO_BACKUPS\\RC4_STARTUP_FIX_20261107\\POST\\
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI").resolve()
BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\RC4_STARTUP_FIX_20261107\POST")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    print("=== HK NPU STUDIO RC4 STARTUP FIX POST-BACKUP ===")
    drive_d = Path("D:/")
    if not drive_d.exists():
        print("ERROR: Drive D: is not available.")
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Target Backup Directory: {BACKUP_DIR}")

    files_to_backup = [
        REPO_ROOT / "gui_v2.py",
        REPO_ROOT / "tools" / "patch_sprint106_files.py",
        REPO_ROOT / "engine" / "startup_diagnostics.py",
        REPO_ROOT / "tests" / "test_frozen_qnn_worker_fix.py",
        REPO_ROOT / "tools" / "create_pre_backup_rc4_fix.py",
    ]

    manifest = []
    print("\nCopying modified and verified files and calculating SHA-256 hashes:")
    for src in files_to_backup:
        if not src.exists():
            print(f"  WARNING: File missing: {src}")
            continue

        rel_path = src.relative_to(REPO_ROOT)
        dst = BACKUP_DIR / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

        src_hash = sha256_file(src)
        dst_hash = sha256_file(dst)

        if src_hash != dst_hash:
            print(f"  ERROR: Hash mismatch for {rel_path}!")
            return 2

        print(f"  [OK] {rel_path} -> {src_hash}")
        manifest.append({
            "relative_path": str(rel_path).replace("\\", "/"),
            "size_bytes": src.stat().st_size,
            "sha256": src_hash
        })

    # Save manifest files
    manifest_json = BACKUP_DIR / "SHA256_MANIFEST.json"
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    manifest_txt = BACKUP_DIR / "SHA256_MANIFEST.txt"
    with open(manifest_txt, "w", encoding="utf-8") as f:
        for item in manifest:
            f.write(f"{item['sha256']}  {item['relative_path']}\n")

    print(f"\nManifest saved to:")
    print(f"  {manifest_json}")
    print(f"  {manifest_txt}")
    print("\nPOST-BACKUP COMPLETED AND VERIFIED SUCCESSFULLY.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
