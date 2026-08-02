from __future__ import annotations

import subprocess
import tkinter as tk
from pathlib import Path
import pytest

import widgets.phoenix.views.home_view as home_module
from widgets.phoenix.views.home_view import PhoenixHomeView
from app.i18n import set_language, tr


def test_new_localization_keys():
    """Verify that all new localization keys are loaded correctly in all supported languages."""
    keys = [
        "home_error_title",
        "home_file_not_found",
        "home_explorer_error",
        "home_open_in_explorer",
        "home_delete_all_confirm_with_count",
    ]
    for lang in ["de_DE", "en_US", "es_ES"]:
        set_language(lang)
        for key in keys:
            val = tr(key)
            assert val != key
            assert len(val) > 0
    # Revert to default language
    set_language("de_DE")


def test_delete_single_generation_cancel(tmp_path, monkeypatch):
    """Test that cancelling single generation deletion changes nothing."""
    first = tmp_path / "first.png"
    first.write_bytes(b"image")
    first.with_suffix(".json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(home_module, "OUTPUT_DIR", tmp_path)
    # Mock askyesno to return False (cancel)
    monkeypatch.setattr(home_module.messagebox, "askyesno", lambda *a, **k: False)
    
    view = object.__new__(PhoenixHomeView)
    view.refresh = lambda **kwargs: None

    view._delete_generation(first)
    
    assert first.exists()
    assert first.with_suffix(".json").exists()


def test_delete_all_generations_with_count(tmp_path, monkeypatch):
    """Test that deleting all generations only deletes displayed ones and shows the correct count in message."""
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    third = tmp_path / "third.png"
    
    for img in (first, second, third):
        img.write_bytes(b"image")
        img.with_suffix(".json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(home_module, "OUTPUT_DIR", tmp_path)
    
    # We want to verify the count placeholder formatting is called
    recorded_message = []
    def mock_askyesno(title, message, parent=None):
        recorded_message.append(message)
        return True

    monkeypatch.setattr(home_module.messagebox, "askyesno", mock_askyesno)
    
    view = object.__new__(PhoenixHomeView)
    view.refresh = lambda **kwargs: None
    
    # Mock _read_latest_generations to return only first and second (displayed)
    from widgets.phoenix.views.home_view import GenerationInfo
    mock_latest = [
        GenerationInfo(path=first, filename=first.name, model="test", resolution="512x512", created_at=""),
        GenerationInfo(path=second, filename=second.name, model="test", resolution="512x512", created_at=""),
    ]
    view._read_latest_generations = lambda: mock_latest

    view._delete_all_generations()

    # Verify that first and second are deleted (along with sidecars), but third is kept
    assert not first.exists()
    assert not first.with_suffix(".json").exists()
    assert not second.exists()
    assert not second.with_suffix(".json").exists()
    
    assert third.exists()
    assert third.with_suffix(".json").exists()
    
    # Verify confirm message mentions the count (2)
    assert len(recorded_message) == 1
    assert "2" in recorded_message[0]


def test_open_in_explorer_missing_file(monkeypatch):
    """Test that trying to open a non-existent file in explorer displays an error message."""
    non_existent = Path("C:/SnapdragonAI/output/does_not_exist.png")
    
    recorded_errors = []
    def mock_showerror(title, message, parent=None):
        recorded_errors.append((title, message))
        
    monkeypatch.setattr(home_module.messagebox, "showerror", mock_showerror)
    
    view = object.__new__(PhoenixHomeView)
    view._open_in_explorer(non_existent)
    
    assert len(recorded_errors) == 1
    assert "does_not_exist" in str(recorded_errors[0][1])


def test_open_in_explorer_success(tmp_path, monkeypatch):
    """Test that opening an existing file in explorer runs explorer /select."""
    existing_file = tmp_path / "existing.png"
    existing_file.write_bytes(b"img")
    
    run_args = []
    def mock_run(args, **kwargs):
        run_args.append(args)
        return subprocess.CompletedProcess(args, 0)
        
    monkeypatch.setattr(home_module.subprocess, "run", mock_run)
    
    view = object.__new__(PhoenixHomeView)
    view._open_in_explorer(existing_file)
    
    assert len(run_args) == 1
    assert run_args[0] == ["explorer", "/select,", str(existing_file.resolve())]
