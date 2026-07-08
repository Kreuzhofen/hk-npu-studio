from __future__ import annotations

import os
import shutil
import logging
import urllib.parse
from pathlib import Path
from typing import Callable, Any

from config import MODELS_DIR
from controllers.model_repository import ModelRepository
from engine.download_service import DownloadService, DownloadErrorCode

logger = logging.getLogger("ModelInstallService")


class ModelInstallService:
    """
    Foundation service for local AI model installation, verification, and removal.
    Integrates with ModelRepository as the source of truth.
    """

    def __init__(self, repository: ModelRepository | None = None) -> None:
        self.repository = repository or ModelRepository()
        self.download_service = DownloadService()

    @staticmethod
    def _is_download_url(source_path: str) -> bool:
        parsed = urllib.parse.urlparse(source_path)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def _set_package_status(
        self,
        model_id: str,
        *,
        installed: bool | None = None,
        downloaded: bool | None = None,
        path: str | None = None,
        status: str | None = None,
    ) -> None:
        updates: dict[str, Any] = {}
        if installed is not None:
            updates["installed"] = installed
        if downloaded is not None:
            updates["downloaded"] = downloaded
        if path is not None:
            updates["path"] = path
        if status is not None:
            updates["status"] = status
        if updates:
            self.repository.update_model(model_id, **updates)

    def validate_model(self, source_path: str) -> dict[str, Any]:
        """
        Validates the source path for installation.
        Checks:
        - existence, type (file or folder), read access.
        - file extension or presence of at least one model file in folders.
        - non-zero size.
        Returns a dictionary:
        {
            "success": bool,
            "message": str,
            "warnings": list[str],
            "size_bytes": int
        }
        """
        allowed_extensions = {".onnx", ".bin", ".safetensors", ".gguf", ".json", ".pb", ".pt", ".pth"}
        result = {
            "success": False,
            "message": "Validierung gestartet.",
            "warnings": [],
            "size_bytes": 0
        }
        
        p = Path(source_path)
        
        # 1. Check exists
        if not p.exists():
            result["message"] = f"Pfad '{source_path}' existiert nicht."
            return result

        # 2. Check type (file or folder)
        if not p.is_file() and not p.is_dir():
            result["message"] = f"Pfad '{source_path}' ist weder eine reguläre Datei noch ein Verzeichnis."
            return result

        # 3. Check readable
        if not os.access(source_path, os.R_OK):
            result["message"] = f"Pfad '{source_path}' ist nicht lesbar (keine Leserechte)."
            return result

        # 4. Check contents and extensions
        if p.is_file():
            suffix = p.suffix.lower()
            if suffix not in allowed_extensions:
                result["message"] = f"Datei '{p.name}' hat keine gültige Modell-Dateiendung. Erlaubt sind: {', '.join(allowed_extensions)}"
                return result
            
            size = p.stat().st_size
            if size <= 0:
                result["message"] = f"Datei '{p.name}' ist leer (Größe = 0 Bytes)."
                return result
                
            result["size_bytes"] = size
            if size > 10 * 1024 * 1024 * 1024:  # > 10 GB
                result["warnings"].append(f"Sehr große Modelldatei ({size / (1024**3):.1f} GB) erkannt. Kopieren kann lange dauern.")

        elif p.is_dir():
            try:
                all_files = [f for f in p.rglob("*") if f.is_file()]
            except Exception as e:
                result["message"] = f"Fehler beim Lesen des Verzeichnisses: {e}"
                return result
                
            if not all_files:
                result["message"] = f"Verzeichnis '{p.name}' ist leer."
                return result
                
            model_files = [f for f in all_files if f.suffix.lower() in allowed_extensions]
            if not model_files:
                result["message"] = f"Verzeichnis '{p.name}' enthält keine der erlaubten Modelldateien ({', '.join(allowed_extensions)})."
                return result
                
            total_size = sum(f.stat().st_size for f in all_files)
            if total_size <= 0:
                result["message"] = f"Die Dateien im Verzeichnis '{p.name}' sind alle leer."
                return result
                
            result["size_bytes"] = total_size
            
            non_model_count = len(all_files) - len(model_files)
            if non_model_count > 0:
                result["warnings"].append(f"Verzeichnis enthält {non_model_count} Nicht-Modell-Dateien, die mitkopiert werden.")
            if total_size > 10 * 1024 * 1024 * 1024:
                result["warnings"].append(f"Sehr großes Modellverzeichnis ({total_size / (1024**3):.1f} GB) erkannt. Kopieren kann lange dauern.")
                
        result["success"] = True
        result["message"] = "Validierung erfolgreich."
        return result

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

        validation = self.validate_model(source_path)
        if not validation["success"]:
            logger.error(f"Installation failed: {validation['message']}")
            return False

        src_path = Path(source_path)
        dest_dir = Path(MODELS_DIR) / model_id
        
        # Calculate size and check disk space
        model_size = validation["size_bytes"]
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
        Download a package into temp/downloads and keep it staged for installation.
        """
        logger.info(f"Download triggered for model '{model_id}' from URL '{url}'.")
        self._set_package_status(model_id, status="Downloading")
        result = self.download_service.download(url, progress_callback=progress_callback)
        if not result.success:
            self._set_package_status(model_id, status=f"Download Failed: {result.error_code}")
            return False
        self._set_package_status(
            model_id,
            downloaded=True,
            path=str(result.path.resolve()) if result.path else None,
            status="Downloaded"
        )
        return True

    def cancel_download(self, model_id: str) -> bool:
        """
        Cancel a running package download.
        """
        logger.info(f"Download cancellation triggered for model '{model_id}'.")
        self.download_service.cancel()
        self._set_package_status(model_id, status="Download Cancelled")
        return True

    def validate_package(self, model_id: str) -> dict[str, Any]:
        """
        Validate an installed SMP package by verifying all its components.
        """
        model = self.repository.get_model(model_id)
        if not model or not model.get("installed", False):
            return {
                "success": False,
                "message": f"Model '{model_id}' is not installed.",
                "components": {}
            }
            
        pkg = self.repository.build_runtime_package(model_id)
        if not pkg:
            return {
                "success": False,
                "message": f"Failed to build runtime package for '{model_id}'.",
                "components": {}
            }
            
        statuses = pkg.verify_components()
        is_ready = pkg.is_fully_ready()
        
        # Collect component runtimes and paths for centralized display
        components_info = {}
        for name, status in statuses.items():
            components_info[name] = {
                "status": status,
                "path": pkg.get_component_path(name),
                "runtime": pkg.get_component_runtime(name) or "Unknown"
            }
            
        return {
            "success": is_ready,
            "message": "SMP package is READY for real local inference." if is_ready else "SMP package validation failed (stubs/missing files).",
            "components": components_info,
            "is_fully_ready": is_ready,
            "package_version": pkg.package_version,
            "author": pkg.author,
            "display_name": pkg.display_name
        }

    def update_package(self, model_id: str, new_source_path: str) -> bool:
        """
        Update an existing package by copying the new source path components over the old ones.
        """
        logger.info(f"Triggering package update for '{model_id}' from '{new_source_path}'")
        return self.install_model(model_id, new_source_path)

    def remove_package(self, model_id: str) -> bool:
        """
        Remove/Uninstall the model package.
        """
        logger.info(f"Triggering package removal for '{model_id}'")
        return self.uninstall_model(model_id)
        
    def install_package(
        self,
        model_id: str,
        source_path: str,
        progress_callback: Callable[[float], None] | None = None,
    ) -> bool:
        """
        Install an SMP package from a local path or a future remote download URL.
        """
        logger.info(f"Triggering package installation for '{model_id}' from '{source_path}'")
        install_source = source_path
        downloaded_source = False

        if self._is_download_url(source_path):
            self._set_package_status(model_id, status="Downloading")
            download_result = self.download_service.download(
                source_path,
                progress_callback=progress_callback,
            )
            if not download_result.success or not download_result.path:
                status = "Download Failed"
                if download_result.error_code == DownloadErrorCode.FILE_EXISTS:
                    status = "Download Failed: File Exists"
                elif download_result.error_code == DownloadErrorCode.TIMEOUT:
                    status = "Download Failed: Timeout"
                elif download_result.error_code == DownloadErrorCode.INCOMPLETE_DOWNLOAD:
                    status = "Download Failed: Incomplete"
                elif download_result.error_code == DownloadErrorCode.INVALID_FILE:
                    status = "Download Failed: Invalid File"
                elif download_result.error_code == DownloadErrorCode.NETWORK_ERROR:
                    status = "Download Failed: Network Error"
                elif download_result.error_code == DownloadErrorCode.CANCELLED:
                    status = "Download Cancelled"
                self._set_package_status(model_id, downloaded=False, status=status)
                logger.error(
                    "Package download failed for '%s': %s",
                    model_id,
                    download_result.message,
                )
                return False

            install_source = str(download_result.path)
            downloaded_source = True
            self._set_package_status(
                model_id,
                downloaded=True,
                path=install_source,
                status="Downloaded",
            )

        self._set_package_status(model_id, status="Installing")
        if not self.install_model(model_id, install_source):
            self._set_package_status(model_id, installed=False, status="Install Failed")
            return False

        if not downloaded_source:
            return True

        validation = self.validate_package(model_id)
        if validation.get("success"):
            self._set_package_status(model_id, installed=True, downloaded=True, status="Ready")
            return True

        self._set_package_status(model_id, installed=True, downloaded=True, status="Invalid")
        logger.error(
            "Package validation failed for '%s' after installation: %s",
            model_id,
            validation.get("message", "Unknown validation error"),
        )
        return False
