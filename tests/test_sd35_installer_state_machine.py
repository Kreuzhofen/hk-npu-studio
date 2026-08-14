import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from controllers.model_repository import ModelRepository
from dialogs.model_direct_download_dialog import ModelDirectDownloadDialog
from engine.model_install_service import ModelInstallService, SD35InstallState
from tools.sd35_setup_helper import SD35SetupHelper


class _Installer:
    def __init__(self, service, result=True, activation_failed=False):
        self.install_service = service
        self.result = result
        self.activation_failed = activation_failed
        self.sources = []

    def install_sd35_qualcomm_folder(self, source, callback):
        self.sources.append(Path(source))
        if self.activation_failed:
            callback({"phase": "activation_failed", "percent": 95.0})
        return self.result


class SD35InstallerStateMachineTests(unittest.TestCase):
    def setUp(self):
        self.service = ModelInstallService.__new__(ModelInstallService)
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _write_required(self, root, count=None):
        for relative in self.service.SD35_REQUIRED_FILES[:count]:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"test")

    def _run_helper(self, installer, archive, **kwargs):
        events = []
        with patch("tools.sd35_setup_helper.TEMP_DIR", self.root), patch(
            "tools.sd35_setup_helper.tempfile.gettempdir", return_value=str(self.root)
        ):
            result = SD35SetupHelper.run_setup(
                str(archive), installer, events.append, **kwargs
            )
        return result, events

    def _repository(self, installation, installation_roots=None):
        definitions = self.root / "definitions"
        definitions.mkdir(exist_ok=True)
        source = Path("resources/models/stable_diffusion_v3_5_qai.json")
        definition = json.loads(source.read_text(encoding="utf-8"))
        definition.update(installed=True, downloaded=True, path=str(installation), status="Ready")
        (definitions / source.name).write_text(json.dumps(definition), encoding="utf-8")
        return ModelRepository(
            str(definitions),
            installation_roots=[] if installation_roots is None else installation_roots,
        )

    def _ui(self):
        dialog = ModelDirectDownloadDialog.__new__(ModelDirectDownloadDialog)
        dialog._step_states = ["NOT_STARTED"] * 6
        dialog._step_texts = [str(index) for index in range(6)]
        dialog._render_step_states = MagicMock()
        return dialog

    def test_01_fresh_install_is_zero_of_n_and_allows_first_path(self):
        state = self.service.inspect_sd35_qualcomm_source(str(self.root / "missing"))
        self.assertIs(state.state, SD35InstallState.FRESH_INSTALL)
        self.assertEqual(state.present_count, 0)

    def test_02_empty_models_and_gitkeep_remain_fresh(self):
        models = self.root / "models"
        models.mkdir()
        (models / ".gitkeep").write_text("", encoding="utf-8")
        state = self.service.inspect_sd35_qualcomm_source(str(models))
        self.assertIs(state.state, SD35InstallState.FRESH_INSTALL)

    def test_03_one_of_n_is_partial_and_requires_explicit_redownload(self):
        workspace = self.root / SD35SetupHelper.WORKSPACE_NAME
        self._write_required(workspace, 1)
        state = self.service.inspect_sd35_qualcomm_source(str(workspace))
        result, events = self._run_helper(_Installer(self.service), self.root / "unused.zip")
        self.assertIs(state.state, SD35InstallState.PARTIAL_DOWNLOAD)
        self.assertFalse(result)
        self.assertEqual(events[-1]["phase"], "redownload_required")

    def test_04_complete_source_is_reused_without_download_process(self):
        workspace = self.root / SD35SetupHelper.WORKSPACE_NAME
        self._write_required(workspace)
        with patch("tools.sd35_setup_helper.subprocess.Popen") as popen:
            result, _ = self._run_helper(_Installer(self.service), self.root / "unused.zip")
        self.assertTrue(result)
        popen.assert_not_called()

    def test_05_import_failure_retries_complete_source_without_download(self):
        workspace = self.root / SD35SetupHelper.WORKSPACE_NAME
        self._write_required(workspace)
        first, _ = self._run_helper(_Installer(self.service, result=False), self.root / "unused.zip")
        with patch("tools.sd35_setup_helper.subprocess.Popen") as popen:
            second, _ = self._run_helper(_Installer(self.service), self.root / "unused.zip")
        self.assertFalse(first)
        self.assertTrue(second)
        popen.assert_not_called()

    def test_06_restart_redetects_complete_source_from_filesystem(self):
        workspace = self.root / SD35SetupHelper.WORKSPACE_NAME
        self._write_required(workspace)
        first = self.service.inspect_sd35_qualcomm_source(str(workspace))
        second_service = ModelInstallService.__new__(ModelInstallService)
        second = second_service.inspect_sd35_qualcomm_source(str(workspace))
        self.assertIs(first.state, SD35InstallState.COMPLETE_SOURCE)
        self.assertIs(second.state, SD35InstallState.COMPLETE_SOURCE)

    def test_07_missing_final_folder_reconciles_to_not_installed(self):
        model = self._repository(self.root / "missing-final").get_model("stable_diffusion_v3_5_qai")
        self.assertFalse(model["installed"])
        self.assertEqual(model["status"], "Not Installed")

    def test_08_incomplete_final_folder_reconciles_to_invalid(self):
        final = self.root / "incomplete-final"
        final.mkdir()
        (final / "package.json").write_text(
            json.dumps({"model_id": "stable_diffusion_v3_5_qai", "components": {"model": {"path": "missing.bin"}}}),
            encoding="utf-8",
        )
        model = self._repository(final, installation_roots=[final.parent]).get_model("stable_diffusion_v3_5_qai")
        self.assertFalse(model["installed"])
        self.assertEqual(model["status"], "Invalid")

    def test_09_complete_final_folder_reconciles_to_ready(self):
        final = self.root / "ready-final"
        final.mkdir()
        (final / "model.bin").write_bytes(b"ready")
        (final / "package.json").write_text(
            json.dumps({"model_id": "stable_diffusion_v3_5_qai", "components": {"model": {"path": "model.bin"}}}),
            encoding="utf-8",
        )
        model = self._repository(final, installation_roots=[final.parent]).get_model("stable_diffusion_v3_5_qai")
        self.assertTrue(model["installed"])
        self.assertEqual(model["status"], "Ready")

    def test_10_ready_install_remains_success_when_activation_fails(self):
        workspace = self.root / SD35SetupHelper.WORKSPACE_NAME
        self._write_required(workspace)
        result, events = self._run_helper(
            _Installer(self.service, activation_failed=True), self.root / "unused.zip"
        )
        phases = [event["phase"] for event in events]
        self.assertTrue(result)
        self.assertIn("activation_failed", phases)
        self.assertNotIn("ready", phases)

    def test_11_fresh_install_ui_starts_with_zero_checkmarks(self):
        dialog = self._ui()
        self.assertEqual(dialog._step_states, ["NOT_STARTED"] * 6)

    def test_12_running_step_is_not_success(self):
        dialog = self._ui()
        dialog._update_step_states("sd35_find_zip", {})
        self.assertEqual(dialog._step_states[0], "RUNNING")
        self.assertNotIn("SUCCESS", dialog._step_states)

    def test_13_success_is_set_only_by_following_real_event(self):
        dialog = self._ui()
        dialog._update_step_states("sd35_installing_deps", {})
        self.assertEqual(dialog._step_states[0], "SUCCESS")
        self.assertEqual(dialog._step_states[1], "RUNNING")

    def test_14_failed_step_marks_x_and_leaves_following_steps_neutral(self):
        dialog = self._ui()
        dialog._update_step_states("dependency_failed", {"failed_step": 1})
        self.assertEqual(dialog._step_states[1], "FAILED")
        self.assertEqual(dialog._step_states[2:], ["NOT_STARTED"] * 4)

    def test_15_continue_after_import_failure_reuses_source(self):
        workspace = self.root / SD35SetupHelper.WORKSPACE_NAME
        self._write_required(workspace)
        with patch("tools.sd35_setup_helper.subprocess.Popen") as popen:
            result, events = self._run_helper(_Installer(self.service), self.root / "unused.zip")
        self.assertTrue(result)
        self.assertEqual(events[0]["phase"], "sd35_reusing_models")
        popen.assert_not_called()

    def test_16_explicit_redownload_allows_partial_source_to_continue(self):
        workspace = self.root / SD35SetupHelper.WORKSPACE_NAME
        self._write_required(workspace, 1)
        archive = self.root / "sample.zip"
        script = (
            "qai-appbuilder-main/samples/models/generative_ai/image_generation/"
            "stable_diffusion_v3_5/python/stable_diffusion_v3_5.py"
        )
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(script, "")
        process = MagicMock(returncode=1)
        process.stdout.readline.return_value = ""
        with patch("tools.sd35_setup_helper.subprocess.Popen", return_value=process):
            result, events = self._run_helper(
                _Installer(self.service), archive, allow_redownload=True
            )
        self.assertFalse(result)
        self.assertNotIn("redownload_required", [event["phase"] for event in events])

    def test_17_zero_of_n_never_shows_redownload_failure(self):
        archive = self.root / "empty.zip"
        with zipfile.ZipFile(archive, "w"):
            pass
        result, events = self._run_helper(_Installer(self.service), archive)
        phases = [event["phase"] for event in events]
        self.assertFalse(result)
        self.assertNotIn("redownload_required", phases)

    def test_18_qualcomm_exit_code_non_zero_but_complete_source_succeeds(self) -> None:
        workspace = self.root / SD35SetupHelper.WORKSPACE_NAME
        archive = self.root / "sample.zip"
        script = (
            "qai-appbuilder-main/samples/models/generative_ai/image_generation/"
            "stable_diffusion_v3_5/python/stable_diffusion_v3_5.py"
        )
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(script, "")

        process = MagicMock(returncode=1)
        process.stdout.readline.return_value = ""
        process.stdout.read.return_value = ""

        models_dir = workspace / "qai-appbuilder-main/samples/models/generative_ai/image_generation/stable_diffusion_v3_5/models"

        def mock_popen(cmd, *args, **kwargs):
            if "pip" in cmd:
                pip_process = MagicMock(returncode=0)
                pip_process.stdout.readline.return_value = ""
                return pip_process
            self._write_required(models_dir)
            return process

        with patch("tools.sd35_setup_helper.subprocess.Popen", side_effect=mock_popen):
            result, events = self._run_helper(
                _Installer(self.service), archive, allow_redownload=True
            )

        self.assertTrue(result)
        self.assertEqual(events[-1]["phase"], "ready")


if __name__ == "__main__":
    unittest.main()
