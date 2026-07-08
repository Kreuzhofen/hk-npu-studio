from __future__ import annotations

import os
import json
import shutil
import logging
import urllib.parse
from pathlib import Path
from typing import Callable, Any

from config import MODELS_DIR
from controllers.model_repository import ModelRepository
from controllers.package_status import PackageStatus
from engine.download_service import DownloadService, DownloadErrorCode
from engine.package_catalog_service import PackageCatalogService

logger = logging.getLogger("ModelInstallService")


class ModelInstallService:
    """
    Foundation service for local AI model installation, verification, and removal.
    Integrates with ModelRepository as the source of truth.
    """

    def __init__(self, repository: ModelRepository | None = None) -> None:
        self.repository = repository or ModelRepository()
        self.download_service = DownloadService()
        self.catalog_service = PackageCatalogService()

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

    @staticmethod
    def _is_version_older(installed_version: str, catalog_version: str) -> bool:
        def normalize(version: str) -> list[str]:
            parts: list[str] = []
            for part in version.replace("-", ".").split("."):
                if part.isdigit():
                    parts.append(part.zfill(8))
                elif part:
                    parts.append(part)
            return parts

        return normalize(installed_version) < normalize(catalog_version)

    def get_catalog_status(self, model_id: str) -> PackageStatus:
        catalog_entry = self.catalog_service.get_entry(model_id)
        model = self.repository.get_model(model_id)

        if not catalog_entry:
            return self.repository.get_package_status(model_id)

        if not model or not model.get("installed", False):
            return PackageStatus.NOT_INSTALLED

        repository_status = self.repository.get_package_status(model_id)
        if repository_status == PackageStatus.INVALID:
            return PackageStatus.INVALID

        if repository_status in {PackageStatus.INSTALLED, PackageStatus.READY}:
            installed_version = str(model.get("version", ""))
            if installed_version and self._is_version_older(installed_version, catalog_entry.version):
                return PackageStatus.UPDATE_AVAILABLE
            return repository_status

        return repository_status

    def list_available_packages(self) -> list[dict[str, Any]]:
        packages = []
        for package in self.catalog_service.list_packages():
            model_id = str(package["model_id"])
            enriched = dict(package)
            enriched["status"] = str(self.get_catalog_status(model_id))
            model = self.repository.get_model(model_id)
            if model:
                enriched["installed_version"] = model.get("version", "")
                enriched["installed_path"] = model.get("path", "")
            else:
                enriched["installed_version"] = ""
                enriched["installed_path"] = ""
            packages.append(enriched)
        return packages

    def reconcile_installed_packages(self) -> list[dict[str, Any]]:
        reconciled = []
        for model in self.repository.get_all_models():
            model_id = str(model.get("id", ""))
            if not model_id:
                continue
            catalog_entry = self.catalog_service.get_package(model_id)
            status = self.get_catalog_status(model_id)
            reconciled.append({
                "model_id": model_id,
                "display_name": model.get("display_name", model_id),
                "installed": bool(model.get("installed", False)),
                "installed_version": model.get("version", ""),
                "installed_path": model.get("path", ""),
                "catalog_version": catalog_entry.get("version", "") if catalog_entry else "",
                "catalog_available": catalog_entry is not None,
                "status": str(status),
            })
        return reconciled

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
        Validate an installed SMP package using local files only.
        No downloads, updates, installations, or repository writes are performed.
        """
        result: dict[str, Any] = {
            "success": False,
            "message": "Package validation failed.",
            "components": {},
            "issues": [],
            "warnings": [],
            "missing_files": [],
            "manifest_found": False,
            "manifest_readable": False,
            "package_dir": "",
            "manifest_path": "",
            "package_version": "",
            "catalog_version": "",
            "version_hint": "Nicht verfügbar",
            "runtime_hint": "Nicht verfügbar",
            "capabilities_hint": "Nicht verfügbar",
            "checksum_hint": "Nicht geprüft",
            "is_fully_ready": False,
        }

        def add_issue(message: str) -> None:
            if message not in result["issues"]:
                result["issues"].append(message)

        model = self.repository.get_model(model_id)
        catalog_package = self.catalog_service.get_package(model_id)
        if catalog_package:
            result["catalog_version"] = str(catalog_package.get("version", "") or "")
        else:
            add_issue("Kein Katalogeintrag für dieses Package gefunden.")

        if not model:
            add_issue(f"Model '{model_id}' ist nicht im lokalen Repository registriert.")
            result["message"] = "Invalid: Repository-Eintrag fehlt."
            return result

        if not model.get("installed", False):
            add_issue("Package ist nicht als installiert markiert.")
            result["message"] = "Invalid: Package ist nicht installiert."
            return result

        model_path = str(model.get("path") or "").strip()
        if not model_path:
            add_issue("Package-Pfad fehlt im Repository-Eintrag.")
            result["message"] = "Invalid: Package-Pfad fehlt."
            return result

        package_dir = Path(model_path)
        result["package_dir"] = str(package_dir)
        if not package_dir.exists():
            add_issue("Package-Verzeichnis fehlt.")
            result["message"] = "Invalid: Package-Verzeichnis fehlt."
            return result
        if not package_dir.is_dir():
            add_issue("Package-Pfad ist kein Verzeichnis.")
            result["message"] = "Invalid: Package-Pfad ist kein Verzeichnis."
            return result

        manifest_path = package_dir / "package.json"
        result["manifest_path"] = str(manifest_path)
        if not manifest_path.exists() or not manifest_path.is_file():
            add_issue("Manifest package.json fehlt.")
            result["message"] = "Invalid: Manifest fehlt."
            return result
        result["manifest_found"] = True

        try:
            with open(manifest_path, "r", encoding="utf-8") as manifest_file:
                manifest = json.load(manifest_file)
        except (OSError, json.JSONDecodeError) as exc:
            add_issue(f"Manifest ist nicht lesbar: {exc}")
            result["message"] = "Invalid: Manifest ist nicht lesbar."
            return result

        if not isinstance(manifest, dict):
            add_issue("Manifest muss ein JSON-Objekt sein.")
            result["message"] = "Invalid: Manifest-Struktur ist ungültig."
            return result
        result["manifest_readable"] = True

        manifest_id = str(
            manifest.get("model_id") or manifest.get("package_id") or manifest.get("id") or ""
        ).strip()
        if not manifest_id:
            add_issue("Package-ID fehlt im Manifest.")
        elif manifest_id != model_id:
            add_issue(f"Package-ID stimmt nicht überein: Manifest '{manifest_id}', Katalog '{model_id}'.")

        package_version = str(manifest.get("package_version") or manifest.get("version") or "").strip()
        result["package_version"] = package_version
        catalog_version = str(result.get("catalog_version") or "").strip()
        if not package_version:
            add_issue("Version fehlt im Manifest.")
            result["version_hint"] = "Version fehlt im Manifest."
        elif catalog_version and package_version != catalog_version:
            result["version_hint"] = f"Installiert: {package_version}; Katalog: {catalog_version}"
            result["warnings"].append("Installierte Version weicht vom Katalog ab.")
        else:
            result["version_hint"] = f"Installiert: {package_version}"

        capabilities = manifest.get("capabilities")
        if not isinstance(capabilities, dict) or not capabilities:
            add_issue("Capabilities fehlen im Manifest.")
        else:
            enabled = sorted(str(name) for name, active in capabilities.items() if bool(active))
            result["capabilities_hint"] = ", ".join(enabled) if enabled else "Keine aktiven Capabilities"

        components = manifest.get("components")
        if not isinstance(components, dict) or not components:
            add_issue("Runtime-/Model-Komponenten fehlen im Manifest.")
        else:
            runtimes: set[str] = set()
            for component_name, component_config in components.items():
                if not isinstance(component_config, dict):
                    add_issue(f"Komponente '{component_name}' ist ungültig definiert.")
                    result["components"][component_name] = {
                        "status": "INVALID",
                        "path": "",
                        "runtime": "Unknown",
                    }
                    continue

                rel_path = str(component_config.get("path") or "").strip()
                runtime = str(component_config.get("runtime") or "").strip()
                if runtime:
                    runtimes.add(runtime)
                else:
                    add_issue(f"Runtime fehlt für Komponente '{component_name}'.")
                    runtime = "Unknown"

                if not rel_path:
                    add_issue(f"Dateipfad fehlt für Komponente '{component_name}'.")
                    result["components"][component_name] = {
                        "status": "MISSING",
                        "path": "",
                        "runtime": runtime,
                    }
                    continue

                component_path = package_dir / rel_path
                component_exists = component_path.exists()
                if component_exists and component_path.is_dir():
                    try:
                        component_exists = any(component_path.iterdir())
                    except OSError:
                        component_exists = False
                if not component_exists:
                    missing_path = str(component_path)
                    result["missing_files"].append(missing_path)
                    add_issue(f"Erwartete Datei fehlt: {rel_path}")

                result["components"][component_name] = {
                    "status": "READY" if component_exists else "MISSING",
                    "path": str(component_path),
                    "runtime": runtime,
                }

            result["runtime_hint"] = ", ".join(sorted(runtimes)) if runtimes else "Runtime fehlt"

        checksum = catalog_package.get("checksum") if catalog_package else None
        if checksum:
            result["checksum_hint"] = "Checksumme definiert; keine lokale Prüfinfrastruktur aktiv."
            result["warnings"].append("Checksumme wurde nicht geprüft, weil keine lokale Prüfinfrastruktur angebunden ist.")
        else:
            result["checksum_hint"] = "Keine Checksumme definiert"

        result["success"] = not result["issues"]
        result["is_fully_ready"] = bool(result["success"])
        result["message"] = (
            "Valid: Package-Dateien und Manifest sind lokal konsistent."
            if result["success"]
            else "Invalid: Lokale Package-Validierung hat Probleme gefunden."
        )
        return result

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

