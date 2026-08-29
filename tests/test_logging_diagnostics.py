from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel
from engine.error_diagnostics import diagnose_exception
from engine.job_lifecycle import JobStatus, get_job_status
from engine.qnn_dlc_diagnostic_runner import QnnDlcDiagnosticPaths
from engine.qnn_dlc_runtime_service import QnnDlcRuntimePaths
from engine.logging_config import (
    LOG_FILE_NAME,
    close_logging,
    configure_logging,
    get_logger,
)


class LoggingDiagnosticsTests(unittest.TestCase):
    def tearDown(self) -> None:
        close_logging()
        configure_logging(force=True)

    def test_configuration_creates_log_directory_and_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = configure_logging(temporary_directory, force=True)
            logger = get_logger("LoggingDiagnosticsTests")
            logger.info("strukturierter Testeintrag")
            for handler in logging.getLogger().handlers:
                handler.flush()

            self.assertEqual(LOG_FILE_NAME, log_path.name)
            self.assertTrue(log_path.is_file())
            content = log_path.read_text(encoding="utf-8")
            self.assertIn("INFO | LoggingDiagnosticsTests", content)
            self.assertIn("strukturierter Testeintrag", content)
            close_logging()

    def test_rotation_limits_active_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = configure_logging(
                temporary_directory,
                max_bytes=256,
                backup_count=2,
                force=True,
            )
            logger = get_logger("RotationTest")
            for index in range(40):
                logger.info("Eintrag %s %s", index, "x" * 40)
            for handler in logging.getLogger().handlers:
                handler.flush()

            rotated_files = list(Path(temporary_directory).glob(f"{log_path.name}.*"))
            self.assertTrue(rotated_files)
            self.assertLessEqual(len(rotated_files), 2)
            close_logging()

    def test_exception_diagnostic_contains_context_and_fails_job(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            configure_logging(temporary_directory, force=True)
            logger = get_logger("DiagnosticTest")
            job = GenerationJob(session=GenerationSessionModel())
            error = RuntimeError("Testfehler")

            diagnostic = diagnose_exception(
                logger,
                error,
                category="pipeline",
                context="test_run",
                job=job,
                backend_name="TestBackend",
            )

            self.assertEqual("RuntimeError", diagnostic.exception_type)
            self.assertEqual("test_run", diagnostic.context)
            self.assertEqual(JobStatus.FAILED, get_job_status(job))
            self.assertEqual("Testfehler", job.error_message)
            close_logging()

    def test_qnn_dlc_paths_use_dynamic_app_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            models = root / "managed-models"
            logs = root / "logs"
            with patch("engine.qnn_dlc_diagnostic_runner.BASE", root), patch(
                "engine.qnn_dlc_diagnostic_runner.MODELS_DIR", models
            ), patch("engine.qnn_dlc_diagnostic_runner.LOG_DIR", logs), patch(
                "engine.qnn_dlc_runtime_service.BASE", root
            ), patch("engine.qnn_dlc_runtime_service.LOG_DIR", logs):
                diagnostic_paths = QnnDlcDiagnosticPaths()
                runtime_paths = QnnDlcRuntimePaths()
                self.assertEqual(root, diagnostic_paths.project_root)
                self.assertEqual(root, runtime_paths.project_root)
                self.assertEqual(logs / "diagnostics", diagnostic_paths.diagnostics_root)
                self.assertEqual(logs / "diagnostics", runtime_paths.diagnostics_root)
                self.assertEqual(
                    models / "qnn_mobilenet_v2" / "qnn_dlc_w8a8"
                    / "mobilenet_v2-qnn_dlc-w8a8" / "mobilenet_v2.dlc",
                    diagnostic_paths.model_path,
                )

    def test_model_manager_diagnostic_route_uses_runner(self) -> None:
        from controllers.model_manager_controller import ModelManagerController

        expected = {"status": "not_run"}
        runner = MagicMock()
        runner.run.return_value = expected
        with patch(
            "controllers.model_manager_controller.QnnDlcDiagnosticRunner",
            return_value=runner,
        ):
            result = ModelManagerController.__new__(ModelManagerController).run_npu_diagnostic()

        self.assertEqual(expected, result)
        runner.run.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
