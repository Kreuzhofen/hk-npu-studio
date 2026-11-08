"""Pre-Backup Script for Sprint APP-ACCEPTANCE-56."""
import hashlib
import json
from pathlib import Path
import shutil

REPO_ROOT = Path("C:/SnapdragonAI")
BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\APP_ACCEPTANCE_56_20261102\PRE")

FILES_TO_BACKUP = [
    # Core reference images and reports
    "reports/app_acceptance_54/acceptance54_original.png",
    "reports/app_acceptance_54/acceptance54_mask_overlay.png",
    "reports/app_acceptance_54/acceptance54_mask.png",
    "reports/app_acceptance_54/acceptance54_edited_result.png",
    "reports/app_acceptance_54/acceptance54_comparison_grid.png",
    "reports/app_acceptance_54/acceptance54_metrics.json",
    "APP-ACCEPTANCE-55_REPORT.md",
    "APP_ACCEPTANCE_54_REPORT.md",
    # Core Inpainting & View Components
    "controllers/inpainting_controller.py",
    "widgets/phoenix/inpainting_canvas.py",
    "widgets/phoenix/views/inpainting_view.py",
    "engine/backends/sd15_qnn_inpainting_adapter.py",
    # Drivers and tools
    "tools/run_app_acceptance_sprint54.py",
    "tools/create_pre_backup_sprint55.py",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print(f"Creating Pre-Backup at: {BACKUP_DIR}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {}
    verified_count = 0

    for rel_path_str in FILES_TO_BACKUP:
        src = REPO_ROOT / rel_path_str
        if not src.is_file():
            print(f"[ERROR] Source file missing: {src}")
            return False

        dst = BACKUP_DIR / rel_path_str
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

        src_hash = sha256_file(src)
        dst_hash = sha256_file(dst)

        if src_hash != dst_hash:
            print(f"[MISMATCH] {rel_path_str} src={src_hash} dst={dst_hash}")
            return False

        manifest[rel_path_str] = dst_hash
        verified_count += 1
        print(f"  [OK] {rel_path_str} -> {dst_hash[:16]}...")

    manifest_path = BACKUP_DIR / "PRE_BACKUP_SHA256_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n-------------------------------------------------------------")
    print(f"Pre-Backup Status: SUCCESS")
    print(f"Total Files Backed Up: {verified_count}/{len(FILES_TO_BACKUP)}")
    print(f"SHA-256 Manifest: {manifest_path}")
    print("-------------------------------------------------------------")
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
