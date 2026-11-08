#!/usr/bin/env python3
"""
HK NPU STUDIO - SPRINT 107 POST-BACKUP
Target: D:\HK_NPU_STUDIO_BACKUPS\SPRINT_107_INSTALLER_VALIDATION_20261105\POST\
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI").resolve()
BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_107_INSTALLER_VALIDATION_20261105\POST")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    print("=== HK NPU STUDIO SPRINT 107 POST-BACKUP ===")
    drive_d = Path("D:/")
    if not drive_d.exists():
        print("ERROR: Drive D: is not available.")
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Target Backup Directory: {BACKUP_DIR}")

    files_to_backup = [
        REPO_ROOT / "installer" / "snapdragon_ai_studio.iss",
        REPO_ROOT / "tools" / "build_installer.py",
        REPO_ROOT / "tools" / "audit_sprint107_installer_validation.py",
        REPO_ROOT / "tools" / "create_pre_backup_sprint107.py",
        REPO_ROOT / "tools" / "create_post_backup_sprint107.py",
        REPO_ROOT / "SPRINT-107-REPORT.md",
        REPO_ROOT / "GOVERNANCE" / "CHANGELOG.md",
        REPO_ROOT / "reports" / "sprint_107_installer_validation" / "SPRINT_107_INSTALLER_VALIDATION_REPORT.md",
        REPO_ROOT / "reports" / "sprint_107_installer_validation" / "sprint107_installer_audit_telemetry.json",
        REPO_ROOT / "reports" / "sprint_107_installer_validation" / "sprint107_sha256_manifest.json",
        REPO_ROOT / "reports" / "sprint_107_installer_validation" / "images" / "card1_installer_architecture_and_security.png",
        REPO_ROOT / "reports" / "sprint_107_installer_validation" / "images" / "card2_hardware_preflight_and_driver_binding.png",
        REPO_ROOT / "reports" / "sprint_107_installer_validation" / "images" / "card3_install_upgrade_uninstall_lifecycle.png",
        REPO_ROOT / "reports" / "sprint_107_installer_validation" / "images" / "sprint107_installer_validation_dashboard.png",
    ]

    manifest = []
    print("\nCopying files and calculating SHA-256 hashes:")
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

    # Also record the installer artifact hash
    installer_exe = REPO_ROOT / "dist" / "installer" / "HKNPUStudio-2.0.0-rc.4-ARM64-Setup.exe"
    if installer_exe.exists():
        inst_hash = sha256_file(installer_exe)
        manifest.append({
            "relative_path": "dist/installer/HKNPUStudio-2.0.0-rc.4-ARM64-Setup.exe",
            "size_bytes": installer_exe.stat().st_size,
            "sha256": inst_hash,
            "note": "ARM64 Setup Installer internal build artifact"
        })
        print(f"  [RECORDED ARTIFACT] {installer_exe.name} -> {inst_hash} ({installer_exe.stat().st_size:,} bytes)")

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
    print("\n=== POST-BACKUP VERIFIED AND COMPLETE ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
