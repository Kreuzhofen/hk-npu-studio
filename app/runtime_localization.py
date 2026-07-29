from __future__ import annotations

import re

from app.i18n import tr


_STATUS_KEYS: dict[str, tuple[str, str]] = {
    "ready": ("ready", "Bereit"),
    "bereit": ("ready", "Bereit"),
    "listo": ("ready", "Bereit"),
    "idle": ("idle", "Inaktiv"),
    "inaktiv": ("idle", "Inaktiv"),
    "inactivo": ("idle", "Inaktiv"),
    "active": ("status_active_title", "Aktiv"),
    "aktiv": ("status_active_title", "Aktiv"),
    "activo": ("status_active_title", "Aktiv"),
    "running": ("running", "Läuft"),
    "läuft": ("running", "Läuft"),
    "en ejecución": ("running", "Läuft"),
    "generating": ("status_generating", "Generierung läuft"),
    "generierung läuft": ("status_generating", "Generierung läuft"),
    "generación en curso": ("status_generating", "Generierung läuft"),
    "paused": ("paused", "Pausiert"),
    "pausiert": ("paused", "Pausiert"),
    "en pausa": ("paused", "Pausiert"),
    "stopping": ("stopping", "Stoppt"),
    "stoppt": ("stopping", "Stoppt"),
    "deteniendo": ("stopping", "Stoppt"),
    "stopped": ("stopped", "Gestoppt"),
    "gestoppt": ("stopped", "Gestoppt"),
    "detenido": ("stopped", "Gestoppt"),
    "finished": ("status_completed", "Fertig"),
    "completed": ("status_completed", "Fertig"),
    "complete": ("status_completed", "Fertig"),
    "abgeschlossen": ("status_completed", "Fertig"),
    "fertig": ("status_completed", "Fertig"),
    "finalizado": ("status_completed", "Fertig"),
    "completado": ("status_completed", "Fertig"),
    "success": ("status_completed", "Fertig"),
    "done": ("worker_done", "Worker fertig"),
    "busy": ("worker_busy", "Worker beschäftigt"),
    "cancelled": ("status_cancelled", "Abgebrochen"),
    "canceled": ("status_cancelled", "Abgebrochen"),
    "cancelado": ("status_cancelled", "Abgebrochen"),
    "abgebrochen": ("status_cancelled", "Abgebrochen"),
    "cancel_requested": ("cancel_requested", "Abbruch angefordert"),
    "failed": ("status_failed", "Fehler"),
    "error": ("status_failed", "Fehler"),
    "fehler": ("status_failed", "Fehler"),
    "installed": ("status_installed_title", "Installiert"),
    "installiert": ("status_installed_title", "Installiert"),
    "instalado": ("status_installed_title", "Installiert"),
    "not installed": ("not_installed", "Nicht installiert"),
    "nicht installiert": ("not_installed", "Nicht installiert"),
    "no instalado": ("not_installed", "Nicht installiert"),
    "no_output": ("no_output", "Keine Ausgabe"),
    "waiting": ("queue_status_waiting", "Wartet"),
    "wartet": ("queue_status_waiting", "Wartet"),
    "en espera": ("queue_status_waiting", "Wartet"),
    "processing": ("queue_status_processing", "Wird verarbeitet"),
    "verarbeitet": ("queue_status_processing", "Wird verarbeitet"),
    "procesando": ("queue_status_processing", "Wird verarbeitet"),
    "deferred": ("queue_status_deferred", "Zurückgestellt"),
    "zurückgestellt": ("queue_status_deferred", "Zurückgestellt"),
    "aplazado": ("queue_status_deferred", "Zurückgestellt"),
}

_ERROR_PREFIX = re.compile(r"^(?:error|fehler|error del proceso)\s*:\s*", re.IGNORECASE)


def localize_runtime_text(value: object) -> str:
    """Translate a canonical or previously localized runtime value at the UI boundary."""
    text = str(value or "").strip()
    if not text:
        return text

    error_match = _ERROR_PREFIX.match(text)
    if error_match:
        detail = text[error_match.end():]
        return f"{tr('error', 'Fehler')}: {detail}"

    normalized = text.casefold()
    entry = _STATUS_KEYS.get(normalized)
    if entry is None:
        return text
    key, fallback = entry
    return tr(key, fallback)
