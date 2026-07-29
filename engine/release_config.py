from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RELEASE_CONFIG_PATH = Path(__file__).resolve().parents[1] / "release.json"


@dataclass(frozen=True)
class ReleaseConfig:
    app_name: str
    display_version: str
    package_version: str
    build: str
    codename: str
    publisher: str
    architecture: str
    executable_name: str

    @classmethod
    def load(cls, path: str | Path = RELEASE_CONFIG_PATH) -> "ReleaseConfig":
        source = Path(path)
        raw: Any = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Release-Konfiguration muss ein JSON-Objekt sein.")
        required = {field_name for field_name in cls.__dataclass_fields__}
        missing = sorted(required - raw.keys())
        if missing:
            raise ValueError(
                "Release-Konfiguration unvollständig: " + ", ".join(missing)
            )
        values = {key: str(raw[key]).strip() for key in required}
        if any(not value for value in values.values()):
            raise ValueError("Release-Konfiguration enthält leere Pflichtwerte.")
        if values["architecture"].casefold() != "arm64":
            raise ValueError("Release-Architektur muss ARM64 sein.")
        return cls(**values)


RELEASE = ReleaseConfig.load()
