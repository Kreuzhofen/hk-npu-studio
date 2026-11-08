"""Pre-Backup Script for Sprint 66 – Phoenix Material Lab: Reproduzierbarkeits- und Qualitätsaudit."""
import hashlib
import json
from pathlib import Path
import shutil

REPO_ROOT = Path("C:/SnapdragonAI")
BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\PHOENIX_MATERIAL_LAB_66_20261102\PRE")

FILES_TO_BACKUP = [
    # Core Architecture & UI Components (Read-Only)
    "engine/material_priming.py",
    "controllers/inpainting_controller.py",
    "widgets/phoenix/views/inpainting_view.py",
    "widgets/phoenix/gallery/inspector.py",
    "widgets/phoenix/inpainting_canvas.py",
    "engine/backends/sd15_qnn_inpainting_adapter.py",
    # Test Suites & Scripts
    "tests/test_phoenix_material_lab_ui.py",
    "tools/run_phoenix_material_lab_sprint65.py",
    # Sprint 65 Deliverables & Inputs to be audited
    "PHOENIX-MATERIAL-LAB-65_REPORT.md",
    "reports/phoenix_material_lab_65/motives_manifest.json",
    "reports/phoenix_material_lab_65/m1_glass_original.png",
    "reports/phoenix_material_lab_65/m1_glass_mask.png",
    "reports/phoenix_material_lab_65/m1_glass_mask_overlay.png",
    "reports/phoenix_material_lab_65/m3_metal_original.png",
    "reports/phoenix_material_lab_65/m3_metal_mask.png",
    "reports/phoenix_material_lab_65/m3_metal_mask_overlay.png",
    "reports/phoenix_material_lab_65/phoenix_material_lab_65_master_grid.png",
    "reports/phoenix_material_lab_65/phoenix_material_lab_65_chrome_grid.png",
    "reports/phoenix_material_lab_65/phoenix_material_lab_65_metrics.json",
    "reports/phoenix_material_lab_65/test_protocol.json",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print(f"Creating Pre-Backup for Sprint 66 at: {BACKUP_DIR}")
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
