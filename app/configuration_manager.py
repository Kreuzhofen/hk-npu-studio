from __future__ import annotations

import json
import logging
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


logger = logging.getLogger("ConfigurationManager")

CURRENT_SCHEMA_VERSION = 3

DEFAULT_GENERATION_SETTINGS: dict[str, Any] = {
    "prompt": "",
    "negative_prompt": "",
    "model_name": "stable_diffusion_v3_5_qai",
    "seed": -1,
    "steps": 20,
    "cfg_scale": 7.5,
    "width": 512,
    "height": 512,
    "sampler": "Euler",
    "scheduler": "Normal",
    "batch_size": 1,
    "upscale_profile": "off",
    "controlnet_enabled": False,
    "canny_low_threshold": 50,
    "canny_high_threshold": 150,
    "controlnet_conditioning_scale": 1.0,
    "input_image_path": None,
    "phoenix_boost_enabled": False,
}

DEFAULT_PREFERENCES: dict[str, Any] = {
    "schema_version": CURRENT_SCHEMA_VERSION,
    "active_model_id": None,
    "hf_token": "",
    "thread_count": "Auto",
    "execution_provider": "QNN EP",
    "hardware_accel": "True",
    "output_dir": "",
    "models_dir": "",
    "theme": "Dunkel",
    "language": "Deutsch",
    "last_prompt": "",
    "last_negative_prompt": "",
    "generation_settings": deepcopy(DEFAULT_GENERATION_SETTINGS),
}


