from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import config
from engine.backends.fidesr_photo_restore_backend import FiDeSRPhotoRestoreBackend
from engine.backends.photo_restore_package_resolver import (
    FIDESR_ARTIFACT_PATHS,
    PhotoRestoreArtifacts,
    PhotoRestorePackageError,
    PhotoRestorePackageResolver,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "engine/backends/fidesr_photo_restore_backend.py"
RUNNER_PATH = PROJECT_ROOT / "engine/backends/fidesr_strong_runner_template.py"


def create_complete_package(root: Path) -> PhotoRestoreArtifacts:
    for relative_path in FIDESR_ARTIFACT_PATHS.values():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"artifact")
    resolution = PhotoRestorePackageResolver([root]).resolve()
    assert resolution.artifacts is not None
    return resolution.artifacts


def test_current_development_package_resolves_all_six_artifacts():
    resolution = PhotoRestorePackageResolver([config.BASE / "models"]).resolve()

    assert resolution.ready is True
    assert resolution.artifacts is not None
    assert len(resolution.artifacts.required_files()) == 6
    assert all(path.is_file() for path in resolution.artifacts.required_files())


def test_future_managed_root_resolves_without_copying(tmp_path):
    managed_root = tmp_path / "managed-models"
    expected = create_complete_package(managed_root)

    resolution = PhotoRestorePackageResolver([managed_root]).resolve()

    assert resolution.ready is True
    assert resolution.artifacts == expected
    assert resolution.artifacts.root == managed_root.resolve()


def test_existing_bundled_root_is_used_when_managed_root_has_no_package(tmp_path):
    managed_root = tmp_path / "managed-models"
    bundled_root = tmp_path / "bundled-models"
    managed_root.mkdir()
    create_complete_package(bundled_root)

    resolution = PhotoRestorePackageResolver(
        [managed_root, bundled_root]
    ).resolve()

    assert resolution.ready is True
    assert resolution.artifacts is not None
    assert resolution.artifacts.root == bundled_root.resolve()


def test_first_complete_root_wins_in_declared_priority(tmp_path):
    first = tmp_path / "configured-models"
    second = tmp_path / "default-models"
    create_complete_package(first)
    create_complete_package(second)

    resolution = PhotoRestorePackageResolver([first, second]).resolve()

    assert resolution.ready is True
    assert resolution.artifacts is not None
    assert resolution.artifacts.root == first.resolve()


def test_default_priority_reuses_model_repository_then_legacy_bundle(tmp_path):
    configured = tmp_path / "configured-models"
    managed = tmp_path / "managed-models"
    frozen = tmp_path / "frozen-models"
    bundled_base = tmp_path / "bundle"

    with patch(
        "controllers.model_repository.ModelRepository._build_installation_roots",
        return_value=[configured, managed, frozen],
    ), patch.object(config, "BASE", bundled_base):
        resolver = PhotoRestorePackageResolver()

    assert resolver._roots == tuple(
        path.resolve()
        for path in (
            configured,
            managed,
            frozen,
            bundled_base / "models",
        )
    )


def test_partial_higher_priority_package_is_not_silently_ready(tmp_path):
    partial = tmp_path / "partial-models"
    complete = tmp_path / "bundled-models"
    first_relative = next(iter(FIDESR_ARTIFACT_PATHS.values()))
    partial_file = partial / first_relative
    partial_file.parent.mkdir(parents=True)
    partial_file.write_bytes(b"partial")
    create_complete_package(complete)

    resolution = PhotoRestorePackageResolver([partial, complete]).resolve()

    assert resolution.ready is False
    assert resolution.status == "NOT_READY"
    assert len(resolution.missing_files) == 5
    assert str(partial.resolve()) in resolution.message


def test_required_artifact_must_be_a_regular_file(tmp_path):
    root = tmp_path / "models"
    create_complete_package(root)
    required = root / FIDESR_ARTIFACT_PATHS["epsilon_seed"]
    required.unlink()
    required.mkdir()

    resolution = PhotoRestorePackageResolver([root]).resolve()

    assert resolution.ready is False
    assert required.resolve() in resolution.missing_files


def test_path_outside_approved_root_is_rejected(tmp_path):
    with pytest.raises(PhotoRestorePackageError, match="escapes approved model root"):
        PhotoRestorePackageResolver._resolve_within_root(
            tmp_path / "models", Path("../outside.bin")
        )


def test_backend_initialization_uses_resolver_result(tmp_path):
    artifacts = create_complete_package(tmp_path / "models")
    runner = tmp_path / "runner.py"
    runner.write_text("# runner", encoding="utf-8")

    class StubResolver:
        def __init__(self):
            self.calls = 0

        def require_ready(self):
            self.calls += 1
            return artifacts

    resolver = StubResolver()
    backend = FiDeSRPhotoRestoreBackend(
        runner_template=runner,
        package_resolver=resolver,
    )

    backend.initialize()

    assert resolver.calls == 1
    assert backend._artifacts == artifacts
    assert backend.status == "INITIALIZED"


def test_backend_passes_same_six_concrete_paths_to_runner_contract():
    backend_text = BACKEND_PATH.read_text(encoding="utf-8")
    runner_text = RUNNER_PATH.read_text(encoding="utf-8")
    environment_names = (
        "HK_NPU_FIDESR_VAE_ENCODER_CONTEXT",
        "HK_NPU_FIDESR_UNET_CONTEXT",
        "HK_NPU_FIDESR_LRRB_CONTEXT",
        "HK_NPU_FIDESR_VAE_DECODER_CONTEXT",
        "HK_NPU_FIDESR_EMPTY_PROMPT_EMBEDS",
        "HK_NPU_FIDESR_EPSILON_SEED",
    )

    for name in environment_names:
        assert f'"{name}"' in backend_text
        assert f'os.environ["{name}"]' in runner_text

    assert 'ROOT / "models" / "photo_restore"' not in runner_text
    assert 'ROOT / "models" / "photo_restore_context"' not in runner_text
    assert 'MODEL_DIR = ROOT / "models"' not in backend_text
    assert "FIDESR_REQUIRED" not in backend_text
