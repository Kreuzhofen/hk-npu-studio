"""
POST-Backup Script for Sprint 94 - MobileSAM HTP Provisioning.
Secures all created implementation files, verification scripts, baseline components,
and validation audits to D:\HK_NPU_STUDIO_BACKUPS\SPRINT_94_MOBILE_SAM_20261104\POST\
and computes complete SHA-256 manifests.
"""

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path("C:/SnapdragonAI")
BACKUP_DIR = Path("D:/HK_NPU_STUDIO_BACKUPS/SPRINT_94_MOBILE_SAM_20261104/POST")

FILES_TO_BACKUP = [
    Path("engine/backends/mobilesam_qnn_adapter.py"),
    Path("tools/provision_sprint94_mobilesam.py"),
    Path("tools/run_sprint94_mobilesam_validation.py"),
    Path("tools/create_pre_backup_sprint94.py"),
    Path("tools/create_post_backup_sprint94.py"),
    Path("engine/backends/sd15_qnn_inpainting_adapter.py"),
    Path("engine/qnn_dlc_runtime_service.py"),
    Path("engine/color_spatial_segmenter.py"),
    Path("controllers/prompt_edit_controller.py"),
    Path("config.py"),
    Path("models/mobilesam_qnn/SHA256_MANIFEST.json"),
    Path("reports/sprint_94_mobilesam_htp/mobilesam_htp_validation_audit.json"),
    Path("reports/sprint_94_mobilesam_htp/images/sprint_94_mobilesam_master_card.png"),
]


def sha256_of_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}

    print(f"=== SPRINT 94: POST-BACKUP TO {BACKUP_DIR} ===")
    for rel_path in FILES_TO_BACKUP:
        src = REPO_ROOT / rel_path
        dst = BACKUP_DIR / rel_path
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            src_sha = sha256_of_file(src)
            dst_sha = sha256_of_file(dst)
            assert src_sha == dst_sha, f"SHA mismatch for {rel_path}!"
            manifest[str(rel_path).replace("\\", "/")] = {
                "sha256": src_sha,
                "size_bytes": src.stat().st_size,
            }
            print(f"  [OK] {rel_path} ({src.stat().st_size} bytes, SHA-256: {src_sha[:12]}...)")
        else:
            print(f"  [MISSING] {rel_path}")

    manifest_txt = BACKUP_DIR / "SHA256_MANIFEST.txt"
    with open(manifest_txt, "w", encoding="utf-8") as f:
        for p, meta in sorted(manifest.items()):
            f.write(f"{meta['sha256']}  {p}\n")

    metadata_json = BACKUP_DIR / "BACKUP_METADATA.json"
    with open(metadata_json, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "sprint": "SPRINT_94_MOBILE_SAM_20261104",
                "phase": "POST",
                "git_head": "8784a43f5b7666f1007292393c6ea947b5cdd788",
                "files_count": len(manifest),
                "manifest": manifest,
            },
            f,
            indent=2,
        )

    print(f"\nPOST-Backup completed: {len(manifest)}/{len(FILES_TO_BACKUP)} files verified bit-identically.")
    print(f"Manifest written to: {manifest_txt}")


if __name__ == "__main__":
    main()
