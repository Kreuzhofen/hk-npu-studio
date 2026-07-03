"""
Snapdragon AI Studio

Phoenix Scheduler

Created by Holger Kreuzhofen
Phoenix Engine 1.0
"""


class PhoenixScheduler:
    """
    Phoenix Scheduler.

    Steuert Jobs aus einer PhoenixQueue und liefert
    Fortschrittsinformationen für GUI, CLI oder spätere Services.
    """

    STATUS_IDLE = "idle"
    STATUS_RUNNING = "running"
    STATUS_PAUSED = "paused"
    STATUS_STOPPED = "stopped"
    STATUS_CANCEL_REQUESTED = "cancel_requested"

    def __init__(self):
        self.status = self.STATUS_IDLE
        self.current_job = None
        self.processed_jobs = 0
        self.failed_jobs = 0
        self.total_jobs = 0
        self.current_index = 0
        self.cancel_requested = False

    def start(self):
        if self.status == self.STATUS_RUNNING:
            return False

        self.cancel_requested = False
        self.status = self.STATUS_RUNNING
        return True

    def stop(self):
        self.cancel_requested = True
        self.status = self.STATUS_STOPPED
        return True

    def request_cancel(self):
        self.cancel_requested = True
        self.status = self.STATUS_CANCEL_REQUESTED
        return True

    def pause(self):
        if self.status != self.STATUS_RUNNING:
            return False

        self.status = self.STATUS_PAUSED
        return True

    def resume(self):
        if self.status != self.STATUS_PAUSED:
            return False

        self.status = self.STATUS_RUNNING
        return True

    def reset(self):
        self.status = self.STATUS_IDLE
        self.current_job = None
        self.processed_jobs = 0
        self.failed_jobs = 0
        self.total_jobs = 0
        self.current_index = 0
        self.cancel_requested = False
        return True

    def is_running(self):
        return self.status == self.STATUS_RUNNING

    def is_paused(self):
        return self.status == self.STATUS_PAUSED

    def is_stopped(self):
        return self.status == self.STATUS_STOPPED

    def is_idle(self):
        return self.status == self.STATUS_IDLE

    def is_cancel_requested(self):
        return self.cancel_requested

    def set_current_job(self, job):
        self.current_job = job

    def clear_current_job(self):
        self.current_job = None

    def get_current_job(self):
        return self.current_job

    def mark_job_done(self):
        self.processed_jobs += 1
        self.clear_current_job()

    def mark_job_failed(self):
        self.failed_jobs += 1
        self.clear_current_job()

    def get_next_waiting_job(self, phoenix_queue):
        for job in phoenix_queue.get_jobs():
            if job.get("status") == "wartet":
                return job

        return None

    def count_waiting_jobs(self, phoenix_queue):
        count = 0

        for job in phoenix_queue.get_jobs():
            if job.get("status") == "wartet":
                count += 1

        return count

    def process_next_job(
        self,
        phoenix_queue,
        worker,
        task,
        on_job_start=None,
        on_job_done=None,
        on_job_error=None,
    ):
        if not self.is_running():
            return None

        if self.cancel_requested:
            return None

        job = self.get_next_waiting_job(phoenix_queue)

        if job is None:
            return None

        self.current_index += 1
        self.set_current_job(job)
        job["status"] = "läuft"

        if on_job_start:
            on_job_start(job)

        result = worker.run(job, task)

        if result["status"] == worker.STATUS_DONE:
            output_path = result["result"]

            job["status"] = "fertig"
            job["output_path"] = output_path

            self.mark_job_done()

            if on_job_done:
                on_job_done(job, output_path)

            return result

        job["status"] = "Fehler"
        self.mark_job_failed()

        if on_job_error:
            on_job_error(job, result["error"])

        return result

    def process_all_jobs(
        self,
        phoenix_queue,
        worker,
        task,
        on_job_start=None,
        on_job_done=None,
        on_job_error=None,
    ):
        self.start()

        self.total_jobs = self.count_waiting_jobs(phoenix_queue)
        self.current_index = 0
        self.processed_jobs = 0
        self.failed_jobs = 0

        results = []

        while self.is_running():
            if self.cancel_requested:
                break

            job = self.get_next_waiting_job(phoenix_queue)

            if job is None:
                break

            result = self.process_next_job(
                phoenix_queue=phoenix_queue,
                worker=worker,
                task=task,
                on_job_start=on_job_start,
                on_job_done=on_job_done,
                on_job_error=on_job_error,
            )

            if result is not None:
                results.append(result)

        if self.cancel_requested:
            self.status = self.STATUS_STOPPED
        else:
            self.status = self.STATUS_STOPPED
            self.cancel_requested = False

        return results

    def get_progress(self):
        if self.total_jobs <= 0:
            percent = 0
        else:
            completed = self.processed_jobs + self.failed_jobs
            percent = int((completed / self.total_jobs) * 100)

        return {
            "status": self.status,
            "current": self.current_index,
            "total": self.total_jobs,
            "processed": self.processed_jobs,
            "failed": self.failed_jobs,
            "percent": percent,
            "running": self.is_running(),
            "cancel_requested": self.cancel_requested,
        }

    def get_status(self):
        return {
            "status": self.status,
            "current_job": self.current_job,
            "processed_jobs": self.processed_jobs,
            "failed_jobs": self.failed_jobs,
            "total_jobs": self.total_jobs,
            "current_index": self.current_index,
            "cancel_requested": self.cancel_requested,
            "progress": self.get_progress(),
        }