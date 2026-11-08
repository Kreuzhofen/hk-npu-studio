"""Pre-Backup Script for Sprint APP-ACCEPTANCE-51."""
import hashlib
import json
from pathlib import Path
import shutil

REPO_ROOT = Path("C:/SnapdragonAI")
BACKUP_DIR = Path("D:/HK_NPU_STUDIO_BACKUPS/APP_ACCEPTANCE_51_20261102/PRE")

FILES_TO_BACKUP = [
    # Core app entry points
    "gui_v2.py",
    "start_gui.bat",
    "phoenix.py",
    "app/application.py",
    # Core inpainting & gallery & view components
    "widgets/phoenix/views/gallery_view.py",
    "widgets/phoenix/gallery/inspector.py",
    "controllers/gallery_controller.py",
    "controllers/gallery_image_loader.py",
    "controllers/gallery_model.py",
    "widgets/phoenix/views/image_to_image_view.py",
    "controllers/image_to_image_controller.py",
    "widgets/phoenix/views/inpainting_view.py",
    "widgets/phoenix/inpainting_canvas.py",
    "controllers/inpainting_controller.py",
    "widgets/phoenix/views/photo_restore_view.py",
    "controllers/prompt_workspace_controller.py",
    "controllers/generation_controller.py",
    "engine/backends/sd15_qnn_inpainting_adapter.py",
    "engine/backends/sd15_qnn_backend_adapter.py",
    "engine/backends/backend_manager.py",
    # Workspace & Controls
    "widgets/phoenix/views/image_lab_view.py",
    "widgets/phoenix/views/image_lab_workspace.py",
    "widgets/phoenix/workspace.py",
    "widgets/phoenix/controls/button.py",
    "widgets/phoenix/theme.py",
    "config.py",
    "locales/de_DE.json",
    "locales/en_US.json",
    # Tests & Drivers
    "tools/run_app_acceptance_sprint50.py",
    "tools/run_appl_edit_test_49.py",
    "tools/run_app_acceptance_sprint48.py",
    "tests/test_gallery.py",
    "tests/test_gallery_view.py",
    "tests/test_phoenix_image_to_image_ui.py",
    "tests/test_phoenix_image_lab_navigation.py",
    "tests/test_phoenix_inpainting_ui.py",
    "tests/test_cpu_generation_fail_closed.py",
    "tests/test_backend_contract.py",
    # Previous acceptance reports and outputs
    "APP_ACCEPTANCE_50_REPORT.md",
    "APPL_EDIT_TEST_49_REPORT.md",
    "APP_ACCEPTANCE_48_REPORT.md",
    "IMG_EDIT_RC_47_REPORT.md",
    "VIDEO_RESEARCH_48_REPORT.md",
    # Acceptance Source Image
    "acceptance48_text_to_image.png",
    # Sprint 50 images for comparison & root cause analysis
    "reports/app_acceptance_50/acceptance50_original.png",
    "reports/app_acceptance_50/acceptance50_mask.png",
    "reports/app_acceptance_50/acceptance50_golden_apple.png",
    "reports/app_acceptance_50/acceptance50_comparison_grid.png",
    "reports/app_acceptance_50/acceptance50_metrics.json",
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
    print(f"Pre-Backup Status: SUCCESS")
    print(f"Total Files Backed Up: {verified_count}/{len(FILES_TO_BACKUP)}")
    print(f"SHA-256 Manifest: {manifest_path}")
    print("-------------------------------------------------------------")
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
