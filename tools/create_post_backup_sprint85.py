"""
Create POST Backup for Sprint 85 on Drive D:
Destination: D:\HK_NPU_STUDIO_BACKUPS\SPRINT_85_MATERIAL_POLISH_20261103\POST\
Computes and verifies SHA-256 checksums for all backed up files.
"""

import hashlib
import json
import shutil
from pathlib import Path

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def create_post_backup():
    src_root = Path("C:/SnapdragonAI")
    dst_root = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_85_MATERIAL_POLISH_20261103\POST")
    dst_root.mkdir(parents=True, exist_ok=True)

    files_to_backup = [
        "engine/material_priming.py",
        "controllers/prompt_edit_controller.py",
        "tests/test_prompt_engine_foundation.py",
        "tools/run_sprint85_apple_polish.py",
        "tools/run_sprint85_glass_seed_matrix.py",
        "tools/run_sprint85_full_canonical_validation.py",
        "tools/generate_sprint85_visual_assets.py",
        "reports/sprint_85_material_polish/canonical_validation_evidence.json",
        "reports/sprint_85_material_polish/glass_seed_matrix.json",
        "reports/sprint_85_material_polish/apple_polish_result.json",
        "reports/sprint_85_material_polish/SPRINT-85-REPORT.md",
        "reports/sprint_85_material_polish/images/sprint_85_master_comparison_grid.png",
        "reports/sprint_85_material_polish/images/sprint_85_apple_polish_comparison.png",
        "reports/sprint_85_material_polish/images/sprint_85_glass_polish_comparison.png",
        "reports/sprint_85_material_polish/images/motif1_apple_polished_htp.png",
        "reports/sprint_85_material_polish/images/motif2_glass_polished_htp.png",
        "reports/sprint_85_material_polish/images/motif3_jacket_polished_htp.png",
    ]

    manifest = {}
    verified = True

    print(f"Creating POST Backup at: {dst_root}")
    for rel_path in files_to_backup:
        src_path = src_root / rel_path
        if not src_path.exists():
            print(f"WARNING: File does not exist yet: {src_path}")
            continue

        dst_path = dst_root / rel_path
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)

        src_hash = compute_sha256(src_path)
        dst_hash = compute_sha256(dst_path)

        if src_hash != dst_hash:
            print(f"ERROR: SHA-256 mismatch for {rel_path}!")
            verified = False
        else:
            print(f"OK [VERIFIED]: {rel_path} ({dst_path.stat().st_size} bytes, SHA-256={dst_hash[:12]}...)")

        manifest[rel_path] = {
            "sha256": dst_hash,
            "bytes": dst_path.stat().st_size,
            "verified": src_hash == dst_hash
        }

    manifest_path = dst_root / "SHA256_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest written to {manifest_path}")
    if verified:
        print("ALL POST-BACKUP FILES VERIFIED SUCCESSFULLY!")
    else:
        print("VERIFICATION FAILED FOR SOME FILES!")

if __name__ == "__main__":
    create_post_backup()
