from __future__ import annotations

import json
import logging
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


logger = logging.getLogger("ConfigurationManager")

CURRENT_SCHEMA_VERSION = 2

DEFAULT_PREFERENCES: dict[str, Any] = {
    "schema_version": CURRENT_SCHEMA_VERSION,
    "active_model_id": None,
    "hf_token": "",
    "thread_count": "Auto",
    "execution_provider": "QNN EP",
    "hardware_accel": "True",
    "output_dir": r"C:\SnapdragonAI\output",
    "models_dir": r"C:\SnapdragonAI\models",
    "theme": "Dunkel",
    "language": "Deutsch",
}


@dataclass(frozen=True)
class ConfigurationValidation:
    values: dict[str, Any]
    errors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        return not self.errors


class ConfigurationManager:
    """Versionierte, validierte und atomare Verwaltung einer JSON-Konfiguration."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self, *, persist_migration: bool = True) -> dict[str, Any]:
        if not self.path.is_file():
            return deepcopy(DEFAULT_PREFERENCES)
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            logger.error("Konfiguration konnte nicht gelesen werden: %s", error)
            return deepcopy(DEFAULT_PREFERENCES)
        if not isinstance(raw, dict):
            logger.error("Konfigurationswurzel muss ein JSON-Objekt sein.")
            return deepcopy(DEFAULT_PREFERENCES)

        migrated, changed = self.migrate(raw)
        validation = self.validate(migrated)
        if validation.errors:
            logger.warning(
                "Konfigurationswerte wurden korrigiert: %s",
                "; ".join(validation.errors),
            )
            changed = True
        if persist_migration and changed:
            self._write_atomic(validation.values)
        return validation.values

    def save(self, values: dict[str, Any], *, merge: bool = True) -> bool:
        if not isinstance(values, dict):
            return False
        current = self.load() if merge else deepcopy(DEFAULT_PREFERENCES)
        current.update(values)
        validation = self.validate(current)
        if validation.errors:
            logger.warning(
                "Ungültige Konfigurationswerte wurden normalisiert: %s",
                "; ".join(validation.errors),
            )
        return self._write_atomic(validation.values)

    @staticmethod
    def migrate(values: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        migrated = deepcopy(values)
        changed = False
        version = migrated.get("schema_version", migrated.get("version", 0))
        try:
            version = int(version)
        except (TypeError, ValueError):
            version = 0

        if version < 1:
            nested = migrated.pop("settings", None)
            if isinstance(nested, dict):
                for key, value in nested.items():
                    migrated.setdefault(key, value)
            if "model_id" in migrated and "active_model_id" not in migrated:
                migrated["active_model_id"] = migrated.pop("model_id")
            if "hf_access_token" in migrated and "hf_token" not in migrated:
                migrated["hf_token"] = migrated.pop("hf_access_token")
            version = 1
            changed = True

        if version < 2:
            hardware_accel = migrated.get("hardware_accel")
            if isinstance(hardware_accel, bool):
                migrated["hardware_accel"] = str(hardware_accel)
            thread_count = migrated.get("thread_count")
            if isinstance(thread_count, int):
                migrated["thread_count"] = str(thread_count)
            version = 2
            changed = True

        if version > CURRENT_SCHEMA_VERSION:
            logger.warning(
                "Konfigurationsschema %s ist neuer als unterstütztes Schema %s.",
                version,
                CURRENT_SCHEMA_VERSION,
            )
        migrated.pop("version", None)
        if migrated.get("schema_version") != CURRENT_SCHEMA_VERSION:
            migrated["schema_version"] = CURRENT_SCHEMA_VERSION
            changed = True
        return migrated, changed

    @staticmethod
    def validate(values: dict[str, Any]) -> ConfigurationValidation:
        validated = deepcopy(values)
        errors: list[str] = []
        validated["schema_version"] = CURRENT_SCHEMA_VERSION

        def string_value(key: str, *, allow_empty: bool = True) -> str:
            value = validated.get(key, DEFAULT_PREFERENCES[key])
            if value is None and key == "active_model_id":
                return ""
            if not isinstance(value, str):
                errors.append(f"{key}: Zeichenkette erwartet")
                value = str(value) if value is not None else ""
            value = value.strip()
            if not allow_empty and not value:
                errors.append(f"{key}: leerer Wert nicht zulässig")
                return str(DEFAULT_PREFERENCES[key])
            return value

        active_model = validated.get("active_model_id")
        if active_model is not None and not isinstance(active_model, str):
            errors.append("active_model_id: Zeichenkette oder null erwartet")
            active_model = str(active_model)
        validated["active_model_id"] = active_model.strip() if isinstance(active_model, str) else None
        validated["hf_token"] = string_value("hf_token")

        thread_count = validated.get("thread_count", "Auto")
        if isinstance(thread_count, int):
            thread_count = str(thread_count)
        if not isinstance(thread_count, str):
            errors.append("thread_count: 'Auto' oder Ganzzahl erwartet")
            thread_count = "Auto"
        if thread_count != "Auto":
            try:
                number = int(thread_count)
                if not 1 <= number <= 256:
                    raise ValueError
                thread_count = str(number)
            except ValueError:
                errors.append("thread_count: Wert muss zwischen 1 und 256 liegen")
                thread_count = "Auto"
        validated["thread_count"] = thread_count

        provider = string_value("execution_provider", allow_empty=False)
        allowed_providers = {"QNN EP", "CPU EP", "ONNX Runtime", "CPU", "Auto"}
        if provider not in allowed_providers:
            errors.append("execution_provider: unbekannter Provider")
            provider = str(DEFAULT_PREFERENCES["execution_provider"])
        validated["execution_provider"] = provider

        hardware_accel = validated.get("hardware_accel", "True")
        if isinstance(hardware_accel, bool):
            hardware_accel = str(hardware_accel)
        if str(hardware_accel).casefold() not in {"true", "false"}:
            errors.append("hardware_accel: boolescher Wert erwartet")
            hardware_accel = DEFAULT_PREFERENCES["hardware_accel"]
        validated["hardware_accel"] = (
            "True" if str(hardware_accel).casefold() == "true" else "False"
        )

        validated["output_dir"] = string_value("output_dir", allow_empty=False)
        validated["models_dir"] = string_value("models_dir", allow_empty=False)

        theme = string_value("theme", allow_empty=False)
        if theme not in {"Dunkel", "Hell", "Dark", "Light"}:
            errors.append("theme: unbekanntes Theme")
            theme = str(DEFAULT_PREFERENCES["theme"])
        validated["theme"] = theme

        language = string_value("language", allow_empty=False)
        if language not in {"Deutsch", "English", "de_DE", "en_US"}:
            errors.append("language: unbekannte Sprache")
            language = str(DEFAULT_PREFERENCES["language"])
        validated["language"] = language
        return ConfigurationValidation(values=validated, errors=tuple(errors))

    def _write_atomic(self, values: dict[str, Any]) -> bool:
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path.write_text(
                json.dumps(values, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            temporary_path.replace(self.path)
            return True
        except OSError as error:
            logger.error("Konfiguration konnte nicht gespeichert werden: %s", error)
            temporary_path.unlink(missing_ok=True)
            return False
