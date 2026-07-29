from __future__ import annotations

import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Any, Callable, Iterator

from engine.logging_config import get_logger


logger = get_logger("PerformanceMetrics")


class PerformanceOperation(str, Enum):
    MODEL_LOAD = "model_load"
    INFERENCE = "inference"
    RESOURCE_RELEASE = "resource_release"


@dataclass(frozen=True)
class PerformanceMetric:
    operation: PerformanceOperation
    duration_seconds: float
    success: bool
    captured_at: float
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMeasurement:
    success: bool = True


class PerformanceMetrics:
    """Thread-safe internal store for bounded runtime measurements."""

    def __init__(
        self,
        *,
        max_metrics: int = 1000,
        clock: Callable[[], float] = time.perf_counter,
        wall_clock: Callable[[], float] = time.time,
    ) -> None:
        self._metrics: deque[PerformanceMetric] = deque(maxlen=max_metrics)
        self._clock = clock
        self._wall_clock = wall_clock
        self._lock = Lock()

    def record(
        self,
        operation: PerformanceOperation | str,
        duration_seconds: float,
        *,
        success: bool,
        tags: dict[str, Any] | None = None,
    ) -> PerformanceMetric:
        normalized_operation = PerformanceOperation(operation)
        metric = PerformanceMetric(
            operation=normalized_operation,
            duration_seconds=max(0.0, float(duration_seconds)),
            success=bool(success),
            captured_at=self._wall_clock(),
            tags={str(key): str(value) for key, value in (tags or {}).items()},
        )
        with self._lock:
            self._metrics.append(metric)
        logger.info(
            "Performance | operation=%s duration_ms=%.3f success=%s tags=%s",
            metric.operation.value,
            metric.duration_seconds * 1000.0,
            metric.success,
            metric.tags,
        )
        return metric

    @contextmanager
    def measure(
        self,
        operation: PerformanceOperation | str,
        **tags: Any,
    ) -> Iterator[PerformanceMeasurement]:
        started = self._clock()
        measurement = PerformanceMeasurement()
        try:
            yield measurement
        except BaseException:
            measurement.success = False
            raise
        finally:
            try:
                self.record(
                    operation,
                    self._clock() - started,
                    success=measurement.success,
                    tags=tags,
                )
            except Exception:
                logger.exception(
                    "Performance-Metrik konnte nicht gespeichert werden | operation=%s",
                    operation,
                )

    def get_metrics(
        self, operation: PerformanceOperation | str | None = None
    ) -> list[PerformanceMetric]:
        normalized = PerformanceOperation(operation) if operation is not None else None
        with self._lock:
            values = list(self._metrics)
        if normalized is None:
            return values
        return [metric for metric in values if metric.operation is normalized]

    def clear(self) -> None:
        with self._lock:
            self._metrics.clear()


performance_metrics = PerformanceMetrics()


def measured(
    operation: PerformanceOperation,
    *,
    tags: Callable[..., dict[str, Any]] | None = None,
    success: Callable[[Any], bool] | None = None,
):
    """Decorator for central service methods with result-based success states."""

    def decorate(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                metric_tags = tags(*args, **kwargs) if tags is not None else {}
            except Exception:
                metric_tags = {}
            with performance_metrics.measure(operation, **metric_tags) as measurement:
                result = function(*args, **kwargs)
                if success is not None:
                    measurement.success = bool(success(result))
                return result

        return wrapper

    return decorate
