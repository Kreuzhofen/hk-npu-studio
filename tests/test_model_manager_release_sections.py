import json
import unittest
from pathlib import Path

from app.i18n import set_language
from widgets.phoenix.views.model_manager_view import PhoenixModelManagerView


class ModelManagerReleaseSectionsTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    @classmethod
    def setUpClass(cls) -> None:
        cls.models = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((cls.ROOT / "resources" / "models").glob("*.json"))
        ]
        catalog = json.loads((cls.ROOT / "resources" / "package_catalog.json").read_text(encoding="utf-8"))
        cls.catalog = {entry["model_id"]: entry for entry in catalog["packages"]}

    def tearDown(self) -> None:
        set_language("de_DE")

    def test_exact_release_sections_and_catalog_contract(self) -> None:
        available, experimental = PhoenixModelManagerView._partition_models(self.models)
        self.assertEqual([model["id"] for model in available], list(PhoenixModelManagerView.AVAILABLE_MODEL_ORDER))
        self.assertEqual([model["id"] for model in experimental], list(PhoenixModelManagerView.EXPERIMENTAL_MODEL_ORDER))
        visible_ids = {model["id"] for model in available + experimental}
        self.assertTrue(set(PhoenixModelManagerView.HIDDEN_TECHNICAL_VARIANTS).isdisjoint(visible_ids))
        for model in self.models:
            self.assertEqual(model["release_status"], self.catalog[model["id"]]["release_status"])

    def test_hidden_qai_contracts_and_backends_remain_registered(self) -> None:
        model_ids = {model["id"] for model in self.models}
        self.assertTrue(set(PhoenixModelManagerView.HIDDEN_TECHNICAL_VARIANTS).issubset(model_ids))
        source = (self.ROOT / "engine" / "inference_backend_factory.py").read_text(encoding="utf-8")
        self.assertIn("Qualcomm SD1.5 QAI AppBuilder (HTP)", source)
        self.assertIn("Qualcomm SD2.1 QAI AppBuilder (HTP)", source)

    def test_experimental_install_action_is_disabled_but_installed_entry_remains(self) -> None:
        for model in self.models:
            if model["release_status"] == "experimental":
                self.assertFalse(PhoenixModelManagerView._offers_normal_install(model))
        installed = dict(next(model for model in self.models if model["id"] == "sdxl_base"), installed=True)
        _, experimental = PhoenixModelManagerView._partition_models([installed])
        self.assertEqual(experimental, [installed])
        self.assertEqual(PhoenixModelManagerView._model_action_state(True, False), "use")

    def test_available_actions_titles_and_ratings_remain_productive(self) -> None:
        available, _ = PhoenixModelManagerView._partition_models(self.models)
        set_language("de_DE")
        for model in available:
            self.assertTrue(PhoenixModelManagerView._offers_normal_install(model))
            self.assertNotIn("Standardpaket", PhoenixModelManagerView._display_title(model))
            self.assertNotIn("Externes Paket", PhoenixModelManagerView._display_title(model))
            self.assertIn("★", PhoenixModelManagerView._beginner_model_summary(model, False))
        controlnet = next(model for model in available if model["id"] == "controlnet_canny_qnn")
        summary = PhoenixModelManagerView._beginner_model_summary(controlnet, False)
        self.assertIn("Strukturkontrolle", summary)
        self.assertNotIn("Bildqualität", summary)

    def test_new_locale_keys_exist_in_all_languages(self) -> None:
        keys = {
            "model_section_available", "model_section_experimental", "model_phoenix_rating_note",
            "model_image_quality_very_high", "model_image_quality_high", "model_image_quality_good",
            "model_structure_control_very_high", "model_summary_sd35", "model_summary_sd21",
            "model_summary_sd15", "model_summary_controlnet", "model_status_in_development",
            "model_experimental_summary",
        }
        for name in ("de_DE.json", "en_US.json", "es_ES.json"):
            locale = json.loads((self.ROOT / "locales" / name).read_text(encoding="utf-8"))
            self.assertTrue(keys.issubset(locale), name)
            self.assertTrue(all(locale[key] and "{" not in locale[key] for key in keys), name)


if __name__ == "__main__":
    unittest.main()
