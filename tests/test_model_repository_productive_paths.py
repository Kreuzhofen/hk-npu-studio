import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from controllers.model_repository import ModelRepository


def model_data(model_id, path, required):
    return {
        "id": model_id,
        "display_name": model_id,
        "author": "Test",
        "version": "1",
        "license": "Test",
        "description": "Test",
        "category": "Text-to-Image",
        "backend": "Test",
        "recommended_backend": "Test",
        "minimum_ram_gb": 1,
        "recommended_ram_gb": 1,
        "supports": ["txt2img"],
        "installed": True,
        "downloaded": True,
        "path": str(path),
        "status": "Ready",
        "required_files": required,
        "capabilities": {"txt2img": True},
    }


class ProductiveModelPathTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.definitions = self.base / "definitions"
        self.models = self.base / "models"
        self.phoenix_temp = self.base / "temp"
        self.definitions.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _repository(self, entries, roots=None):
        for entry in entries:
            (self.definitions / f"{entry['id']}.json").write_text(
                json.dumps(entry), encoding="utf-8"
            )
        with patch("controllers.model_repository.TEMP_DIR", self.phoenix_temp):
            return ModelRepository(
                str(self.definitions), installation_roots=roots or [self.models]
            )

    def _make_valid(self, root, model_id, filename="model.bin"):
        folder = root / model_id
        folder.mkdir(parents=True)
        (folder / filename).write_bytes(b"valid")
        return folder

    def test_01_inspection_temp_path_is_not_installed(self):
        path = self._make_valid(self.phoenix_temp, "sd15_inspection")
        model = self._repository([model_data("sd15", path, ["model.bin"]) ]).get_model("sd15")
        self.assertFalse(model["installed"])
        self.assertEqual(model["status"], "Not Installed")

    def test_02_gate_temp_path_is_not_installed(self):
        path = self._make_valid(self.phoenix_temp, "controlnet_gate")
        model = self._repository([model_data("canny", path, ["model.bin"]) ]).get_model("canny")
        self.assertFalse(model["installed"])

    def test_03_arbitrary_temp_subpath_is_not_installed(self):
        path = self._make_valid(self.phoenix_temp / "setup" / "staging", "future")
        model = self._repository([model_data("future", path, ["model.bin"]) ]).get_model("future")
        self.assertFalse(model["installed"])

    def test_04_missing_productive_folder_with_temp_copy_is_not_installed(self):
        temp_path = self._make_valid(self.phoenix_temp, "sd21")
        model = self._repository([model_data("sd21", temp_path, ["model.bin"]) ]).get_model("sd21")
        self.assertFalse((self.models / "sd21").exists())
        self.assertEqual(model["status"], "Not Installed")

    def test_05_valid_configured_models_path_remains_ready(self):
        path = self._make_valid(self.models, "sdxl")
        model = self._repository([model_data("sdxl", path, ["model.bin"]) ]).get_model("sdxl")
        self.assertTrue(model["installed"])
        self.assertEqual(model["status"], "Ready")

    def test_06_custom_models_dir_remains_supported(self):
        custom = self.base / "custom-models"
        path = self._make_valid(custom, "custom")
        model = self._repository(
            [model_data("custom", path, ["model.bin"])], roots=[custom]
        ).get_model("custom")
        self.assertTrue(model["installed"])
        self.assertEqual(Path(model["path"]), path.resolve())

    def test_07_rule_is_generic_for_two_model_types(self):
        qnn = self._make_valid(self.phoenix_temp, "qnn_gate")
        controlnet = self._make_valid(self.phoenix_temp, "controlnet_inspection")
        repository = self._repository([
            model_data("sd15_qnn", qnn, ["model.bin"]),
            model_data("controlnet", controlnet, ["model.bin"]),
        ])
        self.assertFalse(repository.get_model("sd15_qnn")["installed"])
        self.assertFalse(repository.get_model("controlnet")["installed"])


if __name__ == "__main__":
    unittest.main()
