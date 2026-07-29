from __future__ import annotations

import ctypes
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from engine.logging_config import get_logger


logger = get_logger("ResourceMonitor")


@dataclass(frozen=True)
class BackendResourceStatus:
    name: str
    kind: str
    available: bool | None
    healthy: bool | None
    utilization_percent: float | None = None


@dataclass(frozen=True)
class ResourceSnapshot:
    captured_at: float
    cpu_percent: float | None
    ram_percent: float | None
    ram_available_bytes: int | None
    ram_total_bytes: int | None
    backend: BackendResourceStatus


@dataclass(frozen=True)
class ResourceWarning:
    code: str
    message: str
    severity: str = "warning"
    value: float | None = None
    threshold: float | None = None


@dataclass
class JobResourceState:
    snapshot: ResourceSnapshot
    warnings: list[ResourceWarning] = field(default_factory=list)


class WindowsResourceCollector:
    """Collects host resources without optional third-party dependencies."""

    def __init__(self) -> None:
        self._cpu_lock = Lock()
        self._previous_cpu_times: tuple[int, int, int] | None = None

    def collect(self, backend: Any = None) -> ResourceSnapshot:
        cpu_percent = self._collect_cpu_percent()
        ram_percent, ram_available, ram_total = self._collect_memory()
        return ResourceSnapshot(
            captured_at=time.time(),
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            ram_available_bytes=ram_available,
            ram_total_bytes=ram_total,
            backend=self._collect_backend(backend),
        )

    def _collect_cpu_percent(self) -> float | None:
        if not hasattr(ctypes, "windll"):
            return None

        idle = ctypes.c_ulonglong()
        kernel = ctypes.c_ulonglong()
        user = ctypes.c_ulonglong()
        try:
            ok = ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
            )
            if not ok:
                return None
            current = (idle.value, kernel.value, user.value)
            with self._cpu_lock:
                previous = self._previous_cpu_times
                self._previous_cpu_times = current
            if previous is None:
                return None
            idle_delta = current[0] - previous[0]
            total_delta = (current[1] - previous[1]) + (current[2] - previous[2])
            if total_delta <= 0:
                return None
            return round(max(0.0, min(100.0, 100.0 * (1 - idle_delta / total_delta))), 1)
        except (AttributeError, OSError):
            return None

    @staticmethod
    def _collect_memory() -> tuple[float | None, int | None, int | None]:
        if not hasattr(ctypes, "windll"):
            return None, None, None

        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(MemoryStatus)
        try:
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return (
                    float(status.dwMemoryLoad),
                    int(status.ullAvailPhys),
                    int(status.ullTotalPhys),
                )
        except (AttributeError, OSError):
            pass
        return None, None, None

    @staticmethod
    def _collect_backend(backend: Any) -> BackendResourceStatus:
        if backend is None:
            return BackendResourceStatus(
                name="Unbekannt",
                kind="unknown",
                available=None,
                healthy=None,
            )
        try:
            name = str(backend.get_backend_name())
        except Exception:
            name = type(backend).__name__
        normalized = name.casefold()
        kind = "npu" if "qnn" in normalized or "npu" in normalized or "htp" in normalized else (
            "onnx" if "onnx" in normalized else "cpu" if "cpu" in normalized else "backend"
        )
        try:
            available = bool(backend.is_available())
        except Exception:
            available = None
        try:
            healthy = bool(backend.health_check())
        except Exception:
            healthy = None
        return BackendResourceStatus(
            name=name,
            kind=kind,
            available=available,
            healthy=healthy,
        )


class ResourceMonitor:
    """Passive, throttled resource monitoring for running jobs."""

    def __init__(
        self,
        collector: Any | None = None,
        *,
        cpu_warning_percent: float = 90.0,
        ram_warning_percent: float = 90.0,
        minimum_interval_seconds: float = 1.0,
    ) -> None:
        self._collector = collector or WindowsResourceCollector()
        self._cpu_warning_percent = cpu_warning_percent
        self._ram_warning_percent = ram_warning_percent
        self._minimum_interval = minimum_interval_seconds
        self._states: dict[str, JobResourceState] = {}
        self._last_sample: dict[str, float] = {}
        self._lock = Lock()

    def observe(self, job: Any, backend: Any = None) -> JobResourceState | None:
        job_id = self._job_id(job)
        now = time.monotonic()
        with self._lock:
            previous = self._last_sample.get(job_id)
            current_state = self._states.get(job_id)
            backend_upgrade = (
                backend is not None
                and current_state is not None
                and current_state.snapshot.backend.kind == "unknown"
            )
            if (
                not backend_upgrade
                and previous is not None
                and now - previous < self._minimum_interval
            ):
                return self._states.get(job_id)
            self._last_sample[job_id] = now

        try:
            snapshot = self._collector.collect(backend)
            warnings = self._classify(snapshot)
            state = JobResourceState(snapshot=snapshot, warnings=warnings)
            with self._lock:
                self._states[job_id] = state
            for warning in warnings:
                logger.warning(
                    "Ressourcenwarnung | job_id=%s code=%s value=%s threshold=%s backend=%s",
                    job_id,
                    warning.code,
                    warning.value,
                    warning.threshold,
                    snapshot.backend.name,
                )
            return state
        except Exception:
            logger.exception("Ressourcenmessung fehlgeschlagen | job_id=%s", job_id)
            return None

    def get_job_state(self, job: Any) -> JobResourceState | None:
        with self._lock:
            return self._states.get(self._job_id(job))

    def get_job_warnings(self, job: Any) -> list[ResourceWarning]:
        state = self.get_job_state(job)
        return list(state.warnings) if state is not None else []

    def _classify(self, snapshot: ResourceSnapshot) -> list[ResourceWarning]:
        warnings: list[ResourceWarning] = []
        if (
            snapshot.cpu_percent is not None
            and snapshot.cpu_percent >= self._cpu_warning_percent
        ):
            warnings.append(
                ResourceWarning(
                    "CPU_PRESSURE",
                    "Hohe CPU-Auslastung während des laufenden Jobs.",
                    value=snapshot.cpu_percent,
                    threshold=self._cpu_warning_percent,
                )
            )
        if (
            snapshot.ram_percent is not None
            and snapshot.ram_percent >= self._ram_warning_percent
        ):
            warnings.append(
                ResourceWarning(
                    "RAM_PRESSURE",
                    "Hohe RAM-Auslastung während des laufenden Jobs.",
                    value=snapshot.ram_percent,
                    threshold=self._ram_warning_percent,
                )
            )
        if snapshot.backend.available is False:
            warnings.append(
                ResourceWarning(
                    "BACKEND_UNAVAILABLE",
                    f"Backend '{snapshot.backend.name}' ist nicht verfügbar.",
                )
            )
        elif snapshot.backend.healthy is False:
            warnings.append(
                ResourceWarning(
                    "BACKEND_UNHEALTHY",
                    f"Backend '{snapshot.backend.name}' meldet einen fehlerhaften Zustand.",
                )
            )
        return warnings

    @staticmethod
    def _job_id(job: Any) -> str:
        if isinstance(job, dict):
            value = job.get("job_id") or job.get("id")
        else:
            value = getattr(job, "job_id", None) or getattr(job, "id", None)
        return str(value) if value is not None else f"object:{id(job)}"


resource_monitor = ResourceMonitor()


def observe_running_job(job: Any, backend: Any = None) -> JobResourceState | None:
    """Best-effort hook used by the common job lifecycle."""
    return resource_monitor.observe(job, backend)
