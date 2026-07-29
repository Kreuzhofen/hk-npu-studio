from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ErrorDiagnostic:
    """Strukturierte, UI-unabhängige Beschreibung eines Laufzeitfehlers."""

    category: str
    context: str
    exception_type: str
    message: str
    job_id: str | None = None
    backend_name: str | None = None

    def as_log_message(self) -> str:
        fields = [
            f"category={self.category}",
            f"context={self.context}",
            f"exception={self.exception_type}",
            f"message={self.message}",
        ]
        if self.job_id:
            fields.append(f"job_id={self.job_id}")
        if self.backend_name:
            fields.append(f"backend={self.backend_name}")
        return " | ".join(fields)


def diagnose_exception(
    logger: logging.Logger,
    error: BaseException,
    *,
    category: str,
    context: str,
    job: Any = None,
    backend_name: str | None = None,
) -> ErrorDiagnostic:
    """Protokolliert einen Fehler mit Traceback und aktualisiert optional den Job."""
    job_id = str(getattr(job, "job_id", "")) or None
    diagnostic = ErrorDiagnostic(
        category=category,
        context=context,
        exception_type=type(error).__name__,
        message=str(error),
        job_id=job_id,
        backend_name=backend_name,
    )
    logger.error(diagnostic.as_log_message(), exc_info=error)
    if job is not None:
        fail = getattr(job, "fail", None)
        if callable(fail):
            fail(error)
    return diagnostic
