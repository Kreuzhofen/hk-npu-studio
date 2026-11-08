"""Post-Backup Script for Sprint 66 – Phoenix Material Lab: Reproduzierbarkeits- und Qualitätsaudit."""
import hashlib
import json
from pathlib import Path
import shutil

REPO_ROOT = Path("C:/SnapdragonAI")
BACKUP_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\PHOENIX_MATERIAL_LAB_66_20261102\POST")

FILES_TO_BACKUP = [
    # Tools
    "tools/create_pre_backup_sprint66.py",
    "tools/create_post_backup_sprint66.py",
    "tools/run_phoenix_material_lab_sprint66.py",
    # Deliverables & Reports
    "PHOENIX-MATERIAL-LAB-66_REPORT.md",
    "reports/phoenix_material_lab_66/quality_comparison_grid.png",
    "reports/phoenix_material_lab_66/reproducibility_metrics.json",
    "reports/phoenix_material_lab_66/chrom_causality_analysis.md",
    "reports/phoenix_material_lab_66/test_protocol.json",
    # Causality Experiment Artifacts
    "reports/phoenix_material_lab_66/causality_m1_desat_context_input.png",
    "reports/phoenix_material_lab_66/causality_m1_desat_chrome_htp.png",
    "reports/phoenix_material_lab_66/causality_m1_desat_chrome_htp.json",
    "reports/phoenix_material_lab_66/causality_m3_tinted_context_input.png",
    "reports/phoenix_material_lab_66/causality_m3_tinted_chrome_htp.png",
    "reports/phoenix_material_lab_66/causality_m3_tinted_chrome_htp.json",
    # Reproducibility HTP Images (sample selection)
    "reports/phoenix_material_lab_66/repro_htp_m1_glass_24k_gold.png",
    "reports/phoenix_material_lab_66/repro_htp_m1_glass_antique_brass.png",
    "reports/phoenix_material_lab_66/repro_htp_m1_glass_copper.png",
    "reports/phoenix_material_lab_66/repro_htp_m1_glass_chrome.png",
    "reports/phoenix_material_lab_66/repro_htp_m3_metal_24k_gold.png",
    "reports/phoenix_material_lab_66/repro_htp_m3_metal_antique_brass.png",
    "reports/phoenix_material_lab_66/repro_htp_m3_metal_copper.png",
    "reports/phoenix_material_lab_66/repro_htp_m3_metal_chrome.png",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print(f"Creating Post-Backup for Sprint 66 at: {BACKUP_DIR}")
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
