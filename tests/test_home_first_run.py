import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.i18n import set_language, tr
from widgets.phoenix.views.home_view import PhoenixHomeView


class HomeFirstRunTests(unittest.TestCase):
    def _view_stub(self):
        return SimpleNamespace(
            _model_ready=False,
            _readiness_title=MagicMock(),
            _readiness_status=MagicMock(),
            _readiness_button=MagicMock(),
        )

    def test_no_model_shows_install_action(self) -> None:
        view = self._view_stub()
        PhoenixHomeView._render_readiness(view, False)
        self.assertFalse(view._model_ready)
        self.assertEqual(
            view._readiness_title.configure.call_args.kwargs["text"],
            tr("home_setup_required"),
        )
        self.assertEqual(
            view._readiness_button.configure.call_args.kwargs["text"],
            tr("home_start_setup"),
        )
        status = view._readiness_status.configure.call_args.kwargs["text"]
        self.assertIn("✓ " + tr("home_model_folder_ready"), status)
        self.assertIn("✓ " + tr("home_system_ready"), status)
        self.assertIn("→ " + tr("home_select_install_next"), status)

    def test_active_model_shows_generate_action(self) -> None:
        view = self._view_stub()
        PhoenixHomeView._render_readiness(view, True)
        self.assertTrue(view._model_ready)
        self.assertEqual(
            view._readiness_title.configure.call_args.kwargs["text"],
            tr("home_studio_ready"),
        )
        self.assertEqual(
            view._readiness_button.configure.call_args.kwargs["text"],
            tr("home_create_first_image"),
        )

    def test_readiness_navigation(self) -> None:
        navigate = MagicMock()
        view = SimpleNamespace(_model_ready=False, _navigate=navigate)
        PhoenixHomeView._on_readiness_action(view)
        navigate.assert_called_once_with("models")
        navigate.reset_mock()
        view._model_ready = True
        PhoenixHomeView._on_readiness_action(view)
        navigate.assert_called_once_with("prompt")

    def test_localization_keys_complete(self) -> None:
        required = {
            "home_setup_required", "home_studio_ready", "home_model_folder_ready",
            "home_model_folder_not_ready", "home_system_ready", "home_system_not_ready",
            "home_select_install_next", "home_start_setup", "home_create_first_image",
        }
        root = Path(__file__).resolve().parents[1]
        for locale in ("de_DE", "en_US", "es_ES"):
            data = json.loads((root / "locales" / f"{locale}.json").read_text(encoding="utf-8"))
            self.assertTrue(required.issubset(data), locale)
            set_language(locale)
            for key in required:
                self.assertNotEqual(tr(key), key)


if __name__ == "__main__":
    unittest.main()
