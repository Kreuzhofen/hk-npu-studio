from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from controllers.model_repository import ModelRepository
from engine.model_registry import ModelHealthStatus, ModelRegistry
from engine.sd35_qai_appbuilder_backend import _model_dir


def valid_metadata(**overrides):
    data = {
        "id": "demo",
        "display_name": "Demo",
        "author": "Test",
        "version": "1.0.0",
        "license": "Test",
        "description": "Test model",
        "category": "Image",
        "backend": "ONNX Runtime",
        "recommended_backend": "ONNX Runtime (Stub)",
        "minimum_ram_gb": 1,
        "recommended_ram_gb": 2,
        "supports": ["txt2img"],
        "installed": False,
        "downloaded": False,
        "path": "",
        "status": "Available",
        "capabilities": {"txt2img": True, "onnx_runtime": True},
    }
    data.update(overrides)
    return data


class ModelRegistryTests(unittest.TestCase):
    def test_metadata_is_normalized_to_current_schema(self):
        result = ModelRegistry().validate_metadata(
            valid_metadata(), available_backends=["ONNX Runtime (Stub)"]
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.metadata["schema_version"], 1)
        self.assertEqual(result.status, ModelHealthStatus.AVAILABLE)

    def test_missing_metadata_is_rejected_and_backend_issue_is_reported(self):
        data = valid_metadata(recommended_backend="Unknown")
        del data["capabilities"]

        result = ModelRegistry().validate_metadata(
            data, available_backends=["ONNX Runtime (Stub)"]
        )

        self.assertFalse(result.valid)
        self.assertEqual(result.status, ModelHealthStatus.INVALID)
        self.assertEqual(
            {issue.code for issue in result.issues},
            {"required_field_missing", "backend_incompatible"},
        )

    def test_backend_incompatibility_is_diagnostic_not_quarantine(self):
        result = ModelRegistry().validate_metadata(
            valid_metadata(recommended_backend="Future Backend"),
            available_backends=["ONNX Runtime (Stub)"],
        )

        self.assertTrue(result.valid)
        self.assertEqual(
            [issue.code for issue in result.issues], ["backend_incompatible"]
        )

    def test_installed_model_with_missing_path_is_invalid(self):
        result = ModelRegistry().validate_installation(
            valid_metadata(installed=True, path="Z:/does-not-exist")
        )

        self.assertFalse(result.valid)
        self.assertEqual(result.status, ModelHealthStatus.INVALID)
        self.assertEqual(result.issues[0].code, "installation_missing")

    def test_manifest_structure_and_sha256_are_validated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            component = base / "model.onnx"
            component.write_bytes(b"model")
            digest = hashlib.sha256(b"model").hexdigest()
            (base / "package.json").write_text(
                json.dumps(
                    {
                        "model_id": "demo",
                        "components": {
                            "unet": {
                                "path": "model.onnx",
                                "runtime": "ONNX",
                                "sha256": digest,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = ModelRegistry().validate_installation(
                valid_metadata(installed=True, path=str(base)),
                verify_hashes=True,
            )

            self.assertTrue(result.valid)
            self.assertEqual(result.checked_hashes, 1)
            self.assertEqual(result.status, ModelHealthStatus.READY)

            component.write_bytes(b"tampered")
            invalid = ModelRegistry().validate_installation(
                valid_metadata(installed=True, path=str(base)),
                verify_hashes=True,
            )
            self.assertFalse(invalid.valid)
            self.assertIn("hash_mismatch", {issue.code for issue in invalid.issues})

    def test_component_paths_cannot_escape_package(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "package.json").write_text(
                json.dumps(
                    {
                        "model_id": "demo",
                        "components": {
                            "unet": {"path": "../outside.onnx", "runtime": "ONNX"}
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = ModelRegistry().validate_installation(
                valid_metadata(installed=True, path=str(base))
            )

            self.assertFalse(result.valid)
            self.assertIn(
                "unsafe_component_path", {issue.code for issue in result.issues}
            )

    def test_repository_quarantines_invalid_definitions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "valid.json").write_text(
                json.dumps(valid_metadata()), encoding="utf-8"
            )
            (base / "broken.json").write_text("{", encoding="utf-8")

            repository = ModelRepository(str(base))

            self.assertEqual([model["id"] for model in repository.get_all_models()], ["demo"])
            self.assertIn("broken.json", repository.get_invalid_models())

    def test_repository_uses_shared_backend_resolution(self):
        class Backend:
            pass

        expected = Backend()

        class Manager:
            def get_best_backend(self, model):
                self.model = model
                return expected

        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            (base / "valid.json").write_text(
                json.dumps(valid_metadata()), encoding="utf-8"
            )
            repository = ModelRepository(str(base))
            manager = Manager()

            self.assertIs(repository.resolve_backend("demo", manager), expected)
            self.assertEqual(manager.model["id"], "demo")

    def test_repository_resolves_stale_definition_from_configured_models_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            definitions = base / "definitions"
            installations = base / "models"
            definitions.mkdir()
            installed_model = installations / "demo"
            installed_model.mkdir(parents=True)
            (installed_model / "package.json").write_text(
                json.dumps({"model_id": "demo", "components": {}}),
                encoding="utf-8",
            )
            (definitions / "demo.json").write_text(
                json.dumps(valid_metadata(installed=False, path="")),
                encoding="utf-8",
            )

            repository = ModelRepository(
                str(definitions),
                installation_roots=[installations],
            )
            model = repository.get_model("demo")

            self.assertIsNotNone(model)
            self.assertTrue(model["installed"])
            self.assertEqual(Path(model["path"]), installed_model.resolve())

    def test_repository_prefers_existing_declared_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            definitions = base / "definitions"
            declared = base / "declared"
            configured = base / "models"
            definitions.mkdir()
            declared.mkdir()
            (configured / "demo").mkdir(parents=True)
            (definitions / "demo.json").write_text(
                json.dumps(valid_metadata(installed=True, path=str(declared))),
                encoding="utf-8",
            )

            repository = ModelRepository(
                str(definitions),
                installation_roots=[configured],
            )

            self.assertEqual(
                Path(repository.get_model("demo")["path"]),
                declared.resolve(),
            )

    def test_frozen_upgrade_includes_existing_installation_models_root(self):
        executable = Path("C:/Program Files/Snapdragon AI Studio/SnapdragonAIStudio.exe")
        with patch("controllers.model_repository.sys.frozen", True, create=True), patch(
            "controllers.model_repository.sys.executable", str(executable)
        ), patch(
            "controllers.model_repository.ConfigurationManager.load", return_value={}
        ):
            roots = ModelRepository._build_installation_roots(
                None, include_configured_roots=True
            )
        self.assertIn(executable.parent / "models", roots)

    def test_sd35_backend_uses_existing_frozen_legacy_model_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir) / "SnapdragonAIStudio.exe"
            legacy = executable.parent / "models" / "stable_diffusion_v3_5_qai"
            legacy.mkdir(parents=True)
            missing_canonical = executable.parent / "new-models"
            with patch("engine.sd35_qai_appbuilder_backend.sys.frozen", True, create=True), patch(
                "engine.sd35_qai_appbuilder_backend.sys.executable", str(executable)
            ), patch(
                "engine.sd35_qai_appbuilder_backend.MODELS_DIR", missing_canonical
            ):
                self.assertEqual(_model_dir(), legacy)


if __name__ == "__main__":
    unittest.main()
