from __future__ import annotations

import json
from unittest.mock import patch

from engine.asset_files import (
    atomic_copy_file,
    atomic_write_json,
    copy_asset_with_sidecar,
    read_asset_metadata,
)


def test_nested_and_top_level_sidecar_metadata_are_normalized(tmp_path):
    sidecar = tmp_path / "image.json"
    sidecar.write_text(
        json.dumps(
            {
                "controlnet_enabled": True,
                "metadata": {"prompt": "nested", "seed": 42},
            }
        ),
        encoding="utf-8",
    )

    metadata, error = read_asset_metadata(sidecar)

    assert error is False
    assert metadata == {
        "controlnet_enabled": True,
        "prompt": "nested",
        "seed": 42,
    }


def test_invalid_sidecar_is_reported_without_partial_metadata(tmp_path):
    sidecar = tmp_path / "image.json"
    sidecar.write_text("{invalid", encoding="utf-8")

    metadata, error = read_asset_metadata(sidecar)

    assert metadata == {}
    assert error is True


def test_atomic_copy_replaces_destination_without_staging_residue(tmp_path):
    source = tmp_path / "source.png"
    destination = tmp_path / "gallery" / "image.png"
    source.write_bytes(b"new-image")
    destination.parent.mkdir()
    destination.write_bytes(b"old-image")

    atomic_copy_file(source, destination)

    assert destination.read_bytes() == b"new-image"
    assert not list(destination.parent.glob(".*.tmp"))


def test_failed_atomic_copy_preserves_existing_destination(tmp_path):
    source = tmp_path / "source.png"
    destination = tmp_path / "image.png"
    source.write_bytes(b"new-image")
    destination.write_bytes(b"old-image")

    with patch(
        "engine.asset_files.shutil.copy2",
        side_effect=OSError("copy failed"),
    ):
        try:
            atomic_copy_file(source, destination)
        except OSError:
            pass

    assert destination.read_bytes() == b"old-image"
    assert not list(tmp_path.glob(".*.tmp"))


def test_atomic_json_write_replaces_complete_document(tmp_path):
    destination = tmp_path / "image.json"
    destination.write_text('{"old": true}', encoding="utf-8")

    atomic_write_json(destination, {"prompt": "new", "seed": 42})

    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "prompt": "new",
        "seed": 42,
    }
    assert not list(tmp_path.glob(".*.tmp"))


def test_asset_copy_keeps_same_stem_sidecar_consistent(tmp_path):
    source = tmp_path / "source.png"
    source.write_bytes(b"image")
    source.with_suffix(".json").write_text(
        json.dumps({"prompt": "test"}), encoding="utf-8"
    )
    destination = tmp_path / "gallery" / "renamed.png"

    copied_image, copied_sidecar = copy_asset_with_sidecar(source, destination)

    assert copied_image.read_bytes() == b"image"
    assert copied_sidecar == destination.with_suffix(".json")
    assert json.loads(copied_sidecar.read_text(encoding="utf-8"))["prompt"] == "test"


def test_copy_without_sidecar_removes_stale_destination_metadata(tmp_path):
    source = tmp_path / "source.png"
    source.write_bytes(b"image")
    destination = tmp_path / "gallery.png"
    destination.write_bytes(b"old")
    destination.with_suffix(".json").write_text("{}", encoding="utf-8")

    copy_asset_with_sidecar(source, destination)

    assert destination.read_bytes() == b"image"
    assert not destination.with_suffix(".json").exists()
