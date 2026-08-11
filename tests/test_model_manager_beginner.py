import json
import unittest
from pathlib import Path

from app.i18n import set_language, tr
from widgets.phoenix.views.model_manager_view import PhoenixModelManagerView


class ModelManagerBeginnerTests(unittest.TestCase):
    def test_beginner_guidance_is_localized(self) -> None:
        set_language("de_DE")
        self.assertIn("empfohlene Modell", tr("model_beginner_guide"))

    def test_exactly_one_supported_recommendation(self) -> None:
        models = [
            {"id": "stable_diffusion_v1_5_qnn"},
            {"id": "stable_diffusion_v2_1_qnn"},
            {"id": "stable_diffusion_v3_5_qai"},
            {"id": "sdxl_base"},
        ]
        recommended = [
            model for model in models
            if PhoenixModelManagerView._is_beginner_recommended(model)
        ]
        self.assertEqual(recommended, [{"id": "stable_diffusion_v1_5_qnn"}])

    def test_action_states(self) -> None:
        action = PhoenixModelManagerView._model_action_state
        self.assertEqual(action(False, False), "install")
        self.assertEqual(action(True, False), "use")
        self.assertEqual(action(True, True), "active")

    def test_display_names_use_metadata_without_backend_suffixes(self) -> None:
        display_name = PhoenixModelManagerView._display_name
        self.assertEqual(
            display_name({"id": "stable_diffusion_v1_5_qnn", "display_name": "Stable Diffusion 1.5 QNN"}),
            "Stable Diffusion 1.5",
        )
        self.assertEqual(
            display_name({"id": "stable_diffusion_v1_5_qai", "display_name": "Stable Diffusion 1.5 QAI AppBuilder"}),
            "Stable Diffusion 1.5",
        )
        self.assertEqual(
            display_name({"id": "stable_diffusion_v2_1_qai", "display_name": "Stable Diffusion 2.1 QAI AppBuilder"}),
            "Stable Diffusion 2.1",
        )
        self.assertEqual(
            display_name({"id": "stable_diffusion_v3_5_qai", "display_name": "Stable Diffusion 3.5 Medium QAI AppBuilder"}),
            "Stable Diffusion 3.5 Medium",
        )

    def test_display_name_fallback_order(self) -> None:
        display_name = PhoenixModelManagerView._display_name
        self.assertEqual(display_name({"display_name": "Friendly", "name": "Other"}), "Friendly")
        self.assertEqual(display_name({"name": "Named", "title": "Titled"}), "Named")
        self.assertEqual(display_name({"title": "Titled", "id": "technical_id"}), "Titled")

    def test_duplicate_names_have_clear_localized_variants(self) -> None:
        set_language("de_DE")
        title = PhoenixModelManagerView._display_title
        standard = title({"display_name": "Stable Diffusion 1.5", "beginner_variant_label": "Standard package"})
        local = title({"display_name": "Stable Diffusion 1.5", "beginner_variant_label": "Local package"})
        self.assertEqual(standard, "Stable Diffusion 1.5 — Standardpaket")
        self.assertEqual(local, "Stable Diffusion 1.5 — Lokales Paket")
        self.assertNotEqual(standard, local)

    def test_localization_keys_complete(self) -> None:
        required = {
            "model_beginner_guide", "model_beginner_recommended",
            "model_quality_entry", "model_quality_high", "model_quality_good",
            "model_speed_fast", "model_speed_patient", "model_speed_balanced",
            "model_storage_approx", "model_storage_package",
            "model_status_active_ready", "model_status_installed",
            "model_status_not_installed", "model_install_action",
            "model_use_action", "model_active_ready_action",
            "model_variant_standard", "model_variant_external", "model_variant_local",
        }
        root = Path(__file__).resolve().parents[1]
        for locale in ("de_DE", "en_US", "es_ES"):
            data = json.loads((root / "locales" / f"{locale}.json").read_text(encoding="utf-8"))
            self.assertTrue(required.issubset(data), locale)


if __name__ == "__main__":
    unittest.main()
