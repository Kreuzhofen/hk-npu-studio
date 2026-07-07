from __future__ import annotations

import os
import shutil
import logging
from pathlib import Path
from typing import Callable

from config import MODELS_DIR
from controllers.model_repository import ModelRepository

logger = logging.getLogger("ModelInstallService")


class ModelInstallService:
    """
    Foundation service for local AI model installation, verification, and removal.
    Integrates with ModelRepository as the source of truth.
    """

    def __init__(self, repository: ModelRepository | None = None) -> None:
        self.repository = repository or ModelRepository()

    def validate_model(self, source_path: str) -> bool:
        """
        Validate if the source path exists, is readable, and contains files of non-zero size.
        For directories, it verifies that at least one file exists.
        """
        p = Path(source_path)
        if not p.exists():
            logger.error(f"Validation failed: Path '{source_path}' does not exist.")
            return False

        if p.is_file():
            return p.stat().st_size > 0
        elif p.is_dir():
            # Ensure it's not an empty directory
            files = [f for f in p.rglob("*") if f.is_file()]
            if not files:
                logger.error(f"Validation failed: Directory '{source_path}' contains no files.")
                return False
            # Ensure at least some file has non-zero size
            return any(f.stat().st_size > 0 for f in files)
        
        return False

    def get_model_size(self, path: str) -> int:
        """
        Calculate total size of the file or directory in bytes.
        """
        p = Path(path)
        if not p.exists():
            return 0
        if p.is_file():
            return p.stat().st_size
        elif p.is_dir():
            return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        return 0

    def check_available_disk_space(self, path: str) -> int:
        """
        Check the available free space in bytes on the partition containing the given path.
        """
        p = Path(path).resolve()
        # If path does not exist yet, check the parent directory
        while not p.exists() and p.parent != p:
            p = p.parent
        try:
            usage = shutil.disk_usage(p)
            return usage.free
        except Exception as e:
            logger.error(f"Failed to check disk usage for '{p}': {e}")
            return 0

    def install_model(self, model_id: str, source_path: str) -> bool:
        """
        Installs a local model by copying its file(s) into the standard models directory
        and registering it in the ModelRepository.
        """
        model = self.repository.get_model(model_id)
        if not model:
            logger.error(f"Installation failed: Model '{model_id}' is not registered in the repository.")
            return False

        if not self.validate_model(source_path):
            logger.error(f"Installation failed: Source model validation failed at '{source_path}'.")
            return False

        src_path = Path(source_path)
        dest_dir = Path(MODELS_DIR) / model_id
        
        # Calculate size and check disk space
        model_size = self.get_model_size(source_path)
        available_space = self.check_available_disk_space(str(dest_dir.parent))

        # Add a 50MB safety buffer
        safety_buffer = 50 * 1024 * 1024
        if available_space < (model_size + safety_buffer):
            logger.error(
                f"Installation failed: Insufficient disk space on destination drive. "
                f"Required: {model_size} bytes, Available: {available_space} bytes."
            )
            return False

        try:
            # Ensure destination parent directory exists
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # If destination already exists, remove it first for clean install
            if dest_dir.exists():
                if dest_dir.is_dir():
                    shutil.rmtree(dest_dir)
                else:
                    dest_dir.unlink()

            # Copy file/folder
            if src_path.is_file():
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / src_path.name
                shutil.copy2(src_path, dest_path)
            else:
                shutil.copytree(src_path, dest_dir)
                dest_path = dest_dir

            # Update repository
            success = self.repository.update_model(
                model_id,
                installed=True,
                downloaded=True,
                path=str(dest_path.resolve()),
                status="Installed"
            )
            if success:
                logger.info(f"Model '{model_id}' installed successfully to '{dest_path}'.")
                return True
            else:
                logger.error(f"Failed to update model repository metadata for '{model_id}'.")
                return False

        except Exception as e:
            logger.error(f"Failed to copy model files from '{source_path}' to '{dest_dir}': {e}")
            # Try to cleanup
            if dest_dir.exists():
                try:
                    if dest_dir.is_dir():
                        shutil.rmtree(dest_dir)
                    else:
                        dest_dir.unlink()
                except Exception:
                    pass
            return False

    def uninstall_model(self, model_id: str) -> bool:
        """
        Uninstalls a model by deleting its local files and updating the repository status.
        """
        model = self.repository.get_model(model_id)
        if not model:
            logger.error(f"Uninstallation failed: Model '{model_id}' not found.")
            return False

        model_path_str = model.get("path")
        if not model_path_str:
            # Not installed, but let's ensure repository is clean in database
            self.repository.update_model(
                model_id,
                installed=False,
                downloaded=False,
                path="",
                status="Available for Download"
            )
            return True

        model_path = Path(model_path_str)
        try:
            # Delete model files (either the folder or specific file)
            # Check if it resides inside our standard models directory before deleting for safety
            if model_path.exists():
                if MODELS_DIR.resolve() in model_path.resolve().parents or model_path.resolve() == MODELS_DIR.resolve():
                    # For safety, if it's the model folder we created (MODELS_DIR / model_id)
                    target_folder = MODELS_DIR / model_id
                    if target_folder.exists() and target_folder.is_dir():
                        shutil.rmtree(target_folder)
                    elif model_path.is_file():
                        model_path.unlink()
                else:
                    # If it was installed at a custom external path, just remove the specific file/folder if inside workspace
                    if Path(r"C:\SnapdragonAI").resolve() in model_path.resolve().parents:
                        if model_path.is_dir():
                            shutil.rmtree(model_path)
                        else:
                            model_path.unlink()

            # Update repository
            success = self.repository.update_model(
                model_id,
                installed=False,
                downloaded=False,
                path="",
                status="Available for Download"
            )
            if success:
                logger.info(f"Model '{model_id}' uninstalled successfully.")
                return True
            else:
                logger.error(f"Failed to update model repository metadata for uninstalled '{model_id}'.")
                return False

        except Exception as e:
            logger.error(f"Failed to delete model files for '{model_id}' at '{model_path}': {e}")
            return False

    # ==========================================
    # FUTURE ROADMAP HOOKS FOR DOWNLOADS
    # ==========================================
    
    def start_download(
        self, 
        model_id: str, 
        url: str, 
        progress_callback: Callable[[float], None] | None = None
    ) -> bool:
        """
        Placeholder hook for future Hugging Face or remote API model download.
        Will trigger downloading files chunk-by-chunk and call progress_callback(percentage).
        """
        logger.info(f"Future download hook triggered for model '{model_id}' from URL '{url}'.")
        return False

    def cancel_download(self, model_id: str) -> bool:
        """
        Placeholder hook to cancel a running download job.
        """
        logger.info(f"Future download cancellation hook triggered for model '{model_id}'.")
        return False
