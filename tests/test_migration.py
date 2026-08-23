from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import pytest

import config
from app.migration import migrate_legacy_generations
from tools.build_installer import validate_release_staging


def test_release_staging_rejects_runtime_output_and_preserves_files(tmp_path):
    runtime_output = tmp_path / "output"
    image = runtime_output / "generate_0001.png"
    sidecar = runtime_output / "generate_0001.json"
    runtime_output.mkdir()
    image.write_bytes(b"image")
    sidecar.write_text('{"prompt": "legacy"}', encoding="utf-8")

    with pytest.raises(RuntimeError, match="Runtime-Ausgabeordner"):
        validate_release_staging(tmp_path)

    assert image.read_bytes() == b"image"
    assert sidecar.read_text(encoding="utf-8") == '{"prompt": "legacy"}'


def test_clean_release_staging_has_no_runtime_output(tmp_path):
    (tmp_path / "SnapdragonAIStudio.exe").write_bytes(b"executable")
    validate_release_staging(tmp_path)


def test_installer_excludes_runtime_output_from_recursive_staging():
    installer_script = Path(__file__).resolve().parents[1] / "installer" / "snapdragon_ai_studio.iss"
    assert 'Excludes: "output\\*"' in installer_script.read_text(encoding="utf-8")

def test_migration_legacy_folder_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    mock_localappdata = tmp_path / "mock_appdata"
    monkeypatch.setenv("LOCALAPPDATA", str(mock_localappdata))
    
    mock_output_dir = tmp_path / "mock_output"
    monkeypatch.setattr(config, "OUTPUT_DIR", mock_output_dir)
    
    migrate_legacy_generations()
    assert not mock_output_dir.exists()

def test_migration_legacy_folder_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    mock_localappdata = tmp_path / "mock_appdata"
    legacy_dir = mock_localappdata / "Programs" / "Snapdragon AI Studio" / "output"
    legacy_dir.mkdir(parents=True)
    monkeypatch.setenv("LOCALAPPDATA", str(mock_localappdata))
    
    mock_output_dir = tmp_path / "mock_output"
    monkeypatch.setattr(config, "OUTPUT_DIR", mock_output_dir)
    
    migrate_legacy_generations()
    assert not mock_output_dir.exists()

def test_migration_files_copied_not_overwritten_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    # 1. Setup mock directories
    mock_localappdata = tmp_path / "mock_appdata"
    legacy_dir = mock_localappdata / "Programs" / "Snapdragon AI Studio" / "output"
    legacy_dir.mkdir(parents=True)
    monkeypatch.setenv("LOCALAPPDATA", str(mock_localappdata))
    
    mock_output_dir = tmp_path / "mock_output"
    mock_output_dir.mkdir(parents=True)
    monkeypatch.setattr(config, "OUTPUT_DIR", mock_output_dir)
    
    # 2. Write source files
    source_png1 = legacy_dir / "generate_0001.png"
    source_png1.write_bytes(b"png1_data")
    source_json1 = legacy_dir / "generate_0001.json"
    source_json1.write_text('{"prompt": "gen1"}', encoding="utf-8")
    
    source_png2 = legacy_dir / "generate_0002.png"
    source_png2.write_bytes(b"png2_data")
    
    source_jpg = legacy_dir / "generate_0003.jpg"
    source_jpg.write_bytes(b"jpg_data")
    source_json3 = legacy_dir / "generate_0003.json"
    source_json3.write_text('{"prompt": "gen3"}', encoding="utf-8")
    
    source_webp = legacy_dir / "generate_0004.webp"
    source_webp.write_bytes(b"webp_data")
    
    source_other = legacy_dir / "random.jpg"
    source_other.write_bytes(b"random_data")
    
    # 3. Write target conflict file
    target_png1 = mock_output_dir / "generate_0001.png"
    target_png1.write_bytes(b"existing_png1_data")
    target_json1 = mock_output_dir / "generate_0001.json"
    target_json1.write_text('{"prompt": "existing_gen1"}', encoding="utf-8")
    
    # Run migration
    migrate_legacy_generations()
    
    # 4. Verifications
    assert (mock_output_dir / "generate_0002.png").exists()
    assert (mock_output_dir / "generate_0002.png").read_bytes() == b"png2_data"
    
    assert (mock_output_dir / "generate_0003.jpg").exists()
    assert (mock_output_dir / "generate_0003.jpg").read_bytes() == b"jpg_data"
    assert (mock_output_dir / "generate_0003.json").exists()
    assert json.loads((mock_output_dir / "generate_0003.json").read_text(encoding="utf-8")) == {"prompt": "gen3"}
    
    assert (mock_output_dir / "generate_0004.webp").exists()
    assert (mock_output_dir / "generate_0004.webp").read_bytes() == b"webp_data"
    
    assert not (mock_output_dir / "random.jpg").exists()
    
    # Conflict check
    assert target_png1.read_bytes() == b"existing_png1_data"
    assert json.loads(target_json1.read_text(encoding="utf-8")) == {"prompt": "existing_gen1"}
    
    # Source check (no files deleted)
    assert source_png1.exists()
    assert source_png1.read_bytes() == b"png1_data"
    assert source_json1.exists()
    assert source_png2.exists()
    assert source_jpg.exists()
    assert source_json3.exists()
    assert source_webp.exists()
    assert source_other.exists()
    
    # Second run (idempotency check)
    migrate_legacy_generations()
    assert target_png1.read_bytes() == b"existing_png1_data"
    assert len(list(mock_output_dir.iterdir())) == 6
