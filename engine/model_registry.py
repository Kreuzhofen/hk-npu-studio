from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from engine.error_diagnostics import diagnose_exception
from engine.logging_config import get_logger


logger = get_logger("ModelRegistry")

MODEL_METADATA_SCHEMA_VERSION = 1
ALLOWED_MODEL_EXTENSIONS = frozenset(
    {".onnx", ".dlc", ".bin", ".safetensors", ".gguf", ".json", ".pb", ".pt", ".pth"}
)
REQUIRED_METADATA_FIELDS = frozenset(
    {
        "id",
        "display_name",
        "author",
        "version",
        "license",
        "description",
        "category",
        "backend",
        "recommended_backend",
        "minimum_ram_gb",
        "recommended_ram_gb",
        "supports",
        "installed",
        "downloaded",
        "path",
        "status",
        "capabilities",
    }
)


class ModelHealthStatus(str, Enum):
    AVAILABLE = "available"
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    READY = "ready"
    INVALID = "invalid"


@dataclass(frozen=True)
class ModelValidationIssue:
    code: str
    message: str
    field: str | None = None
    path: str | None = None


@dataclass
class ModelValidationResult:
    model_id: str
    status: ModelHealthStatus
    valid: bool
    metadata: dict[str, Any] | None = None
    issues: list[ModelValidationIssue] = field(default_factory=list)
    checked_hashes: int = 0

    @property
    def messages(self) -> list[str]:
        return [issue.message for issue in self.issues]


