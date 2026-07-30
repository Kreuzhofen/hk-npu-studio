from __future__ import annotations

import contextvars
import datetime
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from engine.logging_config import get_logger


logger = get_logger("CpuPipelineDiagnostics")
_CURRENT: contextvars.ContextVar["CpuPipelineDiagnostics | None"] = contextvars.ContextVar(
    "cpu_pipeline_diagnostics",
    default=None,
)


def _timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="milliseconds")


def current_diagnostics() -> "CpuPipelineDiagnostics | None":
    return _CURRENT.get()


class CpuPipelineDiagnostics:
    """Passive timing diagnostics for the SDXL CPU pipeline."""

    WATCHDOG_INTERVAL_SECONDS = 30.0

    def __init__(self, job: Any, model_name: str, model_path: str | Path) -> None:
        self.job = job
        self.model_name = model_name
        self.model_path = str(Path(model_path).resolve()) if model_path else ""
        self.provider = "CPUExecutionProvider"
        self.started = time.perf_counter()
        self.current_phase = "Generierungsauftrag empfangen"

    @contextmanager
    def activate(self) -> Iterator["CpuPipelineDiagnostics"]:
        token = _CURRENT.set(self)
        thread_id = threading.get_ident()
        logger.info(
            "[CPU PIPELINE] Generierungsauftrag empfangen | Start: %s | Thread: %s | "
            "Provider: %s | Model: %s | Path: %s | Progress: %.1f%%",
            _timestamp(), thread_id, self.provider, self.model_name, self.model_path,
            self.progress_percent(),
        )
        logger.info(
            "[CPU PIPELINE] CPU-Pipeline gestartet | Start: %s | Thread: %s | "
            "Provider: %s | Model: %s | Path: %s",
            _timestamp(), thread_id, self.provider, self.model_name, self.model_path,
        )
        logger.info(
            "[MODEL] Modellpfade aufgelöst | Time: %s | Thread: %s | Provider: %s | "
            "Model: %s | Path: %s",
            _timestamp(), thread_id, self.provider, self.model_name, self.model_path,
        )
        try:
            yield self
        except BaseException as error:
            logger.exception(
                "[ERROR] CPU-SDXL generation failed | Type: %s | Message: %s | "
                "Phase: %s | Model path: %s | Thread: %s",
                type(error).__name__, error, self.current_phase, self.model_path,
                threading.get_ident(),
            )
            raise
        finally:
            duration = time.perf_counter() - self.started
            logger.info(
                "[TIMING] Gesamtdauer CPU-SDXL | End: %s | Duration: %.3fs | "
                "Thread: %s | Provider: %s | Model: %s | Path: %s",
                _timestamp(), duration, threading.get_ident(), self.provider,
                self.model_name, self.model_path,
            )
            _CURRENT.reset(token)

    @contextmanager
    def phase(self, prefix: str, name: str, *, model_path: str | Path | None = None) -> Iterator[None]:
        previous_phase = self.current_phase
        self.current_phase = name
        path = str(model_path or self.model_path)
        started_at = _timestamp()
        started = time.perf_counter()
        logger.info(
            "%s %s started | Start: %s | Thread: %s | Provider: %s | Model path: %s",
            prefix, name, started_at, threading.get_ident(), self.provider, path,
        )
        try:
            yield
        except BaseException as error:
            logger.exception(
                "[ERROR] %s failed | Type: %s | Message: %s | Phase: %s | "
                "Model path: %s | Thread: %s",
                name, type(error).__name__, error, self.current_phase, path,
                threading.get_ident(),
            )
            raise
        finally:
            duration = time.perf_counter() - started
            logger.info(
                "%s %s ended | End: %s | Duration: %.3fs | Thread: %s | "
                "Provider: %s | Model path: %s",
                prefix, name, _timestamp(), duration, threading.get_ident(),
                self.provider, path,
            )
            self.current_phase = previous_phase

    def progress_percent(self) -> float:
        if isinstance(self.job, dict):
            progress = self.job.get("progress", 0.0)
        else:
            progress = getattr(self.job, "progress", 0.0)
        return float(progress or 0.0) * 100.0

    def record_progress(self, old_value: float, new_value: float, phase: str) -> None:
        logger.info(
            "[PROGRESS] %.1f%% -> %.1f%% | Phase: %s | Time: %s | Thread: %s",
            old_value * 100.0, new_value * 100.0, phase or self.current_phase,
            _timestamp(), threading.get_ident(),
        )

    def log_session(self, session: Any, component_name: str, model_path: str | Path) -> None:
        inputs = [
            {"name": item.name, "shape": list(item.shape)}
            for item in session.get_inputs()
        ]
        outputs = [
            {"name": item.name, "shape": list(item.shape)}
            for item in session.get_outputs()
        ]
        try:
            import onnxruntime as ort
            registered = list(ort.get_available_providers())
        except Exception:
            registered = []
        actual = list(session.get_providers())
        logger.info(
            "[ONNX SESSION] Model: %s | Path: %s | Registered providers: %s | "
            "Actual providers: %s | Inputs: %s | Outputs: %s | Time: %s | Thread: %s",
            component_name, model_path, registered, actual, inputs, outputs,
            _timestamp(), threading.get_ident(),
        )

    def run_session(
        self,
        session: Any,
        output_names: Any,
        inputs: dict[str, Any],
        *,
        phase: str,
        component_name: str,
        model_path: str | Path,
    ) -> Any:
        origin_thread = threading.get_ident()
        started = time.perf_counter()
        completed = threading.Event()
        logger.info(
            "[ONNX SESSION] Session.Run before | Phase: %s | Model: %s | Path: %s | "
            "Time: %s | Thread: %s | Inputs: %s",
            phase, component_name, model_path, _timestamp(), origin_thread,
            {name: list(getattr(value, "shape", ())) for name, value in inputs.items()},
        )

        def watch() -> None:
            while not completed.wait(self.WATCHDOG_INTERVAL_SECONDS):
                logger.warning(
                    "[WATCHDOG] %s Session.Run still active after %.1f seconds | "
                    "Model: %s | Progress: %.1f%% | Thread: %s",
                    phase, time.perf_counter() - started, component_name,
                    self.progress_percent(), origin_thread,
                )

        watchdog = threading.Thread(
            target=watch,
            name=f"CPUWatchdog-{component_name}",
            daemon=True,
        )
        watchdog.start()
        try:
            result = session.run(output_names, inputs)
            logger.info(
                "[ONNX SESSION] Session.Run outputs | Phase: %s | Model: %s | "
                "Outputs: %s | Thread: %s",
                phase,
                component_name,
                [list(getattr(value, "shape", ())) for value in result],
                origin_thread,
            )
            return result
        finally:
            completed.set()
            duration = time.perf_counter() - started
            logger.info(
                "[ONNX SESSION] Session.Run after | Phase: %s | Model: %s | Path: %s | "
                "Time: %s | Duration: %.3fs | Thread: %s | Progress: %.1f%%",
                phase, component_name, model_path, _timestamp(), duration,
                origin_thread, self.progress_percent(),
            )


def diagnostic_session_run(
    session: Any,
    output_names: Any,
    inputs: dict[str, Any],
    *,
    phase: str,
    component_name: str,
    model_path: str | Path,
) -> Any:
    diagnostics = current_diagnostics()
    if diagnostics is None:
        return session.run(output_names, inputs)
    return diagnostics.run_session(
        session,
        output_names,
        inputs,
        phase=phase,
        component_name=component_name,
        model_path=model_path,
    )
