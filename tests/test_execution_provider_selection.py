from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from app.settings_manager import SettingsManager
from engine.backends.backend_manager import BackendManager
from engine.onnx_provider_service import OnnxProviderService
from gui.controllers.batch_controller import BatchController
from widgets.phoenix.views.home_view import PhoenixHomeView


class _QnnDiscovery:
    qnn_sdk_found = True
    qnn_tools_found = True


class ExecutionProviderSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.preferences_path = Path(self.temporary_directory.name) / "preferences.json"
        self.path_patch = patch.object(
            SettingsManager, "get_preferences_path", return_value=self.preferences_path
        )
        self.path_patch.start()

    def tearDown(self) -> None:
        self.path_patch.stop()
        self.temporary_directory.cleanup()

    def _save_provider(self, provider: str) -> None:
        self.assertTrue(
            SettingsManager.save_settings(
                {"execution_provider": provider, "hardware_accel": "True"}
            )
        )

    def test_cpu_selection_survives_reload_and_controls_runtime(self) -> None:
        self._save_provider("CPU EP")

        self.assertEqual("CPU EP", SettingsManager.load_settings()["execution_provider"])
        self.assertEqual(
            SettingsManager.CPU_EXECUTION_PROVIDER,
            SettingsManager.get_execution_provider(),
        )
        self.assertEqual(
            "ONNX Runtime CPU",
            BackendManager().get_best_backend().get_backend_name(),
        )
        manager = BackendManager()
        self.assertEqual("ONNX Runtime CPU", manager.get_active_backend().get_backend_name())
        self.assertEqual("CPU EP", manager.get_active_execution_provider_label())
        self.assertEqual("CPU EP", SettingsManager.get_execution_provider_label())
        self.assertEqual(
            SettingsManager.CPU_EXECUTION_PROVIDER,
            PhoenixHomeView._execution_provider_status(_QnnDiscovery()),
        )

        with patch.object(OnnxProviderService, "initialize"), patch.object(
            OnnxProviderService,
            "_providers_after",
            ["QNNExecutionProvider", "CPUExecutionProvider"],
        ):
            self.assertEqual(
                ["CPUExecutionProvider"],
                OnnxProviderService.preferred_providers(),
            )

    def test_qnn_selection_survives_reload_and_controls_runtime(self) -> None:
        self._save_provider("QNN EP")

        self.assertEqual("QNN EP", SettingsManager.load_settings()["execution_provider"])
        self.assertEqual(
            SettingsManager.QNN_EXECUTION_PROVIDER,
            SettingsManager.get_execution_provider(),
        )
        self.assertIn(
            "Qualcomm",
            BackendManager().get_best_backend().get_backend_name(),
        )
        self.assertEqual(
            SettingsManager.QNN_EXECUTION_PROVIDER,
            PhoenixHomeView._execution_provider_status(_QnnDiscovery()),
        )

        with patch.object(OnnxProviderService, "initialize"), patch.object(
            OnnxProviderService,
            "_providers_after",
            ["QNNExecutionProvider", "CPUExecutionProvider"],
        ), patch.object(
            OnnxProviderService,
            "provider_options",
            return_value={"backend_path": "QnnHtp.dll"},
        ):
            providers = OnnxProviderService.preferred_providers()
        self.assertEqual(
            ("QNNExecutionProvider", {"backend_path": "QnnHtp.dll"}),
            providers[0],
        )
        self.assertEqual("CPUExecutionProvider", providers[1])

    def test_session_factory_passes_only_configured_cpu_provider(self) -> None:
        self._save_provider("CPU EP")
        session = MagicMock()
        session.get_providers.return_value = ["CPUExecutionProvider"]
        fake_ort = MagicMock()
        fake_ort.InferenceSession.return_value = session

        with patch.object(OnnxProviderService, "initialize"), patch.dict(
            "sys.modules", {"onnxruntime": fake_ort}
        ):
            created = OnnxProviderService.create_session("model.onnx", "test")

        self.assertIs(session, created)
        fake_ort.InferenceSession.assert_called_once_with(
            "model.onnx", providers=["CPUExecutionProvider"]
        )

    def test_dashboard_reports_the_configured_provider(self) -> None:
        runtime = MagicMock()
        runtime.get_engine_status.return_value = {}
        runtime.get_last_output.return_value = None
        with patch(
            "gui.controllers.batch_controller.create_application_adapter",
            return_value=MagicMock(),
        ), patch(
            "gui.controllers.batch_controller.create_batch_runtime_adapter",
            return_value=runtime,
        ), patch(
            "gui.controllers.batch_controller.create_batch_ui_adapter",
            return_value=MagicMock(),
        ):
            controller = BatchController(MagicMock())

        for stored, expected in (
            ("CPU EP", "CPUExecutionProvider"),
            ("QNN EP", "QNNExecutionProvider"),
        ):
            with self.subTest(provider=stored):
                self._save_provider(stored)
                self.assertEqual(
                    expected,
                    controller.get_dashboard_snapshot()["backend"],
                )


if __name__ == "__main__":
    unittest.main()
