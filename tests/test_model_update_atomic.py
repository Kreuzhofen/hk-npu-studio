from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from controllers.model_repository import ModelRepository
from engine.model_install_service import ModelInstallService


def write_package(path: Path, version: str, *, checksum: str | None = None) -> None:
    path.mkdir(parents=True)
    (path / "model.onnx").write_bytes(f"weights-{version}".encode())
    component = {"path": "model.onnx", "runtime": "ONNX"}
    if checksum:
        component["sha256"] = checksum
    (path / "package.json").write_text(
        json.dumps(
            {
                "model_id": "demo",
                "package_version": version,
                "capabilities": {"txt2img": True},
                "components": {"unet": component},
            }
        ),
        encoding="utf-8",
    )


def metadata(path: Path) -> dict:
    return {
        "id": "demo",
        "display_name": "Demo",
        "author": "Test",
        "version": "1.0.0",
        "license": "Test",
        "description": "Update test",
        "category": "Image",
        "backend": "ONNX Runtime",
        "recommended_backend": "ONNX Runtime (Stub)",
        "minimum_ram_gb": 1,
        "recommended_ram_gb": 2,
        "supports": ["txt2img"],
        "installed": True,
        "downloaded": True,
        "path": str(path),
        "status": "Ready",
        "capabilities": {"txt2img": True, "onnx_runtime": True},
    }


class AtomicModelUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.installed = self.root / "installed"
        self.source = self.root / "source"
        self.definitions = self.root / "definitions"
        self.definitions.mkdir()
        write_package(self.installed, "1.0.0")
        write_package(self.source, "2.0.0")
        (self.definitions / "demo.json").write_text(
            json.dumps(metadata(self.installed)), encoding="utf-8"
        )
        self.original_preferences = ModelRepository._preferences_path
        ModelRepository._preferences_path = self.root / "preferences.json"
        self.repository = ModelRepository(str(self.definitions))
        self.service = ModelInstallService(self.repository)

    def tearDown(self) -> None:
        ModelRepository._preferences_path = self.original_preferences
        self.temp.cleanup()

    def test_newer_package_is_swapped_and_registry_committed(self):
        self.assertTrue(self.service.update_package("demo", str(self.source)))

        manifest = json.loads(
            (self.installed / "package.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["package_version"], "2.0.0")
        self.assertEqual(self.repository.get_model("demo")["version"], "2.0.0")
        self.assertEqual(self.repository.get_model("demo")["status"], "Ready")
        self.assertEqual(list(self.root.glob(".installed.*")), [])

    def test_invalid_staged_package_never_changes_registry_or_installation(self):
        manifest_path = self.source / "package.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["components"]["unet"]["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        self.assertFalse(self.service.update_package("demo", str(self.source)))

        installed_manifest = json.loads(
            (self.installed / "package.json").read_text(encoding="utf-8")
        )
        self.assertEqual(installed_manifest["package_version"], "1.0.0")
        self.assertEqual(self.repository.get_model("demo")["version"], "1.0.0")

    def test_registry_failure_rolls_files_back_to_previous_version(self):
        with patch.object(
            self.repository, "update_model", side_effect=[False, True]
        ):
            self.assertFalse(self.service.update_package("demo", str(self.source)))

        manifest = json.loads(
            (self.installed / "package.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["package_version"], "1.0.0")
        self.assertTrue((self.installed / "model.onnx").exists())

    def test_same_or_older_version_is_rejected(self):
        older = self.root / "older"
        write_package(older, "0.9.0")

        self.assertFalse(self.service.update_package("demo", str(older)))
        self.assertFalse(self.service.update_package("demo", str(self.installed)))
        self.assertEqual(self.repository.get_model("demo")["version"], "1.0.0")

    def test_catalog_update_check_compares_installed_version(self):
        with patch.object(
            self.service.catalog_service,
            "get_package",
            return_value={"version": "1.1.0"},
        ):
            self.assertTrue(self.service.check_for_update("demo"))

        with patch.object(
            self.service.catalog_service,
            "get_package",
            return_value={"version": "1.0.0"},
        ):
            self.assertFalse(self.service.check_for_update("demo"))


if __name__ == "__main__":
    unittest.main()
