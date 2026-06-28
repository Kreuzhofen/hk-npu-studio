"""
SnapdragonAI Studio

Phoenix Worker

Created by Holger Kreuzhofen
Phoenix Engine 1.0
"""

import traceback


class PhoenixWorker:
    """
    Führt genau einen Phoenix Job aus.

    Der Worker ist bewusst unabhängig von tkinter und GUI.
    Er bekommt eine callable Funktion, führt sie aus und gibt
    ein Ergebnis-Dictionary zurück.

    Die spätere Verbindung zum PhoenixAdapter erfolgt im Scheduler
    bzw. Controller.
    """

    STATUS_IDLE = "idle"
    STATUS_RUNNING = "running"
    STATUS_DONE = "done"
    STATUS_ERROR = "error"

    def __init__(self, name="PhoenixWorker"):
        self.name = name
        self.status = self.STATUS_IDLE
        self.current_job = None
        self.last_result = None
        self.last_error = None

    def run(self, job, task):
        """
        Führt einen Job mit einer übergebenen Funktion aus.

        job:
            Beliebiges Job-Objekt oder Dictionary.

        task:
            Callable, z. B. eine Funktion, die den Job verarbeitet.

        Rückgabe:
            Dictionary mit status, job, result und error.
        """

        self.current_job = job
        self.status = self.STATUS_RUNNING
        self.last_result = None
        self.last_error = None

        try:
            result = task(job)

            self.status = self.STATUS_DONE
            self.last_result = result

            return {
                "status": self.STATUS_DONE,
                "job": job,
                "result": result,
                "error": None,
            }

        except Exception:
            error = traceback.format_exc()

            self.status = self.STATUS_ERROR
            self.last_error = error

            return {
                "status": self.STATUS_ERROR,
                "job": job,
                "result": None,
                "error": error,
            }

        finally:
            self.current_job = None

    def reset(self):
        """
        Setzt den Worker zurück.
        """

        self.status = self.STATUS_IDLE
        self.current_job = None
        self.last_result = None
        self.last_error = None

    def is_idle(self):
        return self.status == self.STATUS_IDLE

    def is_running(self):
        return self.status == self.STATUS_RUNNING

    def is_done(self):
        return self.status == self.STATUS_DONE

    def has_error(self):
        return self.status == self.STATUS_ERROR

    def get_status(self):
        """
        Liefert den aktuellen Worker-Status.
        """

        return {
            "name": self.name,
            "status": self.status,
            "current_job": self.current_job,
            "last_result": self.last_result,
            "last_error": self.last_error,
        }