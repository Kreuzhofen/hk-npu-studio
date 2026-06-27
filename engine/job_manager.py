"""
SnapdragonAI Studio

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
        self.jobs = deque()

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
                **job.kwargs
            )

            job.finish(result)

        except Exception as e:
            job.fail(str(e))
            raise

        return job