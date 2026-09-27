import json
import subprocess
import sys
import tkinter as tk
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.i18n import set_language, tr
from widgets.phoenix.views.home_view import (
    PhoenixHomeView,
    RC3_AUTOMATIC_GENERATION_MODEL_SETUP,
    RC3_PRIMARY_PRODUCT_VIEW,
)


class HomeFirstRunTests(unittest.TestCase):
    def _view_stub(self):
        return SimpleNamespace(
            _model_ready=False,
            _readiness_title=MagicMock(),
            _readiness_status=MagicMock(),
            _readiness_button=MagicMock(),
            _readiness_energy_dots=MagicMock(),
            _draw_energy_dots=MagicMock(),
            _start_energy_flow=MagicMock(),
            _stop_energy_flow=MagicMock(),
        )

    def test_no_model_shows_install_action_and_energy_dots(self) -> None:
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
        view._start_energy_flow.assert_called_once_with()
        view._readiness_energy_dots.grid.assert_called_once_with()

    def test_active_model_hides_energy_dots(self) -> None:
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
        view._stop_energy_flow.assert_called_once_with()
        view._readiness_energy_dots.grid_remove.assert_called_once_with()

    def test_energy_flow_lifecycle_is_cancelled_on_unmap_and_destroy(self) -> None:
        view = PhoenixHomeView.__new__(PhoenixHomeView)
        view._model_ready = False
        view._energy_flow_after_id = None
        view._energy_flow_step = 0
        view._energy_flow_active = False
        view._readiness_energy_dots = MagicMock()
        view._readiness_energy_dots.winfo_exists.return_value = True
        view._draw_energy_dots = MagicMock()
        view.winfo_exists = MagicMock(return_value=True)
        view.after = MagicMock(return_value="energy-1")
        view.after_cancel = MagicMock()

        PhoenixHomeView._start_energy_flow(view)
        self.assertTrue(view._energy_flow_active)
        self.assertEqual(view._energy_flow_after_id, "energy-1")
        view.after.assert_called_once()

        PhoenixHomeView._on_readiness_unmap(view, MagicMock())
        self.assertFalse(view._energy_flow_active)
        self.assertIsNone(view._energy_flow_after_id)
        view.after_cancel.assert_called_once_with("energy-1")

        view._model_ready = True
        PhoenixHomeView._on_readiness_map(view, MagicMock())
        self.assertFalse(view._energy_flow_active)

        view._energy_flow_active = True
        view._energy_flow_after_id = "energy-2"
        with patch("tkinter.Frame.destroy") as frame_destroy:
            PhoenixHomeView.destroy(view)
        view.after_cancel.assert_called_with("energy-2")
        frame_destroy.assert_called_once_with()

    def test_energy_dots_use_theme_and_flow_left_to_right(self) -> None:
        dark_inactive, dark_active = PhoenixHomeView._energy_dot_colors_for(
            "#20242a", "#aab2c0", "#2f80ed"
        )
        light_inactive, light_active = PhoenixHomeView._energy_dot_colors_for(
            "#f7f8f8", "#586575", "#2f80ed"
        )
        self.assertNotEqual(dark_inactive, dark_active)
        self.assertNotEqual(light_inactive, light_active)
        self.assertEqual(dark_active, "#2f80ed")
        self.assertEqual(light_active, "#2f80ed")

        view = PhoenixHomeView.__new__(PhoenixHomeView)
        view._model_ready = False
        view._energy_flow_after_id = None
        view._energy_flow_step = 0
        view._energy_flow_active = False
        view._readiness_energy_dots = MagicMock()
        view._readiness_energy_dots.winfo_exists.return_value = True
        view._readiness_button = MagicMock()
        view._draw_energy_dots = MagicMock()
        view.winfo_exists = MagicMock(return_value=True)
        view.after = MagicMock(return_value="energy")

        PhoenixHomeView._start_energy_flow(view)
        for _ in range(3):
            PhoenixHomeView._animate_energy_flow(view)
        self.assertEqual(
            [call.args[0] for call in view._draw_energy_dots.call_args_list],
            [0, 1, 2, 3],
        )
        view._readiness_button.configure.assert_not_called()

        draw_view = PhoenixHomeView.__new__(PhoenixHomeView)
        draw_view._readiness_energy_dots = MagicMock()
        draw_view._energy_dot_colors = MagicMock(
            return_value=("#586575", "#2f80ed")
        )
        PhoenixHomeView._draw_energy_dots(draw_view, 0)
        first_positions = [
            call.args[:4]
            for call in draw_view._readiness_energy_dots.create_oval.call_args_list
        ]
        draw_view._readiness_energy_dots.reset_mock()
        PhoenixHomeView._draw_energy_dots(draw_view, 3)
        last_positions = [
            call.args[:4]
            for call in draw_view._readiness_energy_dots.create_oval.call_args_list
        ]
        self.assertEqual(len(first_positions), 4)
        self.assertEqual(first_positions, last_positions)

    def test_rc3_readiness_navigation_opens_photo_restore(self) -> None:
        navigate = MagicMock()
        view = SimpleNamespace(_model_ready=False, _navigate=navigate)
        PhoenixHomeView._on_readiness_action(view)
        navigate.assert_called_once_with("inpainting")
        navigate.reset_mock()
        view._model_ready = True
        PhoenixHomeView._on_readiness_action(view)
        navigate.assert_called_once_with("inpainting")

    def test_rc3_clean_start_does_not_offer_automatic_generation_model_setup(self) -> None:
        self.assertFalse(RC3_AUTOMATIC_GENERATION_MODEL_SETUP)
        self.assertEqual(RC3_PRIMARY_PRODUCT_VIEW, "inpainting")

        navigate = MagicMock()
        clean_start = SimpleNamespace(_model_ready=False, _navigate=navigate)
        PhoenixHomeView._on_readiness_action(clean_start)

        navigate.assert_called_once_with("inpainting")
        self.assertNotIn(
            navigate.call_args.args[0],
            {"models", "prompt", "generative_fill", "retouch"},
        )

    def test_missing_sd35_model_does_not_trigger_legacy_installer(self) -> None:
        from widgets.phoenix.views.model_manager_view import PhoenixModelManagerView

        navigate = MagicMock()
        clean_start = SimpleNamespace(_model_ready=False, _navigate=navigate)
        with patch.object(PhoenixModelManagerView, "_on_install_selected") as install:
            PhoenixHomeView._on_readiness_action(clean_start)

        navigate.assert_called_once_with("inpainting")
        install.assert_not_called()

    def test_real_normal_and_first_run_keep_sd35_dialog_closed(self) -> None:
        script_template = textwrap.dedent(
            """
            import tkinter as tk
            from types import SimpleNamespace
            from unittest.mock import MagicMock, patch

            from widgets.phoenix.views.photo_restore_view import PhoenixPhotoRestoreView
            from widgets.phoenix.workspace import PhoenixWorkspace
            from tools.build_app import FIDESR_PRODUCT_FILES

            assert all(path.is_file() for path, _destination in FIDESR_PRODUCT_FILES)

            root = tk.Tk()
            root.withdraw()
            model_controller = MagicMock()
            model_controller.get_all_models.return_value = __MODELS__
            model_controller.get_active_model_id.return_value = __ACTIVE_MODEL__
            model_controller.get_discovery_result.return_value = SimpleNamespace(
                qnn_sdk_found=True,
                qnn_tools_found=True,
                onnx_available=False,
                onnx_version=None,
            )
            model_controller.reconcile_installed_packages.return_value = []
            try:
                with patch(
                    "widgets.phoenix.views.home_view.ModelManagerController",
                    return_value=model_controller,
                ), patch(
                    "widgets.phoenix.views.home_view.SettingsManager.get_execution_provider",
                    return_value="QNNExecutionProvider",
                ), patch(
                    "widgets.phoenix.views.model_manager_view.PhoenixModelManagerView._on_install_selected"
                ) as auto_install, patch(
                    "dialogs.model_source_dialog.ModelSourceDialog"
                ) as source_dialog, patch(
                    "dialogs.model_direct_download_dialog.ModelDirectDownloadDialog"
                ) as direct_dialog, patch(
                    "tools.sd35_setup_helper.SD35SetupHelper.run_setup"
                ) as sd35_setup:
                    workspace = PhoenixWorkspace(root)
                    root.update_idletasks()
                    root.update()
                    workspace._refresh_views()
                    root.update_idletasks()
                    assert workspace.current_view == "home"
                    assert "models" not in workspace._views
                    assert auto_install.call_count == 0
                    assert source_dialog.call_count == 0
                    assert direct_dialog.call_count == 0
                    assert sd35_setup.call_count == 0
                    workspace.show_view("inpainting")
                    assert isinstance(
                        workspace._views["inpainting"], PhoenixPhotoRestoreView
                    )
                    workspace.destroy()
            finally:
                root.destroy()
            """
        )
        scenarios = (
            ("normal", [{"id": "stable_diffusion_v1_5_qnn", "installed": True}], "stable_diffusion_v1_5_qnn"),
            ("first_run", [], None),
        )
        for name, models, active_model in scenarios:
            with self.subTest(scenario=name):
                script = script_template.replace("__MODELS__", repr(models)).replace(
                    "__ACTIVE_MODEL__", repr(active_model)
                )
                result = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd=Path(__file__).resolve().parents[1],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_home_content_uses_its_own_scroll_container(self) -> None:
        root = tk.Tk()
        root.withdraw()
        try:
            with patch("widgets.phoenix.views.home_view.ModelManagerController"), \
                 patch.object(PhoenixHomeView, "refresh"):
                view = PhoenixHomeView(root)
            self.assertIs(view.home_content.master, view.home_canvas)
            self.assertEqual(view.home_canvas.winfo_manager(), "grid")
            self.assertIs(view._last_card.master, view.home_content)
            view.destroy()
        finally:
            root.destroy()

    def test_render_readiness_no_generations(self) -> None:
        view = self._view_stub()
        PhoenixHomeView._render_readiness(view, model_ready=True, has_generations=False)
        self.assertEqual(
            view._readiness_button.configure.call_args.kwargs["text"],
            tr("home_create_first_image"),
        )

    def test_render_readiness_with_generations(self) -> None:
        view = self._view_stub()
        PhoenixHomeView._render_readiness(view, model_ready=True, has_generations=True)
        self.assertEqual(
            view._readiness_button.configure.call_args.kwargs["text"],
            tr("home_create_new_image"),
        )

    def test_localization_keys_complete(self) -> None:
        required = {
            "home_setup_required", "home_studio_ready", "home_model_folder_ready",
            "home_model_folder_not_ready", "home_system_ready", "home_system_not_ready",
            "home_select_install_next", "home_start_setup", "home_create_first_image",
            "home_create_new_image",
        }
        root = Path(__file__).resolve().parents[1]
        for locale in ("de_DE", "en_US", "es_ES"):
            data = json.loads(
                (root / "locales" / f"{locale}.json").read_text(encoding="utf-8")
            )
            self.assertTrue(required.issubset(data), locale)
            set_language(locale)
            for key in required:
                self.assertNotEqual(tr(key), key)


if __name__ == "__main__":
    unittest.main()
