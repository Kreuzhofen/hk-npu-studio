from __future__ import annotations

import os
import json
import shutil
import logging
import urllib.parse
import zipfile
from uuid import uuid4
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
        version: str | None = None,
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
        if version is not None:
            updates["version"] = version
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
    @staticmethod
    def _manifest_model_id(manifest: dict[str, Any]) -> str:
        return str(manifest.get("model_id") or manifest.get("package_id") or manifest.get("id") or "").strip()

    @staticmethod
    def _manifest_version(manifest: dict[str, Any]) -> str:
        return str(manifest.get("package_version") or manifest.get("version") or "").strip()

    def _read_local_package_manifest(self, source_path: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "success": False,
            "message": "Package-Quelle ist ungültig.",
            "manifest": None,
            "source_type": "",
            "manifest_prefix": "",
        }
        source = Path(source_path)
        if not source.exists():
            result["message"] = "Lokale Package-Quelle existiert nicht."
            return result

        try:
            if source.is_dir():
                manifest_path = source / "package.json"
                if not manifest_path.is_file():
                    result["message"] = "Manifest package.json fehlt im Package-Verzeichnis."
                    return result
                with open(manifest_path, "r", encoding="utf-8") as manifest_file:
                    manifest = json.load(manifest_file)
                result.update({"success": isinstance(manifest, dict), "manifest": manifest, "source_type": "directory"})
                if not isinstance(manifest, dict):
                    result["message"] = "Manifest muss ein JSON-Objekt sein."
                return result

            if source.is_file() and zipfile.is_zipfile(source):
                with zipfile.ZipFile(source, "r") as package_zip:
                    names = [name for name in package_zip.namelist() if not name.endswith("/")]
                    manifest_name = "package.json" if "package.json" in names else ""
                    if not manifest_name:
                        candidates = [name for name in names if name.endswith("/package.json")]
                        manifest_name = candidates[0] if candidates else ""
                    if not manifest_name:
                        result["message"] = "Manifest package.json fehlt im Package-Archiv."
                        return result
                    with package_zip.open(manifest_name) as manifest_file:
                        manifest = json.load(manifest_file)
                    prefix = manifest_name[:-len("package.json")]
                result.update({
                    "success": isinstance(manifest, dict),
                    "manifest": manifest,
                    "source_type": "archive",
                    "manifest_prefix": prefix,
                })
                if not isinstance(manifest, dict):
                    result["message"] = "Manifest muss ein JSON-Objekt sein."
                return result
        except (OSError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
            result["message"] = f"Manifest konnte nicht gelesen werden: {exc}"
            return result

        result["message"] = "Package-Quelle muss ein lokaler Ordner oder ein lokales ZIP/SMP-Archiv sein."
        return result

    def _validate_local_package_source(self, model_id: str, source_path: str) -> dict[str, Any]:
        result = self._read_local_package_manifest(source_path)
        if not result.get("success"):
            return result

        manifest = result.get("manifest")
        if not isinstance(manifest, dict):
            result.update({"success": False, "message": "Manifest-Struktur ist ungültig."})
            return result

        issues: list[str] = []
        manifest_id = self._manifest_model_id(manifest)
        if not manifest_id:
            issues.append("Package-ID fehlt im Manifest.")
        elif manifest_id != model_id:
            issues.append(f"Package-ID stimmt nicht überein: Manifest '{manifest_id}', Auswahl '{model_id}'.")

        if not self._manifest_version(manifest):
            issues.append("Version fehlt im Manifest.")
        if not isinstance(manifest.get("capabilities"), dict) or not manifest.get("capabilities"):
            issues.append("Capabilities fehlen im Manifest.")

        components = manifest.get("components")
        if not isinstance(components, dict) or not components:
            issues.append("Runtime-/Model-Komponenten fehlen im Manifest.")
        else:
            source = Path(source_path)
            if result.get("source_type") == "directory":
                for name, config in components.items():
                    rel_path = str(config.get("path") if isinstance(config, dict) else "").strip()
                    if not rel_path:
                        issues.append(f"Dateipfad fehlt für Komponente '{name}'.")
                        continue
                    component_path = source / rel_path
                    if component_path.is_dir():
                        try:
                            exists = any(component_path.iterdir())
                        except OSError:
                            exists = False
                    else:
                        exists = component_path.is_file()
                    if not exists:
                        issues.append(f"Erwartete Datei fehlt: {rel_path}")
            elif result.get("source_type") == "archive":
                prefix = str(result.get("manifest_prefix") or "")
                with zipfile.ZipFile(source, "r") as package_zip:
                    names = set(package_zip.namelist())
                    for name, config in components.items():
                        rel_path = str(config.get("path") if isinstance(config, dict) else "").strip().replace("\\", "/")
                        if not rel_path:
                            issues.append(f"Dateipfad fehlt für Komponente '{name}'.")
                            continue
                        archive_path = f"{prefix}{rel_path}"
                        has_file = archive_path in names
                        has_dir_content = any(member.startswith(archive_path.rstrip("/") + "/") for member in names)
                        if not has_file and not has_dir_content:
                            issues.append(f"Erwartete Datei fehlt: {rel_path}")

        if issues:
            result.update({"success": False, "message": "Package-Quelle ist ungültig.", "issues": issues})
            return result

        result.update({"success": True, "message": "Package-Quelle ist lokal gültig.", "issues": []})
        return result

    @staticmethod
    def _ensure_safe_extract_path(destination: Path, target: Path) -> bool:
        destination_resolved = destination.resolve()
        target_resolved = target.resolve()
        return target_resolved == destination_resolved or destination_resolved in target_resolved.parents

    def _copy_local_package_source(self, source_path: str, destination: Path, source_info: dict[str, Any]) -> None:
        source = Path(source_path)
        if destination.exists():
            if destination.is_dir():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        destination.parent.mkdir(parents=True, exist_ok=True)

        if source_info.get("source_type") == "directory":
            shutil.copytree(source, destination)
            return

        if source_info.get("source_type") == "archive":
            destination.mkdir(parents=True, exist_ok=True)
            prefix = str(source_info.get("manifest_prefix") or "")
            with zipfile.ZipFile(source, "r") as package_zip:
                for member in package_zip.infolist():
                    member_name = member.filename
                    if prefix and not member_name.startswith(prefix):
                        continue
                    relative_name = member_name[len(prefix):] if prefix else member_name
                    if not relative_name:
                        continue
                    target_path = destination / relative_name
                    if not self._ensure_safe_extract_path(destination, target_path):
                        raise ValueError(f"Unsicherer Archivpfad erkannt: {member.filename}")
                    if member.is_dir():
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with package_zip.open(member, "r") as source_file, open(target_path, "wb") as target_file:
                            shutil.copyfileobj(source_file, target_file)
            return

        raise ValueError("Unbekannter Package-Quellentyp.")


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
        allowed_extensions = {".onnx", ".dlc", ".bin", ".safetensors", ".gguf", ".json", ".pb", ".pt", ".pth"}
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
    # DOWNLOAD LIFECYCLE
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
        catalog_package = self.catalog_service.get_package(model_id)
        expected_sha256 = (
            str(catalog_package.get("checksum") or "")
            if catalog_package
            else ""
        )
        result = self.download_service.download(
            url,
            progress_callback=progress_callback,
            expected_sha256=expected_sha256,
            resume=True,
            require_checksum=bool(expected_sha256),
        )
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

    def validate_package_source(self, model_id: str, source_path: str) -> dict[str, Any]:
        """Validate a staged local package without installing or modifying models."""
        return self._validate_local_package_source(model_id, source_path)

    def cleanup_staged_download(self, source_path: str) -> None:
        """Remove only a staged download inside the managed download directory."""
        candidate = Path(source_path)
        try:
            candidate.resolve().relative_to(self.download_service.download_dir.resolve())
        except (OSError, ValueError):
            logger.warning("Refusing to clean download outside staging directory: %s", candidate)
            return
        try:
            if candidate.is_file():
                candidate.unlink()
        except OSError as exc:
            logger.warning("Failed to clean staged download '%s': %s", candidate, exc)

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

        registry_validation = self.repository.validate_model_installation(
            model_id, verify_hashes=True
        )
        if registry_validation is not None:
            for issue in registry_validation.issues:
                add_issue(issue.message)
            if registry_validation.checked_hashes:
                result["checksum_hint"] = (
                    f"{registry_validation.checked_hashes} SHA-256-Prüfung(en) erfolgreich."
                )

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
        if registry_validation is not None and registry_validation.checked_hashes:
            pass
        elif checksum:
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
        Atomically replace an installed package after staging and validation.
        The previous package remains available for rollback until the registry commit succeeds.
        """
        logger.info(f"Triggering local package update for '{model_id}' from '{new_source_path}'")
        model = self.repository.get_model(model_id)
        if not model or model.get("installed") is not True:
            logger.error("Package update rejected: '%s' is not installed.", model_id)
            return False

        source_info = self._validate_local_package_source(model_id, new_source_path)
        manifest = source_info.get("manifest")
        if not source_info.get("success") or not isinstance(manifest, dict):
            logger.error(
                "Package update source invalid | model=%s message=%s",
                model_id,
                source_info.get("message"),
            )
            return False

        installed_version = str(model.get("version") or "")
        package_version = self._manifest_version(manifest)
        if installed_version and not self._is_version_older(
            installed_version, package_version
        ):
            logger.error(
                "Package update rejected: version is not newer | model=%s installed=%s candidate=%s",
                model_id,
                installed_version,
                package_version,
            )
            return False

        package_dir = Path(str(model.get("path") or ""))
        if not package_dir.exists() or not package_dir.is_dir():
            logger.error("Package update rejected: installed path is invalid | model=%s", model_id)
            return False

        operation_id = uuid4().hex
        staging_dir = package_dir.parent / f".{package_dir.name}.update-{operation_id}"
        backup_dir = package_dir.parent / f".{package_dir.name}.backup-{operation_id}"
        previous = {
            "installed": bool(model.get("installed")),
            "downloaded": bool(model.get("downloaded")),
            "path": str(model.get("path") or ""),
            "status": str(model.get("status") or ""),
            "version": installed_version,
        }
        swapped = False
        try:
            self._copy_local_package_source(new_source_path, staging_dir, source_info)
            candidate = dict(model)
            candidate.update(
                {
                    "installed": True,
                    "downloaded": True,
                    "path": str(staging_dir.resolve()),
                    "version": package_version,
                    "status": "Ready",
                }
            )
            validation = self.repository.registry.validate_installation(
                candidate, verify_hashes=True
            )
            if not validation.valid:
                raise ValueError(
                    "Staged package validation failed: "
                    + "; ".join(validation.messages)
                )

            package_dir.replace(backup_dir)
            staging_dir.replace(package_dir)
            swapped = True

            if not self.repository.update_model(
                model_id,
                installed=True,
                downloaded=True,
                path=str(package_dir.resolve()),
                status="Ready",
                version=package_version,
            ):
                raise RuntimeError("Registry update failed after package swap.")

            try:
                shutil.rmtree(backup_dir)
            except OSError as cleanup_error:
                logger.warning(
                    "Update-Backup konnte nach erfolgreichem Commit nicht entfernt werden "
                    "| model=%s path=%s error=%s",
                    model_id,
                    backup_dir,
                    cleanup_error,
                )
            logger.info(
                "Package update committed | model=%s previous=%s version=%s",
                model_id,
                installed_version,
                package_version,
            )
            return True
        except Exception as exc:
            logger.error("Package update failed; rolling back | model=%s error=%s", model_id, exc)
            try:
                if swapped:
                    if package_dir.exists():
                        shutil.rmtree(package_dir)
                    if backup_dir.exists():
                        backup_dir.replace(package_dir)
                self.repository.update_model(model_id, **previous)
            except Exception as rollback_error:
                logger.critical(
                    "Package rollback failed | model=%s error=%s",
                    model_id,
                    rollback_error,
                )
            return False
        finally:
            if staging_dir.exists():
                try:
                    shutil.rmtree(staging_dir)
                except OSError as cleanup_error:
                    logger.warning(
                        "Update-Artefakt konnte nicht entfernt werden | path=%s error=%s",
                        staging_dir,
                        cleanup_error,
                    )

    def check_for_update(self, model_id: str) -> bool:
        """Return whether the catalog contains a newer version for an installed model."""
        model = self.repository.get_model(model_id)
        catalog = self.catalog_service.get_package(model_id)
        if not model or model.get("installed") is not True or not catalog:
            return False
        installed_version = str(model.get("version") or "")
        catalog_version = str(catalog.get("version") or "")
        return bool(
            installed_version
            and catalog_version
            and self._is_version_older(installed_version, catalog_version)
        )

    def remove_package(self, model_id: str) -> bool:
        """
        Remove only the package-owned directory under MODELS_DIR / model_id.
        """
        logger.info(f"Triggering safe package removal for '{model_id}'")
        model = self.repository.get_model(model_id)
        if not model:
            logger.error("Package removal failed: Model '%s' not found.", model_id)
            return False

        package_dir = MODELS_DIR / model_id
        try:
            package_dir_resolved = package_dir.resolve()
            models_dir_resolved = MODELS_DIR.resolve()
            if package_dir.exists():
                if models_dir_resolved not in package_dir_resolved.parents:
                    logger.error("Package removal blocked outside models directory: %s", package_dir)
                    return False
                if package_dir.is_dir():
                    shutil.rmtree(package_dir)
                else:
                    package_dir.unlink()

            return self.repository.update_model(
                model_id,
                installed=False,
                downloaded=False,
                path="",
                status="Available for Download",
            )
        except Exception as exc:
            logger.error("Package removal failed for '%s': %s", model_id, exc)
            return False

    def install_package(
        self,
        model_id: str,
        source_path: str,
        progress_callback: Callable[[float], None] | None = None,
        replace_existing: bool = True,
    ) -> bool:
        """
        Install an SMP package from a local directory or local ZIP/SMP archive only.
        """
        del progress_callback
        logger.info(f"Triggering local package installation for '{model_id}' from '{source_path}'")

        if self._is_download_url(source_path):
            logger.error("Package installation rejected remote URL for '%s'.", model_id)
            self._set_package_status(model_id, status="Install Failed")
            return False

        source_info = self._validate_local_package_source(model_id, source_path)
        if not source_info.get("success"):
            logger.error("Package source validation failed for '%s': %s", model_id, source_info.get("message"))
            self._set_package_status(model_id, status="Install Failed")
            return False

        manifest = source_info.get("manifest")
        if not isinstance(manifest, dict):
            self._set_package_status(model_id, status="Install Failed")
            return False

        package_dir = MODELS_DIR / model_id
        if package_dir.exists() and not replace_existing:
            logger.error("Package installation refused to replace existing model '%s'.", model_id)
            self._set_package_status(model_id, status="Install Failed")
            return False
        try:
            self._set_package_status(model_id, status="Installing")
            self._copy_local_package_source(source_path, package_dir, source_info)
            package_version = self._manifest_version(manifest)
            self.repository.update_model(
                model_id,
                installed=True,
                downloaded=True,
                path=str(package_dir.resolve()),
                status="Installed",
                version=package_version or None,
            )

            validation = self.validate_package(model_id)
            if validation.get("success"):
                self._set_package_status(model_id, installed=True, downloaded=True, status="Ready")
                return True

            self._set_package_status(model_id, installed=True, downloaded=True, status="Invalid")
            logger.error(
                "Package validation failed for '%s' after local installation: %s",
                model_id,
                validation.get("message", "Unknown validation error"),
            )
            return False
        except Exception as exc:
            logger.error("Package installation failed for '%s': %s", model_id, exc)
            if package_dir.exists():
                try:
                    if package_dir.is_dir():
                        shutil.rmtree(package_dir)
                    else:
                        package_dir.unlink()
                except Exception:
                    logger.warning("Failed to clean incomplete package directory: %s", package_dir)
            self._set_package_status(model_id, installed=False, downloaded=False, path="", status="Install Failed")
            return False




