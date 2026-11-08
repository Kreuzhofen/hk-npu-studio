"""
Create pre-sprint backup for Sprint 72 (Phoenix Prompt Engine Segmenter Optimization).
Target: D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_72_SEGMENTER_OPTIMIZATION_20261103\\PRE
"""

import hashlib
import json
import shutil
from pathlib import Path

BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_72_SEGMENTER_OPTIMIZATION_20261103\PRE")
PROJECT_ROOT = Path(r"C:\SnapdragonAI")

FILES_TO_BACKUP = [
    PROJECT_ROOT / "config.py",
    PROJECT_ROOT / "engine" / "color_spatial_segmenter.py",
    PROJECT_ROOT / "engine" / "prompt_intent_parser.py",
    PROJECT_ROOT / "engine" / "material_priming.py",
    PROJECT_ROOT / "tests" / "test_prompt_engine_foundation.py",
    PROJECT_ROOT / "tests" / "test_phoenix_material_lab_ui.py",
    PROJECT_ROOT / "SPRINT-71-REPORT.md",
    PROJECT_ROOT / "reports" / "sprint_71_engine_foundation" / "SPRINT-71-REPORT.md",
    PROJECT_ROOT / "reports" / "sprint_71_engine_foundation" / "parser_test_results.json",
    PROJECT_ROOT / "reports" / "sprint_71_engine_foundation" / "segmentation_metrics.json",
    PROJECT_ROOT / "reports" / "sprint_71_engine_foundation" / "runtime_benchmark.json",
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

        if src_hash == dst_hash:
            verified += 1
            status = "VERIFIED"
        else:
            status = "HASH_MISMATCH"

        manifest[str(rel)] = {
            "source": str(src),
            "destination": str(dst),
            "sha256": dst_hash,
            "status": status,
            "size_bytes": dst.stat().st_size,
        }
        print(f"[{status}] {rel} -> {dst_hash[:16]}...")

    manifest_path = BACKUP_DIR / "pre_backup_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "sprint": "SPRINT_72_SEGMENTER_OPTIMIZATION",
                "phase": "PRE",
                "total_files": len(FILES_TO_BACKUP),
                "verified_files": verified,
                "all_verified": (verified == len(FILES_TO_BACKUP)),
                "files": manifest,
            },
            f,
            indent=2,
        )

    print(f"\nPre-Backup Complete: {verified}/{len(FILES_TO_BACKUP)} files verified.")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    main()
