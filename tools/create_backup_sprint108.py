#!/usr/bin/env python3
"""
HK NPU STUDIO - SPRINT 108
RC4 Installer Forensics & Comparison - Backup Tool
Target: D:\HK_NPU_STUDIO_BACKUPS\SPRINT_108_INSTALLER_COMPARISON_20261105\
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

BACKUP_ROOT = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_108_INSTALLER_COMPARISON_20261105")
INSTALLERS_BACKUP_DIR = BACKUP_ROOT / "installers"

ORIGINAL_RC4_SOURCE = Path(r"D:\HK_NPU_STUDIO_BACKUPS\RC4_PRE_IMG_EDIT_20261031\dist\installer\HKNPUStudio-2.0.0-rc.4-ARM64-Setup.exe")
SPRINT107_SOURCE = Path(r"C:\SnapdragonAI\dist\installer\HKNPUStudio-2.0.0-rc.4-ARM64-Setup.exe")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    print("=== HK NPU STUDIO SPRINT 108 BACKUP & IDENTIFICATION ===")
    drive_d = Path("D:/")
    if not drive_d.exists():
        print("ERROR: Drive D: is not accessible.")
        return 1

    INSTALLERS_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not ORIGINAL_RC4_SOURCE.exists():
        print(f"ERROR: Original RC4 installer missing at: {ORIGINAL_RC4_SOURCE}")
        return 1

    if not SPRINT107_SOURCE.exists():
        print(f"ERROR: Sprint 107 installer missing at: {SPRINT107_SOURCE}")
        return 1

    print("\n1. Verifying & Backing Up Original RC4 Installer:")
    orig_dst = INSTALLERS_BACKUP_DIR / "HKNPUStudio-2.0.0-rc.4-ARM64-Setup-ORIGINAL.exe"
    if not orig_dst.exists() or orig_dst.stat().st_size != ORIGINAL_RC4_SOURCE.stat().st_size:
        print(f"  Copying {ORIGINAL_RC4_SOURCE.name} to {orig_dst.name}...")
        shutil.copy2(ORIGINAL_RC4_SOURCE, orig_dst)
    orig_sha = sha256_file(orig_dst)
    orig_size = orig_dst.stat().st_size
    print(f"  [OK] Original RC4: {orig_dst.name}")
    print(f"       Size:   {orig_size:,} Bytes ({orig_size / (1024*1024):.2f} MB)")
    print(f"       SHA256: {orig_sha}")

    print("\n2. Verifying & Backing Up Sprint 107 Installer:")
    s107_dst = INSTALLERS_BACKUP_DIR / "HKNPUStudio-2.0.0-rc.4-ARM64-Setup-SPRINT107.exe"
    if not s107_dst.exists() or s107_dst.stat().st_size != SPRINT107_SOURCE.stat().st_size:
        print(f"  Copying {SPRINT107_SOURCE.name} to {s107_dst.name}...")
        shutil.copy2(SPRINT107_SOURCE, s107_dst)
    s107_sha = sha256_file(s107_dst)
    s107_size = s107_dst.stat().st_size
    print(f"  [OK] Sprint 107: {s107_dst.name}")
    print(f"       Size:   {s107_size:,} Bytes ({s107_size / (1024*1024):.2f} MB)")
    print(f"       SHA256: {s107_sha}")

    # Generate Manifest
    manifest = {
        "timestamp": "2026-11-05T21:15:00+01:00",
        "backup_directory": str(BACKUP_ROOT),
        "installers": [
            {
                "identifier": "ORIGINAL_RC4",
                "filename": orig_dst.name,
                "original_path": str(ORIGINAL_RC4_SOURCE),
                "size_bytes": orig_size,
                "size_mb": round(orig_size / (1024 * 1024), 2),
                "sha256": orig_sha,
                "known_sha256_match": orig_sha == "7d1d9b9c566c58cef55f9478a215171351b9cddfe1313c7379f8c11856800f0b"
            },
            {
                "identifier": "SPRINT_107",
                "filename": s107_dst.name,
                "original_path": str(SPRINT107_SOURCE),
                "size_bytes": s107_size,
                "size_mb": round(s107_size / (1024 * 1024), 2),
                "sha256": s107_sha,
                "known_sha256_match": s107_sha == "eb56b374d1f28c6a3b48e020d0244a8d6d5f9593fb8a6187039aa2c229df4cba"
            }
        ]
    }

    manifest_json = BACKUP_ROOT / "SHA256_MANIFEST.json"
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    manifest_txt = BACKUP_ROOT / "SHA256_MANIFEST.txt"
    with open(manifest_txt, "w", encoding="utf-8") as f:
        f.write(f"{orig_sha}  installers/{orig_dst.name}\n")
        f.write(f"{s107_sha}  installers/{s107_dst.name}\n")

    print(f"\nManifest saved to: {manifest_json}")
    print("=== SPRINT 108 BACKUP COMPLETED SUCCESSFULLY ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
