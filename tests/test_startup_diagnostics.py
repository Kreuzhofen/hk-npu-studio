from __future__ import annotations

from dataclasses import dataclass

from engine.startup_diagnostics import (
    CPU_FALLBACK_BACKEND,
    StartupCheckStatus,
    StartupDiagnostics,
    run_startup_diagnostics,
)


@dataclass
class FakeDiscovery:
    os_name: str = "Windows"
    architecture: str = "ARM64"
    python_version: str = "3.11"
    is_windows_arm64: bool = True
    available_backends: list[str] = None
    warnings: list[str] = None
    errors: list[str] = None

    def __post_init__(self):
        self.available_backends = self.available_backends or ["CPU"]
        self.warnings = self.warnings or []
        self.errors = self.errors or []


class FakeBackend:
    def get_backend_name(self):
        return "ONNX Runtime"


class HealthyBackendManager:
    def run_discovery(self):
        return FakeDiscovery()

    def get_all_backend_names(self):
        return [CPU_FALLBACK_BACKEND, "ONNX Runtime"]

    def get_best_backend(self):
        return FakeBackend()


class FailingBackendManager:
    def __init__(self):
        raise RuntimeError("backend unavailable")


class FakeRegistry:
    def __init__(self, invalid=None):
        self.invalid = invalid or {}
        self.loaded = False

    def load_directory(self, path, *, available_backends):
        self.loaded = True

    def get_all_models(self):
        return [{"id": "model"}]

    def get_invalid_reports(self):
        return self.invalid


def test_startup_diagnostics_reports_environment_backend_and_models(tmp_path):
    report = StartupDiagnostics(
        backend_manager_factory=HealthyBackendManager,
        registry_factory=FakeRegistry,
        model_definitions_dir=tmp_path,
    ).run()

    assert report.safe_to_start is True
    assert report.selected_backend == "ONNX Runtime"
    assert report.fallback_active is False
    assert {check.category for check in report.checks} == {
        "environment",
        "backend",
        "models",
    }
    assert all(check.status is StartupCheckStatus.OK for check in report.checks)


def test_backend_failure_activates_safe_cpu_fallback(tmp_path):
    report = StartupDiagnostics(
        backend_manager_factory=FailingBackendManager,
        registry_factory=FakeRegistry,
        model_definitions_dir=tmp_path,
    ).run()

    backend_check = next(c for c in report.checks if c.category == "backend")
    assert report.safe_to_start is True
    assert report.fallback_active is True
    assert report.selected_backend == CPU_FALLBACK_BACKEND
    assert backend_check.status is StartupCheckStatus.FALLBACK
    assert backend_check.details["error_type"] == "RuntimeError"


def test_invalid_models_are_classified_as_warning(tmp_path):
    report = StartupDiagnostics(
        backend_manager_factory=HealthyBackendManager,
        registry_factory=lambda: FakeRegistry({"broken.json": object()}),
        model_definitions_dir=tmp_path,
    ).run()

    model_check = next(c for c in report.checks if c.category == "models")
    assert model_check.status is StartupCheckStatus.WARNING
    assert model_check.details["invalid"] == 1


def test_model_registry_failure_does_not_block_start(tmp_path):
    def fail_registry():
        raise OSError("registry unreadable")

    report = StartupDiagnostics(
        backend_manager_factory=HealthyBackendManager,
        registry_factory=fail_registry,
        model_definitions_dir=tmp_path,
    ).run()

    model_check = next(c for c in report.checks if c.category == "models")
    assert report.safe_to_start is True
    assert model_check.status is StartupCheckStatus.ERROR
    assert model_check.details["error_type"] == "OSError"


def test_public_entrypoint_converts_internal_diagnostic_failure(monkeypatch):
    monkeypatch.setattr(
        "engine.startup_diagnostics.StartupDiagnostics.run",
        lambda self: (_ for _ in ()).throw(RuntimeError("diagnostic fault")),
    )

    report = run_startup_diagnostics()

    assert report.safe_to_start is True
    assert report.fallback_active is True
    assert report.selected_backend == CPU_FALLBACK_BACKEND
    assert report.checks[0].status is StartupCheckStatus.FALLBACK
