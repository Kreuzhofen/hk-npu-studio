"""
Verify Sprint 87 PRE and POST Backups on Drive D:
Checks every file against SHA256_MANIFEST.json.
"""

import hashlib
import json
from pathlib import Path

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_backup(backup_dir: Path, name: str):
    print(f"\n--- VERIFYING {name} BACKUP: {backup_dir} ---")
    manifest_path = backup_dir / "SHA256_MANIFEST.json"
    if not manifest_path.exists():
        print(f"ERROR: {manifest_path} does not exist!")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    all_ok = True
    for rel_path, entry in manifest.items():
        file_path = backup_dir / rel_path
        if not file_path.exists():
            print(f"FAIL [MISSING]: {file_path}")
            all_ok = False
            continue

        calc_hash = compute_sha256(file_path)
        expected_hash = entry["sha256"]
        actual_size = file_path.stat().st_size
        expected_size = entry["bytes"]

        if calc_hash == expected_hash and actual_size == expected_size:
            print(f"OK [MATCH]: {rel_path} ({actual_size} bytes, SHA-256={calc_hash[:12]}...)")
        else:
            print(f"FAIL [MISMATCH]: {rel_path} - Expected {expected_hash}, got {calc_hash}")
            all_ok = False

    return all_ok

if __name__ == "__main__":
    pre_dir = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_87_FINAL_COLOR_CORRECTION_20261104\PRE")
    post_dir = Path(r"D:\HK_NPU_STUDIO_BACKUPS\SPRINT_87_FINAL_COLOR_CORRECTION_20261104\POST")

    pre_ok = verify_backup(pre_dir, "PRE")
    post_ok = verify_backup(post_dir, "POST")

    print("\n=======================================================")
    print(f"PRE-Backup Verified:  {pre_ok}")
    print(f"POST-Backup Verified: {post_ok}")
    print("=======================================================")
