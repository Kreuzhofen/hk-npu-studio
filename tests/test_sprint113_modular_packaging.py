"""
HK NPU STUDIO â€“ Sprint 113: Modular Packaging and FiDeSR Isolation Test Suite
Verifies decoupling of FiDeSR weights from base installer, QNN runtime retention,
SMP archive validity, and Model Manager installation detection.
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
import pytest

import config
from controllers.model_repository import ModelRepository
from engine.backends.photo_restore_package_resolver import PhotoRestorePackageResolver
from engine.model_registry import ModelHealthStatus, ModelRegistry
import tools.build_app as build_app

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_payload_has_no_fidesr_weights():
    """Verify that build_app._required_add_data_files() contains NO FiDeSR weights."""
    required = build_app._required_add_data_files()
    weight_files = [
        str(src) for src, _ in required
        if "photo_restore" in str(src).lower() and str(src).endswith(".bin")
    ]
    assert len(weight_files) == 0, f"Found unexpected FiDeSR weights in build payload: {weight_files}"


def test_qnn_htp_runtime_preserved_in_build():
    """Verify that QNN HTP runtime binaries and qnn-net-run remain bundled."""
    qnn_files = build_app._resolve_fidesr_qnn_runtime_files()
    file_names = {src.name for src, _ in qnn_files}
    assert "qnn-net-run.exe" in file_names
    assert "QnnHtp.dll" in file_names
    assert "libQnnHtpV73Skel.so" in file_names
    assert "QnnSystem.dll" in file_names


def test_installer_iss_excludes_photo_restore():
    """Verify that snapdragon_ai_studio.iss excludes photo_restore and photo_restore_context."""
    iss_content = (REPO_ROOT / "installer" / "snapdragon_ai_studio.iss").read_text(encoding="utf-8")
    assert "Excludes: \"output\\*,models\\photo_restore\\*,models\\photo_restore_context\\*\"" in iss_content


def test_photo_restore_smp_package_integrity():
    """Verify that dist/packages/photo_restore.smp exists and contains all required components."""
    smp_path = REPO_ROOT / "dist" / "packages" / "photo_restore.smp"
    assert smp_path.is_file(), f"photo_restore.smp not found at {smp_path}"
    assert smp_path.stat().st_size > 1_000_000_000, "photo_restore.smp is smaller than 1 GB!"

    with zipfile.ZipFile(smp_path, "r") as zf:
        namelist = set(zf.namelist())
        expected = {
            "package.json",
            "models/fidesr_empty_prompt_embeds.bin",
            "models/fidesr_epsilon_seed231.bin",
            "context/fidesr_vae_encoder/fidesr_vae_encoder.serialized.bin.bin",
            "context/fidesr_unet/fidesr_unet_merged.serialized.bin.bin",
            "context/fidesr_lrrb/fidesr_lrrb.serialized.bin.bin",
            "context/fidesr_vae_decoder/fidesr_vae_decoder.serialized.bin.bin",
        }
        for item in expected:
            assert item in namelist, f"Missing required file in SMP archive: {item}"


def test_model_repository_recognizes_installed_photo_restore():
    """Verify that ModelRepository marks installed photo_restore in AppData as Ready."""
    repo = ModelRepository()
    model = repo.get_model("photo_restore")
    assert model is not None
    assert model.get("installed") is True
    assert model.get("status") == "Ready"
    expected_path = config.LOCAL_APP_DATA / config.PRODUCT_DATA_DIR_NAME / "models" / "photo_restore"
    assert Path(model.get("path")).resolve() == expected_path.resolve()


def test_model_repository_handles_uninstalled_state():
    """Verify that ModelRepository marks uninstalled model as Not Installed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        empty_root = Path(temp_dir) / "empty"
        empty_root.mkdir()
        repo = ModelRepository(installation_roots=[empty_root])
        model = repo.get_model("photo_restore")
        assert model is not None
        assert model.get("installed") is False
        assert model.get("status") == "Not Installed"
        assert model.get("path") == ""
