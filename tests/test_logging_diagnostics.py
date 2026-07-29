from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel
from engine.error_diagnostics import diagnose_exception
from engine.job_lifecycle import JobStatus, get_job_status
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


if __name__ == "__main__":
    unittest.main()
