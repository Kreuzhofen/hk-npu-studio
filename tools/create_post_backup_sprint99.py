"""
Create POST-backup for Sprint 99 on Drive D.
"""
import hashlib
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI")
POST_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_99_FINAL_HYBRID_REPAIR_20261104\POST")
POST_DIR.mkdir(parents=True, exist_ok=True)

FILES_TO_BACKUP = [
    "engine/phoenix_hybrid_segmenter.py",
    "engine/color_spatial_segmenter.py",
    "engine/backends/mobilesam_qnn_adapter.py",
    "tests/test_phoenix_hybrid_segmenter.py",
    "tools/run_sprint99_hybrid_repair_validation.py",
    "tools/audit_sprint98_release_acceptance.py",
    "GOVERNANCE/CHANGELOG.md",
    "reports/sprint_99_final_hybrid_repair/sprint99_hybrid_repair_telemetry.json",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

manifest = {}

print("=== Creating Sprint 99 POST-Backup ===")
for rel_path in FILES_TO_BACKUP:
    src = REPO_ROOT / rel_path
    dst = POST_DIR / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        shutil.copy2(src, dst)
        src_sha = sha256_file(src)
        dst_sha = sha256_file(dst)
        assert src_sha == dst_sha, f"SHA-256 mismatch for {rel_path}!"
        manifest[rel_path] = {
            "sha256": src_sha,
            "size_bytes": src.stat().st_size,
        }
        print(f"Backed up: {rel_path} -> {src_sha[:16]}... OK")
    else:
        print(f"File not found: {rel_path}")

manifest_path = POST_DIR / "MANIFEST_SHA256_POST.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

txt_manifest = POST_DIR / "MANIFEST_SHA256_POST.txt"
with open(txt_manifest, "w", encoding="utf-8") as f:
    for k, v in manifest.items():
        f.write(f"{v['sha256']}  {k}\n")

print(f"Manifest written: {manifest_path}")
print("POST-Backup successfully verified on Drive D.")
