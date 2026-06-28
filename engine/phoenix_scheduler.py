"""
SnapdragonAI Studio

Phoenix Scheduler

Created by Holger Kreuzhofen
Phoenix Engine 1.0
"""


class PhoenixScheduler:
    """
    Grundgerüst des Phoenix Schedulers.

    Der Scheduler steuert später die automatische Verarbeitung
    von Jobs, Queues und Workern.

    In Sprint 018.3A enthält diese Klasse bewusst noch keine
    Thread-Logik und keine direkte Plugin-Ausführung.
    """

    STATUS_IDLE = "idle"
    STATUS_RUNNING = "running"
    STATUS_PAUSED = "paused"
    STATUS_STOPPED = "stopped"

    def __init__(self):
        self.status = self.STATUS_IDLE
        self.current_job = None
        self.processed_jobs = 0
        self.failed_jobs = 0

    def start(self):
        """
        Startet den Scheduler.
        """

        if self.status == self.STATUS_RUNNING:
            return False

        self.status = self.STATUS_RUNNING
        return True

    def stop(self):
        """
        Stoppt den Scheduler.
        """

        self.status = self.STATUS_STOPPED
        self.current_job = None
        return True

    def pause(self):
        """
        Pausiert den Scheduler.
        """

        if self.status != self.STATUS_RUNNING:
            return False

        self.status = self.STATUS_PAUSED
        return True

    def resume(self):
        """
        Setzt einen pausierten Scheduler fort.
        """

        if self.status != self.STATUS_PAUSED:
            return False

        self.status = self.STATUS_RUNNING
        return True

    def reset(self):
        """
        Setzt den Scheduler zurück.
        """

        self.status = self.STATUS_IDLE
        self.current_job = None
        self.processed_jobs = 0
        self.failed_jobs = 0
        return True

    def is_running(self):
        """
        Gibt zurück, ob der Scheduler läuft.
        """

        return self.status == self.STATUS_RUNNING

    def is_paused(self):
        """
        Gibt zurück, ob der Scheduler pausiert ist.
        """

        return self.status == self.STATUS_PAUSED

    def is_stopped(self):
        """
        Gibt zurück, ob der Scheduler gestoppt ist.
        """

        return self.status == self.STATUS_STOPPED

    def is_idle(self):
        """
        Gibt zurück, ob der Scheduler im Leerlauf ist.
        """

        return self.status == self.STATUS_IDLE

    def set_current_job(self, job):
        """
        Setzt den aktuellen Job.
        """

        self.current_job = job

    def clear_current_job(self):
        """
        Entfernt den aktuellen Job.
        """

        self.current_job = None

    def get_current_job(self):
        """
        Gibt den aktuellen Job zurück.
        """

        return self.current_job

    def mark_job_done(self):
        """
        Markiert einen Job als erfolgreich verarbeitet.
        """

        self.processed_jobs += 1
        self.clear_current_job()

    def mark_job_failed(self):
        """
        Markiert einen Job als fehlgeschlagen.
        """

        self.failed_jobs += 1
        self.clear_current_job()

    def process_next_job(self):
        """
        Platzhalter für die spätere Job-Verarbeitung.

        Die echte Queue- und Worker-Logik folgt in den nächsten Sprints.
        """

        if not self.is_running():
            return None

        return self.current_job

    def get_status(self):
        """
        Gibt den aktuellen Scheduler-Status zurück.
        """

        return {
            "status": self.status,
            "current_job": self.current_job,
            "processed_jobs": self.processed_jobs,
            "failed_jobs": self.failed_jobs,
        }