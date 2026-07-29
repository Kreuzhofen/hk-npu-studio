from __future__ import annotations

from types import SimpleNamespace

from engine.performance_metrics import (
    PerformanceMetrics,
    PerformanceOperation,
    measured,
    performance_metrics,
)


class Clock:
    def __init__(self, *values):
        self.values = iter(values)

    def __call__(self):
        return next(self.values)


def test_measurement_records_duration_success_and_tags():
    metrics = PerformanceMetrics(clock=Clock(10.0, 10.25), wall_clock=lambda: 20.0)

    with metrics.measure(
        PerformanceOperation.INFERENCE, job_id="job-1", backend="QNN"
    ):
        pass

    metric = metrics.get_metrics()[0]
    assert metric.operation is PerformanceOperation.INFERENCE
    assert metric.duration_seconds == 0.25
    assert metric.success is True
    assert metric.captured_at == 20.0
    assert metric.tags == {"job_id": "job-1", "backend": "QNN"}


def test_failed_context_is_recorded_and_exception_is_preserved():
    metrics = PerformanceMetrics(clock=Clock(1.0, 1.1))

    try:
        with metrics.measure(PerformanceOperation.RESOURCE_RELEASE):
            raise RuntimeError("release failed")
    except RuntimeError as error:
        assert str(error) == "release failed"

    assert metrics.get_metrics()[0].success is False


def test_metrics_can_be_filtered_by_operation():
    metrics = PerformanceMetrics(clock=Clock(1.0, 2.0, 3.0, 5.0))
    with metrics.measure(PerformanceOperation.MODEL_LOAD):
        pass
    with metrics.measure(PerformanceOperation.INFERENCE):
        pass

    inference = metrics.get_metrics(PerformanceOperation.INFERENCE)

    assert len(inference) == 1
    assert inference[0].duration_seconds == 2.0


def test_summary_evaluates_duration_and_failures_by_operation():
    metrics = PerformanceMetrics()
    metrics.record(PerformanceOperation.MODEL_LOAD, 0.2, success=True)
    metrics.record(PerformanceOperation.MODEL_LOAD, 0.4, success=False)
    metrics.record(PerformanceOperation.INFERENCE, 2.0, success=True)

    summary = metrics.get_summary()

    assert summary["model_load"] == {
        "count": 2,
        "failures": 1,
        "total_seconds": 0.6000000000000001,
        "average_seconds": 0.30000000000000004,
        "minimum_seconds": 0.2,
        "maximum_seconds": 0.4,
    }
    assert summary["inference"]["average_seconds"] == 2.0
    assert "resource_release" not in summary


def test_store_is_bounded():
    metrics = PerformanceMetrics(max_metrics=2)
    metrics.record(PerformanceOperation.MODEL_LOAD, 1, success=True)
    metrics.record(PerformanceOperation.INFERENCE, 2, success=True)
    metrics.record(PerformanceOperation.RESOURCE_RELEASE, 3, success=True)

    assert [metric.duration_seconds for metric in metrics.get_metrics()] == [2, 3]


def test_metric_storage_failure_does_not_change_measured_result(monkeypatch):
    metrics = PerformanceMetrics(clock=Clock(1.0, 2.0))
    monkeypatch.setattr(
        metrics,
        "record",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("store failed")),
    )

    with metrics.measure(PerformanceOperation.INFERENCE):
        result = "unchanged"

    assert result == "unchanged"


def test_decorator_uses_result_based_success_and_tags():
    performance_metrics.clear()

    @measured(
        PerformanceOperation.MODEL_LOAD,
        tags=lambda model_id: {"model_id": model_id},
        success=lambda result: result.success,
    )
    def load(model_id):
        return SimpleNamespace(success=False)

    result = load("model-a")

    metric = performance_metrics.get_metrics(PerformanceOperation.MODEL_LOAD)[-1]
    assert result.success is False
    assert metric.success is False
    assert metric.tags["model_id"] == "model-a"
