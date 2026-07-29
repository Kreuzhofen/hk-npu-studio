from __future__ import annotations

import platform
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from config import BASE
from engine.backends.backend_manager import BackendManager
from engine.logging_config import get_logger
from engine.model_registry import ModelRegistry


logger = get_logger("StartupDiagnostics")
CPU_FALLBACK_BACKEND = "CPU (Stub)"


class StartupCheckStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class StartupCheck:
    category: str
    status: StartupCheckStatus
    message: str
    details: dict[str, object] = field(default_factory=dict)


@dataclass
class StartupDiagnosticReport:
    checks: list[StartupCheck] = field(default_factory=list)
    selected_backend: str = CPU_FALLBACK_BACKEND
    fallback_active: bool = False
    safe_to_start: bool = True

    def add(
        self,
        category: str,
        status: StartupCheckStatus,
        message: str,
        **details: object,
    ) -> None:
        self.checks.append(StartupCheck(category, status, message, details))


class StartupDiagnostics:
    """Fail-safe start checks without initializing inference runtimes."""

    def __init__(
        self,
        *,
        backend_manager_factory=BackendManager,
        registry_factory=ModelRegistry,
        model_definitions_dir: str | Path | None = None,
    ) -> None:
        self._backend_manager_factory = backend_manager_factory
        self._registry_factory = registry_factory
        self._model_definitions_dir = (
            Path(model_definitions_dir)
            if model_definitions_dir is not None
            else BASE / "resources" / "models"
        )

    def run(self) -> StartupDiagnosticReport:
        report = StartupDiagnosticReport()
        backend_names = self._check_environment_and_backends(report)
        self._check_models(report, backend_names)
        self._log_report(report)
        return report

    def _check_environment_and_backends(
        self, report: StartupDiagnosticReport
    ) -> list[str]:
        try:
            manager = self._backend_manager_factory()
            discovery = manager.run_discovery()
            backend_names = manager.get_all_backend_names()
            best_backend = manager.get_best_backend()
            if best_backend is None:
                report.fallback_active = True
                report.add(
                    "backend",
                    StartupCheckStatus.FALLBACK,
                    "Kein ausführbares Backend erkannt; sicherer CPU-Fallback bleibt aktiv.",
                )
            else:
                report.selected_backend = best_backend.get_backend_name()
                report.add(
                    "backend",
                    StartupCheckStatus.OK,
                    "Backend-Prüfung abgeschlossen.",
                    selected=report.selected_backend,
                    available=discovery.available_backends,
                )

            environment_status = (
                StartupCheckStatus.OK
                if discovery.is_windows_arm64
                else StartupCheckStatus.WARNING
            )
            report.add(
                "environment",
                environment_status,
                "Startumgebung geprüft.",
                os=discovery.os_name,
                architecture=discovery.architecture,
                python=discovery.python_version,
                warnings=discovery.warnings,
                errors=discovery.errors,
            )
            return backend_names
        except Exception as error:
            report.fallback_active = True
            report.selected_backend = CPU_FALLBACK_BACKEND
            report.add(
                "backend",
                StartupCheckStatus.FALLBACK,
                "Backend-Diagnose fehlgeschlagen; sicherer CPU-Fallback wird verwendet.",
                error_type=type(error).__name__,
                error=str(error),
            )
            report.add(
                "environment",
                StartupCheckStatus.ERROR,
                "Umgebungsdiagnose konnte nicht vollständig ausgeführt werden.",
                os=platform.system(),
                architecture=platform.machine(),
                python=platform.python_version(),
            )
            return [CPU_FALLBACK_BACKEND]

    def _check_models(
        self, report: StartupDiagnosticReport, backend_names: list[str]
    ) -> None:
        try:
            registry = self._registry_factory()
            registry.load_directory(
                self._model_definitions_dir,
                available_backends=backend_names,
            )
            models = registry.get_all_models()
            invalid = registry.get_invalid_reports()
            status = (
                StartupCheckStatus.WARNING if invalid else StartupCheckStatus.OK
            )
            report.add(
                "models",
                status,
                "Modellstatus geprüft.",
                registered=len(models),
                invalid=len(invalid),
                definitions_dir=str(self._model_definitions_dir),
            )
        except Exception as error:
            report.add(
                "models",
                StartupCheckStatus.ERROR,
                "Modellstatus konnte nicht gelesen werden; Start ohne aktives Modell.",
                error_type=type(error).__name__,
                error=str(error),
            )

    @staticmethod
    def _log_report(report: StartupDiagnosticReport) -> None:
        for check in report.checks:
            log_method = {
                StartupCheckStatus.OK: logger.info,
                StartupCheckStatus.WARNING: logger.warning,
                StartupCheckStatus.ERROR: logger.error,
                StartupCheckStatus.FALLBACK: logger.warning,
            }[check.status]
            log_method(
                "Startprüfung | category=%s status=%s message=%s details=%s",
                check.category,
                check.status.value,
                check.message,
                check.details,
            )
        logger.info(
            "Startprüfung abgeschlossen | safe_to_start=%s backend=%s fallback=%s",
            report.safe_to_start,
            report.selected_backend,
            report.fallback_active,
        )


def run_startup_diagnostics() -> StartupDiagnosticReport:
    """Run diagnostics without ever turning a diagnostic fault into a crash."""
    try:
        return StartupDiagnostics().run()
    except Exception as error:
        logger.exception(
            "Unerwarteter Fehler der Startdiagnose; CPU-Fallback bleibt aktiv."
        )
        report = StartupDiagnosticReport(fallback_active=True)
        report.add(
            "startup",
            StartupCheckStatus.FALLBACK,
            "Startdiagnose intern fehlgeschlagen; sicherer CPU-Fallback wird verwendet.",
            error_type=type(error).__name__,
            error=str(error),
        )
        return report
