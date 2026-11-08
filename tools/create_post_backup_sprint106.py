"""
HK NPU STUDIO - SPRINT 106
Create POST-Backup on Drive D: with SHA-256 Manifest Verification.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI")
POST_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_106_STANDALONE_VALIDATION_20261105\POST")
POST_DIR.mkdir(parents=True, exist_ok=True)

FILES_TO_BACKUP = [
    "config.py",
    "launcher.py",
    "phoenix.py",
    "version.py",
    "release.json",
    "requirements.txt",
    "requirements-qnn.txt",
    "requirements-qai.txt",
    "gui_v2.py",
    "HK_NPU_STUDIO.spec",
    "rthook_backports.py",
    "engine/backends/mobilesam_qnn_adapter.py",
    "engine/onnx_provider_service.py",
    "engine/phoenix_hybrid_segmenter.py",
    "engine/backends/sd15_qnn_inpainting_adapter.py",
    "controllers/prompt_edit_controller.py",
    "controllers/inpainting_controller.py",
    "tools/create_pre_backup_sprint106.py",
    "tools/audit_sprint106_standalone_validation.py",
    "SPRINT-106-REPORT.md",
    "GOVERNANCE/CHANGELOG.md",
    "reports/sprint_106_standalone_validation/sprint106_standalone_telemetry.json",
    "reports/sprint_106_standalone_validation/SPRINT-106-REPORT.md",
    "reports/sprint_106_standalone_validation/images/sprint_106_area1_discrepancy_forensics.png",
    "reports/sprint_106_standalone_validation/images/sprint_106_area2_spec_and_assets.png",
    "reports/sprint_106_standalone_validation/images/sprint_106_area3_clean_pc_validation.png",
    "reports/sprint_106_standalone_validation/images/sprint_106_master_validation_dashboard.png",
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("=== Creating Sprint 106 POST-Backup on Drive D: ===")
    manifest = {}

    for rel_path in FILES_TO_BACKUP:
        src = REPO_ROOT / rel_path
        dst = POST_DIR / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dst)
            src_sha = sha256_file(src)
            dst_sha = sha256_file(dst)
            assert src_sha == dst_sha, f"SHA-256 mismatch for {rel_path}!"
            manifest[rel_path.replace("/", "\\")] = {
                "sha256": src_sha,
                "size_bytes": src.stat().st_size,
            }
            print(f"Backed up: {rel_path} -> {src_sha[:16]}... OK ({src.stat().st_size:,} bytes)")
        else:
            print(f"Warning: File not found: {rel_path}")

    # Write JSON manifest
    manifest_json = POST_DIR / "MANIFEST_SHA256_POST.json"
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Write text manifest
    manifest_txt = POST_DIR / "MANIFEST_SHA256_POST.txt"
    with open(manifest_txt, "w", encoding="utf-8") as f:
        for k, v in manifest.items():
            f.write(f"{v['sha256']}  {k}\n")

    print(f"\nManifests written to:\n  {manifest_json}\n  {manifest_txt}")
    print(f"Total files backed up: {len(manifest)}")
    print("POST-Backup verified successfully on Drive D.")


if __name__ == "__main__":
    main()
