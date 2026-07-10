from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from engine.onnx_provider_service import OnnxProviderService
    from engine.qnn_dlc_runtime_service import QnnDlcRunConfig, QnnDlcRuntimePaths, QnnDlcRuntimeService
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from engine.onnx_provider_service import OnnxProviderService
    from engine.qnn_dlc_runtime_service import QnnDlcRunConfig, QnnDlcRuntimePaths, QnnDlcRuntimeService


@dataclass(frozen=True)
class QnnDlcDiagnosticPaths:
    project_root: Path = Path(r"C:\SnapdragonAI")
    ai_stack_root: Path = OnnxProviderService.AI_STACK_ROOT
    model_path: Path = Path(
        r"C:\SnapdragonAI\models\qnn_mobilenet_v2\qnn_dlc_w8a8"
        r"\mobilenet_v2-qnn_dlc-w8a8\mobilenet_v2.dlc"
    )

    @property
    def architecture_dir(self) -> str:
        return "aarch64-windows-msvc"

    @property
    def diagnostics_root(self) -> Path:
        return self.project_root / "diagnostics"

    @property
    def input_dir(self) -> Path:
        return self.diagnostics_root / "qnn_dlc_inputs"

    @property
    def output_dir(self) -> Path:
        return self.diagnostics_root / "qnn_dlc_outputs"

    @property
    def reports_dir(self) -> Path:
        return self.diagnostics_root / "reports"


class QnnDlcDiagnosticRunner:
    """Runs the local MobileNetV2 DLC smoke test through the QNN DLC runtime service."""

    INPUT_NAME = "image_tensor"
    INPUT_SHAPE = (1, 224, 224, 3)
    INPUT_DTYPE = "uint8"
    INPUT_SIZE_BYTES = 150528
    OUTPUT_NAME = "class_logits"

    def __init__(self, paths: QnnDlcDiagnosticPaths | None = None) -> None:
        self.paths = paths or QnnDlcDiagnosticPaths()
        self.runtime_service = QnnDlcRuntimeService(QnnDlcRuntimePaths(
            project_root=self.paths.project_root,
            ai_stack_root=self.paths.ai_stack_root,
            architecture_dir=self.paths.architecture_dir,
        ))
        self._active_output_dir = self.paths.output_dir

    def run(self) -> dict[str, Any]:
        started_at = time.strftime("%Y-%m-%d %H:%M:%S")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self._active_output_dir = self.paths.output_dir / timestamp
        report: dict[str, Any] = {
            "diagnostic": "qnn_dlc_mobilenet_v2_smoke_test",
            "runtime_name": QnnDlcRuntimeService.RUNTIME_NAME,
            "started_at": started_at,
            "status": "not_run",
            "qnn_available": OnnxProviderService.qnn_available(),
            "qnn_provider_registration_status": OnnxProviderService.provider_registration_status(),
            "runtime_diagnostics": self.runtime_service.diagnostics(),
            "input": {
                "name": self.INPUT_NAME,
                "shape": list(self.INPUT_SHAPE),
                "layout": "NHWC",
                "dtype": self.INPUT_DTYPE,
                "size_bytes": self.INPUT_SIZE_BYTES,
            },
            "paths": self._path_report(),
            "missing_files": self._missing_required_files(),
        }

        if report["missing_files"]:
            report["status"] = "missing_required_files"
            return self._save_report(report, timestamp)

        input_files = self._prepare_dummy_input()
        report["generated_input_files"] = {
            "raw": str(input_files["raw"]),
            "input_list": str(input_files["input_list"]),
        }

        run_config = QnnDlcRunConfig(
            model_path=self.paths.model_path,
            input_list_path=input_files["input_list"],
            output_dir=self._active_output_dir,
            profiling_level="basic",
        )
        report["command"] = self.runtime_service.build_command(run_config)

        completed = self.runtime_service.run(run_config)
        report["exit_code"] = completed.returncode
        report["stdout"] = completed.stdout
        report["stderr"] = completed.stderr
        report["output_files"] = QnnDlcRuntimeService.collect_files(self._active_output_dir)
        report["profiling_files"] = self._collect_profiling_files()
        report["result_0_exists"] = (self._active_output_dir / "Result_0").exists()
        report["class_logits_exists"] = (self._active_output_dir / "Result_0" / "class_logits.raw").exists()
        report["execution_metadata"] = self._read_text_file(self._active_output_dir / "execution_metadata.yaml")
        report["htp_indicators"] = self._extract_htp_indicators(report)
        report["status"] = "success" if completed.returncode == 0 and report["class_logits_exists"] else "failed"
        return self._save_report(report, timestamp)

    def _path_report(self) -> dict[str, str]:
        runtime_paths = self.runtime_service.paths
        return {
            "ai_stack_root": str(runtime_paths.ai_stack_root),
            "qnn_net_run": str(runtime_paths.qnn_net_run),
            "qnn_htp_backend": str(runtime_paths.qnn_htp_backend),
            "qnn_model_dlc": str(runtime_paths.qnn_model_dlc),
            "model_path": str(self.paths.model_path),
            "input_dir": str(self.paths.input_dir),
            "output_dir": str(self._active_output_dir),
            "reports_dir": str(self.paths.reports_dir),
        }

    def _missing_required_files(self) -> list[str]:
        missing = self.runtime_service.missing_runtime_files()
        if not self.paths.model_path.exists():
            missing.append(self.paths.model_path)
        return [str(path) for path in missing]

    def _prepare_dummy_input(self) -> dict[str, Path]:
        self.paths.input_dir.mkdir(parents=True, exist_ok=True)
        raw_path = self.paths.input_dir / "image_tensor.raw"
        input_list_path = self.paths.input_dir / "input_list.txt"
        raw_path.write_bytes(bytes(self.INPUT_SIZE_BYTES))
        input_list_path.write_text(f"{self.INPUT_NAME}:={raw_path}", encoding="ascii")
        return {"raw": raw_path, "input_list": input_list_path}

    def _collect_profiling_files(self) -> list[dict[str, Any]]:
        if not self._active_output_dir.exists():
            return []
        files = [
            path
            for path in self._active_output_dir.rglob("*")
            if path.is_file() and "profil" in path.name.lower()
        ]
        return [QnnDlcRuntimeService.file_info(path) for path in sorted(files)]

    def _read_text_file(self, path: Path) -> str:
        if not path.exists() or not path.is_file():
            return ""
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""

    def _extract_htp_indicators(self, report: dict[str, Any]) -> list[str]:
        text = "\n".join([
            report.get("stdout", ""),
            report.get("stderr", ""),
            report.get("execution_metadata", ""),
        ])
        indicators = []
        for needle in [
            "QnnHtp.dll",
            "QNN accelerator",
            "Accelerator (execute)",
            "qnn-profiling-data",
            "QNN_DATATYPE_UFIXED_POINT_8",
            "inferences_completed: 1",
        ]:
            if needle in text or any(needle in item["path"] for item in report.get("profiling_files", [])):
                indicators.append(needle)
        return indicators

    def _save_report(self, report: dict[str, Any], timestamp: str) -> dict[str, Any]:
        self.paths.reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.paths.reports_dir / f"qnn_dlc_mobilenet_v2_{timestamp}.json"
        report["report_path"] = str(report_path)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return report


if __name__ == "__main__":
    result = QnnDlcDiagnosticRunner().run()
    print(json.dumps(result, indent=2, ensure_ascii=False))
