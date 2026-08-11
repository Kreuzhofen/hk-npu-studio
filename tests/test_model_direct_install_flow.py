import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from controllers.model_manager_controller import ModelManagerController
from dialogs.model_direct_download_dialog import ModelDirectDownloadDialog
from widgets.phoenix.views.model_manager_view import PhoenixModelManagerView


class _Repository:
    def __init__(self, model: dict, active: str | None = "previous_model") -> None:
        self.model = model
        self.active = active

    def get_model(self, _model_id: str) -> dict:
        return dict(self.model)

    def update_model(self, _model_id: str, **updates) -> bool:
        self.model.update(updates)
        return True

    def is_selectable_model(self, model_id: str) -> bool:
        return model_id == self.model.get("id") and self.model.get("installed") is True

    def set_active_model_id(self, model_id: str | None) -> None:
        if model_id is None or self.is_selectable_model(model_id):
            self.active = model_id

    def get_active_model_id(self) -> str | None:
        return self.active


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
        install_service.validate_package_source.return_value = {"success": True}
        install_service.install_package.side_effect = lambda *_args, **_kwargs: repository.model.update(installed=True) or True
        controller = ModelManagerController.__new__(ModelManagerController)
        controller.model = SimpleNamespace(repository=repository)
        controller.install_service = install_service
        updates = []

        with tempfile.TemporaryDirectory() as directory, patch(
            "controllers.model_manager_controller.config.MODELS_DIR", Path(directory)
        ):
            self.assertTrue(controller.download_and_install_package("direct_model", source_url, updates.append))
        self.assertEqual(
            [update["phase"] for update in updates],
            ["downloading", "download_complete", "checking", "installing", "activating", "ready"],
        )
        install_service.install_package.assert_called_once_with(
            "direct_model", r"C:\temp\model.zip", replace_existing=False
        )
        install_service.cleanup_staged_download.assert_called_once_with(r"C:\temp\model.zip")
        self.assertEqual(repository.active, "direct_model")

    def test_validation_failure_preserves_previous_active_model(self) -> None:
        source_url = "https://example.invalid/model.zip"
        repository = _Repository({
            "id": "direct_model", "installed": False, "downloaded": False,
            "source_type": "direct", "source_url": source_url, "path": "", "status": "Available",
        })
        service = MagicMock()
        service.start_download.side_effect = lambda _id, _url, _cb: repository.model.update(path=r"C:\temp\bad.zip") or True
        service.validate_package_source.return_value = {"success": False}
        controller = ModelManagerController.__new__(ModelManagerController)
        controller.model = SimpleNamespace(repository=repository)
        controller.install_service = service
        updates = []
        with tempfile.TemporaryDirectory() as directory, patch(
            "controllers.model_manager_controller.config.MODELS_DIR", Path(directory)
        ):
            self.assertFalse(controller.download_and_install_package("direct_model", source_url, updates.append))
        service.install_package.assert_not_called()
        service.cleanup_staged_download.assert_called_once_with(r"C:\temp\bad.zip")
        self.assertEqual(repository.active, "previous_model")
        self.assertIn("validation_failed", [update["phase"] for update in updates])

    def test_install_failure_does_not_activate_or_replace_previous_model(self) -> None:
        source_url = "https://example.invalid/model.zip"
        repository = _Repository({
            "id": "direct_model", "installed": False, "downloaded": False,
            "source_type": "direct", "source_url": source_url, "path": "", "status": "Available",
        })
        service = MagicMock()
        service.start_download.side_effect = lambda _id, _url, _cb: repository.model.update(path=r"C:\temp\model.zip") or True
        service.validate_package_source.return_value = {"success": True}
        service.install_package.return_value = False
        controller = ModelManagerController.__new__(ModelManagerController)
        controller.model = SimpleNamespace(repository=repository)
        controller.install_service = service
        updates = []
        with tempfile.TemporaryDirectory() as directory, patch(
            "controllers.model_manager_controller.config.MODELS_DIR", Path(directory)
        ):
            self.assertFalse(controller.download_and_install_package("direct_model", source_url, updates.append))
        self.assertEqual(repository.active, "previous_model")
        service.cleanup_staged_download.assert_called_once_with(r"C:\temp\model.zip")
        self.assertIn("install_failed", [update["phase"] for update in updates])

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
        dialog._failure_message_shown = False
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
            "direct_model_download_complete", "direct_model_checking",
            "direct_model_installing", "direct_model_activating", "direct_model_ready",
            "direct_model_download_failed", "direct_model_validation_failed",
            "direct_model_installation_failed", "direct_model_activation_failed",
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

    def test_success_exposes_first_image_action(self) -> None:
        dialog = ModelDirectDownloadDialog.__new__(ModelDirectDownloadDialog)
        dialog.progress_var = MagicMock()
        dialog.status_label = MagicMock()
        dialog.start_button = MagicMock()
        dialog._on_installed = MagicMock()
        dialog._on_open_generate = MagicMock()
        dialog._running = True
        dialog._finish(True)
        dialog._on_installed.assert_called_once()
        self.assertEqual(
            dialog.start_button.configure.call_args.kwargs["command"],
            dialog._open_generate,
        )

    def test_footer_buttons_fit_minimum_dialog_width(self) -> None:
        button_width = (
            ModelDirectDownloadDialog.START_BUTTON_WIDTH
            + ModelDirectDownloadDialog.CANCEL_BUTTON_WIDTH
        )
        self.assertLess(button_width, ModelDirectDownloadDialog.MIN_SIZE[0])


if __name__ == "__main__":
    unittest.main()
