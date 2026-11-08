"""
HK NPU STUDIO 2.1.0 – Phoenix Evolution
PRE-Backup Tool for Sprint: PHOENIX_EVOLUTION_2_1_0_20261107
Target: D:\\HK_NPU_STUDIO_BACKUPS\\PHOENIX_EVOLUTION_2_1_0_20261107\\PRE\\
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI")
PRE_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\PHOENIX_EVOLUTION_2_1_0_20261107\PRE")
PRE_DIR.mkdir(parents=True, exist_ok=True)

FILES_TO_BACKUP = [
    "release.json",
    "engine/release_config.py",
    "engine/brand_manager.py",
    "version.py",
    "config.py",
    "widgets/phoenix/header.py",
    "build/release/version_info.txt",
    "installer/snapdragon_ai_studio.iss",
    "app/application.py",
    "GOVERNANCE/CHANGELOG.md",
    "tests/test_release_configuration.py",
    "HK_NPU_STUDIO.spec",
    "tools/build_installer.py",
    "tools/validate_release_artifacts.py",
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    print("=== Creating HK NPU STUDIO 2.1.0 PRE-Backup ===")
    manifest = {}

    for rel_path in FILES_TO_BACKUP:
        src = REPO_ROOT / rel_path
        dst = PRE_DIR / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not src.exists():
            print(f"ERROR: Source file missing: {src}")
            return 1
        shutil.copy2(src, dst)
        src_sha = sha256_file(src)
        dst_sha = sha256_file(dst)
        if src_sha != dst_sha:
            print(f"ERROR: SHA-256 mismatch for {rel_path}!")
            return 1
        manifest[rel_path] = {
            "sha256": src_sha,
            "size_bytes": src.stat().st_size,
        }
        print(f"Backed up: {rel_path} -> {src_sha[:16]}... OK")

    manifest_json = PRE_DIR / "SHA256_MANIFEST.json"
    manifest_json.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    manifest_txt = PRE_DIR / "SHA256_MANIFEST.txt"
    with open(manifest_txt, "w", encoding="utf-8") as f:
        for k, v in manifest.items():
            f.write(f"{v['sha256']}  {k}\n")

    print(f"\nManifest JSON: {manifest_json}")
    print(f"Manifest TXT:  {manifest_txt}")
    print(f"Total files backed up: {len(manifest)}")
    print("PRE-Backup successfully completed and verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
