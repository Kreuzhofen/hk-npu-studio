"""
Create pre-sprint backup for Sprint 71 (Phoenix Prompt Engine Foundation).
Target: D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_71_ENGINE_FOUNDATION_20261103\\PRE
"""

import hashlib
import json
import shutil
from pathlib import Path

BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_71_ENGINE_FOUNDATION_20261103\PRE")
PROJECT_ROOT = Path(r"C:\SnapdragonAI")

FILES_TO_BACKUP = [
    PROJECT_ROOT / "config.py",
    PROJECT_ROOT / "engine" / "material_priming.py",
    PROJECT_ROOT / "controllers" / "inpainting_controller.py",
    PROJECT_ROOT / "controllers" / "image_to_image_controller.py",
    PROJECT_ROOT / "engine" / "backends" / "sd15_qnn_inpainting_adapter.py",
    PROJECT_ROOT / "engine" / "controlnet_canny_backend.py",
    PROJECT_ROOT / "tests" / "test_phoenix_material_lab_ui.py",
    PROJECT_ROOT / "tests" / "test_phoenix_inpainting_ui.py",
    PROJECT_ROOT / "reports" / "sprint_70_prompt_image_editing" / "SPRINT-70-ARCHITEKTURANALYSE.md",
]


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    print(f"Creating Pre-Backup in: {BACKUP_DIR}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {}
    verified = 0

    for src in FILES_TO_BACKUP:
        if not src.exists():
            print(f"ERROR: Source file does not exist: {src}")
            continue

        rel = src.relative_to(PROJECT_ROOT)
        dst = BACKUP_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src, dst)

        src_hash = sha256_file(src)
        dst_hash = sha256_file(dst)

        if src_hash != dst_hash:
            print(f"FAIL: Hash mismatch for {rel}")
            print(f"  src: {src_hash}")
            print(f"  dst: {dst_hash}")
        else:
            manifest[str(rel)] = {
                "sha256": src_hash,
                "size_bytes": src.stat().st_size,
            }
            verified += 1
            print(f"[OK] {rel} -> {src_hash[:16]}... ({src.stat().st_size:,} bytes)")

    manifest_path = BACKUP_DIR / "pre_backup_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nSuccessfully verified and backed up {verified}/{len(FILES_TO_BACKUP)} files.")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    main()