class ModelRegistry:
    """Central source of truth for model metadata, status, and validation."""

    def __init__(self) -> None:
        self._models: dict[str, dict[str, Any]] = {}
        self._reports: dict[str, ModelValidationResult] = {}
        self._source_reports: dict[str, ModelValidationResult] = {}

    def clear(self) -> None:
        self._models.clear()
        self._reports.clear()
        self._source_reports.clear()

    def load_directory(
        self,
        models_dir: str | Path,
        *,
        available_backends: Iterable[str] | None = None,
    ) -> None:
        self.clear()
        directory = Path(models_dir)
        if not directory.exists():
            logger.warning("Model-Verzeichnis fehlt | path=%s", directory)
            return

        for source in sorted(directory.glob("*.json")):
            try:
                raw = json.loads(source.read_text(encoding="utf-8"))
                result = self.validate_metadata(
                    raw, source=source, available_backends=available_backends
                )
            except (OSError, json.JSONDecodeError) as error:
                diagnose_exception(
                    logger,
                    error,
                    category="model_registry",
                    context=f"load_definition:{source}",
                )
                result = ModelValidationResult(
                    model_id=source.stem,
                    status=ModelHealthStatus.INVALID,
                    valid=False,
                    issues=[
                        ModelValidationIssue(
                            "definition_unreadable",
                            f"Modelldefinition ist nicht lesbar: {error}",
                            path=str(source),
                        )
                    ],
                )

            report_key = result.model_id or source.stem
            self._source_reports[source.name] = result
            self._reports[report_key] = result
            if result.valid and result.metadata is not None:
                model = deepcopy(result.metadata)
                model["_filepath"] = str(source)
                self._models[result.model_id] = model
            else:
                logger.error(
                    "Ungültige Modelldefinition | source=%s issues=%s",
                    source,
                    "; ".join(result.messages),
                )

    def validate_metadata(
        self,
        data: Any,
        *,
        source: str | Path | None = None,
        available_backends: Iterable[str] | None = None,
    ) -> ModelValidationResult:
        issues: list[ModelValidationIssue] = []
        source_text = str(source) if source is not None else None
        if not isinstance(data, dict):
            return ModelValidationResult(
                model_id=Path(source_text).stem if source_text else "",
                status=ModelHealthStatus.INVALID,
                valid=False,
                issues=[
                    ModelValidationIssue(
                        "metadata_type",
                        "Modelldefinition muss ein JSON-Objekt sein.",
                        path=source_text,
                    )
                ],
            )

        model_id = str(data.get("id") or "").strip()
        missing = sorted(REQUIRED_METADATA_FIELDS.difference(data))
        for name in missing:
            issues.append(
                ModelValidationIssue(
                    "required_field_missing",
                    f"Pflichtfeld '{name}' fehlt.",
                    field=name,
                    path=source_text,
                )
            )

        string_fields = (
            "id",
            "display_name",
            "author",
            "version",
            "license",
            "description",
            "category",
            "backend",
            "recommended_backend",
            "path",
            "status",
        )
        for name in string_fields:
            if name in data and not isinstance(data[name], str):
                issues.append(
                    ModelValidationIssue(
                        "invalid_field_type",
                        f"Feld '{name}' muss eine Zeichenkette sein.",
                        field=name,
                        path=source_text,
                    )
                )
        for name in ("installed", "downloaded"):
            if name in data and not isinstance(data[name], bool):
                issues.append(
                    ModelValidationIssue(
                        "invalid_field_type",
                        f"Feld '{name}' muss boolesch sein.",
                        field=name,
                        path=source_text,
                    )
                )
        for name in ("minimum_ram_gb", "recommended_ram_gb"):
            value = data.get(name)
            if name in data and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0):
                issues.append(
                    ModelValidationIssue(
                        "invalid_field_type",
                        f"Feld '{name}' muss eine nichtnegative Zahl sein.",
                        field=name,
                        path=source_text,
                    )
                )
        if "supports" in data and not isinstance(data["supports"], list):
            issues.append(
                ModelValidationIssue(
                    "invalid_field_type",
                    "Feld 'supports' muss eine Liste sein.",
                    field="supports",
                    path=source_text,
                )
            )
        if "capabilities" in data and not isinstance(data["capabilities"], dict):
            issues.append(
                ModelValidationIssue(
                    "invalid_field_type",
                    "Feld 'capabilities' muss ein Objekt sein.",
                    field="capabilities",
                    path=source_text,
                )
            )

        schema_version = data.get("schema_version", MODEL_METADATA_SCHEMA_VERSION)
        if schema_version != MODEL_METADATA_SCHEMA_VERSION:
            issues.append(
                ModelValidationIssue(
                    "unsupported_schema",
                    f"Nicht unterstützte Modell-Schemaversion: {schema_version}.",
                    field="schema_version",
                    path=source_text,
                )
            )

        backend_names = set(available_backends or ())
        preferred = data.get("recommended_backend")
        if backend_names and isinstance(preferred, str) and preferred not in backend_names:
            issues.append(
                ModelValidationIssue(
                    "backend_incompatible",
                    f"Empfohlenes Backend '{preferred}' ist nicht registriert.",
                    field="recommended_backend",
                    path=source_text,
                )
            )

        normalized = deepcopy(data)
        normalized["schema_version"] = MODEL_METADATA_SCHEMA_VERSION
        valid = not any(
            issue.code != "backend_incompatible" for issue in issues
        )
        status = (
            ModelHealthStatus.INSTALLED
            if valid and normalized.get("installed") is True
            else ModelHealthStatus.AVAILABLE
            if valid
            else ModelHealthStatus.INVALID
        )
        return ModelValidationResult(
            model_id=model_id,
            status=status,
            valid=valid,
            metadata=normalized if valid else None,
            issues=issues,
        )

    def validate_installation(
        self,
        model: dict[str, Any],
        *,
        verify_hashes: bool = False,
    ) -> ModelValidationResult:
        model_id = str(model.get("id") or "")
        if model.get("installed") is not True:
            return ModelValidationResult(
                model_id=model_id,
                status=ModelHealthStatus.NOT_INSTALLED,
                valid=True,
                metadata=deepcopy(model),
            )

        issues: list[ModelValidationIssue] = []
        checked_hashes = 0
        path_value = str(model.get("path") or "").strip()
        base = Path(path_value) if path_value else None
        if base is None or not base.exists():
            issues.append(
                ModelValidationIssue(
                    "installation_missing",
                    "Installationspfad fehlt oder existiert nicht.",
                    field="path",
                    path=path_value or None,
                )
            )
        elif not base.is_dir():
            issues.append(
                ModelValidationIssue(
                    "installation_not_directory",
                    "Installationspfad ist kein Verzeichnis.",
                    field="path",
                    path=str(base),
                )
            )
        else:
            manifest_path = base / "package.json"
            if manifest_path.exists():
                manifest_issues, checked_hashes = self._validate_manifest(
                    base, manifest_path, model_id, verify_hashes
                )
                issues.extend(manifest_issues)
            else:
                required_files = model.get("required_files", [])
                if isinstance(required_files, list):
                    for relative in required_files:
                        target = self._safe_child(base, relative)
                        if target is None or not target.exists():
                            issues.append(
                                ModelValidationIssue(
                                    "required_file_missing",
                                    f"Erforderliche Modelldatei fehlt: {relative}",
                                    path=str(relative),
                                )
                            )

        valid = not issues
        return ModelValidationResult(
            model_id=model_id,
            status=ModelHealthStatus.READY if valid else ModelHealthStatus.INVALID,
            valid=valid,
            metadata=deepcopy(model),
            issues=issues,
            checked_hashes=checked_hashes,
        )

    def validate_source(self, source_path: str | Path) -> ModelValidationResult:
        source = Path(source_path)
        issues: list[ModelValidationIssue] = []
        if not source.exists():
            issues.append(ModelValidationIssue("source_missing", "Modellquelle existiert nicht.", path=str(source)))
        elif source.is_file():
            if source.suffix.lower() not in ALLOWED_MODEL_EXTENSIONS:
                issues.append(ModelValidationIssue("unsupported_file", "Dateityp der Modellquelle wird nicht unterstützt.", path=str(source)))
            elif source.stat().st_size <= 0:
                issues.append(ModelValidationIssue("empty_file", "Modelldatei ist leer.", path=str(source)))
        elif source.is_dir():
            files = [item for item in source.rglob("*") if item.is_file()]
            if not any(item.suffix.lower() in ALLOWED_MODEL_EXTENSIONS for item in files):
                issues.append(ModelValidationIssue("model_files_missing", "Verzeichnis enthält keine unterstützten Modelldateien.", path=str(source)))
        else:
            issues.append(ModelValidationIssue("invalid_source", "Modellquelle ist weder Datei noch Verzeichnis.", path=str(source)))
        return ModelValidationResult(
            model_id=source.stem,
            status=ModelHealthStatus.READY if not issues else ModelHealthStatus.INVALID,
            valid=not issues,
            issues=issues,
        )

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        return self._models.get(model_id)

    def get_all_models(self) -> list[dict[str, Any]]:
        return list(self._models.values())

    def get_report(self, model_id: str) -> ModelValidationResult | None:
        return self._reports.get(model_id)

    def get_invalid_reports(self) -> dict[str, ModelValidationResult]:
        return {
            source: report
            for source, report in self._source_reports.items()
            if not report.valid
        }

    @staticmethod
    def _safe_child(base: Path, relative: Any) -> Path | None:
        if not isinstance(relative, str) or not relative.strip():
            return None
        try:
            base_resolved = base.resolve()
            target = (base / relative).resolve()
            target.relative_to(base_resolved)
            return target
        except (OSError, ValueError):
            return None

    def _validate_manifest(
        self,
        base: Path,
        manifest_path: Path,
        model_id: str,
        verify_hashes: bool,
    ) -> tuple[list[ModelValidationIssue], int]:
        issues: list[ModelValidationIssue] = []
        checked_hashes = 0
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return [
                ModelValidationIssue(
                    "manifest_unreadable",
                    f"Manifest package.json ist nicht lesbar: {error}",
                    path=str(manifest_path),
                )
            ], 0
        if not isinstance(manifest, dict):
            return [ModelValidationIssue("manifest_type", "Manifest muss ein JSON-Objekt sein.", path=str(manifest_path))], 0

        manifest_id = str(
            manifest.get("model_id") or manifest.get("package_id") or manifest.get("id") or ""
        )
        if manifest_id and manifest_id != model_id:
            issues.append(
                ModelValidationIssue(
                    "manifest_id_mismatch",
                    f"Manifest-ID '{manifest_id}' stimmt nicht mit '{model_id}' überein.",
                    field="model_id",
                    path=str(manifest_path),
                )
            )
        components = manifest.get("components", {})
        if not isinstance(components, dict):
            issues.append(ModelValidationIssue("components_type", "Manifest-Komponenten müssen ein Objekt sein.", field="components"))
            return issues, checked_hashes

        for name, declaration in components.items():
            if not isinstance(declaration, dict):
                issues.append(ModelValidationIssue("component_type", f"Komponente '{name}' muss ein Objekt sein.", field=str(name)))
                continue
            relative = declaration.get("path")
            target = self._safe_child(base, relative)
            if target is None:
                issues.append(ModelValidationIssue("unsafe_component_path", f"Komponente '{name}' hat einen ungültigen Pfad.", field=str(name)))
                continue
            optional = declaration.get("optional") is True
            if not target.exists() and not optional:
                issues.append(ModelValidationIssue("component_missing", f"Komponente '{name}' fehlt.", field=str(name), path=str(target)))
                continue
            expected_hash = declaration.get("sha256") or declaration.get("checksum")
            if verify_hashes and target.is_file() and expected_hash:
                normalized_hash = str(expected_hash).lower().removeprefix("sha256:")
                if len(normalized_hash) != 64 or any(char not in "0123456789abcdef" for char in normalized_hash):
                    issues.append(ModelValidationIssue("hash_invalid", f"SHA-256 für Komponente '{name}' ist ungültig.", field=str(name)))
                    continue
                actual_hash = self._sha256(target)
                checked_hashes += 1
                if actual_hash != normalized_hash:
                    issues.append(ModelValidationIssue("hash_mismatch", f"SHA-256 für Komponente '{name}' stimmt nicht überein.", field=str(name), path=str(target)))
        return issues, checked_hashes

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
