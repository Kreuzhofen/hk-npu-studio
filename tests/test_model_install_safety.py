from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engine.model_install_service import ModelInstallService


class Repository:
    def __init__(self, model_id: str, path: Path) -> None:
        self.model_id = model_id
        self.model = {
            "id": model_id,
            "installed": True,
            "downloaded": True,
            "path": str(path),
            "status": "Ready",
        }

    def get_model(self, model_id: str):
        return self.model if model_id == self.model_id else None

    def update_model(self, model_id: str, **updates) -> bool:
        if model_id != self.model_id:
            return False
        self.model.update(updates)
        return True


class ManagedModelUninstallSafetyTests(unittest.TestCase):
    def _service(self, model_id: str, path: Path) -> tuple[ModelInstallService, Repository]:
        repository = Repository(model_id, path)
        service = ModelInstallService.__new__(ModelInstallService)
        service.repository = repository
        return service, repository

    def test_managed_model_target_is_deleted_and_registry_is_reset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            models_dir = Path(directory) / "dynamic-models"
            target = models_dir / "demo"
            target.mkdir(parents=True)
            (target / "model.bin").write_bytes(b"model")
            service, repository = self._service("demo", target)

            with patch("engine.model_install_service.MODELS_DIR", models_dir):
                self.assertTrue(service.uninstall_model("demo"))

            self.assertFalse(target.exists())
            self.assertFalse(repository.model["installed"])
            self.assertFalse(repository.model["downloaded"])
            self.assertEqual("", repository.model["path"])

    def test_custom_path_is_preserved_while_registry_is_reset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            models_dir = root / "managed"
            custom = root / "custom" / "demo"
            custom.mkdir(parents=True)
            marker = custom / "model.bin"
            marker.write_bytes(b"custom")
            service, repository = self._service("demo", custom)

            with patch("engine.model_install_service.MODELS_DIR", models_dir):
                self.assertTrue(service.uninstall_model("demo"))

            self.assertTrue(marker.is_file())
            self.assertEqual("", repository.model["path"])

    def test_historical_repository_subdirectory_is_never_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            models_dir = root / "managed"
            historical_docs = root / "SnapdragonAI" / "docs"
            historical_docs.mkdir(parents=True)
            marker = historical_docs / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            service, repository = self._service("demo", historical_docs)

            with patch("engine.model_install_service.MODELS_DIR", models_dir):
                self.assertTrue(service.uninstall_model("demo"))

            self.assertTrue(marker.is_file())
            self.assertEqual("", repository.model["path"])

    def test_unsafe_model_ids_never_resolve_or_change_registry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            models_dir = root / "managed"
            protected = root / "protected"
            protected.mkdir()
            cases = ("", "..", "../protected", r"..\protected", str(protected.resolve()))
            for model_id in cases:
                with self.subTest(model_id=model_id):
                    service, repository = self._service(model_id, protected)
                    with patch("engine.model_install_service.MODELS_DIR", models_dir):
                        self.assertIsNone(service._resolve_managed_model_target(model_id))
                        self.assertFalse(service.uninstall_model(model_id))
                    self.assertTrue(protected.is_dir())
                    self.assertTrue(repository.model["installed"])

    def test_models_dir_itself_is_never_a_managed_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            models_dir = Path(directory) / "managed"
            models_dir.mkdir()
            with patch("engine.model_install_service.MODELS_DIR", models_dir):
                self.assertIsNone(ModelInstallService._resolve_managed_model_target("."))


if __name__ == "__main__":
    unittest.main()
