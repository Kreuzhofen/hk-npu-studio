"""Pre-Backup Script for Sprint IMG-EDIT-RC-47."""
import hashlib
import json
from pathlib import Path
import shutil

REPO_ROOT = Path("C:/SnapdragonAI")
BACKUP_DIR = Path("D:/HK_NPU_STUDIO_BACKUPS/IMG_EDIT_RC_47_20261101/PRE")

FILES_TO_BACKUP = [
    # Gallery & Inspector
    "widgets/phoenix/views/gallery_view.py",
    "widgets/phoenix/gallery/inspector.py",
    "controllers/gallery_controller.py",
    "controllers/gallery_image_loader.py",
    "controllers/gallery_model.py",
    # Image-to-Image & Inpainting
    "widgets/phoenix/views/image_to_image_view.py",
    "controllers/image_to_image_controller.py",
    "widgets/phoenix/views/inpainting_view.py",
    "widgets/phoenix/inpainting_canvas.py",
    "controllers/inpainting_controller.py",
    "widgets/phoenix/views/photo_restore_view.py",
    "engine/backends/sd15_qnn_inpainting_adapter.py",
    # Workspace & Controls
    "widgets/phoenix/views/image_lab_view.py",
    "widgets/phoenix/views/image_lab_workspace.py",
    "widgets/phoenix/workspace.py",
    "widgets/phoenix/controls/button.py",
    "widgets/phoenix/theme.py",
    "config.py",
    "locales/de_DE.json",
    "locales/en_US.json",
    # Tests
    "tests/test_gallery.py",
    "tests/test_gallery_view.py",
    "tests/test_phoenix_image_to_image_ui.py",
    "tests/test_phoenix_image_lab_navigation.py",
    "tests/test_phoenix_inpainting_ui.py",
    # Previous verification tool & report
    "tools/verify_gallery_workflow_sprint46.py",
    "IMG_EDIT_UX_46_REPORT.md",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print(f"Creating Pre-Backup at: {BACKUP_DIR}")
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

    manifest_path = BACKUP_DIR / "PRE_BACKUP_SHA256_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n-------------------------------------------------------------")
    print(f"Pre-Backup complete: {verified_count}/{len(FILES_TO_BACKUP)} files verified.")
    print(f"Manifest written to: {manifest_path}")
    print("-------------------------------------------------------------")
    return True

if __name__ == "__main__":
    if not main():
        exit(1)
