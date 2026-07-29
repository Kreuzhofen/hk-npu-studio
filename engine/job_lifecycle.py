from __future__ import annotations

from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    """Kanonische Zustände aller ausführbaren Jobs und Pipeline-Aufträge."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


TERMINAL_JOB_STATUSES = frozenset(
    {JobStatus.FINISHED, JobStatus.FAILED, JobStatus.CANCELLED}
)

_STATUS_ALIASES = {
    "queued": JobStatus.QUEUED,
    "waiting": JobStatus.QUEUED,
    "wartet": JobStatus.QUEUED,
    "deferred": JobStatus.QUEUED,
    "zurückgestellt": JobStatus.QUEUED,
    "running": JobStatus.RUNNING,
    "läuft": JobStatus.RUNNING,
    "done": JobStatus.FINISHED,
    "finished": JobStatus.FINISHED,
    "fertig": JobStatus.FINISHED,
    "success": JobStatus.FINISHED,
    "error": JobStatus.FAILED,
    "failed": JobStatus.FAILED,
    "fehler": JobStatus.FAILED,
    "cancelled": JobStatus.CANCELLED,
    "canceled": JobStatus.CANCELLED,
}


def normalize_job_status(value: JobStatus | str) -> JobStatus:
    """Normalisiert historische Statuswerte auf den kanonischen Vertrag."""
    if isinstance(value, JobStatus):
        return value
    text = str(value).strip()
    try:
        return JobStatus(text.upper())
    except ValueError as error:
        alias = _STATUS_ALIASES.get(text.casefold())
        if alias is None:
            raise ValueError(f"Unbekannter Jobstatus: {value!r}") from error
        return alias


def clamp_progress(value: float | int) -> float:
    """Begrenzt normalisierten Fortschritt auf den Bereich 0,0 bis 1,0."""
    return max(0.0, min(1.0, float(value)))


def get_job_status(job: Any) -> JobStatus:
    value = job.get("status", JobStatus.QUEUED) if isinstance(job, dict) else job.status
    return normalize_job_status(value)


def set_job_status(job: Any, status: JobStatus | str) -> JobStatus:
    normalized = normalize_job_status(status)
    if isinstance(job, dict):
        job["status"] = normalized.value
    else:
        job.status = normalized.value
    if normalized is JobStatus.RUNNING:
        _observe_resources(job)
    return normalized


def set_job_progress(
    job: Any,
    progress: float | int,
    message: str = "",
    *,
    notify: bool = True,
) -> float:
    """Aktualisiert Fortschritt und meldet kompatible Prozentwerte an Callbacks."""
    normalized = clamp_progress(progress)
    if isinstance(job, dict):
        job["progress"] = normalized
        job["progress_message"] = message
        callback = job.get("progress_callback")
    else:
        job.progress = normalized
        if hasattr(job, "progress_message"):
            job.progress_message = message
        callback = getattr(job, "progress_callback", None)
    if notify and callable(callback):
        try:
            callback(round(normalized * 100.0, 10), message)
        except Exception:
            pass
    if get_job_status(job) is JobStatus.RUNNING:
        _observe_resources(job)
    return normalized


def _observe_resources(job: Any) -> None:
    """Keep monitoring passive: diagnostics must never affect job behavior."""
    try:
        from engine.resource_monitor import observe_running_job

        observe_running_job(job, getattr(job, "backend_adapter", None))
    except Exception:
        pass


def cancel_job(job: Any) -> None:
    cancel_requested = (
        job.get("cancel_requested") if isinstance(job, dict)
        else getattr(job, "cancel_requested", None)
    )
    if cancel_requested is not None and hasattr(cancel_requested, "set"):
        cancel_requested.set()
    set_job_status(job, JobStatus.CANCELLED)


def fail_job(job: Any, error: BaseException | str) -> None:
    message = str(error)
    if isinstance(job, dict):
        job["error"] = message
    else:
        if hasattr(job, "error_message"):
            job.error_message = message
        elif hasattr(job, "error"):
            job.error = message
    set_job_status(job, JobStatus.FAILED)
