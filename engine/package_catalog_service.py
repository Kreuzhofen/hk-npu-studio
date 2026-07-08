from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import BASE

logger = logging.getLogger("PackageCatalogService")


@dataclass(frozen=True)
class PackageCatalogEntry:
    model_id: str
    display_name: str
    version: str
    description: str
    package_type: str
    capabilities: dict[str, Any]
    recommended_runtime: str
    estimated_size_gb: float
    download_url: str
    checksum: str | None = None
    status: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PackageCatalogEntry":
        required = {
            "model_id",
            "display_name",
            "version",
            "description",
            "package_type",
            "capabilities",
            "recommended_runtime",
            "estimated_size_gb",
            "download_url",
        }
        missing = sorted(required - set(data))
        if missing:
            raise ValueError(f"Catalog entry is missing required fields: {', '.join(missing)}")

        return cls(
            model_id=str(data["model_id"]),
            display_name=str(data["display_name"]),
            version=str(data["version"]),
            description=str(data["description"]),
            package_type=str(data["package_type"]),
            capabilities=dict(data["capabilities"]),
            recommended_runtime=str(data["recommended_runtime"]),
            estimated_size_gb=float(data["estimated_size_gb"]),
            download_url=str(data["download_url"]),
            checksum=str(data["checksum"]) if data.get("checksum") else None,
            status=str(data["status"]) if data.get("status") else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "version": self.version,
            "description": self.description,
            "package_type": self.package_type,
            "capabilities": self.capabilities,
            "recommended_runtime": self.recommended_runtime,
            "estimated_size_gb": self.estimated_size_gb,
            "download_url": self.download_url,
            "checksum": self.checksum,
            "status": self.status,
        }


class PackageCatalogService:
    """
    Loads the local AI package catalog from resources/package_catalog.json.
    No network access or downloads are performed here.
    """

    def __init__(self, catalog_path: Path | None = None) -> None:
        self.catalog_path = catalog_path or (BASE / "resources" / "package_catalog.json")
        self._entries: dict[str, PackageCatalogEntry] = {}
        self.load_catalog()

    def load_catalog(self) -> None:
        self._entries.clear()
        if not self.catalog_path.exists():
            logger.warning("Package catalog not found: %s", self.catalog_path)
            return

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as catalog_file:
                data = json.load(catalog_file)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load package catalog '%s': %s", self.catalog_path, exc)
            return

        raw_entries = data.get("packages", data if isinstance(data, list) else [])
        if not isinstance(raw_entries, list):
            logger.error("Package catalog root must be a list or contain a 'packages' list.")
            return

        for raw_entry in raw_entries:
            if not isinstance(raw_entry, dict):
                logger.warning("Skipping non-object package catalog entry.")
                continue
            try:
                entry = PackageCatalogEntry.from_dict(raw_entry)
            except (TypeError, ValueError) as exc:
                logger.warning("Skipping invalid package catalog entry: %s", exc)
                continue
            self._entries[entry.model_id] = entry

    def list_packages(self) -> list[dict[str, Any]]:
        return [entry.to_dict() for entry in self._entries.values()]

    def get_package(self, model_id: str) -> dict[str, Any] | None:
        entry = self._entries.get(model_id)
        return entry.to_dict() if entry else None

    def get_entry(self, model_id: str) -> PackageCatalogEntry | None:
        return self._entries.get(model_id)

    def has_package(self, model_id: str) -> bool:
        return model_id in self._entries
