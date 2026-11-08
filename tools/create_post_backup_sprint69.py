"""
Create post-sprint backup for Sprint 69 (Final Acceptance).
Target: D:\\HK_NPU_STUDIO_BACKUPS\\PHOENIX_MATERIAL_LAB_69_20261102\\POST
"""

import hashlib
import json
import shutil
from pathlib import Path

BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\PHOENIX_MATERIAL_LAB_69_20261102\POST")
PROJECT_ROOT = Path(r"C:\SnapdragonAI")

FILES_TO_BACKUP = [
    PROJECT_ROOT / "PHOENIX-MATERIAL-LAB-69_REPORT.md",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "clean_profile_test.json",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "end_to_end_workflow.json",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "htp_execution_evidence.json",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "regression_results.json",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_scenario1_standard_result.png",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_scenario1_standard_result.json",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_scenario2_gold_result.png",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_scenario2_gold_result.json",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_scenario3_chrome_result.png",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_scenario3_chrome_result.json",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_workflow_master_grid.png",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_scenario1_standard.png",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_scenario2_gold.png",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_scenario3_chrome.png",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_preview_gold.png",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_preview_chrome.png",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_preview_antique_brass.png",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "e2e_preview_copper.png",
    PROJECT_ROOT / "reports" / "phoenix_material_lab_69" / "gui_light_theme_parity.png",
    PROJECT_ROOT / "tools" / "run_phoenix_material_lab_sprint69.py",
    PROJECT_ROOT / "tools" / "create_pre_backup_sprint69.py",
]


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

    manifest_path = BACKUP_DIR / "post_backup_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nSuccessfully verified and backed up {verified}/{len(FILES_TO_BACKUP)} files.")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    main()
