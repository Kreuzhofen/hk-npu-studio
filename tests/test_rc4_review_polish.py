from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from app.i18n import set_language, tr
from dialogs.update_dialog import UpdateDialog


class Rc4ReviewPolishTests(unittest.TestCase):
    def setUp(self) -> None:
        set_language("de_DE")

    def tearDown(self) -> None:
        set_language("de_DE")

    def test_spanish_menu_update_translation(self) -> None:
        locales_dir = Path(__file__).parent.parent / "locales"
        es_data = json.loads((locales_dir / "es_ES.json").read_text(encoding="utf-8"))
        self.assertEqual(es_data.get("menu_update"), "Actualización")

    def test_all_locales_key_parity(self) -> None:
        locales_dir = Path(__file__).parent.parent / "locales"
        de_keys = set(json.loads((locales_dir / "de_DE.json").read_text(encoding="utf-8")).keys())
        en_keys = set(json.loads((locales_dir / "en_US.json").read_text(encoding="utf-8")).keys())
        es_keys = set(json.loads((locales_dir / "es_ES.json").read_text(encoding="utf-8")).keys())
        self.assertEqual(de_keys - en_keys, set())
        self.assertEqual(en_keys - de_keys, set())
        self.assertEqual(de_keys - es_keys, set())

    def test_update_dialog_newer_installed_version_display(self) -> None:
        details = UpdateDialog._version_details(
            installed_version="2.0.0-rc.4",
            remote_version="2.0.0-rc.3",
            remote_key="update_latest_version",
            remote_fallback="Neueste Version",
        )
        self.assertIn("Installierte Version:  v2.0.0-rc.4", details)
        self.assertIn("Neueste öffentliche Version:  v2.0.0-rc.3", details)
        self.assertIn("(Installierter Release Candidate ist neuer)", details)

    def test_update_dialog_normal_update_display(self) -> None:
        details = UpdateDialog._version_details(
            installed_version="2.0.0-rc.3",
            remote_version="2.0.0-rc.4",
            remote_key="update_latest_version",
            remote_fallback="Neueste Version",
        )
        self.assertIn("Installierte Version:  v2.0.0-rc.3", details)
        self.assertIn("Neueste Version:  v2.0.0-rc.4", details)
        self.assertNotIn("(Installierter Release Candidate ist neuer)", details)

    def test_update_dialog_empty_remote_version_fallbacks(self) -> None:
        set_language("en_US")
        details = UpdateDialog._version_details(
            installed_version="",
            remote_version=None,
            remote_key="update_latest_version",
            remote_fallback="Latest Version",
        )
        self.assertEqual(details.count("Unknown"), 2)

    def test_home_view_dismissal_preserves_file(self) -> None:
        from widgets.phoenix.views.home_view import PhoenixHomeView

        view = object.__new__(PhoenixHomeView)
        view._dismissed_generations = set()
        view.refresh = MagicMock()

        fake_path = Path("output/sample_gen.png")
        view._dismiss_generation(fake_path)
        self.assertIn("sample_gen.png", view._dismissed_generations)
        view.refresh.assert_called_once_with(force=True)

    def test_home_view_cache_invalidation_and_show_view(self) -> None:
        from widgets.phoenix.views.home_view import PhoenixHomeView
        from widgets.phoenix.workspace import PhoenixWorkspace

        view = object.__new__(PhoenixHomeView)
        view._cached_installed_packages = "2"
        view._cached_discovery = object()
        view.invalidate_cache()
        self.assertIsNone(view._cached_installed_packages)
        self.assertIsNone(view._cached_discovery)

        ws = object.__new__(PhoenixWorkspace)
        ws._view_factories = {"home": lambda _: view}
        ws._views = {"home": view}
        ws.current_view = "models"
        ws.right_panel = None
        ws.sidebar = MagicMock()
        ws.header = MagicMock()
        ws._view_title = MagicMock(return_value="Home")
        view.grid = MagicMock()
        view.grid_forget = MagicMock()
        view.refresh = MagicMock()
        view.invalidate_cache = MagicMock()

        ws.show_view("home")
        view.invalidate_cache.assert_called_once()
        view.refresh.assert_called_once_with(force=True)
