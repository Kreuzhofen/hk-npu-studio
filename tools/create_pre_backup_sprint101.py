"""
Create PRE-backup for Sprint 101 on Drive D.
"""
import hashlib
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI")
PRE_DIR = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_101_ZERO_SPILLOVER_20261105\PRE")
PRE_DIR.mkdir(parents=True, exist_ok=True)

FILES_TO_BACKUP = [
    "engine/phoenix_hybrid_segmenter.py",
    "engine/color_spatial_segmenter.py",
    "engine/backends/mobilesam_qnn_adapter.py",
    "tests/test_phoenix_hybrid_segmenter.py",
    "GOVERNANCE/CHANGELOG.md",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

manifest = {}

print("=== Creating Sprint 101 PRE-Backup ===")
for rel_path in FILES_TO_BACKUP:
    src = REPO_ROOT / rel_path
    dst = PRE_DIR / rel_path
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

manifest_path = PRE_DIR / "MANIFEST_SHA256_PRE.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

txt_manifest = PRE_DIR / "MANIFEST_SHA256_PRE.txt"
with open(txt_manifest, "w", encoding="utf-8") as f:
    for k, v in manifest.items():
        f.write(f"{v['sha256']}  {k}\n")

print(f"Manifest written: {manifest_path}")
print("PRE-Backup successfully verified on Drive D.")