def _default_preferences() -> dict[str, Any]:
    """Resolve path defaults lazily to avoid config's initialization cycle."""
    from config import MODELS_DIR, OUTPUT_DIR

    defaults = deepcopy(DEFAULT_PREFERENCES)
    defaults["output_dir"] = str(OUTPUT_DIR)
    defaults["models_dir"] = str(MODELS_DIR)
    defaults["generation_settings"] = deepcopy(DEFAULT_GENERATION_SETTINGS)
    return defaults


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
            return _default_preferences()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            logger.error("Konfiguration konnte nicht gelesen werden: %s", error)
            return _default_preferences()
        if not isinstance(raw, dict):
            logger.error("Konfigurationswurzel muss ein JSON-Objekt sein.")
            return _default_preferences()

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
        current = self.load() if merge else _default_preferences()
        current.update(values)
        validation = self.validate(current)
        if validation.errors:
            logger.warning(
                "Ungültige Konfigurationswerte wurden normalisiert: %s",
                "; ".join(validation.errors),
            )
        return self._write_atomic(validation.values)

    @classmethod
    def validate_generation_settings(
        cls, settings: dict[str, Any]
    ) -> tuple[dict[str, Any], list[str]]:
        """Validiert und normalisiert die Generierungseinstellungen robust."""
        validated = deepcopy(settings) if isinstance(settings, dict) else {}
        errors: list[str] = []
        defaults = DEFAULT_GENERATION_SETTINGS

        # String fields
        for key in ("prompt", "negative_prompt"):
            val = validated.get(key, defaults[key])
            if not isinstance(val, str):
                errors.append(f"generation_settings.{key}: Zeichenkette erwartet")
                val = str(val) if val is not None else ""
            validated[key] = val

        # Model name
        model_name = validated.get("model_name", defaults["model_name"])
        if model_name is not None and not isinstance(model_name, str):
            errors.append("generation_settings.model_name: Zeichenkette oder None erwartet")
            model_name = str(model_name)
        validated["model_name"] = model_name.strip() if isinstance(model_name, str) else None

        # Numeric: seed
        seed_val = validated.get("seed", defaults["seed"])
        try:
            validated["seed"] = int(seed_val)
        except (TypeError, ValueError):
            errors.append("generation_settings.seed: Ganzzahl erwartet")
            validated["seed"] = defaults["seed"]

        # Numeric: steps
        steps_val = validated.get("steps", defaults["steps"])
        try:
            steps = int(steps_val)
            if not 1 <= steps <= 500:
                errors.append("generation_settings.steps: Wert muss zwischen 1 und 500 liegen")
                steps = defaults["steps"]
            validated["steps"] = steps
        except (TypeError, ValueError):
            errors.append("generation_settings.steps: Ganzzahl erwartet")
            validated["steps"] = defaults["steps"]

        # Numeric: cfg_scale (or cfg)
        cfg_val = validated.get("cfg_scale", validated.get("cfg", defaults["cfg_scale"]))
        try:
            cfg = float(cfg_val)
            if not 0.0 <= cfg <= 50.0:
                errors.append("generation_settings.cfg_scale: Wert muss zwischen 0.0 und 50.0 liegen")
                cfg = defaults["cfg_scale"]
            validated["cfg_scale"] = round(cfg, 2)
        except (TypeError, ValueError):
            errors.append("generation_settings.cfg_scale: Gleitkommazahl erwartet")
            validated["cfg_scale"] = defaults["cfg_scale"]
        validated.pop("cfg", None)

        # Resolution: width & height
        for res_key in ("width", "height"):
            res_val = validated.get(res_key, defaults[res_key])
            try:
                res = int(res_val)
                if not 64 <= res <= 4096:
                    errors.append(f"generation_settings.{res_key}: Wert muss zwischen 64 und 4096 liegen")
                    res = defaults[res_key]
                validated[res_key] = res
            except (TypeError, ValueError):
                errors.append(f"generation_settings.{res_key}: Ganzzahl erwartet")
                validated[res_key] = defaults[res_key]

        # Sampler & Scheduler
        for opt_key in ("sampler", "scheduler"):
            opt_val = validated.get(opt_key, defaults[opt_key])
            if not isinstance(opt_val, str) or not opt_val.strip():
                errors.append(f"generation_settings.{opt_key}: nicht-leere Zeichenkette erwartet")
                opt_val = defaults[opt_key]
            validated[opt_key] = opt_val.strip()

        # batch_size (or batch / batch_count)
        batch_val = validated.get(
            "batch_size",
            validated.get("batch", validated.get("batch_count", defaults["batch_size"])),
        )
        try:
            batch = int(batch_val)
            if not 1 <= batch <= 16:
                errors.append("generation_settings.batch_size: Wert muss zwischen 1 und 16 liegen")
                batch = defaults["batch_size"]
            validated["batch_size"] = batch
        except (TypeError, ValueError):
            errors.append("generation_settings.batch_size: Ganzzahl erwartet")
            validated["batch_size"] = defaults["batch_size"]
        validated.pop("batch", None)
        validated.pop("batch_count", None)

        # upscale_profile
        upscale_val = validated.get("upscale_profile", defaults["upscale_profile"])
        if upscale_val is True:
            upscale_val = "2"
        elif upscale_val is False or upscale_val is None:
            upscale_val = "off"
        elif str(upscale_val) not in {"off", "2", "4"}:
            errors.append("generation_settings.upscale_profile: ungültiges Profil")
            upscale_val = defaults["upscale_profile"]
        validated["upscale_profile"] = str(upscale_val)

        # controlnet_enabled
        validated["controlnet_enabled"] = bool(
            validated.get("controlnet_enabled", defaults["controlnet_enabled"])
        )

        # canny thresholds
        for canny_key in ("canny_low_threshold", "canny_high_threshold"):
            canny_val = validated.get(canny_key, defaults[canny_key])
            try:
                canny = int(canny_val)
                if not 0 <= canny <= 255:
                    errors.append(f"generation_settings.{canny_key}: Wert muss zwischen 0 und 255 liegen")
                    canny = defaults[canny_key]
                validated[canny_key] = canny
            except (TypeError, ValueError):
                errors.append(f"generation_settings.{canny_key}: Ganzzahl erwartet")
                validated[canny_key] = defaults[canny_key]

        # controlnet_conditioning_scale
        scale_val = validated.get(
            "controlnet_conditioning_scale", defaults["controlnet_conditioning_scale"]
        )
        try:
            scale = float(scale_val)
            if not 0.0 <= scale <= 2.0:
                errors.append(
                    "generation_settings.controlnet_conditioning_scale: Wert muss zwischen 0.0 und 2.0 liegen"
                )
                scale = defaults["controlnet_conditioning_scale"]
            validated["controlnet_conditioning_scale"] = round(scale, 2)
        except (TypeError, ValueError):
            errors.append("generation_settings.controlnet_conditioning_scale: Gleitkommazahl erwartet")
            validated["controlnet_conditioning_scale"] = defaults["controlnet_conditioning_scale"]

        # input_image_path / reference_image_path
        img_path = validated.get(
            "input_image_path",
            validated.get("reference_image_path", defaults["input_image_path"]),
        )
        if img_path is not None and not isinstance(img_path, str):
            errors.append("generation_settings.input_image_path: Zeichenkette oder None erwartet")
            img_path = str(img_path)
        validated["input_image_path"] = img_path if img_path else None
        validated.pop("reference_image_path", None)

        # phoenix_boost_enabled
        validated["phoenix_boost_enabled"] = bool(
            validated.get("phoenix_boost_enabled", defaults["phoenix_boost_enabled"])
        )

        return validated, errors

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

        if version < 3:
            gen = migrated.get("generation_settings")
            if not isinstance(gen, dict):
                gen = deepcopy(DEFAULT_GENERATION_SETTINGS)
                if "last_prompt" in migrated:
                    gen["prompt"] = str(migrated["last_prompt"])
                if "last_negative_prompt" in migrated:
                    gen["negative_prompt"] = str(migrated["last_negative_prompt"])
                if "active_model_id" in migrated and migrated["active_model_id"]:
                    gen["model_name"] = str(migrated["active_model_id"])
                migrated["generation_settings"] = gen
                changed = True
            else:
                for k, v in DEFAULT_GENERATION_SETTINGS.items():
                    if k not in gen:
                        gen[k] = deepcopy(v)
                        changed = True
            version = 3
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

    @classmethod
    def validate(cls, values: dict[str, Any]) -> ConfigurationValidation:
        defaults = _default_preferences()
        validated = deepcopy(values)
        errors: list[str] = []
        validated["schema_version"] = CURRENT_SCHEMA_VERSION

        def string_value(key: str, *, allow_empty: bool = True) -> str:
            value = validated.get(key, defaults.get(key, ""))
            if value is None and key == "active_model_id":
                return ""
            if not isinstance(value, str):
                errors.append(f"{key}: Zeichenkette erwartet")
                value = str(value) if value is not None else ""
            value = value.strip()
            if not allow_empty and not value:
                errors.append(f"{key}: leerer Wert nicht zulässig")
                return str(defaults.get(key, ""))
            return value

        active_model = validated.get("active_model_id")
        if active_model is not None and not isinstance(active_model, str):
            errors.append("active_model_id: Zeichenkette oder null erwartet")
            active_model = str(active_model)
        validated["active_model_id"] = (
            active_model.strip() if isinstance(active_model, str) else None
        )
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
            provider = str(defaults["execution_provider"])
        validated["execution_provider"] = provider

        hardware_accel = validated.get("hardware_accel", "True")
        if isinstance(hardware_accel, bool):
            hardware_accel = str(hardware_accel)
        if str(hardware_accel).casefold() not in {"true", "false"}:
            errors.append("hardware_accel: boolescher Wert erwartet")
            hardware_accel = defaults["hardware_accel"]
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
        if language not in {"Deutsch", "English", "Español", "de_DE", "en_US", "es_ES"}:
            errors.append("language: unbekannte Sprache")
            language = str(DEFAULT_PREFERENCES["language"])
        validated["language"] = language

        # Validate and sync generation_settings
        gen_raw = validated.get("generation_settings", defaults.get("generation_settings", {}))
        valid_gen, gen_errors = cls.validate_generation_settings(gen_raw)
        errors.extend(gen_errors)

        # Synchronize direct top-level modifications
        if "last_prompt" in values and "generation_settings" not in values:
            valid_gen["prompt"] = string_value("last_prompt")
        if "last_negative_prompt" in values and "generation_settings" not in values:
            valid_gen["negative_prompt"] = string_value("last_negative_prompt")
        if "active_model_id" in values and "generation_settings" not in values:
            if validated["active_model_id"]:
                valid_gen["model_name"] = validated["active_model_id"]

        validated["generation_settings"] = valid_gen
        validated["last_prompt"] = valid_gen["prompt"]
        validated["last_negative_prompt"] = valid_gen["negative_prompt"]
        if valid_gen.get("model_name") and not validated.get("active_model_id"):
            validated["active_model_id"] = valid_gen["model_name"]
        elif validated.get("active_model_id") and not valid_gen.get("model_name"):
            valid_gen["model_name"] = validated["active_model_id"]

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
