from __future__ import annotations

import unittest

from controllers.generation_job import GenerationJob
from controllers.generation_queue import GenerationQueue
from controllers.generation_session import GenerationSessionModel
from engine.generation_progress import report_qnn_progress
from engine.job import Job
from engine.job_lifecycle import (
    JobStatus,
    get_job_status,
    normalize_job_status,
    set_job_progress,
)
from engine.phoenix_queue import PhoenixQueue
from engine.phoenix_scheduler import PhoenixScheduler
from engine.phoenix_worker import PhoenixWorker


class JobEngineTests(unittest.TestCase):
    def test_historical_statuses_are_normalized(self) -> None:
        expected = {
            "wartet": JobStatus.QUEUED,
            "läuft": JobStatus.RUNNING,
            "fertig": JobStatus.FINISHED,
            "Fehler": JobStatus.FAILED,
            "cancelled": JobStatus.CANCELLED,
        }
        for value, status in expected.items():
            with self.subTest(value=value):
                self.assertEqual(status, normalize_job_status(value))

    def test_generation_job_reports_normalized_progress(self) -> None:
        events: list[tuple[float, str]] = []
        job = GenerationJob(
            session=GenerationSessionModel(),
            progress_callback=lambda percent, message: events.append((percent, message)),
        )
        job.report_progress(1.4, "Fertig")
        self.assertEqual(1.0, job.progress)
        self.assertEqual("Fertig", job.progress_message)
        self.assertEqual([(100.0, "Fertig")], events)

    def test_qnn_progress_uses_common_reporting_path(self) -> None:
        events: list[tuple[float, str]] = []
        job = GenerationJob(
            session=GenerationSessionModel(),
            progress_callback=lambda percent, message: events.append((percent, message)),
        )
        self.assertTrue(report_qnn_progress(job, "Step 10/20: Timestep=500"))
        self.assertAlmostEqual(0.575, job.progress)
        self.assertEqual(57.5, events[0][0])
        self.assertIn("10/20", events[0][1])

    def test_generation_queue_uses_canonical_lifecycle(self) -> None:
        queue = GenerationQueue()
        job = GenerationJob(session=GenerationSessionModel(), status="wartet")
        queue.enqueue(job)
        self.assertIs(job, queue.dequeue())
        self.assertEqual(JobStatus.RUNNING, get_job_status(job))
        self.assertTrue(queue.cancel(job.job_id))
        self.assertEqual(JobStatus.CANCELLED, get_job_status(job))
        self.assertTrue(job.cancel_requested.is_set())
        queue.clear_finished()
        self.assertEqual([], queue.get_all_jobs())

    def test_legacy_job_uses_normalized_progress(self) -> None:
        job = Job(skill="test", kwargs={})
        job.start()
        self.assertEqual(JobStatus.RUNNING, get_job_status(job))
        job.finish("ok")
        self.assertEqual(JobStatus.FINISHED, get_job_status(job))
        self.assertEqual(1.0, job.progress)

    def test_worker_standardizes_success_and_error(self) -> None:
        worker = PhoenixWorker()
        successful = {"status": "wartet"}
        result = worker.run(successful, lambda _: "ok")
        self.assertEqual(JobStatus.FINISHED.value, result["status"])
        self.assertEqual(JobStatus.FINISHED, get_job_status(successful))

        failed = {"status": "wartet"}
        result = worker.run(failed, lambda _: 1 / 0)
        self.assertEqual(JobStatus.FAILED.value, result["status"])
        self.assertEqual(JobStatus.FAILED, get_job_status(failed))
        self.assertIn("ZeroDivisionError", failed["error"])

    def test_scheduler_cancels_active_and_waiting_jobs(self) -> None:
        phoenix_queue = PhoenixQueue()
        running = {"status": JobStatus.RUNNING.value}
        waiting = {"status": "zurückgestellt"}
        phoenix_queue.enqueue(running)
        phoenix_queue.enqueue(waiting)
        scheduler = PhoenixScheduler()
        scheduler.current_job = running
        scheduler.request_cancel()
        scheduler.process_all_jobs(phoenix_queue, PhoenixWorker(), lambda _: None)
        self.assertEqual(JobStatus.CANCELLED, get_job_status(running))
        self.assertEqual(JobStatus.CANCELLED, get_job_status(waiting))

    def test_progress_helper_supports_dictionary_jobs(self) -> None:
        job = {"status": "wartet"}
        self.assertEqual(0.0, set_job_progress(job, -1))
        self.assertEqual(0.0, job["progress"])


if __name__ == "__main__":
    unittest.main()
