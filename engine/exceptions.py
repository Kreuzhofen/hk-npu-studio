from __future__ import annotations


class PhoenixError(Exception):
    """Basisklasse für kontrollierte Fehler der Phoenix Engine."""


class BackendError(PhoenixError):
    """Fehler bei Auswahl, Initialisierung oder Ausführung eines Backends."""


class PipelineError(PhoenixError):
    """Fehler während Vorbereitung, Ausführung oder Abschluss einer Pipeline."""


class JobError(PhoenixError):
    """Fehler im Lebenszyklus eines Jobs oder Workers."""


class ConfigurationError(PhoenixError):
    """Fehlerhafte oder unvollständige Laufzeitkonfiguration."""
