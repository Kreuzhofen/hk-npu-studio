import json
import unittest
from collections import defaultdict
from pathlib import Path

from app.model_downloader import ModelDownloader


class ModelSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.models = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((cls.root / "resources" / "models").glob("*.json"))
        ]
        catalog_data = json.loads(
            (cls.root / "resources" / "package_catalog.json").read_text(encoding="utf-8")
        )
        cls.catalog = {entry["model_id"]: entry for entry in catalog_data["packages"]}

    def test_every_visible_model_has_one_complete_source_contract(self) -> None:
        required = {
            "display_name", "beginner_variant_label", "source_type",
            "source_url", "package_format", "download_size", "requires_hf_token",
        }
        for model in self.models:
            with self.subTest(model=model["id"]):
                self.assertTrue(required.issubset(model))
                self.assertIn(model["source_type"], {"direct", "official_external", "local_only"})
                self.assertIn(model["id"], self.catalog)
                for field in required:
                    self.assertEqual(model[field], self.catalog[model["id"]][field])

    def test_direct_sources_are_existing_downloader_sources(self) -> None:
        for model in self.models:
            if model["source_type"] != "direct":
                continue
            with self.subTest(model=model["id"]):
                self.assertTrue(model["source_url"].startswith("https://"))
                self.assertEqual(model["source_url"], ModelDownloader.MODEL_URLS.get(model["id"]))
                self.assertEqual(model["source_url"], self.catalog[model["id"]]["download_url"])

    def test_local_only_models_define_import_format_without_fake_source(self) -> None:
        for model in self.models:
            if model["source_type"] != "local_only":
                continue
            with self.subTest(model=model["id"]):
                self.assertEqual(model["source_url"], "")
                self.assertEqual(model["package_format"], "smp_or_zip")

    def test_external_sources_have_an_existing_official_page(self) -> None:
        for model in self.models:
            if model["source_type"] != "official_external":
                continue
            with self.subTest(model=model["id"]):
                self.assertTrue(model["source_url"].startswith("https://aihub.qualcomm.com/"))
                self.assertEqual(model["package_format"], "smp_or_zip")

    def test_duplicate_display_names_have_distinct_variant_labels(self) -> None:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for model in self.models:
            grouped[model["display_name"]].append(model)
        for name, variants in grouped.items():
            if len(variants) < 2:
                continue
            labels = [str(model["beginner_variant_label"]).strip() for model in variants]
            with self.subTest(display_name=name):
                self.assertTrue(all(labels))
                self.assertEqual(len(labels), len(set(labels)))


if __name__ == "__main__":
    unittest.main()
