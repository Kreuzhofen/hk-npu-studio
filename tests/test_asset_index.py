from __future__ import annotations

import json
from pathlib import Path
import tempfile
import time
import unittest

from PIL import Image

from engine.asset_index import AssetIndexRepository, AssetScanner, SCHEMA_VERSION


class AssetIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.output = self.root / "output"
        self.output.mkdir()
        self.repository = AssetIndexRepository(self.root / "data" / "assets.sqlite3")
        self.scanner = AssetScanner(self.repository)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_image(self, name: str, size: tuple[int, int] = (8, 6)) -> Path:
        path = self.output / name
        Image.new("RGB", size, "navy").save(path)
        return path

    def test_empty_scan_and_schema_version(self) -> None:
        result = self.scanner.scan(self.output)
        self.assertEqual(0, result.discovered)
        self.assertEqual(SCHEMA_VERSION, self.repository.schema_version())

    def test_sidecars_extensions_and_repeat_scan(self) -> None:
        plain = self.create_image("plain.png")
        rich = self.create_image("rich.PNG")
        rich.with_suffix(".json").write_text(json.dumps({
            "prompt": "sidecar prompt", "model": "sd15", "cfg": 7.5,
            "seed": 42, "steps": 20, "width": 12, "height": 10,
        }), encoding="utf-8")
        partial = self.create_image("partial.webp")
        partial.with_suffix(".json").write_text(json.dumps({"prompt": "partial"}), encoding="utf-8")
        invalid = self.create_image("invalid.jpg")
        invalid.with_suffix(".json").write_text("{invalid", encoding="utf-8")

        first = self.scanner.scan(self.output)
        second = self.scanner.scan(self.output)
        assets = self.repository.list_assets()
        self.assertEqual((4, 4, 1), (first.discovered, first.inserted, first.errors))
        self.assertEqual((4, 0, 4), (second.discovered, second.inserted, second.unchanged))
        self.assertEqual(4, len(assets))
        rich_record = next(asset for asset in assets if asset.filename == rich.name)
        self.assertEqual(("sidecar prompt", "sd15", 7.5, 12, 10), (
            rich_record.prompt, rich_record.model_id, rich_record.cfg_scale,
            rich_record.width, rich_record.height,
        ))
        self.assertTrue(plain.exists())

    def test_file_sidecar_missing_restore_rebuild_and_preferences(self) -> None:
        image = self.create_image("changing.png")
        sidecar = image.with_suffix(".json")
        sidecar.write_text(json.dumps({"prompt": "one"}), encoding="utf-8")
        self.scanner.scan(self.output)
        with self.repository._connect() as connection:
            connection.execute(
                "UPDATE assets SET favorite = ?, rating = ? WHERE filename = ?", (1, 4, image.name)
            )

        time.sleep(0.01)
        Image.new("RGB", (11, 9), "red").save(image)
        changed_file = self.scanner.scan(self.output)
        time.sleep(0.01)
        sidecar.write_text(json.dumps({"prompt": "two"}), encoding="utf-8")
        changed_sidecar = self.scanner.scan(self.output)
        record = self.repository.list_assets()[0]
        self.assertEqual((1, 1), (changed_file.updated, changed_sidecar.updated))
        self.assertEqual(("two", 11, 9, True, 4), (
            record.prompt, record.width, record.height, record.favorite, record.rating,
        ))

        image.unlink()
        missing = self.scanner.scan(self.output)
        self.assertEqual(1, missing.missing)
        self.assertTrue(self.repository.list_assets(include_missing=True)[0].missing)
        self.create_image("changing.png", (11, 9))
        restored = self.scanner.scan(self.output)
        self.assertEqual(1, restored.updated)
        self.assertFalse(self.repository.list_assets()[0].missing)

        rebuilt = self.scanner.scan(self.output, rebuild=True)
        self.assertEqual(1, rebuilt.inserted)
        self.assertEqual(1, len(self.repository.list_assets()))

    def test_parameterized_path_with_quote(self) -> None:
        image = self.create_image("owner's image.jpeg")
        result = self.scanner.scan(self.output)
        self.assertEqual(1, result.inserted)
        self.assertEqual(image.name, self.repository.list_assets()[0].filename)

    def test_nested_sidecar_uses_same_metadata_contract_as_gallery(self) -> None:
        image = self.create_image("nested.png")
        image.with_suffix(".json").write_text(
            json.dumps(
                {
                    "controlnet_enabled": True,
                    "metadata": {"prompt": "nested prompt", "model_id": "model-a"},
                }
            ),
            encoding="utf-8",
        )

        self.scanner.scan(self.output)
        record = self.repository.list_assets()[0]

        self.assertEqual("nested prompt", record.prompt)
        self.assertEqual("model-a", record.model_id)


if __name__ == "__main__":
    unittest.main()
