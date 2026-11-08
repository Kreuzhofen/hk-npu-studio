"""Post-Backup Script for Sprint 63 – Phoenix Material Lab UI-Integration."""
import hashlib
import json
from pathlib import Path
import shutil

REPO_ROOT = Path("C:/SnapdragonAI")
BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\PHOENIX_MATERIAL_LAB_63_20261103\POST")

FILES_TO_BACKUP = [
    # Core Architecture & UI Components Modified
    "controllers/inpainting_controller.py",
    "widgets/phoenix/gallery/inspector.py",
    "widgets/phoenix/views/inpainting_view.py",
    "engine/material_priming.py",
    "engine/backends/sd15_qnn_inpainting_adapter.py",
    # Test Suites
    "tests/test_phoenix_material_lab_ui.py",
    "tests/test_phoenix_inpainting_ui.py",
    # Tools
    "tools/run_phoenix_material_lab_sprint63.py",
    "tools/create_pre_backup_sprint63.py",
    "tools/create_post_backup_sprint63.py",
    # Documentation & Report
    "PHOENIX-MATERIAL-LAB-63_REPORT.md",
    # Deliverables & UI Screenshots
    "reports/phoenix_material_lab_63/acceptance56_original.png",
    "reports/phoenix_material_lab_63/phoenix_material_lab_mask.png",
    "reports/phoenix_material_lab_63/ui_inpainting_material_lab_dark.png",
    "reports/phoenix_material_lab_63/ui_material_lab_popup_dark.png",
    "reports/phoenix_material_lab_63/ui_inpainting_material_lab_light.png",
    "reports/phoenix_material_lab_63/ui_material_lab_popup_light.png",
    "reports/phoenix_material_lab_63/ui_gallery_inspector_material.png",
    "reports/phoenix_material_lab_63/priming_24k_gold.png",
    "reports/phoenix_material_lab_63/phoenix_material_lab_result_gold.png",
    "reports/phoenix_material_lab_63/priming_antique_brass.png",
    "reports/phoenix_material_lab_63/phoenix_material_lab_result_brass.png",
    "reports/phoenix_material_lab_63/priming_copper.png",
    "reports/phoenix_material_lab_63/phoenix_material_lab_result_copper.png",
    "reports/phoenix_material_lab_63/priming_chrome.png",
    "reports/phoenix_material_lab_63/phoenix_material_lab_result_chrome.png",
    "reports/phoenix_material_lab_63/phoenix_material_lab_result_unprimed.png",
    "reports/phoenix_material_lab_63/phoenix_material_lab_63_comparison_grid.png",
    "reports/phoenix_material_lab_63/phoenix_material_lab_63_metrics.json",
    "reports/phoenix_material_lab_63/test_protocol.json",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print(f"Creating Post-Backup for Sprint 63 at: {BACKUP_DIR}")
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

    manifest_path = BACKUP_DIR / "manifest_sha256.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest written to {manifest_path}")
    print(f"Successfully backed up and verified {verified_count}/{len(FILES_TO_BACKUP)} files.")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
