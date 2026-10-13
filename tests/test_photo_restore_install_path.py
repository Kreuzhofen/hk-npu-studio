from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from controllers.model_repository import ModelRepository
from engine.backends.photo_restore_package_resolver import (
    FIDESR_PACKAGE_ARTIFACT_PATHS,
    PhotoRestorePackageResolver,
)
from engine.model_install_service import ModelInstallService


ROOT = Path(__file__).resolve().parents[1]
MODEL_DEFINITION = ROOT / "resources" / "models" / "photo_restore.json"
COMPONENT_PATHS = tuple(FIDESR_PACKAGE_ARTIFACT_PATHS.values())


def _manifest(package_id: str = "photo_restore") -> dict:
    return {
        "package_id": package_id,
        "package_version": "1.0.0",
        "architecture": "arm64",
        "capabilities": {"img2img": True, "qnn_runtime": True},
        "components": {
            name: {"path": path.as_posix(), "runtime": "QNN"}
            for name, path in FIDESR_PACKAGE_ARTIFACT_PATHS.items()
        },
    }


def _write_package_archive(path: Path, package_id: str = "photo_restore") -> None:
    with zipfile.ZipFile(path, "w") as package:
        package.writestr(
            "photo_restore/package.json",
            json.dumps(_manifest(package_id)),
        )
        for relative in COMPONENT_PATHS:
            package.writestr(
                f"photo_restore/{relative.as_posix()}",
                b"synthetic-artifact",
            )


def _create_service(root: Path) -> tuple[ModelInstallService, ModelRepository]:
    definitions = root / "definitions"
    definitions.mkdir()
    definition = json.loads(MODEL_DEFINITION.read_text(encoding="utf-8"))
    (definitions / "photo_restore.json").write_text(
        json.dumps(definition), encoding="utf-8"
    )
    managed_models = root / "managed-models"
    repository = ModelRepository(
        models_dir=str(definitions), installation_roots=[managed_models]
    )
    service = ModelInstallService(repository)
    return service, repository


def test_synthetic_zip_installs_to_managed_root_and_resolves() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        managed_models = root / "managed-models"
        archive = root / "photo_restore.zip"
        outside_guard = root / "outside.guard"
        outside_guard.write_bytes(b"unchanged")
        _write_package_archive(archive)
        service, repository = _create_service(root)

        with patch("engine.model_install_service.MODELS_DIR", managed_models):
            expected_target = service._resolve_managed_model_target("photo_restore")
            installed = service.install_package("photo_restore", str(archive))

        package_root = managed_models / "photo_restore"
        assert installed is True
        assert expected_target == package_root.resolve()
        assert repository.get_model("photo_restore")["path"] == str(
            package_root.resolve()
        )
        assert set(managed_models.iterdir()) == {package_root}
        assert outside_guard.read_bytes() == b"unchanged"

        resolution = PhotoRestorePackageResolver([managed_models]).resolve()
        assert resolution.ready is True
        assert resolution.artifacts is not None
        assert resolution.artifacts.root == package_root.resolve()
        expected_files = {
            (package_root / relative).resolve() for relative in COMPONENT_PATHS
        }
        assert set(resolution.artifacts.required_files()) == expected_files
        assert all(path.is_file() for path in expected_files)


def test_wrong_package_id_is_rejected_without_managed_write() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        managed_models = root / "managed-models"
        archive = root / "wrong.zip"
        _write_package_archive(archive, package_id="not_photo_restore")
        service, _ = _create_service(root)

        with patch("engine.model_install_service.MODELS_DIR", managed_models):
            installed = service.install_package("photo_restore", str(archive))

        assert installed is False
        assert not (managed_models / "photo_restore").exists()


def test_missing_managed_artifact_is_not_ready() -> None:
    with tempfile.TemporaryDirectory() as directory:
        managed_models = Path(directory) / "managed-models"
        package_root = managed_models / "photo_restore"
        for relative in COMPONENT_PATHS[:-1]:
            target = package_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"synthetic-artifact")

        resolution = PhotoRestorePackageResolver([managed_models]).resolve()

        assert resolution.ready is False
        assert resolution.status == "NOT_READY"
        assert resolution.missing_files == (
            (package_root / COMPONENT_PATHS[-1]).resolve(),
        )


def test_package_root_can_be_resolved_directly() -> None:
    with tempfile.TemporaryDirectory() as directory:
        package_root = Path(directory) / "photo_restore"
        for relative in COMPONENT_PATHS:
            target = package_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"synthetic-artifact")

        resolution = PhotoRestorePackageResolver([package_root]).resolve()

        assert resolution.ready is True
        assert resolution.artifacts is not None
        assert resolution.artifacts.root == package_root.resolve()
