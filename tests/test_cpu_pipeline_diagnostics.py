from __future__ import annotations

import logging
import time
from types import SimpleNamespace

import numpy as np

from engine.cpu_pipeline_diagnostics import CpuPipelineDiagnostics, current_diagnostics


class _TensorInfo:
    def __init__(self, name: str, shape: list[int]) -> None:
        self.name = name
        self.shape = shape


class _Session:
    def get_inputs(self):
        return [_TensorInfo("sample", [1, 4, 8, 8])]

    def get_outputs(self):
        return [_TensorInfo("noise", [1, 4, 8, 8])]

    def get_providers(self):
        return ["CPUExecutionProvider"]

    def run(self, output_names, inputs):
        time.sleep(0.025)
        return [inputs["sample"]]


def test_diagnostic_session_run_preserves_session_result_and_logs_watchdog(caplog):
    job = SimpleNamespace(progress=0.03)
    diagnostics = CpuPipelineDiagnostics(job, "sdxl_base", ".")
    diagnostics.WATCHDOG_INTERVAL_SECONDS = 0.01
    session = _Session()
    sample = np.zeros((1, 4, 8, 8), dtype=np.float32)

    with caplog.at_level(logging.INFO), diagnostics.activate():
        diagnostics.log_session(session, "unet", "unet/model.onnx")
        result = diagnostics.run_session(
            session,
            None,
            {"sample": sample},
            phase="Denoise Step 1/1",
            component_name="unet",
            model_path="unet/model.onnx",
        )

    assert result[0] is sample
    assert "[WATCHDOG]" in caplog.text
    assert "Session.Run before" in caplog.text
    assert "Session.Run after" in caplog.text
    assert "CPUExecutionProvider" in caplog.text
    assert current_diagnostics() is None


def test_progress_logging_is_observational(caplog):
    job = SimpleNamespace(progress=0.03)
    diagnostics = CpuPipelineDiagnostics(job, "sdxl_base", ".")

    with caplog.at_level(logging.INFO), diagnostics.activate():
        diagnostics.record_progress(0.03, 0.07, "Denoise Step 1/20")

    assert job.progress == 0.03
    assert "[PROGRESS] 3.0% -> 7.0%" in caplog.text
