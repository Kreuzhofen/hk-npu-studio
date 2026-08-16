import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from controllers.model_repository import ModelRepository
from dialogs.model_direct_download_dialog import ModelDirectDownloadDialog
from engine.model_install_service import ModelInstallService, SD35InstallState
from tools.sd35_setup_helper import SD35SetupHelper, resolve_python_executable


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
        from unittest.mock import Mock
        import tools.sd35_setup_helper

        if not isinstance(tools.sd35_setup_helper.subprocess.run, Mock):
            def default_mock_run(cmd, *args, **kwargs):
                if "venv" in cmd:
                    workspace = self.root
                    venv_dir = workspace / "sd35_venv"
                    venv_python = venv_dir / "Scripts" / "python.exe"
                    venv_python.parent.mkdir(parents=True, exist_ok=True)
                    venv_python.write_bytes(b"")
                    (venv_dir / "Lib" / "site-packages").mkdir(parents=True, exist_ok=True)
                    return MagicMock(returncode=0, stdout="", stderr="")
                return MagicMock(returncode=0, stdout="PREFLIGHT_OK", stderr="")

            with patch("tools.sd35_setup_helper.TEMP_DIR", self.root), \
                 patch("tools.sd35_setup_helper.USER_BASE", self.root), \
                 patch("tools.sd35_setup_helper.tempfile.gettempdir", return_value=str(self.root)), \
                 patch("tools.sd35_setup_helper.subprocess.run", side_effect=default_mock_run):
                result = SD35SetupHelper.run_setup(
                    str(archive), installer, events.append, **kwargs
                )
        else:
            with patch("tools.sd35_setup_helper.TEMP_DIR", self.root), \
                 patch("tools.sd35_setup_helper.USER_BASE", self.root), \
                 patch("tools.sd35_setup_helper.tempfile.gettempdir", return_value=str(self.root)):
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
        # Write the 11 required files
        self._write_required(final)
        
        # Write the mock venv python executable
        venv_python = self.root / "sd35_venv" / "Scripts" / "python.exe"
        venv_python.parent.mkdir(parents=True, exist_ok=True)
        venv_python.write_bytes(b"python")
        
        # Create a package.json declaring all 11 components
        components = {}
        for idx, relative in enumerate(self.service.SD35_REQUIRED_FILES):
            components[f"file_{idx}"] = {"path": relative}
        (final / "package.json").write_text(
            json.dumps({"model_id": "stable_diffusion_v3_5_qai", "components": components}),
            encoding="utf-8",
        )
        
        with patch("config.USER_BASE", self.root):
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

    def test_19_python_resolver_and_subprocess_commands_never_use_studio_exe(self) -> None:
        import sys

        self.assertEqual(resolve_python_executable(), sys.executable)

        program_files = self.root / "Program Files"
        interpreter = program_files / "Python311-arm64" / "python.exe"
        interpreter.parent.mkdir(parents=True)
        interpreter.write_bytes(b"python")
        with patch.object(sys, "frozen", True, create=True), patch.object(
            sys, "executable", str(self.root / "SnapdragonAIStudio.exe")
        ), patch.dict("os.environ", {"ProgramFiles": str(program_files)}, clear=False):
            self.assertEqual(resolve_python_executable(), str(interpreter.resolve()))

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
        commands = []

        def record_popen(command, *args, **kwargs):
            commands.append(command)
            if "pip" in command:
                pip_process = MagicMock(returncode=0)
                pip_process.stdout.readline.return_value = ""
                return pip_process
            return process

        with patch(
            "tools.sd35_setup_helper.resolve_python_executable",
            return_value=str(interpreter),
        ), patch("tools.sd35_setup_helper.subprocess.Popen", side_effect=record_popen):
            self._run_helper(_Installer(self.service), archive, allow_redownload=True)

        expected_venv_python = str(self.root / "sd35_venv" / "Scripts" / "python.exe")
        self.assertEqual(commands[0][:3], [expected_venv_python, "-m", "pip"])
        self.assertEqual(commands[1][:3], [expected_venv_python, "-m", "pip"])
        self.assertEqual(commands[2][:3], [expected_venv_python, "-m", "pip"])
        self.assertEqual(commands[3], [expected_venv_python, "stable_diffusion_v3_5.py"])

    def test_20_pip_failure_self_diagnostics(self) -> None:
        archive = self.root / "sample.zip"
        script = (
            "qai-appbuilder-main/samples/models/generative_ai/image_generation/"
            "stable_diffusion_v3_5/python/stable_diffusion_v3_5.py"
        )
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(script, "")

        # Simulate pip output with failure and some sensitive URL token
        pip_lines = [
            "Collecting transformers",
            "WARNING: Retrying after connection broken by SSLError",
            "ERROR: Could not find a version that satisfies the requirement py3-wget (from https://user:pass123@private-repo.com/packages/)",
            "ERROR: No matching distribution found for py3-wget; api_key=super-secret-key"
        ]

        class MockProcess:
            def __init__(self):
                self.returncode = 1
                self._lines = list(pip_lines)
                self.stdout = MagicMock()
                self.stdout.readline.side_effect = self._readline

            def wait(self):
                return self.returncode

            def _readline(self):
                if self._lines:
                    return self._lines.pop(0) + "\n"
                return ""

        process = MockProcess()
        with patch("tools.sd35_setup_helper.subprocess.Popen", return_value=process):
            result, events = self._run_helper(
                _Installer(self.service), archive, allow_redownload=True
            )

        self.assertFalse(result)
        # Find the dependency_failed event
        dep_failed_event = next(e for e in events if e.get("phase") == "dependency_failed")
        error_msg = dep_failed_event["error"]

        # Verify exit code and cause
        self.assertIn("pip exited with code 1", error_msg)
        self.assertIn("ERROR: Could not find a version that satisfies the requirement py3-wget", error_msg)
        self.assertIn("ERROR: No matching distribution found for py3-wget", error_msg)

        # Verify sanitization
        self.assertNotIn("pass123", error_msg)
        self.assertNotIn("super-secret-key", error_msg)
        self.assertIn("api_key=***", error_msg)
        self.assertIn("https://***@private-repo.com", error_msg)

    def test_21_qualcomm_failure_diagnostics(self) -> None:
        archive = self.root / "sample.zip"
        script = (
            "qai-appbuilder-main/samples/models/generative_ai/image_generation/"
            "stable_diffusion_v3_5/python/stable_diffusion_v3_5.py"
        )
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(script, "")

        qc_lines = [
            "ImportError: libQnnHtp.dll not found",
            "Exception: Token=secret-token-xyz",
            "Could not connect to QAI Hub"
        ]
        full_output = "\n".join(qc_lines)
        output_iter = iter(full_output)

        class MockProcess:
            def __init__(self):
                self.returncode = 1
                self.stdout = MagicMock()
                self.stdout.read.side_effect = self._read

            def wait(self):
                return self.returncode

            def _read(self, size):
                try:
                    return next(output_iter)
                except StopIteration:
                    return ""

        def mock_popen(cmd, *args, **kwargs):
            if "pip" in cmd:
                pip_process = MagicMock(returncode=0)
                pip_process.stdout.readline.return_value = ""
                return pip_process
            return MockProcess()

        with patch("tools.sd35_setup_helper.subprocess.Popen", side_effect=mock_popen):
            result, events = self._run_helper(
                _Installer(self.service), archive, allow_redownload=True
            )

        self.assertFalse(result)
        failed_event = next(e for e in events if e.get("phase") == "download_failed")
        error_msg = failed_event["error"]

        self.assertIn("Qualcomm sample exited with code 1", error_msg)
        self.assertIn("ImportError: libQnnHtp.dll not found", error_msg)
        self.assertIn("Exception: Token=***", error_msg)
        self.assertNotIn("secret-token-xyz", error_msg)
        self.assertIn("Could not connect to QAI Hub", error_msg)

    def test_22_isolated_pythonpath_created_correctly(self) -> None:
        archive = self.root / "sample.zip"
        script = (
            "qai-appbuilder-main/samples/models/generative_ai/image_generation/"
            "stable_diffusion_v3_5/python/stable_diffusion_v3_5.py"
        )
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(script, "")

        commands_run = []
        preflight_run = []

        class MockProcess:
            def __init__(self):
                self.returncode = 0
                self.stdout = MagicMock()
                self.stdout.readline.return_value = ""
                self.stdout.read.return_value = ""
                self.stderr = MagicMock()
                self.stderr.splitlines.return_value = []
            def wait(self):
                return self.returncode

        def mock_popen(cmd, *args, **kwargs):
            commands_run.append((cmd, kwargs.get("env", {})))
            return MockProcess()

        def mock_run(cmd, *args, **kwargs):
            if "venv" in cmd:
                workspace = self.root
                venv_dir = workspace / "sd35_venv"
                venv_python = venv_dir / "Scripts" / "python.exe"
                venv_python.parent.mkdir(parents=True, exist_ok=True)
                venv_python.write_bytes(b"")
                (venv_dir / "Lib" / "site-packages").mkdir(parents=True, exist_ok=True)
                return MagicMock(returncode=0, stdout="", stderr="")
            preflight_run.append((cmd, kwargs.get("env", {})))
            return MagicMock(returncode=0, stdout="PREFLIGHT_OK", stderr="")

        exe_parent = self.root / "app_bin"
        exe_parent.mkdir(parents=True, exist_ok=True)
        (exe_parent / "torch").mkdir(exist_ok=True)
        (exe_parent / "torchgen").mkdir(exist_ok=True)
        (exe_parent / "functorch").mkdir(exist_ok=True)
        (exe_parent / "torch-2.14.0.dev20260808+cpu.dist-info").mkdir(exist_ok=True)
        mock_executable = str(exe_parent / "SnapdragonAIStudio.exe")

        with patch("sys.frozen", True, create=True), \
             patch("sys.executable", mock_executable), \
             patch("tools.sd35_setup_helper.subprocess.Popen", side_effect=mock_popen), \
             patch("tools.sd35_setup_helper.subprocess.run", side_effect=mock_run):
            result, events = self._run_helper(
                _Installer(self.service), archive, allow_redownload=True
            )

        self.assertTrue(len(preflight_run) > 0)
        self.assertTrue(len(commands_run) > 0)

        preflight_env = preflight_run[0][1]
        pythonpath = preflight_env.get("PYTHONPATH", "")

        self.assertNotIn(str(exe_parent), pythonpath)

        venv_site_packages = self.root / "sd35_venv" / "Lib" / "site-packages"
        self.assertTrue((venv_site_packages / "torch").is_dir())
        self.assertTrue((venv_site_packages / "torchgen").is_dir())
        self.assertTrue((venv_site_packages / "functorch").is_dir())
        self.assertTrue((venv_site_packages / "torch-2.14.0.dev20260808+cpu.dist-info").is_dir())

    def test_23_preflight_failure_aborts_qualcomm_sample(self) -> None:
        archive = self.root / "sample.zip"
        script = (
            "qai-appbuilder-main/samples/models/generative_ai/image_generation/"
            "stable_diffusion_v3_5/python/stable_diffusion_v3_5.py"
        )
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(script, "")

        pip_run = False
        qualcomm_run = False

        def mock_popen(cmd, *args, **kwargs):
            nonlocal pip_run, qualcomm_run
            if "pip" in cmd:
                pip_run = True
                p = MagicMock(returncode=0)
                p.stdout.readline.return_value = ""
                return p
            else:
                qualcomm_run = True
                p = MagicMock(returncode=0)
                p.stdout.read.return_value = ""
                return p

        def mock_run(cmd, *args, **kwargs):
            if "venv" in cmd:
                workspace = self.root
                venv_dir = workspace / "sd35_venv"
                venv_python = venv_dir / "Scripts" / "python.exe"
                venv_python.parent.mkdir(parents=True, exist_ok=True)
                venv_python.write_bytes(b"")
                (venv_dir / "Lib" / "site-packages").mkdir(parents=True, exist_ok=True)
                return MagicMock(returncode=0, stdout="", stderr="")
            return MagicMock(
                returncode=1,
                stdout="",
                stderr="ModuleNotFoundError: No module named 'yaml'\n"
            )

        exe_parent = self.root / "app_bin"
        exe_parent.mkdir(parents=True, exist_ok=True)
        (exe_parent / "torch").mkdir(exist_ok=True)
        (exe_parent / "torchgen").mkdir(exist_ok=True)
        (exe_parent / "functorch").mkdir(exist_ok=True)
        (exe_parent / "torch-2.14.0.dev20260808+cpu.dist-info").mkdir(exist_ok=True)
        mock_executable = str(exe_parent / "SnapdragonAIStudio.exe")

        with patch("sys.frozen", True, create=True), \
             patch("sys.executable", mock_executable), \
             patch("tools.sd35_setup_helper.subprocess.Popen", side_effect=mock_popen), \
             patch("tools.sd35_setup_helper.subprocess.run", side_effect=mock_run):
            result, events = self._run_helper(
                _Installer(self.service), archive, allow_redownload=True
            )

        self.assertTrue(pip_run)
        self.assertFalse(qualcomm_run)
        self.assertFalse(result)

        failed_event = next(e for e in events if e.get("phase") == "preflight_failed")
        self.assertIn("Preflight check failed", failed_event["error"])
        self.assertIn("ModuleNotFoundError: No module named 'yaml'", failed_event["error"])

    def test_24_junction_cleanup_safety(self) -> None:
        workspace_path = self.root / "fake_workspace"
        isolated_deps = workspace_path / "isolated_deps"
        isolated_deps.mkdir(parents=True, exist_ok=True)

        # Create a fake junction directory and a file in it
        fake_junction = isolated_deps / "torch"
        fake_junction.mkdir()
        fake_file = fake_junction / "do_not_delete.txt"
        fake_file.write_text("critical source file")

        # Mock os.rmdir to raise an OSError when trying to delete the fake junction
        def mock_rmdir(path):
            if Path(path) == fake_junction:
                raise OSError("Access Denied - Simulated fail-safe lock")
            os.rmdir(path)

        with patch("tools.sd35_setup_helper.os.rmdir", side_effect=mock_rmdir):
            SD35SetupHelper.safe_cleanup_temp_dir(str(workspace_path))

        # The clean up should have aborted, leaving isolated_deps and the critical source file intact!
        self.assertTrue(workspace_path.exists())
        self.assertTrue(isolated_deps.exists())
        self.assertTrue(fake_junction.exists())
        self.assertTrue(fake_file.exists())
        self.assertEqual(fake_file.read_text(), "critical source file")

        # Clean up for real
        fake_file.unlink()
        fake_junction.rmdir()
        isolated_deps.rmdir()
        workspace_path.rmdir()

    def test_25_missing_venv_executable_fails(self) -> None:
        archive = self.root / "sample.zip"
        script = (
            "qai-appbuilder-main/samples/models/generative_ai/image_generation/"
            "stable_diffusion_v3_5/python/stable_diffusion_v3_5.py"
        )
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(script, "")

        def mock_run(cmd, *args, **kwargs):
            return MagicMock(returncode=0)

        with patch("tools.sd35_setup_helper.subprocess.run", side_effect=mock_run):
            result, events = self._run_helper(
                _Installer(self.service), archive, allow_redownload=True
            )

        self.assertFalse(result)
        failed_event = next(e for e in events if e.get("phase") == "dependency_failed")
        self.assertIn("Failed to create virtual environment", failed_event["error"])

    def test_26_missing_torch_component_fails(self) -> None:
        archive = self.root / "sample.zip"
        script = (
            "qai-appbuilder-main/samples/models/generative_ai/image_generation/"
            "stable_diffusion_v3_5/python/stable_diffusion_v3_5.py"
        )
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(script, "")

        exe_parent = self.root / "app_bin"
        exe_parent.mkdir(parents=True, exist_ok=True)
        (exe_parent / "torch").mkdir(exist_ok=True)
        # missing torchgen and others
        mock_executable = str(exe_parent / "SnapdragonAIStudio.exe")

        def mock_run(cmd, *args, **kwargs):
            if "venv" in cmd:
                workspace = self.root
                venv_dir = workspace / "sd35_venv"
                venv_python = venv_dir / "Scripts" / "python.exe"
                venv_python.parent.mkdir(parents=True, exist_ok=True)
                venv_python.write_bytes(b"")
                (venv_dir / "Lib" / "site-packages").mkdir(parents=True, exist_ok=True)
                return MagicMock(returncode=0, stdout="", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        import tools.sd35_setup_helper
        with patch("sys.frozen", True, create=True), \
             patch("sys.executable", mock_executable), \
             patch("tools.sd35_setup_helper.subprocess.run", side_effect=mock_run):
            result, events = self._run_helper(
                _Installer(self.service), archive, allow_redownload=True
            )

        self.assertFalse(result)
        failed_event = next(e for e in events if e.get("phase") == "dependency_failed")
        self.assertIn("Required bundled Torch component(s) missing", failed_event["error"])

    def test_27_failed_junction_creation_fails(self) -> None:
        archive = self.root / "sample.zip"
        script = (
            "qai-appbuilder-main/samples/models/generative_ai/image_generation/"
            "stable_diffusion_v3_5/python/stable_diffusion_v3_5.py"
        )
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(script, "")

        exe_parent = self.root / "app_bin"
        exe_parent.mkdir(parents=True, exist_ok=True)
        (exe_parent / "torch").mkdir(exist_ok=True)
        (exe_parent / "torchgen").mkdir(exist_ok=True)
        (exe_parent / "functorch").mkdir(exist_ok=True)
        (exe_parent / "torch-2.14.0.dev20260808+cpu.dist-info").mkdir(exist_ok=True)
        mock_executable = str(exe_parent / "SnapdragonAIStudio.exe")

        def mock_run(cmd, *args, **kwargs):
            if "venv" in cmd:
                workspace = self.root
                venv_dir = workspace / "sd35_venv"
                venv_python = venv_dir / "Scripts" / "python.exe"
                venv_python.parent.mkdir(parents=True, exist_ok=True)
                venv_python.write_bytes(b"")
                (venv_dir / "Lib" / "site-packages").mkdir(parents=True, exist_ok=True)
                return MagicMock(returncode=0, stdout="", stderr="")
            elif "mklink" in cmd or "cmd" in cmd:
                raise subprocess.CalledProcessError(1, cmd, stderr="Access Denied")
            return MagicMock(returncode=0, stdout="", stderr="")

        import tools.sd35_setup_helper
        with patch("sys.frozen", True, create=True), \
             patch("sys.executable", mock_executable), \
             patch("tools.sd35_setup_helper.subprocess.run", side_effect=mock_run), \
             patch.dict("sys.modules", {"_winapi": None}):
            result, events = self._run_helper(
                _Installer(self.service), archive, allow_redownload=True
            )

        self.assertFalse(result)
        failed_event = next(e for e in events if e.get("phase") == "dependency_failed")
        self.assertIn("Failed to create junction", failed_event["error"])

    def test_28_safe_remove_venv_protection(self) -> None:
        # Success path
        venv_dir = self.root / "fake_venv"
        site_packages = venv_dir / "Lib" / "site-packages"
        site_packages.mkdir(parents=True, exist_ok=True)
        (site_packages / "torch").mkdir(exist_ok=True)
        (site_packages / "torchgen").mkdir(exist_ok=True)
        (site_packages / "functorch").mkdir(exist_ok=True)

        rmdir_calls = []
        rmtree_calls = []
        original_rmdir = os.rmdir

        def mock_rmdir(path):
            p = Path(path)
            rmdir_calls.append(p)
            if p.exists():
                original_rmdir(p)

        def mock_rmtree(path):
            rmtree_calls.append(Path(path))

        with patch("tools.sd35_setup_helper.os.rmdir", side_effect=mock_rmdir), \
             patch("tools.sd35_setup_helper.shutil.rmtree", side_effect=mock_rmtree):
            SD35SetupHelper.safe_remove_venv(venv_dir)

        self.assertIn(site_packages / "torch", rmdir_calls)
        self.assertIn(site_packages / "torchgen", rmdir_calls)
        self.assertIn(site_packages / "functorch", rmdir_calls)
        self.assertIn(venv_dir, rmtree_calls)

        # Failure path: simulate failing to remove the junction "torchgen"
        venv_dir_fail = self.root / "fake_venv_fail"
        site_packages_fail = venv_dir_fail / "Lib" / "site-packages"
        site_packages_fail.mkdir(parents=True, exist_ok=True)
        (site_packages_fail / "torch").mkdir(exist_ok=True)
        (site_packages_fail / "torchgen").mkdir(exist_ok=True)
        (site_packages_fail / "functorch").mkdir(exist_ok=True)

        rmdir_calls.clear()
        rmtree_calls.clear()

        def mock_rmdir_fail(path):
            p = Path(path)
            if p.name == "torchgen":
                raise OSError("Access Denied")
            rmdir_calls.append(p)
            if p.exists():
                original_rmdir(p)

        with patch("tools.sd35_setup_helper.os.rmdir", side_effect=mock_rmdir_fail), \
             patch("tools.sd35_setup_helper.shutil.rmtree", side_effect=mock_rmtree):
            with self.assertRaises(RuntimeError) as ctx:
                SD35SetupHelper.safe_remove_venv(venv_dir_fail)
            self.assertIn("Failed to remove junction", str(ctx.exception))

        # Check that shutil.rmtree was NEVER called on the venv
        self.assertNotIn(venv_dir_fail, rmtree_calls)


if __name__ == "__main__":
    unittest.main()
