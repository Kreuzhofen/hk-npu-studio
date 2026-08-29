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
        self.models_dir = self.root / "models"
        self.installed = self.models_dir / "demo"
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
        self.models_dir_patch = patch("engine.model_install_service.MODELS_DIR", self.models_dir)
        self.models_dir_patch.start()
        self.repository = ModelRepository(
            str(self.definitions), installation_roots=[self.models_dir]
        )
        self.service = ModelInstallService(self.repository)

    def tearDown(self) -> None:
        self.models_dir_patch.stop()
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
        self.assertEqual(list(self.models_dir.glob(".demo.*")), [])

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
        self.assertEqual(list(self.models_dir.glob(".demo.*")), [])

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

    def test_custom_installation_path_is_rejected_without_changes(self):
        custom = self.root / "custom" / "demo"
        write_package(custom, "1.0.0")
        model = self.repository.get_model("demo")
        model.update(path=str(custom), installed=True)

        with patch.object(self.repository, "update_model", wraps=self.repository.update_model) as update:
            self.assertFalse(self.service.update_package("demo", str(self.source)))

        self.assertEqual(b"weights-1.0.0", (custom / "model.onnx").read_bytes())
        self.assertEqual(b"weights-1.0.0", (self.installed / "model.onnx").read_bytes())
        update.assert_not_called()

    def test_historical_default_outside_current_models_root_is_rejected(self):
        historical = self.root / "SnapdragonAI" / "models" / "demo"
        write_package(historical, "1.0.0")
        model = self.repository.get_model("demo")
        model.update(path=str(historical), installed=True)

        self.assertFalse(self.service.update_package("demo", str(self.source)))

        self.assertEqual(b"weights-1.0.0", (historical / "model.onnx").read_bytes())
        self.assertEqual("1.0.0", model["version"])

    def test_parent_and_sibling_paths_are_rejected(self):
        for stored_path in (self.models_dir, self.models_dir / "sibling"):
            with self.subTest(path=stored_path):
                stored_path.mkdir(exist_ok=True)
                marker = stored_path / "keep.txt"
                marker.write_text("keep", encoding="utf-8")
                model = self.repository.get_model("demo")
                model.update(path=str(stored_path), installed=True, version="1.0.0")

                self.assertFalse(self.service.update_package("demo", str(self.source)))

                self.assertTrue(marker.is_file())

    def test_unsafe_model_ids_are_rejected_before_repository_or_filesystem_access(self):
        protected = self.root / "protected"
        protected.mkdir()
        for model_id in ("", "..", "../protected", r"..\protected", str(protected.resolve())):
            with self.subTest(model_id=model_id), patch.object(
                self.repository, "get_model", wraps=self.repository.get_model
            ) as get_model:
                self.assertFalse(self.service.update_package(model_id, str(self.source)))
                get_model.assert_not_called()
                self.assertTrue(protected.is_dir())

    def test_backup_and_staging_paths_cannot_escape_managed_root(self):
        class UnsafeOperationId:
            hex = "../../../../outside"

        with patch("engine.model_install_service.uuid4", return_value=UnsafeOperationId()), patch.object(
            self.service, "_copy_local_package_source"
        ) as copy_source:
            self.assertFalse(self.service.update_package("demo", str(self.source)))

        copy_source.assert_not_called()
        self.assertEqual(b"weights-1.0.0", (self.installed / "model.onnx").read_bytes())


class ManagedQaiCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.managed_temp = self.root / "managed-temp"
        self.managed_temp.mkdir()
        self.service = ModelInstallService.__new__(ModelInstallService)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_managed_qai_appbuilder_directory_is_deleted(self) -> None:
        target = self.managed_temp / "qai-appbuilder-main"
        nested = target / "samples" / "models"
        nested.mkdir(parents=True)
        (nested / "model.bin").write_bytes(b"model")

        with patch("engine.model_install_service.TEMP_DIR", self.managed_temp):
            self.assertTrue(self.service._safe_cleanup_qai_appbuilder_main(str(nested)))

        self.assertFalse(target.exists())

    def test_same_directory_name_outside_managed_temp_is_preserved(self) -> None:
        target = self.root / "outside" / "qai-appbuilder-main"
        target.mkdir(parents=True)

        with patch("engine.model_install_service.TEMP_DIR", self.managed_temp):
            self.assertFalse(self.service._safe_cleanup_qai_appbuilder_main(str(target)))

        self.assertTrue(target.is_dir())

    def test_managed_temp_root_itself_is_never_deleted(self) -> None:
        managed_root = self.root / "qai-appbuilder-main"
        managed_root.mkdir()

        with patch("engine.model_install_service.TEMP_DIR", managed_root):
            self.assertFalse(self.service._safe_cleanup_qai_appbuilder_main(str(managed_root)))

        self.assertTrue(managed_root.is_dir())

    def test_parent_and_sibling_qai_directories_are_blocked(self) -> None:
        parent = self.root / "qai-appbuilder-main"
        sibling = self.root / "sibling" / "qai-appbuilder-main"
        parent.mkdir()
        sibling.mkdir(parents=True)

        with patch("engine.model_install_service.TEMP_DIR", self.managed_temp):
            self.assertFalse(self.service._safe_cleanup_qai_appbuilder_main(str(parent)))
            self.assertFalse(self.service._safe_cleanup_qai_appbuilder_main(str(sibling)))

        self.assertTrue(parent.is_dir())
        self.assertTrue(sibling.is_dir())

    def test_snapdragonai_name_has_no_special_case_inside_dynamic_temp(self) -> None:
        dynamic_temp = self.root / "SnapdragonAI" / "temp"
        target = dynamic_temp / "qai-appbuilder-main"
        target.mkdir(parents=True)

        with patch("engine.model_install_service.TEMP_DIR", dynamic_temp):
            self.assertTrue(self.service._safe_cleanup_qai_appbuilder_main(str(target)))

        self.assertFalse(target.exists())

    def test_symlink_escape_is_blocked_when_supported(self) -> None:
        outside = self.root / "outside" / "qai-appbuilder-main"
        outside.mkdir(parents=True)
        link = self.managed_temp / "qai-appbuilder-main"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Directory symlinks unavailable: {exc}")

        with patch("engine.model_install_service.TEMP_DIR", self.managed_temp):
            self.assertFalse(self.service._safe_cleanup_qai_appbuilder_main(str(link)))

        self.assertTrue(outside.is_dir())


if __name__ == "__main__":
    unittest.main()
