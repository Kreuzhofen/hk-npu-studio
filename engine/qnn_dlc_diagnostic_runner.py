from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from engine.onnx_provider_service import OnnxProviderService
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from engine.onnx_provider_service import OnnxProviderService


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
    def qnn_net_run(self) -> Path:
        return self.ai_stack_root / "bin" / self.architecture_dir / "qnn-net-run.exe"

    @property
    def qnn_htp_backend(self) -> Path:
        return self.ai_stack_root / "lib" / self.architecture_dir / "QnnHtp.dll"

    @property
    def qnn_model_dlc(self) -> Path:
        return self.ai_stack_root / "lib" / self.architecture_dir / "QnnModelDlc.dll"

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
    """Runs the local MobileNetV2 DLC smoke test through qnn-net-run."""

    INPUT_NAME = "image_tensor"
    INPUT_SHAPE = (1, 224, 224, 3)
    INPUT_DTYPE = "uint8"
    INPUT_SIZE_BYTES = 150528
    OUTPUT_NAME = "class_logits"

    def __init__(self, paths: QnnDlcDiagnosticPaths | None = None) -> None:
        self.paths = paths or QnnDlcDiagnosticPaths()
        self._active_output_dir = self.paths.output_dir

    def run(self) -> dict[str, Any]:
        started_at = time.strftime("%Y-%m-%d %H:%M:%S")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self._active_output_dir = self.paths.output_dir / timestamp
        report: dict[str, Any] = {
            "diagnostic": "qnn_dlc_mobilenet_v2_smoke_test",
            "started_at": started_at,
            "status": "not_run",
            "qnn_available": OnnxProviderService.qnn_available(),
            "qnn_provider_registration_status": OnnxProviderService.provider_registration_status(),
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

        command = self._build_command(input_files["input_list"])
        report["command"] = command

        completed = self._run_qnn_net_run(command)
        report["exit_code"] = completed.returncode
        report["stdout"] = completed.stdout
        report["stderr"] = completed.stderr
        report["output_files"] = self._collect_output_files()
        report["profiling_files"] = self._collect_profiling_files()
        report["result_0_exists"] = (self._active_output_dir / "Result_0").exists()
        report["class_logits_exists"] = (self._active_output_dir / "Result_0" / "class_logits.raw").exists()
        report["execution_metadata"] = self._read_text_file(self._active_output_dir / "execution_metadata.yaml")
        report["htp_indicators"] = self._extract_htp_indicators(report)
        report["status"] = "success" if completed.returncode == 0 and report["class_logits_exists"] else "failed"
        return self._save_report(report, timestamp)

    def _path_report(self) -> dict[str, str]:
        return {
            "ai_stack_root": str(self.paths.ai_stack_root),
            "qnn_net_run": str(self.paths.qnn_net_run),
            "qnn_htp_backend": str(self.paths.qnn_htp_backend),
            "qnn_model_dlc": str(self.paths.qnn_model_dlc),
            "model_path": str(self.paths.model_path),
            "input_dir": str(self.paths.input_dir),
            "output_dir": str(self._active_output_dir),
            "reports_dir": str(self.paths.reports_dir),
        }

    def _missing_required_files(self) -> list[str]:
        required = [
            self.paths.qnn_net_run,
            self.paths.qnn_htp_backend,
            self.paths.qnn_model_dlc,
            self.paths.model_path,
        ]
        return [str(path) for path in required if not path.exists()]

    def _prepare_dummy_input(self) -> dict[str, Path]:
        self.paths.input_dir.mkdir(parents=True, exist_ok=True)
        raw_path = self.paths.input_dir / "image_tensor.raw"
        input_list_path = self.paths.input_dir / "input_list.txt"
        raw_path.write_bytes(bytes(self.INPUT_SIZE_BYTES))
        input_list_path.write_text(f"{self.INPUT_NAME}:={raw_path}", encoding="ascii")
        return {"raw": raw_path, "input_list": input_list_path}

    def _build_command(self, input_list_path: Path) -> list[str]:
        return [
            str(self.paths.qnn_net_run),
            "--model",
            str(self.paths.qnn_model_dlc),
            "--backend",
            str(self.paths.qnn_htp_backend),
            "--dlc_path",
            str(self.paths.model_path),
            "--input_list",
            str(input_list_path),
            "--output_dir",
            str(self._active_output_dir),
            "--profiling_level",
            "basic",
        ]

    def _run_qnn_net_run(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        bin_dir = self.paths.ai_stack_root / "bin" / self.paths.architecture_dir
        lib_dir = self.paths.ai_stack_root / "lib" / self.paths.architecture_dir
        env["PATH"] = os.pathsep.join([str(bin_dir), str(lib_dir), env.get("PATH", "")])
        self._active_output_dir.mkdir(parents=True, exist_ok=True)
        return subprocess.run(
            command,
            cwd=str(self.paths.project_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

    def _collect_output_files(self) -> list[dict[str, Any]]:
        return self._collect_files(self._active_output_dir)

    def _collect_profiling_files(self) -> list[dict[str, Any]]:
        if not self._active_output_dir.exists():
            return []
        files = [
            path
            for path in self._active_output_dir.rglob("*")
            if path.is_file() and "profil" in path.name.lower()
        ]
        return [self._file_info(path) for path in sorted(files)]

    def _collect_files(self, root: Path) -> list[dict[str, Any]]:
        if not root.exists():
            return []
        return [self._file_info(path) for path in sorted(root.rglob("*")) if path.is_file()]

    def _file_info(self, path: Path) -> dict[str, Any]:
        stat = path.stat()
        return {
            "path": str(path),
            "size_bytes": stat.st_size,
            "modified_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
        }

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
