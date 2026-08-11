import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from controllers.model_manager_controller import ModelManagerController
from dialogs.model_direct_download_dialog import ModelDirectDownloadDialog
from widgets.phoenix.views.model_manager_view import PhoenixModelManagerView


class _Repository:
    def __init__(self, model: dict) -> None:
        self.model = model

    def get_model(self, _model_id: str) -> dict:
        return dict(self.model)


class DirectModelInstallTests(unittest.TestCase):
    def test_direct_handler_opens_progress_dialog_without_file_picker(self) -> None:
        source_url = "https://example.invalid/model.zip"
        repository = _Repository({
            "id": "direct_model", "display_name": "Direct Model",
            "installed": False, "source_type": "direct", "source_url": source_url,
            "requires_hf_token": False, "download_size": 1.25,
        })
        controller = SimpleNamespace(
            model=SimpleNamespace(repository=repository),
            download_and_install_package=MagicMock(return_value=True),
        )
        view = SimpleNamespace(
            selected_model_id="direct_model", controller=controller,
            winfo_toplevel=lambda: SimpleNamespace(brand=None),
            _display_title=lambda model: model["display_name"],
            _last_rendered_signature=("old",), refresh=MagicMock(),
        )

        def run_dialog(*_args, **kwargs):
            updates = []
            self.assertTrue(kwargs["start_install"](updates.append))
            kwargs["on_installed"]()
            self.assertEqual(controller.download_and_install_package.call_args.args[:2], ("direct_model", source_url))

        with patch("dialogs.model_direct_download_dialog.ModelDirectDownloadDialog", side_effect=run_dialog), \
             patch("widgets.phoenix.views.model_manager_view.filedialog.askopenfilename") as picker:
            PhoenixModelManagerView._on_install_selected(view)

        picker.assert_not_called()
        view.refresh.assert_called_once()

    def test_controller_uses_staged_package_and_existing_installer(self) -> None:
        source_url = "https://example.invalid/model.zip"
        repository = _Repository({
            "id": "direct_model", "installed": False,
            "source_type": "direct", "source_url": source_url, "path": "",
        })
        install_service = MagicMock()

        def stage(_model_id, _url, callback):
            callback(42.0)
            repository.model["path"] = r"C:\temp\model.zip"
            return True

        install_service.start_download.side_effect = stage
        install_service.install_package.return_value = True
        controller = ModelManagerController.__new__(ModelManagerController)
        controller.model = SimpleNamespace(repository=repository)
        controller.install_service = install_service
        updates = []

        self.assertTrue(controller.download_and_install_package("direct_model", source_url, updates.append))
        self.assertEqual(updates, [42.0])
        install_service.install_package.assert_called_once_with("direct_model", r"C:\temp\model.zip")

    def test_non_direct_model_does_not_enter_direct_download(self) -> None:
        repository = _Repository({
            "id": "local_model", "display_name": "Local Model",
            "installed": False, "source_type": "local_only", "source_url": "",
        })
        controller = SimpleNamespace(
            model=SimpleNamespace(repository=repository),
            install_package=MagicMock(return_value=False),
        )
        view = SimpleNamespace(
            selected_model_id="local_model", controller=controller,
            winfo_toplevel=lambda: object(),
        )
        with patch("widgets.phoenix.views.model_manager_view.filedialog.askopenfilename", return_value="") as picker, \
             patch("dialogs.model_direct_download_dialog.ModelDirectDownloadDialog") as direct_dialog:
            PhoenixModelManagerView._on_install_selected(view)
        picker.assert_called_once()
        direct_dialog.assert_not_called()

    def test_progress_is_clamped_and_shown(self) -> None:
        dialog = ModelDirectDownloadDialog.__new__(ModelDirectDownloadDialog)
        dialog.progress_var = MagicMock()
        dialog.status_label = MagicMock()
        for percent in (0.0, 50.0, 100.0):
            with self.subTest(percent=percent):
                dialog.progress_var.reset_mock()
                dialog.status_label.reset_mock()
                dialog._set_progress(percent)
                dialog.progress_var.set.assert_called_once_with(percent)
                self.assertIn(f"{percent:.0f}", dialog.status_label.configure.call_args.kwargs["text"])

    def test_direct_localization_keys_exist_in_all_languages(self) -> None:
        keys = {
            "direct_model_install_title", "direct_model_download_size",
            "direct_model_download_size_unknown", "direct_model_install_automatic",
            "direct_model_target_name", "direct_model_target_path",
            "direct_model_automatic_steps",
            "direct_model_ready_to_download", "direct_model_start",
            "direct_model_downloading", "direct_model_downloading_percent",
            "direct_model_install_success", "direct_model_install_error",
            "direct_model_source_unavailable",
        }
        root = Path(__file__).resolve().parents[1]
        for locale in ("de_DE", "en_US", "es_ES"):
            data = json.loads((root / "locales" / f"{locale}.json").read_text(encoding="utf-8"))
            self.assertTrue(keys.issubset(data), locale)

    def test_dialog_uses_existing_green_phoenix_progress_style(self) -> None:
        self.assertEqual(
            ModelDirectDownloadDialog.PROGRESS_STYLE,
            "Phoenix.Horizontal.TProgressbar",
        )

    def test_footer_buttons_fit_minimum_dialog_width(self) -> None:
        button_width = (
            ModelDirectDownloadDialog.START_BUTTON_WIDTH
            + ModelDirectDownloadDialog.CANCEL_BUTTON_WIDTH
        )
        self.assertLess(button_width, ModelDirectDownloadDialog.MIN_SIZE[0])


if __name__ == "__main__":
    unittest.main()
