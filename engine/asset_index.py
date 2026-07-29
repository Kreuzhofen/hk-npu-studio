"""Rebuildable local metadata index for filesystem-backed creative assets."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, fields
import datetime as dt
import logging
import os
from pathlib import Path
import sqlite3
import time
from typing import Any, Iterable, Iterator

from PIL import Image

from config import ASSET_INDEX_DB, OUTPUT_DIR
from engine.asset_files import read_asset_metadata


LOGGER = logging.getLogger(__name__)
SCHEMA_VERSION = 1
SUPPORTED_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})


@dataclass(frozen=True)
class AssetRecord:
    """Immutable, media-neutral representation of one indexed filesystem asset."""

    asset_id: int | None
    canonical_path: str
    filename: str
    extension: str
    asset_type: str
    media_type: str
    file_size: int
    file_created_at: int
    file_modified_at: int
    indexed_at: str
    width: int | None = None
    height: int | None = None
    sidecar_path: str | None = None
    sidecar_modified_at: int | None = None
    prompt: str | None = None
    negative_prompt: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    seed: int | None = None
    steps: int | None = None
    cfg_scale: float | None = None
    sampler: str | None = None
    scheduler: str | None = None
    backend: str | None = None
    device: str | None = None
    favorite: bool = False
    rating: int = 0
    missing: bool = False


@dataclass(frozen=True)
class ScanResult:
    discovered: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    missing: int = 0
    errors: int = 0
    duration: float = 0.0


class AssetIndexRepository:
    """SQLite persistence boundary for the reproducible asset index."""

    _COLUMNS = tuple(field.name for field in fields(AssetRecord))
    _WRITE_COLUMNS = tuple(column for column in _COLUMNS if column != "asset_id")

    def __init__(self, database_path: str | Path = ASSET_INDEX_DB) -> None:
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_info (
                    version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id INTEGER PRIMARY KEY,
                    canonical_path TEXT NOT NULL UNIQUE,
                    filename TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_created_at INTEGER NOT NULL,
                    file_modified_at INTEGER NOT NULL,
                    indexed_at TEXT NOT NULL,
                    width INTEGER,
                    height INTEGER,
                    sidecar_path TEXT,
                    sidecar_modified_at INTEGER,
                    prompt TEXT,
                    negative_prompt TEXT,
                    model_id TEXT,
                    model_version TEXT,
                    seed INTEGER,
                    steps INTEGER,
                    cfg_scale REAL,
                    sampler TEXT,
                    scheduler TEXT,
                    backend TEXT,
                    device TEXT,
                    favorite INTEGER NOT NULL DEFAULT 0 CHECK (favorite IN (0, 1)),
                    rating INTEGER NOT NULL DEFAULT 0 CHECK (rating BETWEEN 0 AND 5),
                    missing INTEGER NOT NULL DEFAULT 0 CHECK (missing IN (0, 1))
                );
                CREATE INDEX IF NOT EXISTS idx_assets_media_missing
                    ON assets(media_type, missing);
                """
            )
            row = connection.execute("SELECT version FROM schema_info LIMIT 1").fetchone()
            if row is None:
                connection.execute("INSERT INTO schema_info(version) VALUES (?)", (SCHEMA_VERSION,))
            elif row[0] != SCHEMA_VERSION:
                raise RuntimeError(f"Unsupported asset index schema version: {row[0]}")

    def schema_version(self) -> int:
        self.initialize()
        with self._connect() as connection:
            return int(connection.execute("SELECT version FROM schema_info LIMIT 1").fetchone()[0])

    def get_by_path(self, canonical_path: str) -> AssetRecord | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT {', '.join(self._COLUMNS)} FROM assets WHERE canonical_path = ?",
                (canonical_path,),
            ).fetchone()
        return self._to_record(row) if row else None

    def list_assets(self, include_missing: bool = False) -> list[AssetRecord]:
        self.initialize()
        query = f"SELECT {', '.join(self._COLUMNS)} FROM assets"
        parameters: tuple[object, ...] = ()
        if not include_missing:
            query += " WHERE missing = ?"
            parameters = (0,)
        query += " ORDER BY filename COLLATE NOCASE, canonical_path"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._to_record(row) for row in rows]

    def upsert(self, record: AssetRecord) -> bool:
        """Insert or refresh metadata while preserving user-managed favorite/rating."""
        self.initialize()
        values = [self._db_value(getattr(record, column)) for column in self._WRITE_COLUMNS]
        update_columns = [
            column for column in self._WRITE_COLUMNS if column not in {"canonical_path", "favorite", "rating"}
        ]
        placeholders = ", ".join("?" for _ in self._WRITE_COLUMNS)
        updates = ", ".join(f"{column} = excluded.{column}" for column in update_columns)
        with self._connect() as connection:
            existed = connection.execute(
                "SELECT 1 FROM assets WHERE canonical_path = ?", (record.canonical_path,)
            ).fetchone() is not None
            connection.execute(
                f"INSERT INTO assets ({', '.join(self._WRITE_COLUMNS)}) VALUES ({placeholders}) "
                f"ON CONFLICT(canonical_path) DO UPDATE SET {updates}",
                values,
            )
        return not existed

    def mark_missing_except(self, root: str | Path, seen_paths: Iterable[str]) -> int:
        root_prefix = _canonical_path(root)
        if not root_prefix.endswith(os.sep):
            root_prefix += os.sep
        seen = set(seen_paths)
        changed = 0
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT canonical_path FROM assets WHERE missing = ?", (0,)
            ).fetchall()
            for row in rows:
                path = str(row[0])
                if path.startswith(root_prefix) and path not in seen:
                    changed += connection.execute(
                        "UPDATE assets SET missing = ? WHERE canonical_path = ?", (1, path)
                    ).rowcount
        return changed

    def rebuild(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("DROP TABLE IF EXISTS assets")
            connection.execute("DROP TABLE IF EXISTS schema_info")
        self.initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _db_value(value: object) -> object:
        return int(value) if isinstance(value, bool) else value

    @staticmethod
    def _to_record(row: sqlite3.Row) -> AssetRecord:
        values = dict(row)
        values["favorite"] = bool(values["favorite"])
        values["missing"] = bool(values["missing"])
        return AssetRecord(**values)


class AssetScanner:
    """Deterministically synchronizes a filesystem tree into an asset repository."""

    def __init__(self, repository: AssetIndexRepository | None = None) -> None:
        self.repository = repository or AssetIndexRepository()

    def scan(self, root: str | Path = OUTPUT_DIR, rebuild: bool = False) -> ScanResult:
        started = time.perf_counter()
        root_path = Path(root)
        if rebuild:
            self.repository.rebuild()
        else:
            self.repository.initialize()

        paths = self._discover(root_path)
        counts = {"inserted": 0, "updated": 0, "unchanged": 0, "errors": 0}
        seen: set[str] = set()
        for path in paths:
            canonical_path = _canonical_path(path)
            seen.add(canonical_path)
            try:
                stat = path.stat()
                sidecar = path.with_suffix(".json")
                sidecar_mtime = sidecar.stat().st_mtime_ns if sidecar.is_file() else None
                current = self.repository.get_by_path(canonical_path)
                if (
                    current
                    and not current.missing
                    and current.file_size == stat.st_size
                    and current.file_modified_at == stat.st_mtime_ns
                    and current.sidecar_modified_at == sidecar_mtime
                ):
                    counts["unchanged"] += 1
                    continue
                record, metadata_error = self._read_asset(
                    path,
                    stat,
                    sidecar if sidecar.is_file() else None,
                    sidecar_mtime,
                )
                inserted = self.repository.upsert(record)
                counts["inserted" if inserted else "updated"] += 1
                counts["errors"] += int(metadata_error)
            except Exception:
                counts["errors"] += 1
                LOGGER.exception("Asset konnte nicht indexiert werden: %s", path)

        missing = self.repository.mark_missing_except(root_path, seen) if root_path.is_dir() else 0
        return ScanResult(
            discovered=len(paths),
            inserted=counts["inserted"],
            updated=counts["updated"],
            unchanged=counts["unchanged"],
            missing=missing,
            errors=counts["errors"],
            duration=time.perf_counter() - started,
        )

    @staticmethod
    def _discover(root: Path) -> list[Path]:
        if not root.is_dir():
            return []
        return sorted(
            (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS),
            key=lambda path: _canonical_path(path),
        )

    def _read_asset(
        self,
        path: Path,
        stat: os.stat_result,
        sidecar: Path | None,
        sidecar_mtime: int | None,
    ) -> tuple[AssetRecord, bool]:
        embedded: dict[str, Any] = {}
        width: int | None = None
        height: int | None = None
        metadata_error = False
        try:
            with Image.open(path) as image:
                width, height = image.size
                embedded = dict(image.info)
        except Exception:
            metadata_error = True
            LOGGER.warning("Bildmetadaten konnten nicht gelesen werden: %s", path, exc_info=True)

        sidecar_data: dict[str, Any] = {}
        if sidecar:
            sidecar_data, sidecar_error = read_asset_metadata(sidecar)
            if sidecar_error:
                metadata_error = True
                LOGGER.warning("Ungültiges Asset-Sidecar: %s", sidecar)

        metadata = {**embedded, **sidecar_data}
        width = _as_int(metadata.get("width")) or width
        height = _as_int(metadata.get("height")) or height
        return AssetRecord(
            asset_id=None,
            canonical_path=_canonical_path(path),
            filename=path.name,
            extension=path.suffix.lower(),
            asset_type="generated_asset",
            media_type="image",
            file_size=stat.st_size,
            file_created_at=stat.st_ctime_ns,
            file_modified_at=stat.st_mtime_ns,
            indexed_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            width=width,
            height=height,
            sidecar_path=_canonical_path(sidecar) if sidecar else None,
            sidecar_modified_at=sidecar_mtime,
            prompt=_as_text(metadata.get("prompt")),
            negative_prompt=_as_text(metadata.get("negative_prompt")),
            model_id=_as_text(metadata.get("model_id") or metadata.get("model")),
            model_version=_as_text(metadata.get("model_version")),
            seed=_as_int(metadata.get("seed")),
            steps=_as_int(metadata.get("steps") or metadata.get("step_count")),
            cfg_scale=_as_float(metadata.get("cfg_scale") or metadata.get("cfg") or metadata.get("guidance_scale")),
            sampler=_as_text(metadata.get("sampler")),
            scheduler=_as_text(metadata.get("scheduler")),
            backend=_as_text(metadata.get("backend")),
            device=_as_text(metadata.get("device")),
        ), metadata_error


def _canonical_path(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(Path(path).resolve(strict=False))))


def _as_text(value: object) -> str | None:
    return str(value) if value is not None and not isinstance(value, (dict, list)) else None


def _as_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _as_float(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
