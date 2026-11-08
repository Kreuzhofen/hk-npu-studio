"""Post-Backup Script for Sprint APP-ACCEPTANCE-57."""
import hashlib
import json
from pathlib import Path
import shutil

REPO_ROOT = Path("C:/SnapdragonAI")
BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\APP_ACCEPTANCE_57_20261102\POST")

FILES_TO_BACKUP = [
    # Sprint 57 Deliverables & Reports
    "reports/app_acceptance_57/acceptance57_original.png",
    "reports/app_acceptance_57/acceptance57_mask.png",
    "reports/app_acceptance_57/acceptance57_mask_overlay.png",
    "reports/app_acceptance_57/acceptance57_result_a_085.png",
    "reports/app_acceptance_57/acceptance57_result_b_095.png",
    "reports/app_acceptance_57/acceptance57_result_c_100.png",
    "reports/app_acceptance_57/acceptance57_comparison_grid.png",
    "reports/app_acceptance_57/acceptance57_metrics.json",
    "APP-ACCEPTANCE-57_REPORT.md",
    # Core Inpainting & View Components
    "controllers/inpainting_controller.py",
    "widgets/phoenix/inpainting_canvas.py",
    "widgets/phoenix/views/inpainting_view.py",
    "engine/backends/sd15_qnn_inpainting_adapter.py",
    # Sprint 57 driver scripts
    "tools/run_app_acceptance_sprint57.py",
    "tools/create_pre_backup_sprint57.py",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print(f"Creating Post-Backup at: {BACKUP_DIR}")
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

    manifest_path = BACKUP_DIR / "POST_BACKUP_SHA256_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n-------------------------------------------------------------")
    print(f"Post-Backup Status: SUCCESS")
    print(f"Total Files Backed Up: {verified_count}/{len(FILES_TO_BACKUP)}")
    print(f"SHA-256 Manifest: {manifest_path}")
    print("-------------------------------------------------------------")
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
