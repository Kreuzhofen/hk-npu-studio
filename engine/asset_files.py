from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4


def read_asset_metadata(sidecar: str | Path) -> tuple[dict[str, Any], bool]:
    """Read and normalize flat and legacy nested gallery sidecars."""
    path = Path(sidecar)
    if not path.is_file():
        return {}, False
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}, True
        nested = raw.get("metadata")
        if isinstance(nested, dict):
            return {
                **{key: value for key, value in raw.items() if key != "metadata"},
                **nested,
            }, False
        return raw, False
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}, True


def atomic_copy_file(source: str | Path, destination: str | Path) -> Path:
    """Copy one file through a sibling staging file and atomically replace it."""
    source_path = Path(source)
    destination_path = Path(destination)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    staging = destination_path.with_name(
        f".{destination_path.name}.{uuid4().hex}.tmp"
    )
    try:
        shutil.copy2(source_path, staging)
        os.replace(staging, destination_path)
    finally:
        staging.unlink(missing_ok=True)
    return destination_path


def atomic_write_json(
    destination: str | Path,
    data: dict[str, Any],
    *,
    indent: int = 2,
) -> Path:
    """Write a UTF-8 JSON object through a sibling file and atomic replace."""
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    staging = destination_path.with_name(
        f".{destination_path.name}.{uuid4().hex}.tmp"
    )
    try:
        with staging.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=indent, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staging, destination_path)
    finally:
        staging.unlink(missing_ok=True)
    return destination_path


def copy_asset_with_sidecar(
    source: str | Path, destination: str | Path
) -> tuple[Path, Path | None]:
    """Atomically copy an image and keep its same-stem sidecar consistent."""
    source_path = Path(source)
    destination_path = Path(destination)
    source_sidecar = source_path.with_suffix(".json")
    destination_sidecar = destination_path.with_suffix(".json")

    copied_sidecar: Path | None = None
    if source_sidecar.is_file():
        copied_sidecar = atomic_copy_file(source_sidecar, destination_sidecar)
    else:
        destination_sidecar.unlink(missing_ok=True)
    atomic_copy_file(source_path, destination_path)
    return destination_path, copied_sidecar
