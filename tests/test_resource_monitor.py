from __future__ import annotations

from types import SimpleNamespace

from engine.job_lifecycle import JobStatus, set_job_progress, set_job_status
from engine.resource_monitor import (
    BackendResourceStatus,
    ResourceMonitor,
    ResourceSnapshot,
)


class Collector:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.calls = 0

    def collect(self, backend=None):
        self.calls += 1
        return self.snapshot


def make_snapshot(cpu=20.0, ram=30.0, available=True, healthy=True):
    return ResourceSnapshot(
        captured_at=1.0,
        cpu_percent=cpu,
        ram_percent=ram,
        ram_available_bytes=7_000,
        ram_total_bytes=10_000,
        backend=BackendResourceStatus(
            name="Qualcomm QNN NPU",
            kind="npu",
            available=available,
            healthy=healthy,
        ),
    )


def test_monitor_captures_cpu_ram_and_npu_backend_state():
    monitor = ResourceMonitor(
        Collector(make_snapshot()), minimum_interval_seconds=0
    )
    job = SimpleNamespace(job_id="job-1")

    state = monitor.observe(job)

    assert state.snapshot.cpu_percent == 20.0
    assert state.snapshot.ram_percent == 30.0
    assert state.snapshot.backend.kind == "npu"
    assert state.snapshot.backend.utilization_percent is None
    assert state.warnings == []


def test_monitor_classifies_resource_pressure_and_backend_health():
    monitor = ResourceMonitor(
        Collector(make_snapshot(cpu=95.0, ram=91.0, healthy=False)),
        minimum_interval_seconds=0,
    )
    job = SimpleNamespace(job_id="job-2")

    monitor.observe(job)
    warnings = monitor.get_job_warnings(job)

    assert [warning.code for warning in warnings] == [
        "CPU_PRESSURE",
        "RAM_PRESSURE",
        "BACKEND_UNHEALTHY",
    ]


def test_unavailable_backend_has_distinct_warning():
    monitor = ResourceMonitor(
        Collector(make_snapshot(available=False, healthy=False)),
        minimum_interval_seconds=0,
    )

    warnings = monitor.observe(SimpleNamespace(job_id="job-3")).warnings

    assert [warning.code for warning in warnings] == ["BACKEND_UNAVAILABLE"]


def test_monitor_throttles_repeated_job_samples():
    collector = Collector(make_snapshot())
    monitor = ResourceMonitor(collector, minimum_interval_seconds=60)
    job = SimpleNamespace(job_id="job-4")

    first = monitor.observe(job)
    second = monitor.observe(job)

    assert second is first
    assert collector.calls == 1


def test_concrete_backend_upgrades_throttled_unknown_backend_sample():
    collector = Collector(make_snapshot())
    monitor = ResourceMonitor(collector, minimum_interval_seconds=60)
    job = SimpleNamespace(job_id="job-backend")
    unknown = make_snapshot()
    collector.snapshot = ResourceSnapshot(
        captured_at=unknown.captured_at,
        cpu_percent=unknown.cpu_percent,
        ram_percent=unknown.ram_percent,
        ram_available_bytes=unknown.ram_available_bytes,
        ram_total_bytes=unknown.ram_total_bytes,
        backend=BackendResourceStatus("Unbekannt", "unknown", None, None),
    )
    monitor.observe(job)
    collector.snapshot = make_snapshot()

    state = monitor.observe(job, backend=object())

    assert state.snapshot.backend.kind == "npu"
    assert collector.calls == 2


def test_collection_failure_never_affects_job():
    class FailingCollector:
        def collect(self, backend=None):
            raise OSError("counter unavailable")

    monitor = ResourceMonitor(FailingCollector(), minimum_interval_seconds=0)

    assert monitor.observe(SimpleNamespace(job_id="job-5")) is None


def test_common_job_lifecycle_observes_only_running_jobs(monkeypatch):
    observed = []
    monkeypatch.setattr(
        "engine.resource_monitor.observe_running_job",
        lambda job, backend=None: observed.append(job),
    )
    job = {"job_id": "job-6", "status": JobStatus.QUEUED.value}

    set_job_progress(job, 0.1)
    set_job_status(job, JobStatus.RUNNING)
    set_job_progress(job, 0.2)
    set_job_status(job, JobStatus.FINISHED)

    assert observed == [job, job]
