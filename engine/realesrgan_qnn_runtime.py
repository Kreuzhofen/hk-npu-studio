"""Runtime contract for the local RealESRGAN QNN context."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from engine.backends.backend_discovery_service import BackendDiscoveryService


MODEL_FILENAME = "real_esrgan_x4plus.bin"


class RealESRGANRuntimeUnavailable(RuntimeError):
    """Structured failure when the QNN-only RealESRGAN runtime is incomplete."""

    def __init__(self, code: str, component: str, detail: str) -> None:
        self.code = code
        self.component = component
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class RealESRGANQnnRuntime:
    model_path: Path
    qnn_net_run: Path
    qnn_htp_backend: Path
    model_source: str
    qnn_htp_skeleton_dirs: tuple[Path, ...] = ()

    @property
    def environment_paths(self) -> tuple[Path, Path]:
        return (self.qnn_htp_backend.parent, self.qnn_net_run.parent)

    def process_environment(self, base_environment: dict[str, str] | None = None) -> dict[str, str]:
        """Build the isolated QNN subprocess environment without global mutation."""
        environment = dict(os.environ if base_environment is None else base_environment)

        def joined(paths: tuple[Path, ...], existing: str | None) -> str:
            entries = [str(path) for path in paths if str(path)]
            if existing:
                entries.append(existing)
            return os.pathsep.join(entries)

        environment["PATH"] = joined(self.environment_paths, environment.get("PATH"))
        environment["ADSP_LIBRARY_PATH"] = joined(
            self.qnn_htp_skeleton_dirs,
            environment.get("ADSP_LIBRARY_PATH"),
        )
        return environment

    def build_command(self, input_list: Path, output_dir: Path, log_level: str) -> list[str]:
        return [
            str(self.qnn_net_run),
            "--retrieve_context",
            str(self.model_path),
            "--backend",
            str(self.qnn_htp_backend),
            "--input_list",
            str(input_list),
            "--output_dir",
            str(output_dir),
            "--log_level",
            log_level,
        ]


def resolve_realesrgan_qnn_runtime(
    *,
    local_app_data: Path | None = None,
    project_root: Path | None = None,
    frozen: bool | None = None,
    discovery_service: type[BackendDiscoveryService] = BackendDiscoveryService,
) -> RealESRGANQnnRuntime:
    """Resolve only a usable HTP context runtime; never select CPU or ONNX."""

    is_frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    app_data = local_app_data or Path(
        os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
    )
    user_model = app_data / "Snapdragon AI Studio" / "models" / MODEL_FILENAME
    development_model = (project_root or Path(__file__).resolve().parents[1]) / "models" / MODEL_FILENAME

    model_path, model_source = (
        (user_model, "user") if is_frozen else (development_model, "development")
    )
    if not model_path.is_file():
        raise RealESRGANRuntimeUnavailable(
            "REALESRGAN_MODEL_MISSING",
            "model",
            "QNN context not found: " + str(model_path),
        )

    discovery = discovery_service.discover()
    runner_text = discovery.qnn_net_run_path if discovery.qnn_tools_found else None
    if not runner_text or not Path(runner_text).is_file():
        raise RealESRGANRuntimeUnavailable(
            "QNN_RUNNER_MISSING",
            "qnn-net-run",
            "qnn-net-run.exe was not discovered for the local QNN runtime.",
        )
    backend_text = getattr(discovery, "qnn_htp_backend_path", None)
    if not backend_text or not Path(backend_text).is_file():
        raise RealESRGANRuntimeUnavailable(
            "QNN_HTP_BACKEND_MISSING",
            "QnnHtp.dll",
            "QnnHtp.dll was not discovered for the local QNN runtime.",
        )
    skeleton_dirs = tuple(
        Path(path) for path in getattr(discovery, "qnn_htp_skeleton_dirs", ())
        if Path(path).is_dir()
    )
    if not skeleton_dirs:
        raise RealESRGANRuntimeUnavailable(
            "QNN_HTP_SKEL_MISSING",
            "HTP skeleton",
            "No signed QNN HTP skeleton and catalog pair was discovered.",
        )

    return RealESRGANQnnRuntime(
        model_path=model_path,
        qnn_net_run=Path(runner_text),
        qnn_htp_backend=Path(backend_text),
        model_source=model_source,
        qnn_htp_skeleton_dirs=skeleton_dirs,
    )
