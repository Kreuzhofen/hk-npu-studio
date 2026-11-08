#!/usr/bin/env python3
"""
HK NPU STUDIO - SPRINT 108 POST-BACKUP & ARTIFACT SYNCHRONIZATION
Target: D:\HK_NPU_STUDIO_BACKUPS\SPRINT_108_INSTALLER_COMPARISON_20261105\
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI").resolve()
BACKUP_ROOT = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_108_INSTALLER_COMPARISON_20261105")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def fix_changelog_formatting():
    p = REPO_ROOT / "GOVERNANCE" / "CHANGELOG.md"
    text = p.read_text(encoding="utf-8")
    text = text.replace("`tools/run_sprint108_installer_comparison.py und Telemetrie sprint108_forensic_telemetry.json.",
                        "`tools/run_sprint108_installer_comparison.py` und Telemetrie `sprint108_forensic_telemetry.json`.")
    text = text.replace("`reports/sprint_108_installer_comparison/SPRINT_108_FORENSIC_COMPARISON_REPORT.md und Sprint-Bericht SPRINT-108-REPORT.md.",
                        "`reports/sprint_108_installer_comparison/SPRINT_108_FORENSIC_COMPARISON_REPORT.md` und Sprint-Bericht `SPRINT-108-REPORT.md`.")
    p.write_text(text, encoding="utf-8")
    print("CHANGELOG formatted cleanly.")


def main() -> int:
    print("=== HK NPU STUDIO SPRINT 108 POST-BACKUP ===")
    drive_d = Path("D:/")
    if not drive_d.exists():
        print("ERROR: Drive D: is not accessible.")
        return 1

    fix_changelog_formatting()
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    files_to_sync = [
        REPO_ROOT / "tools" / "run_sprint108_installer_comparison.py",
        REPO_ROOT / "tools" / "create_backup_sprint108.py",
        REPO_ROOT / "SPRINT-108-REPORT.md",
        REPO_ROOT / "GOVERNANCE" / "CHANGELOG.md",
        REPO_ROOT / "reports" / "sprint_108_installer_comparison" / "SPRINT_108_FORENSIC_COMPARISON_REPORT.md",
        REPO_ROOT / "reports" / "sprint_108_installer_comparison" / "sprint108_forensic_telemetry.json",
        REPO_ROOT / "reports" / "sprint_108_installer_comparison" / "images" / "card1_installer_footprint_and_payload_delta.png",
        REPO_ROOT / "reports" / "sprint_108_installer_comparison" / "images" / "card2_model_and_qnn_runtime_forensics.png",
        REPO_ROOT / "reports" / "sprint_108_installer_comparison" / "images" / "card3_functional_and_architectural_matrix.png",
        REPO_ROOT / "reports" / "sprint_108_installer_comparison" / "images" / "sprint108_installer_forensics_dashboard.png",
    ]

    manifest = []
    print("\nCopying sprint artifacts to backup directory:")
    for src in files_to_sync:
        if not src.exists():
            print(f"  WARNING: File missing: {src}")
            continue

        rel = src.relative_to(REPO_ROOT)
        dst = BACKUP_ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

        src_hash = sha256_file(src)
        dst_hash = sha256_file(dst)
        if src_hash != dst_hash:
            print(f"  ERROR: Hash mismatch for {rel}!")
            return 2

        print(f"  [OK] {rel} -> {src_hash}")
        manifest.append({
            "relative_path": str(rel).replace("\\", "/"),
            "size_bytes": src.stat().st_size,
            "sha256": src_hash
        })

    # Record the two backed up installers
    installers_dir = BACKUP_ROOT / "installers"
    for inst_name in ("HKNPUStudio-2.0.0-rc.4-ARM64-Setup-ORIGINAL.exe", "HKNPUStudio-2.0.0-rc.4-ARM64-Setup-SPRINT107.exe"):
        inst_path = installers_dir / inst_name
        if inst_path.exists():
            inst_hash = sha256_file(inst_path)
            manifest.append({
                "relative_path": f"installers/{inst_name}",
                "size_bytes": inst_path.stat().st_size,
                "sha256": inst_hash,
                "note": "Forensically audited installer binary"
            })
            print(f"  [RECORDED INSTALLER] {inst_name} -> {inst_hash} ({inst_path.stat().st_size:,} bytes)")

    manifest_json = BACKUP_ROOT / "SHA256_MANIFEST.json"
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    manifest_txt = BACKUP_ROOT / "SHA256_MANIFEST.txt"
    with open(manifest_txt, "w", encoding="utf-8") as f:
        for item in manifest:
            f.write(f"{item['sha256']}  {item['relative_path']}\n")

    print(f"\nManifest saved to:")
    print(f"  {manifest_json}")
    print(f"  {manifest_txt}")
    print("\n=== SPRINT 108 POST-BACKUP VERIFIED AND COMPLETE ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
