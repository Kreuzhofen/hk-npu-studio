import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.i18n import set_language, tr
from controllers.model_manager_controller import ModelManagerController
from dialogs.model_direct_download_dialog import ModelDirectDownloadDialog
from dialogs.hf_auth_dialog import HuggingFaceAuthDialog
from dialogs.model_source_dialog import ModelSourceDialog
from dialogs.model_ready_dialog import ModelReadyDialog
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
    def tearDown(self) -> None:
        set_language("de_DE")

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
            _requires_hf_auth=PhoenixModelManagerView._requires_hf_auth,
            _last_rendered_signature=("old",), refresh=MagicMock(),
        )

        def run_dialog(*_args, **kwargs):
            updates = []
            self.assertTrue(kwargs["start_install"](updates.append))
            kwargs["on_installed"]()
            self.assertEqual(controller.download_and_install_package.call_args.args[:2], ("direct_model", source_url))

        with patch("dialogs.model_direct_download_dialog.ModelDirectDownloadDialog", side_effect=run_dialog), \
             patch("dialogs.hf_auth_dialog.HuggingFaceAuthDialog") as auth_dialog, \
             patch("widgets.phoenix.views.model_manager_view.filedialog.askopenfilename") as picker:
            PhoenixModelManagerView._on_install_selected(view)

        picker.assert_not_called()
        auth_dialog.assert_not_called()
        view.refresh.assert_called_once()

    def test_controller_uses_staged_package_and_existing_installer(self) -> None:
        source_url = "https://example.invalid/model.zip"
        repository = _Repository({
            "id": "direct_model", "installed": False,
            "source_type": "direct", "source_url": source_url, "path": "",
        })
        install_service = MagicMock()

        def stage(_model_id, _url, callback, hf_token=None, force_redownload=False):
            self.assertIsNone(hf_token)
            self.assertFalse(force_redownload)
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
            ["download_preparing", "downloading", "download_complete", "checking", "installing", "validating", "activating", "ready"],
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
        service.start_download.side_effect = lambda _id, _url, _cb, **_kwargs: repository.model.update(path=r"C:\temp\bad.zip") or True
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
        service.start_download.side_effect = lambda _id, _url, _cb, **_kwargs: repository.model.update(path=r"C:\temp\model.zip") or True
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

    def test_local_only_shows_explanation_before_file_picker(self) -> None:
        repository = _Repository({
            "id": "local_model", "display_name": "Local Model",
            "installed": False, "source_type": "local_only", "source_url": "",
        })
        controller = SimpleNamespace(
            model=SimpleNamespace(repository=repository),
            install_and_activate_package=MagicMock(return_value=False),
        )
        view = SimpleNamespace(
            selected_model_id="local_model", controller=controller,
            winfo_toplevel=lambda: object(),
            _display_title=lambda model: model["display_name"],
        )
        dialog = SimpleNamespace(choice="cancel")
        with patch("widgets.phoenix.views.model_manager_view.filedialog.askopenfilename") as picker, \
             patch("dialogs.model_source_dialog.ModelSourceDialog", return_value=dialog) as source_dialog, \
             patch("dialogs.model_direct_download_dialog.ModelDirectDownloadDialog") as direct_dialog:
            PhoenixModelManagerView._on_install_selected(view)
        picker.assert_not_called()
        self.assertEqual(source_dialog.call_args.kwargs["source_type"], "local_only")
        self.assertIsNone(source_dialog.call_args.kwargs["source_url"])
        direct_dialog.assert_not_called()

    def test_official_external_uses_existing_source_and_explicit_file_selection(self) -> None:
        source_url = "https://aihub.qualcomm.com/models/stable_diffusion_v1_5"
        repository = _Repository({
            "id": "external_model", "display_name": "External Model",
            "installed": False, "source_type": "official_external",
            "source_url": source_url, "package_format": "smp_or_zip",
        })
        controller = SimpleNamespace(
            model=SimpleNamespace(repository=repository),
            install_and_activate_package=MagicMock(return_value=True),
        )
        view = SimpleNamespace(
            selected_model_id="external_model", controller=controller,
            winfo_toplevel=lambda: SimpleNamespace(brand=None),
            _display_title=lambda model: model["display_name"],
            _last_rendered_signature=None, refresh=MagicMock(),
        )
        dialog = SimpleNamespace(choice="install")
        with patch("dialogs.model_source_dialog.ModelSourceDialog", return_value=dialog) as source_dialog, \
             patch("widgets.phoenix.views.model_manager_view.filedialog.askopenfilename", return_value=r"C:\temp\model.smp") as picker, \
             patch("dialogs.model_ready_dialog.ModelReadyDialog") as ready_dialog:
            PhoenixModelManagerView._on_install_selected(view)
        self.assertEqual(source_dialog.call_args.kwargs["source_url"], source_url)
        self.assertEqual(source_dialog.call_args.kwargs["package_format"], "smp_or_zip")
        self.assertIsNone(source_dialog.call_args.kwargs["required_variant"])
        picker.assert_called_once()
        controller.install_and_activate_package.assert_called_once_with("external_model", r"C:\temp\model.smp")
        ready_dialog.assert_called_once()

    def test_official_page_button_does_not_open_file_picker_or_close_dialog(self) -> None:
        dialog = ModelSourceDialog.__new__(ModelSourceDialog)
        dialog.source_url = "https://aihub.qualcomm.com/models/example"
        dialog.close = MagicMock()
        with patch("dialogs.model_source_dialog.webbrowser.open") as browser:
            dialog._on_download()
        browser.assert_called_once_with(dialog.source_url)
        dialog.close.assert_not_called()

    def test_local_only_success_uses_same_ready_completion(self) -> None:
        repository = _Repository({
            "id": "local_model", "display_name": "Local Model", "installed": False,
            "source_type": "local_only", "source_url": "", "package_format": "smp_or_zip",
        })
        controller = SimpleNamespace(
            model=SimpleNamespace(repository=repository),
            install_and_activate_package=MagicMock(return_value=True),
        )
        view = SimpleNamespace(
            selected_model_id="local_model", controller=controller,
            winfo_toplevel=lambda: SimpleNamespace(brand=None),
            _display_title=lambda model: model["display_name"],
            _last_rendered_signature=None, refresh=MagicMock(),
        )
        with patch("dialogs.model_source_dialog.ModelSourceDialog", return_value=SimpleNamespace(choice="install")), \
             patch("widgets.phoenix.views.model_manager_view.filedialog.askopenfilename", return_value=r"C:\temp\local.zip"), \
             patch("dialogs.model_ready_dialog.ModelReadyDialog") as ready_dialog:
            PhoenixModelManagerView._on_install_selected(view)
        controller.install_and_activate_package.assert_called_once_with("local_model", r"C:\temp\local.zip")
        ready_dialog.assert_called_once()

    def test_install_error_never_shows_ready_completion(self) -> None:
        repository = _Repository({
            "id": "local_model", "display_name": "Local Model", "installed": False,
            "source_type": "local_only", "source_url": "", "package_format": "smp_or_zip",
        })
        controller = SimpleNamespace(
            model=SimpleNamespace(repository=repository),
            install_and_activate_package=MagicMock(return_value=False),
        )
        view = SimpleNamespace(
            selected_model_id="local_model", controller=controller,
            winfo_toplevel=lambda: SimpleNamespace(brand=None),
            _display_title=lambda model: model["display_name"],
        )
        with patch("dialogs.model_source_dialog.ModelSourceDialog", return_value=SimpleNamespace(choice="install")), \
             patch("widgets.phoenix.views.model_manager_view.filedialog.askopenfilename", return_value=r"C:\temp\bad.zip"), \
             patch("dialogs.model_ready_dialog.ModelReadyDialog") as ready_dialog, \
             patch("widgets.phoenix.views.model_manager_view.messagebox.showerror"):
            PhoenixModelManagerView._on_install_selected(view)
        ready_dialog.assert_not_called()

    def test_package_format_is_clear_and_localized(self) -> None:
        set_language("en_US")
        self.assertEqual(ModelSourceDialog.package_format_text("zip"), "ZIP package")
        self.assertEqual(ModelSourceDialog.package_format_text("smp_or_zip"), "SMP or ZIP package")

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
            "model_src_subtitle", "model_src_official_description",
            "model_src_local_description", "model_src_official_source",
            "model_src_official_source_name", "model_src_required_variant",
            "model_src_variant_missing", "model_src_official_compatible_help",
            "model_src_expected_format", "model_src_format_zip",
            "model_src_format_smp", "model_src_format_smp_zip",
            "model_src_official_compatible_help", "model_src_local_install_note",
            "model_src_open_official",
            "model_src_select_existing",
            "settings_hf_token_optional", "hf_auth_title",
            "hf_auth_required_explanation", "hf_auth_token_label",
            "hf_auth_enter_token", "hf_auth_check", "hf_auth_checking_saved",
            "hf_auth_checking", "hf_auth_missing", "hf_auth_invalid",
            "hf_auth_save_failed",
            "setup_complete_title", "home_studio_ready", "home_create_first_image",
        }
        root = Path(__file__).resolve().parents[1]
        for locale in ("de_DE", "en_US", "es_ES"):
            data = json.loads((root / "locales" / f"{locale}.json").read_text(encoding="utf-8"))
            self.assertTrue(keys.issubset(data), locale)
            self.assertNotIn("http", data["model_src_official_source_name"].lower())
            self.assertIn("Qualcomm AI Hub", data["model_src_official_source_name"])
            self.assertNotIn("download the model package required", data["model_src_official_compatible_help"].lower())

    def test_external_contract_does_not_claim_an_unknown_qualcomm_variant(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for model_id in ("stable_diffusion_v1_5_qai", "stable_diffusion_v2_1_qai"):
            model = json.loads(
                (root / "resources" / "models" / f"{model_id}.json").read_text(encoding="utf-8")
            )
            with self.subTest(model=model_id):
                self.assertEqual(model["source_type"], "official_external")
                self.assertEqual(model["package_format"], "smp_or_zip")
                self.assertFalse(model.get("required_variant"))

    def test_official_dialog_wraps_long_text_and_buttons_fit(self) -> None:
        container = MagicMock()
        label = MagicMock()
        ModelSourceDialog._bind_responsive_wrap(container, label)
        callback = container.bind.call_args.args[1]
        callback(SimpleNamespace(width=500))
        label.configure.assert_called_once_with(wraplength=498)
        self.assertGreaterEqual(ModelSourceDialog.OFFICIAL_SIZE[0], 720)
        self.assertGreaterEqual(ModelSourceDialog.OFFICIAL_SIZE[1], 660)
        self.assertLess(460, ModelSourceDialog.OFFICIAL_MIN_SIZE[0])

    def test_official_layout_texts_are_complete_in_all_languages(self) -> None:
        root = Path(__file__).resolve().parents[1]
        keys = {
            "model_src_official_description", "model_src_official_source_name",
            "model_src_expected_format", "model_src_variant_missing",
            "model_src_official_compatible_help", "model_src_open_official",
            "model_src_select_existing",
        }
        for locale in ("de_DE", "en_US", "es_ES"):
            data = json.loads((root / "locales" / f"{locale}.json").read_text(encoding="utf-8"))
            with self.subTest(locale=locale):
                self.assertTrue(all(str(data[key]).strip() for key in keys))
                self.assertTrue(all(max(map(len, str(data[key]).split())) < 45 for key in keys))

    def test_no_current_model_contract_requires_hf_auth(self) -> None:
        root = Path(__file__).resolve().parents[1]
        models = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in (root / "resources" / "models").glob("*.json")
        ]
        self.assertFalse(any(PhoenixModelManagerView._requires_hf_auth(model) for model in models))

    def test_hf_auth_contract_is_demand_driven(self) -> None:
        self.assertFalse(PhoenixModelManagerView._requires_hf_auth({"requires_hf_auth": False}))
        self.assertFalse(PhoenixModelManagerView._requires_hf_auth({"requires_hf_token": False}))
        self.assertTrue(PhoenixModelManagerView._requires_hf_auth({"requires_hf_auth": True}))

    def test_required_hf_auth_passes_verified_token_to_direct_flow(self) -> None:
        source_url = "https://huggingface.co/example/model.zip"
        repository = _Repository({
            "id": "gated_model", "display_name": "Gated Model", "installed": False,
            "source_type": "direct", "source_url": source_url,
            "requires_hf_auth": True, "download_size": None,
        })
        controller = SimpleNamespace(
            model=SimpleNamespace(repository=repository),
            download_and_install_package=MagicMock(return_value=True),
        )
        view = SimpleNamespace(
            selected_model_id="gated_model", controller=controller,
            winfo_toplevel=lambda: SimpleNamespace(brand=None),
            _display_title=lambda model: model["display_name"],
            _requires_hf_auth=PhoenixModelManagerView._requires_hf_auth,
            _last_rendered_signature=None, refresh=MagicMock(),
        )
        auth = SimpleNamespace(authenticated=True, token="hf_verified")

        def run_download(*_args, **kwargs):
            self.assertTrue(kwargs["start_install"](MagicMock()))

        with patch("dialogs.hf_auth_dialog.HuggingFaceAuthDialog", return_value=auth), \
             patch("dialogs.model_direct_download_dialog.ModelDirectDownloadDialog", side_effect=run_download):
            PhoenixModelManagerView._on_install_selected(view)
        self.assertEqual(
            controller.download_and_install_package.call_args.kwargs["hf_token"],
            "hf_verified",
        )

    def test_valid_saved_token_needs_no_new_save_or_entry(self) -> None:
        dialog = HuggingFaceAuthDialog.__new__(HuggingFaceAuthDialog)
        dialog.submit_button = MagicMock()
        dialog.status_label = MagicMock()
        dialog.close = MagicMock()
        with patch("dialogs.hf_auth_dialog.SettingsManager.save_settings") as save:
            dialog._apply_result(True, "hf_saved", False)
        save.assert_not_called()
        self.assertTrue(dialog.authenticated)
        self.assertEqual(dialog.token, "hf_saved")
        dialog.close.assert_called_once()

    def test_invalid_token_keeps_dialog_open_for_retry(self) -> None:
        dialog = HuggingFaceAuthDialog.__new__(HuggingFaceAuthDialog)
        dialog.submit_button = MagicMock()
        dialog.status_label = MagicMock()
        dialog.close = MagicMock()
        dialog._apply_result(False, "hf_invalid", True)
        dialog.submit_button.configure.assert_called_once_with(state="normal")
        dialog.close.assert_not_called()

    def test_local_install_activates_only_after_success(self) -> None:
        repository = _Repository({
            "id": "local_model", "installed": False, "product_available": True,
            "generation_parameters": {"width": {"default": 512}},
        })
        service = MagicMock()
        service.install_package.side_effect = lambda *_args: repository.model.update(installed=True) or True
        controller = ModelManagerController.__new__(ModelManagerController)
        controller.model = SimpleNamespace(repository=repository)
        controller.install_service = service
        self.assertTrue(controller.install_and_activate_package("local_model", r"C:\temp\model.smp"))
        self.assertEqual(repository.active, "local_model")

    def test_local_install_failure_preserves_active_model_and_never_completes(self) -> None:
        repository = _Repository({"id": "local_model", "installed": False})
        service = MagicMock()
        service.install_package.return_value = False
        controller = ModelManagerController.__new__(ModelManagerController)
        controller.model = SimpleNamespace(repository=repository)
        controller.install_service = service
        self.assertFalse(controller.install_and_activate_package("local_model", r"C:\temp\bad.smp"))
        self.assertEqual(repository.active, "previous_model")

    def test_ready_action_navigates_without_starting_generation(self) -> None:
        generation = MagicMock()
        for dialog_class, button_name in (
            (ModelReadyDialog, "create_button"),
            (ModelDirectDownloadDialog, "start_button"),
        ):
            with self.subTest(dialog=dialog_class.__name__):
                order = []
                dialog = dialog_class.__new__(dialog_class)
                dialog.master = MagicMock()
                dialog._on_open_generate = MagicMock(side_effect=lambda: order.append("navigate"))
                dialog.close = MagicMock(side_effect=lambda: order.append("close"))
                button = MagicMock()
                setattr(dialog, button_name, button)

                dialog._open_generate()

                dialog.close.assert_not_called()
                dialog._on_open_generate.assert_not_called()
                self.assertEqual(button.mock_calls, [])
                delay, scheduled = dialog.master.after.call_args.args
                self.assertGreaterEqual(delay, 180)

                scheduled()

                self.assertEqual(order, ["close", "navigate"])
                self.assertEqual(button.mock_calls, [])
        generation.assert_not_called()

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

    def test_all_source_routes_are_safe_before_user_file_selection_in_each_language(self) -> None:
        for locale in ("de_DE", "en_US", "es_ES"):
            set_language(locale)
            for source_type in ("direct", "official_external", "local_only"):
                with self.subTest(locale=locale, source_type=source_type):
                    model = {
                        "id": f"{source_type}_model",
                        "display_name": "Stable Diffusion",
                        "installed": False,
                        "source_type": source_type,
                        "source_url": (
                            "https://example.invalid/model.zip" if source_type == "direct"
                            else "https://aihub.qualcomm.com/models/example" if source_type == "official_external"
                            else ""
                        ),
                        "package_format": "smp_or_zip",
                        "requires_hf_token": False,
                    }
                    repository = _Repository(model)
                    controller = SimpleNamespace(
                        model=SimpleNamespace(repository=repository),
                        download_and_install_package=MagicMock(return_value=False),
                    )
                    view = SimpleNamespace(
                        selected_model_id=model["id"], controller=controller,
                        winfo_toplevel=lambda: SimpleNamespace(brand=None),
                        _display_title=lambda item: item["display_name"],
                        _requires_hf_auth=PhoenixModelManagerView._requires_hf_auth,
                    )
                    with patch(
                        "widgets.phoenix.views.model_manager_view.filedialog.askopenfilename"
                    ) as picker, patch(
                        "dialogs.model_direct_download_dialog.ModelDirectDownloadDialog"
                    ) as direct_dialog, patch(
                        "dialogs.model_source_dialog.ModelSourceDialog",
                        return_value=SimpleNamespace(choice="cancel"),
                    ) as source_dialog:
                        PhoenixModelManagerView._on_install_selected(view)
                    picker.assert_not_called()
                    if source_type == "direct":
                        direct_dialog.assert_called_once()
                        source_dialog.assert_not_called()
                    else:
                        source_dialog.assert_called_once()
                        direct_dialog.assert_not_called()

    def test_first_run_visible_copy_is_resolved_in_each_language(self) -> None:
        expected = {
            "de_DE": ("Einrichtung starten", "Erstes Bild erstellen"),
            "en_US": ("Start setup", "Create your first image"),
            "es_ES": ("Iniciar configuración", "Crear la primera imagen"),
        }
        static_keys = (
            "home_setup_required", "home_studio_ready", "home_start_setup",
            "home_create_first_image", "model_install_action", "model_use_action",
            "model_active_ready_action", "model_src_select_existing",
            "cancel", "direct_model_install_error",
        )
        root = Path(__file__).resolve().parents[1]
        for locale, actions in expected.items():
            data = json.loads(
                (root / "locales" / f"{locale}.json").read_text(encoding="utf-8")
            )
            with self.subTest(locale=locale):
                values = [data[key] for key in static_keys]
                values.extend((
                    data["direct_model_downloading_percent"].format(percent=50.0),
                    data["model_src_official_source"].format(source="Qualcomm AI Hub"),
                ))
                self.assertEqual(
                    (data["home_start_setup"], data["home_create_first_image"]), actions
                )
                self.assertTrue(all(value and "{" not in value and "}" not in value for value in values))

    def test_sd35_routing_opens_guided_qualcomm_flow(self) -> None:
        model = {
            "id": "stable_diffusion_v3_5_qai",
            "display_name": "Stable Diffusion 3.5 Medium",
            "installed": False,
            "source_type": "local_only",
            "package_format": "smp_or_zip",
            "requires_hf_token": False,
        }
        repository = _Repository(model)
        controller = SimpleNamespace(
            model=SimpleNamespace(repository=repository),
            install_and_activate_sd35_qualcomm_folder=MagicMock(),
        )
        view = SimpleNamespace(
            selected_model_id=model["id"],
            controller=controller,
            winfo_toplevel=lambda: SimpleNamespace(brand=None),
            _display_title=lambda item: item["display_name"],
            _requires_hf_auth=lambda *args: False,
        )
        with patch("widgets.phoenix.views.model_manager_view.filedialog.askdirectory") as askdir, \
             patch("widgets.phoenix.views.model_manager_view.filedialog.askopenfilename") as askfile, \
             patch("dialogs.model_direct_download_dialog.ModelDirectDownloadDialog") as direct_dialog, \
             patch("dialogs.model_source_dialog.ModelSourceDialog") as source_dialog:

             # Setup ModelSourceDialog mock to return choice="install_sd35_auto" (which triggers the auto flow)
             source_dialog.return_value = SimpleNamespace(choice="install_sd35_auto")

             # Run routing
             PhoenixModelManagerView._on_install_selected(view)

        # It must open the direct download dialog for the special Qualcomm flow, NOT the file picker or generic error
        direct_dialog.assert_called_once()
        askfile.assert_not_called()


if __name__ == "__main__":
    unittest.main()
