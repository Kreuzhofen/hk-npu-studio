"""
Snapdragon AI Studio

Job Manager

Created by Holger Kreuzhofen
Phoenix Engine
"""

from collections import deque

from engine.job import Job
from engine.phoenix_adapter import PhoenixAdapter


class JobManager:
    """
    Verwaltet KI-Aufträge der Phoenix Engine.
    """

    def __init__(self):
        self.adapter = PhoenixAdapter()

        # Warteschlange
        self.jobs = deque()

        # Abgeschlossene Jobs
        self.history = []

    def add_job(self, skill: str, **kwargs) -> Job:
        """
        Erzeugt einen neuen Job und fügt ihn der Warteschlange hinzu.
        """

        job = Job(skill=skill, kwargs=kwargs)
        self.jobs.append(job)

        return job

    def has_jobs(self) -> bool:
        """
        Prüft, ob sich Jobs in der Warteschlange befinden.
        """

        return len(self.jobs) > 0

    def run_next(self):
        """
        Führt den nächsten Job aus.
        """

        if not self.jobs:
            return None

        job = self.jobs.popleft()

        try:
            job.start()

            result = self.adapter.run(
                job.skill,
                **job.kwargs,
            )

            job.finish(result)

        except Exception as error:
            job.fail(str(error))
            raise

        finally:
            # Jeder beendete Job wird gespeichert
            self.history.append(job)

        return job

    def get_history(self):
        """
        Liefert die Liste aller abgeschlossenen Jobs.
        """

        return list(self.history)

    def clear_history(self):
        """
        Löscht die Job-Historie.
        """

        self.history.clear()
