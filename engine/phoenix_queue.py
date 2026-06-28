"""
SnapdragonAI Studio

Phoenix Queue

Created by Holger Kreuzhofen
Phoenix Engine 1.0
"""

from collections import deque


class PhoenixQueue:
    """
    Verwaltet die Job-Warteschlange der Phoenix Engine.

    In Sprint 018.3B kümmert sich diese Klasse ausschließlich
    um das Speichern und Verwalten von Jobs.

    Die eigentliche Verarbeitung übernimmt später
    der PhoenixScheduler.
    """

    def __init__(self):

        self._queue = deque()

    # ---------------------------------------------------------
    # Queue Verwaltung
    # ---------------------------------------------------------

    def enqueue(self, job):
        """
        Fügt einen Job am Ende der Queue hinzu.
        """

        self._queue.append(job)

    def dequeue(self):
        """
        Entfernt den ersten Job.
        """

        if self.is_empty():
            return None

        return self._queue.popleft()

    def peek(self):
        """
        Liefert den ersten Job,
        ohne ihn aus der Queue zu entfernen.
        """

        if self.is_empty():
            return None

        return self._queue[0]

    def clear(self):
        """
        Löscht die komplette Queue.
        """

        self._queue.clear()

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    def is_empty(self):
        """
        Prüft, ob die Queue leer ist.
        """

        return len(self._queue) == 0

    def size(self):
        """
        Anzahl der Jobs.
        """

        return len(self._queue)

    # ---------------------------------------------------------
    # Zugriff
    # ---------------------------------------------------------

    def get_jobs(self):
        """
        Liefert alle Jobs als Liste.
        """

        return list(self._queue)

    def get_job(self, index):
        """
        Liefert einen Job anhand des Index.
        """

        if index < 0:
            return None

        if index >= len(self._queue):
            return None

        return list(self._queue)[index]

    # ---------------------------------------------------------
    # Entfernen
    # ---------------------------------------------------------

    def remove(self, job):
        """
        Entfernt einen bestimmten Job.
        """

        try:
            self._queue.remove(job)
            return True

        except ValueError:
            return False

    # ---------------------------------------------------------
    # Iterator
    # ---------------------------------------------------------

    def __iter__(self):

        return iter(self._queue)

    def __len__(self):

        return len(self._queue)

    def __repr__(self):

        return (
            f"PhoenixQueue("
            f"jobs={len(self._queue)})"
        )