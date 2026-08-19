from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

def migrate_legacy_generations() -> None:
    """Migrate legacy generations from the old output folder to the new canonical OUTPUT_DIR.
    Does not delete source files, does not overwrite target files, and is idempotent.
    """
    if not getattr(sys, "frozen", False):
        return

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return
        
    legacy_dir = Path(local_app_data) / "Programs" / "Snapdragon AI Studio" / "output"
    if not legacy_dir.is_dir():
        return
        
    from config import OUTPUT_DIR
    target_dir = Path(OUTPUT_DIR)
    
    try:
        if target_dir.resolve() == legacy_dir.resolve():
            return
    except OSError:
        pass
        
    try:
        files = list(legacy_dir.iterdir())
    except OSError:
        return
        
    if not files:
        return
        
    target_dir.mkdir(parents=True, exist_ok=True)
    
    supported_image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
    
    for path in files:
        if not path.is_file():
            continue
            
        suffix = path.suffix.lower()
        if suffix == ".png":
            _safe_copy_with_sidecar(path, target_dir)
        elif suffix in supported_image_extensions:
            has_sidecar = path.with_suffix(".json").is_file()
            starts_with_generate = path.name.startswith("generate")
            if has_sidecar or starts_with_generate:
                _safe_copy_with_sidecar(path, target_dir)

def _safe_copy_with_sidecar(source_image_path: Path, target_dir: Path) -> None:
    try:
        target_image_path = target_dir / source_image_path.name
        source_json_path = source_image_path.with_suffix(".json")
        target_json_path = target_image_path.with_suffix(".json")
        
        # If target image does not exist, copy it
        if not target_image_path.exists():
            shutil.copy2(source_image_path, target_image_path)
            
        # If source has a json sidecar and target json does not exist, copy it
        if source_json_path.is_file() and not target_json_path.exists():
            shutil.copy2(source_json_path, target_json_path)
    except Exception:
        # Ignore errors for individual files so app startup is not blocked
        pass
