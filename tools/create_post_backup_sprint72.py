"""
Create post-sprint backup for Sprint 72 (Phoenix Prompt Engine Segmenter Optimization).
Target: D:\\HK_NPU_STUDIO_BACKUPS\\SPRINT_72_SEGMENTER_OPTIMIZATION_20261103\\POST
"""

import hashlib
import json
import shutil
from pathlib import Path

BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_72_SEGMENTER_OPTIMIZATION_20261103\POST")
PROJECT_ROOT = Path(r"C:\SnapdragonAI")

FILES_TO_BACKUP = [
    PROJECT_ROOT / "engine" / "color_spatial_segmenter.py",
    PROJECT_ROOT / "engine" / "prompt_intent_parser.py",
    PROJECT_ROOT / "tests" / "test_prompt_engine_foundation.py",
    PROJECT_ROOT / "tools" / "run_phoenix_prompt_engine_sprint72.py",
    PROJECT_ROOT / "tools" / "profile_sprint71_segmenter.py",
    PROJECT_ROOT / "tools" / "test_optimized_segmenter.py",
    PROJECT_ROOT / "tools" / "create_pre_backup_sprint72.py",
    PROJECT_ROOT / "SPRINT-72-REPORT.md",
    PROJECT_ROOT / "reports" / "sprint_72_segmenter_optimization" / "SPRINT-72-REPORT.md",
    PROJECT_ROOT / "reports" / "sprint_72_segmenter_optimization" / "performance_benchmark.json",
    PROJECT_ROOT / "reports" / "sprint_72_segmenter_optimization" / "mask_quality_metrics.json",
    PROJECT_ROOT / "reports" / "sprint_72_segmenter_optimization" / "test_results.json",
    PROJECT_ROOT / "reports" / "sprint_72_segmenter_optimization" / "root_cause_analysis.json",
]

# Add all generated images
IMG_DIR = PROJECT_ROOT / "reports" / "sprint_72_segmenter_optimization" / "images"
if IMG_DIR.exists():
    for img in sorted(IMG_DIR.glob("*.png")):
        FILES_TO_BACKUP.append(img)


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    print(f"Creating Post-Backup in: {BACKUP_DIR}")
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

    manifest_path = BACKUP_DIR / "post_backup_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "sprint": "SPRINT_72_SEGMENTER_OPTIMIZATION",
                "phase": "POST",
                "total_files": len(FILES_TO_BACKUP),
                "verified_files": verified,
                "all_verified": (verified == len(FILES_TO_BACKUP)),
                "files": manifest,
            },
            f,
            indent=2,
        )

    print(f"\nPost-Backup Complete: {verified}/{len(FILES_TO_BACKUP)} files verified.")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    main()
