from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config import BASE, LOG_DIR
from engine.onnx_provider_service import OnnxProviderService


@dataclass(frozen=True)
class QnnDlcRuntimePaths:
    """Resolved local Qualcomm QNN DLC runtime paths."""

    project_root: Path = field(default_factory=lambda: BASE)
    ai_stack_root: Path = field(default_factory=lambda: OnnxProviderService.AI_STACK_ROOT)
    architecture_dir: str = "aarch64-windows-msvc"

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
        return LOG_DIR / "diagnostics"


@dataclass(frozen=True)
class QnnDlcRunConfig:
    """Configuration for a qnn-net-run DLC execution."""

    model_path: Path
    input_list_path: Path
    output_dir: Path
    profiling_level: str = "basic"


class QnnDlcRuntimeService:
    """Runtime foundation for Qualcomm QNN DLC / HTP execution via qnn-net-run."""

    RUNTIME_NAME = "Qualcomm QNN DLC / HTP"
    ONNX_CPU_RUNTIME_NAME = "ONNX Runtime CPU"
    ONNX_QNN_PROVIDER_RUNTIME_NAME = "ONNX Runtime QNN Provider"

    def __init__(self, paths: QnnDlcRuntimePaths | None = None) -> None:
        self.paths = paths or QnnDlcRuntimePaths()

    def diagnostics(self) -> dict[str, Any]:
        missing = self.missing_runtime_files()
        return {
            "runtime_name": self.RUNTIME_NAME,
            "ai_stack_root": str(self.paths.ai_stack_root),
            "qnn_net_run": str(self.paths.qnn_net_run),
            "qnn_htp_backend": str(self.paths.qnn_htp_backend),
            "qnn_model_dlc": str(self.paths.qnn_model_dlc),
            "missing_runtime_files": [str(path) for path in missing],
            "available": not missing,
        }

    def missing_runtime_files(self) -> list[Path]:
        required = [
            self.paths.qnn_net_run,
            self.paths.qnn_htp_backend,
            self.paths.qnn_model_dlc,
        ]
        return [path for path in required if not path.exists()]

    def missing_run_files(self, config: QnnDlcRunConfig) -> list[Path]:
        required = [
            self.paths.qnn_net_run,
            self.paths.qnn_htp_backend,
            self.paths.qnn_model_dlc,
            config.model_path,
            config.input_list_path,
        ]
        return [path for path in required if not path.exists()]

    def build_command(self, config: QnnDlcRunConfig) -> list[str]:
        return [
            str(self.paths.qnn_net_run),
            "--model",
            str(self.paths.qnn_model_dlc),
            "--backend",
            str(self.paths.qnn_htp_backend),
            "--dlc_path",
            str(config.model_path),
            "--input_list",
            str(config.input_list_path),
            "--output_dir",
            str(config.output_dir),
            "--profiling_level",
            config.profiling_level,
        ]

    def run(self, config: QnnDlcRunConfig, timeout_seconds: int = 120) -> subprocess.CompletedProcess[str]:
        missing = self.missing_run_files(config)
        if missing:
            missing_text = ", ".join(str(path) for path in missing)
            raise FileNotFoundError(f"Missing QNN DLC runtime files: {missing_text}")

        env = os.environ.copy()
        bin_dir = self.paths.ai_stack_root / "bin" / self.paths.architecture_dir
        lib_dir = self.paths.ai_stack_root / "lib" / self.paths.architecture_dir
        env["PATH"] = os.pathsep.join([str(bin_dir), str(lib_dir), env.get("PATH", "")])
        config.output_dir.mkdir(parents=True, exist_ok=True)
        return subprocess.run(
            self.build_command(config),
            cwd=str(self.paths.project_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )

    @staticmethod
    def collect_files(root: Path) -> list[dict[str, Any]]:
        if not root.exists():
            return []
        return [QnnDlcRuntimeService.file_info(path) for path in sorted(root.rglob("*")) if path.is_file()]

    @staticmethod
    def file_info(path: Path) -> dict[str, Any]:
        stat = path.stat()
        return {
            "path": str(path),
            "size_bytes": stat.st_size,
            "modified_at": stat.st_mtime,
        }
