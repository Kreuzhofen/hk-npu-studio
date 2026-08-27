from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from engine.backends.backend_discovery_service import BackendDiscoveryService
from engine.backends.qnn_backend import QNNBackend
from controllers.prompt_workspace_controller import PromptWorkspaceController
from engine.realesrgan_qnn_runtime import (
    MODEL_FILENAME,
    RealESRGANQnnRuntime,
    RealESRGANRuntimeUnavailable,
    resolve_realesrgan_qnn_runtime,
)
from modules import realesrgan_core
from modules import qnn as qnn_module
from plugins.realesrgan import plugin as realesrgan_plugin_module
from plugins.realesrgan.plugin import RealESRGANPlugin


def _runtime_files(root: Path) -> tuple[Path, Path]:
    runner = root / "bin" / "qnn-net-run.exe"
    backend = root / "lib" / "QnnHtp.dll"
    runner.parent.mkdir(parents=True)
    backend.parent.mkdir(parents=True)
    runner.touch()
    backend.touch()
    skeleton_dir = root / "lib" / "htp"
    skeleton_dir.mkdir(parents=True)
    (skeleton_dir / "libQnnHtpV99Skel.so").touch()
    (skeleton_dir / "libqnnhtpv99.cat").touch()
    return runner, backend


def test_backend_discovery_finds_arm64_qnn_runner_and_htp_backend(tmp_path, monkeypatch):
    sdk_root = tmp_path / "qnn-sdk"
    runner = sdk_root / "bin" / "aarch64-windows-msvc" / "qnn-net-run.exe"
    backend = sdk_root / "lib" / "aarch64-windows-msvc" / "QnnHtp.dll"
    runner.parent.mkdir(parents=True)
    backend.parent.mkdir(parents=True)
    runner.touch()
    backend.touch()

    for variable in BackendDiscoveryService.ENV_QNN_VARS:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("QNN_SDK_ROOT", str(sdk_root))

    result = BackendDiscoveryService.discover()

    assert Path(result.qnn_net_run_path) == runner.resolve()
    assert Path(result.qnn_htp_backend_path) == backend.resolve()


def test_backend_discovery_finds_complete_signed_htp_skeleton_pairs(tmp_path, monkeypatch):
    sdk_root = tmp_path / "qnn-sdk"
    runner = sdk_root / "bin" / "aarch64-windows-msvc" / "qnn-net-run.exe"
    backend = sdk_root / "lib" / "aarch64-windows-msvc" / "QnnHtp.dll"
    signed_v73 = sdk_root / "hexagon" / "v73"
    signed_v81 = sdk_root / "hexagon" / "v81"
    incomplete = sdk_root / "hexagon" / "incomplete"
    for path in (runner, backend):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    for directory, version in ((signed_v73, "73"), (signed_v81, "81"), (signed_v81, "99")):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"libQnnHtpV{version}Skel.so").touch()
        catalog_name = f"libqnnhtpv{version}.cat"
        (directory / (catalog_name.upper() if version == "81" else catalog_name)).touch()
    incomplete.mkdir(parents=True)
    (incomplete / "libQnnHtpV123Skel.so").touch()

    for variable in BackendDiscoveryService.ENV_QNN_VARS:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("QNN_SDK_ROOT", str(sdk_root))

    result = BackendDiscoveryService.discover()

    assert result.qnn_htp_skeleton_dirs == tuple(
        sorted((str(signed_v73.resolve()), str(signed_v81.resolve())), key=str.casefold)
    )


def _discovery(runner: Path | None, backend: Path | None):
    return SimpleNamespace(
        qnn_tools_found=runner is not None,
        qnn_net_run_path=str(runner) if runner else None,
        qnn_htp_backend_path=str(backend) if backend else None,
        qnn_htp_skeleton_dirs=(str(backend.parent / "htp"),) if backend else (),
    )


class _DiscoveryService:
    result = None

    @classmethod
    def discover(cls):
        return cls.result


def test_non_frozen_uses_development_model_when_both_models_exist(tmp_path):
    runner, backend = _runtime_files(tmp_path / "qnn")
    user_model = tmp_path / "appdata" / "HK NPU STUDIO" / "models" / MODEL_FILENAME
    development_model = tmp_path / "source" / "models" / MODEL_FILENAME
    user_model.parent.mkdir(parents=True)
    development_model.parent.mkdir(parents=True)
    bundled_model = tmp_path / "frozen-app" / "models" / MODEL_FILENAME
    bundled_model.parent.mkdir(parents=True)
    user_model.touch()
    development_model.touch()
    bundled_model.touch()
    _DiscoveryService.result = _discovery(runner, backend)

    runtime = resolve_realesrgan_qnn_runtime(
        local_app_data=tmp_path / "appdata",
        project_root=tmp_path / "source",
        frozen=False,
        frozen_app_dir=tmp_path / "frozen-app",
        discovery_service=_DiscoveryService,
    )

    assert runtime.model_path == development_model
    assert runtime.model_source == "development"


def test_frozen_uses_local_app_data_model_when_both_models_exist(tmp_path):
    runner, backend = _runtime_files(tmp_path / "qnn")
    user_model = tmp_path / "appdata" / "HK NPU STUDIO" / "models" / MODEL_FILENAME
    development_model = tmp_path / "source" / "models" / MODEL_FILENAME
    user_model.parent.mkdir(parents=True)
    development_model.parent.mkdir(parents=True)
    bundled_model = tmp_path / "frozen-app" / "models" / MODEL_FILENAME
    bundled_model.parent.mkdir(parents=True)
    user_model.touch()
    development_model.touch()
    bundled_model.touch()
    _DiscoveryService.result = _discovery(runner, backend)

    runtime = resolve_realesrgan_qnn_runtime(
        local_app_data=tmp_path / "appdata",
        project_root=tmp_path / "source",
        frozen=True,
        frozen_app_dir=tmp_path / "frozen-app",
        discovery_service=_DiscoveryService,
    )
    assert runtime.model_path == user_model
    assert runtime.model_source == "user"


def test_frozen_uses_bundled_model_when_user_model_is_missing(tmp_path):
    runner, backend = _runtime_files(tmp_path / "qnn")
    bundled_model = tmp_path / "frozen-app" / "models" / MODEL_FILENAME
    bundled_model.parent.mkdir(parents=True)
    bundled_model.touch()
    _DiscoveryService.result = _discovery(runner, backend)

    runtime = resolve_realesrgan_qnn_runtime(
        local_app_data=tmp_path / "appdata",
        frozen=True,
        frozen_app_dir=tmp_path / "frozen-app",
        discovery_service=_DiscoveryService,
    )

    assert runtime.model_path == bundled_model
    assert runtime.model_source == "bundled"


def test_frozen_reuses_legacy_user_model_before_bundled_model(tmp_path):
    runner, backend = _runtime_files(tmp_path / "qnn")
    legacy_model = (
        tmp_path
        / "appdata"
        / "Snapdragon AI Studio"
        / "models"
        / MODEL_FILENAME
    )
    legacy_model.parent.mkdir(parents=True)
    legacy_model.touch()
    bundled_model = tmp_path / "frozen-app" / "models" / MODEL_FILENAME
    bundled_model.parent.mkdir(parents=True)
    bundled_model.touch()
    _DiscoveryService.result = _discovery(runner, backend)

    runtime = resolve_realesrgan_qnn_runtime(
        local_app_data=tmp_path / "appdata",
        frozen=True,
        frozen_app_dir=tmp_path / "frozen-app",
        discovery_service=_DiscoveryService,
    )

    assert runtime.model_path == legacy_model
    assert runtime.model_source == "legacy_user"


def test_non_frozen_does_not_fall_back_to_local_app_data_model(tmp_path):
    runner, backend = _runtime_files(tmp_path / "qnn")
    user_model = tmp_path / "appdata" / "HK NPU STUDIO" / "models" / MODEL_FILENAME
    user_model.parent.mkdir(parents=True)
    user_model.touch()
    bundled_model = tmp_path / "frozen-app" / "models" / MODEL_FILENAME
    bundled_model.parent.mkdir(parents=True)
    bundled_model.touch()
    _DiscoveryService.result = _discovery(runner, backend)

    with pytest.raises(RealESRGANRuntimeUnavailable) as error:
        resolve_realesrgan_qnn_runtime(
            local_app_data=tmp_path / "appdata",
            project_root=tmp_path / "source",
            frozen=False,
            frozen_app_dir=tmp_path / "frozen-app",
            discovery_service=_DiscoveryService,
        )
    expected = tmp_path / "source" / "models" / MODEL_FILENAME
    assert error.value.code == "REALESRGAN_MODEL_MISSING"
    assert str(expected) in error.value.detail
    assert str(user_model) not in error.value.detail
    assert str(bundled_model) not in error.value.detail


def test_frozen_does_not_fall_back_to_development_model(tmp_path):
    runner, backend = _runtime_files(tmp_path / "qnn")
    development_model = tmp_path / "source" / "models" / MODEL_FILENAME
    development_model.parent.mkdir(parents=True)
    development_model.touch()
    _DiscoveryService.result = _discovery(runner, backend)

    with pytest.raises(RealESRGANRuntimeUnavailable) as error:
        resolve_realesrgan_qnn_runtime(
            local_app_data=tmp_path / "appdata",
            project_root=tmp_path / "source",
            frozen=True,
            frozen_app_dir=tmp_path / "frozen-app",
            discovery_service=_DiscoveryService,
        )
    user_model = tmp_path / "appdata" / "HK NPU STUDIO" / "models" / MODEL_FILENAME
    bundled_model = tmp_path / "frozen-app" / "models" / MODEL_FILENAME
    assert error.value.code == "REALESRGAN_MODEL_MISSING"
    assert str(user_model) in error.value.detail
    assert str(bundled_model) in error.value.detail
    assert str(development_model) not in error.value.detail


@pytest.mark.parametrize(
    ("runner", "backend", "expected_code"),
    ((False, True, "QNN_RUNNER_MISSING"), (True, False, "QNN_HTP_BACKEND_MISSING")),
)
def test_missing_qnn_components_fail_without_fallback(tmp_path, runner, backend, expected_code):
    available_runner, available_backend = _runtime_files(tmp_path / "qnn")
    model = tmp_path / "appdata" / "HK NPU STUDIO" / "models" / MODEL_FILENAME
    model.parent.mkdir(parents=True)
    model.touch()
    _DiscoveryService.result = _discovery(
        available_runner if runner else None,
        available_backend if backend else None,
    )

    with pytest.raises(RealESRGANRuntimeUnavailable) as error:
        resolve_realesrgan_qnn_runtime(
            local_app_data=tmp_path / "appdata",
            frozen=True,
            discovery_service=_DiscoveryService,
        )
    assert error.value.code == expected_code


def test_missing_signed_htp_skeleton_pair_fails_closed(tmp_path):
    runner, backend = _runtime_files(tmp_path / "qnn")
    model = tmp_path / "appdata" / "HK NPU STUDIO" / "models" / MODEL_FILENAME
    model.parent.mkdir(parents=True)
    model.touch()
    _DiscoveryService.result = SimpleNamespace(
        qnn_tools_found=True,
        qnn_net_run_path=str(runner),
        qnn_htp_backend_path=str(backend),
        qnn_htp_skeleton_dirs=(),
    )

    with pytest.raises(RealESRGANRuntimeUnavailable) as error:
        resolve_realesrgan_qnn_runtime(
            local_app_data=tmp_path / "appdata",
            frozen=True,
            discovery_service=_DiscoveryService,
        )
    assert error.value.code == "QNN_HTP_SKEL_MISSING"


def test_qnn_command_uses_the_discovered_runner_and_htp_backend(tmp_path, monkeypatch):
    runner, backend = _runtime_files(tmp_path / "qnn")
    model = tmp_path / "model" / MODEL_FILENAME
    model.parent.mkdir()
    model.touch()
    runtime = RealESRGANQnnRuntime(
        model, runner, backend, "user", (backend.parent / "htp",)
    )
    backend_instance = QNNBackend(runtime_resolver=lambda: runtime)
    backend_instance.output_dir = tmp_path / "output"
    input_list = tmp_path / "input_list.txt"
    input_list.write_text("image.raw", encoding="utf-8")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["environment"] = kwargs["env"]
        captured["cwd"] = kwargs["cwd"]

    monkeypatch.setattr("engine.backends.qnn_backend.subprocess.run", fake_run)
    backend_instance.execute_qnn(input_list)

    assert captured["command"] == runtime.build_command(input_list, backend_instance.output_dir, "info")
    assert str(backend.parent) in captured["environment"]["PATH"]
    assert str(runner.parent) in captured["environment"]["PATH"]
    assert str(backend.parent / "htp") in captured["environment"]["ADSP_LIBRARY_PATH"]
    assert captured["cwd"] == input_list.parent
    assert "onnxruntime" not in Path("engine/realesrgan_qnn_runtime.py").read_text(encoding="utf-8").lower()


def test_qnn_call_sites_share_runtime_process_environment(tmp_path, monkeypatch):
    runner, backend = _runtime_files(tmp_path / "qnn")
    model = tmp_path / "model" / MODEL_FILENAME
    model.parent.mkdir()
    model.touch()
    runtime = RealESRGANQnnRuntime(
        model, runner, backend, "development", (backend.parent / "htp",)
    )
    base_environment = {
        "PATH": "existing-path",
        "ADSP_LIBRARY_PATH": "existing-adsp-path",
        "UNCHANGED": "value",
    }

    environment = runtime.process_environment(base_environment)

    assert environment["PATH"] == os.pathsep.join(
        (str(backend.parent), str(runner.parent), "existing-path")
    )
    assert environment["ADSP_LIBRARY_PATH"] == os.pathsep.join(
        (str(backend.parent / "htp"), "existing-adsp-path")
    )
    assert environment["UNCHANGED"] == "value"

    input_dir = tmp_path / "Local AppData Test"
    input_dir.mkdir()
    input_list = input_dir / "input_list.txt"
    input_list.write_text("image.raw", encoding="utf-8")
    captured = []
    monkeypatch.setattr(
        "engine.backends.qnn_backend.subprocess.run",
        lambda _command, **kwargs: captured.append(kwargs),
    )
    backend_instance = QNNBackend(runtime_resolver=lambda: runtime)
    backend_instance.output_dir = tmp_path / "backend-output"
    backend_instance.execute_qnn(input_list)

    monkeypatch.setattr(qnn_module, "resolve_realesrgan_qnn_runtime", lambda: runtime)
    monkeypatch.setattr(
        qnn_module.subprocess,
        "run",
        lambda _command, **kwargs: captured.append(kwargs),
    )
    qnn_module.run_qnn_context(input_list, tmp_path / "module-output")

    assert len(captured) == 2
    for call in captured:
        assert str(backend.parent) in call["env"]["PATH"]
        assert str(runner.parent) in call["env"]["PATH"]
        assert str(backend.parent / "htp") in call["env"]["ADSP_LIBRARY_PATH"]
        assert call["cwd"] == input_dir


def test_tiled_qnn_call_suppresses_windows_console(tmp_path, monkeypatch):
    runner, backend = _runtime_files(tmp_path / "qnn")
    model = tmp_path / "model" / MODEL_FILENAME
    model.parent.mkdir()
    model.touch()
    runtime = RealESRGANQnnRuntime(
        model, runner, backend, "development", (backend.parent / "htp",)
    )
    input_list = tmp_path / "input_list.txt"
    input_list.write_text("image.raw", encoding="utf-8")
    captured = {}
    no_window = 0x08000000

    monkeypatch.setattr(qnn_module, "resolve_realesrgan_qnn_runtime", lambda: runtime)
    monkeypatch.setattr(qnn_module.subprocess, "CREATE_NO_WINDOW", no_window, raising=False)
    monkeypatch.setattr(
        qnn_module.subprocess,
        "run",
        lambda _command, **kwargs: captured.update(kwargs),
    )

    qnn_module.run_qnn_context(input_list, tmp_path / "output")

    assert captured["creationflags"] == no_window


def test_qnn_input_lists_use_relative_raw_names_with_space_paths(tmp_path, monkeypatch):
    work_dir = tmp_path / "Local AppData Test"
    backend_instance = QNNBackend()
    backend_instance.input_dir = work_dir / "backend"

    class Tensor:
        @staticmethod
        def tofile(path):
            Path(path).write_bytes(b"raw")

    backend_files = backend_instance.write_raw_input(Tensor())
    assert backend_files["input_list"].read_text(encoding="utf-8") == "image.raw"

    def write_raw(_tile, raw_path):
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"raw")

    captured = {}
    monkeypatch.setattr(realesrgan_core, "tile_to_raw", write_raw)
    monkeypatch.setattr(
        realesrgan_core,
        "run_qnn_context",
        lambda input_list, _output_dir, **_kwargs: captured.setdefault("input_list", input_list),
    )
    monkeypatch.setattr(realesrgan_core, "raw_tile_to_image", lambda _path: Image.new("RGB", (1, 1)))

    realesrgan_core.run_tile(Image.new("RGB", (1, 1)), work_dir, 0)

    assert captured["input_list"].read_text(encoding="utf-8") == "image.raw"


def test_tiled_upscale_preserves_original_aspect_and_callbacks(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    Image.new("RGB", (150, 70), "navy").save(source)
    original_bytes = source.read_bytes()
    output_dir = tmp_path / "output"
    temp_dir = tmp_path / "temp"
    events: list[tuple[str, object]] = []

    monkeypatch.setattr(realesrgan_core, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(realesrgan_core, "TEMP_DIR", temp_dir)
    monkeypatch.setattr(realesrgan_core, "run_tile", lambda *args: Image.new("RGB", (512, 512), "red"))

    result = realesrgan_core.upscale_tiled(
        source,
        progress=lambda value: events.append(("progress", value)),
        status=lambda value: events.append(("status", value)),
        percent=lambda value: events.append(("percent", value)),
    )

    assert source.read_bytes() == original_bytes
    with Image.open(result) as image:
        assert image.size == (600, 280)
    assert any(kind == "progress" for kind, _ in events)
    assert any(kind == "status" for kind, _ in events)
    assert events[-1] == ("progress", "100 %")


@pytest.mark.parametrize(
    ("length", "expected"),
    (
        (64, [0]),
        (128, [0]),
        (512, [0, 96, 192, 288, 384]),
        (1024, [0, 112, 224, 336, 448, 560, 672, 784, 896]),
        (1000, [0, 109, 218, 327, 436, 545, 654, 763, 872]),
    ),
)
def test_tile_positions_cover_each_axis_with_controlled_overlap(length, expected):
    positions = realesrgan_core.tile_positions(length)

    assert positions == expected
    assert positions[0] == 0
    assert positions[-1] == max(0, length - realesrgan_core.TILE_SIZE)
    assert all(next_position <= position + realesrgan_core.TILE_SIZE for position, next_position in zip(positions, positions[1:]))
    assert all(next_position < position + realesrgan_core.TILE_SIZE for position, next_position in zip(positions, positions[1:]))


def test_tile_overlaps_are_derived_from_distributed_positions():
    positions = realesrgan_core.tile_positions(512)

    assert realesrgan_core.tile_overlaps(positions, [0], 0, 0, 128, 128) == (0, 32, 0, 0)
    assert realesrgan_core.tile_overlaps(positions, [0], 1, 0, 128, 128) == (32, 32, 0, 0)
    assert realesrgan_core.tile_overlaps(positions, [0], 4, 0, 128, 128) == (32, 0, 0, 0)


def test_tiled_upscale_feathers_overlapping_model_tiles(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    Image.new("RGB", (224, 128), "white").save(source)
    original_bytes = source.read_bytes()
    output_dir = tmp_path / "output"

    monkeypatch.setattr(realesrgan_core, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(realesrgan_core, "TEMP_DIR", tmp_path / "temp")
    monkeypatch.setattr(
        realesrgan_core,
        "run_tile",
        lambda _tile, _work_dir, index: Image.new("RGB", (512, 512), "red" if index == 1 else "blue"),
    )

    result_path = realesrgan_core.upscale_tiled(source)

    assert source.read_bytes() == original_bytes
    with Image.open(result_path) as result:
        assert result.size == (896, 512)
        assert result.getpixel((0, 256)) == (255, 0, 0)
        assert result.getpixel((895, 256)) == (0, 0, 255)
        blended = result.getpixel((96 * 4 + 16 * 4, 256))
        assert blended[0] > 0 and blended[2] > 0


@pytest.mark.parametrize("scale", (2, 4))
def test_controller_upscale_profiles_use_one_qnn_adapter_run_and_keep_original(tmp_path, monkeypatch, scale):
    source = tmp_path / "generated.png"
    intermediate = tmp_path / "native_4x.png"
    Image.new("RGB", (10, 6), "navy").save(source)
    Image.new("RGB", (40, 24), "red").save(intermediate)
    original_bytes = source.read_bytes()
    calls = []

    class Adapter:
        def run(self, skill, **kwargs):
            calls.append((skill, kwargs))
            return {"output_path": str(intermediate)}

    monkeypatch.setattr("engine.phoenix_adapter.PhoenixAdapter", Adapter)
    controller = PromptWorkspaceController.__new__(PromptWorkspaceController)
    result = Path(controller.upscale_generated_image(str(source), scale))

    assert calls == [("image.upscale", {"input_path": str(source.resolve())})]
    assert source.read_bytes() == original_bytes
    assert result.name == f"generated_{scale}x.png"
    with Image.open(result) as image:
        assert image.size == ((20, 12) if scale == 2 else (40, 24))
    assert not intermediate.exists()


def test_controller_4x_profile_never_uses_lanczos_resize(tmp_path, monkeypatch):
    source = tmp_path / "generated.png"
    intermediate = tmp_path / "native_4x.png"
    Image.new("RGB", (8, 8), "navy").save(source)
    Image.new("RGB", (32, 32), "red").save(intermediate)

    class Adapter:
        def run(self, _skill, **_kwargs):
            return {"output_path": str(intermediate)}

    monkeypatch.setattr("engine.phoenix_adapter.PhoenixAdapter", Adapter)
    monkeypatch.setattr(Image.Image, "resize", lambda *_args, **_kwargs: pytest.fail("4x must not resize"))
    controller = PromptWorkspaceController.__new__(PromptWorkspaceController)

    result = Path(controller.upscale_generated_image(str(source), 4))

    assert result.name == "generated_4x.png"


def test_controller_4x_retries_transient_windows_file_lock(tmp_path, monkeypatch):
    source = tmp_path / "generated.png"
    intermediate = tmp_path / "native_4x.png"
    Image.new("RGB", (8, 8), "navy").save(source)
    Image.new("RGB", (32, 32), "red").save(intermediate)
    original_bytes = source.read_bytes()

    class Adapter:
        def run(self, _skill, **_kwargs):
            return {"output_path": str(intermediate)}

    original_replace = Path.replace
    attempts = []

    def replace_with_transient_lock(path, target):
        attempts.append((path, target))
        if len(attempts) < 3:
            error = PermissionError(32, "file is in use", str(path))
            error.winerror = 32
            raise error
        return original_replace(path, target)

    monkeypatch.setattr("engine.phoenix_adapter.PhoenixAdapter", Adapter)
    monkeypatch.setattr(Path, "replace", replace_with_transient_lock)
    monkeypatch.setattr("controllers.prompt_workspace_controller.time.sleep", lambda _delay: None)
    controller = PromptWorkspaceController.__new__(PromptWorkspaceController)

    result = Path(controller.upscale_generated_image(str(source), 4))

    assert len(attempts) == 3
    assert result.name == "generated_4x.png"
    assert result.is_file()
    assert not intermediate.exists()
    assert source.read_bytes() == original_bytes


def test_controller_upscale_profile_rejects_invalid_scale_and_preserves_original(tmp_path):
    source = tmp_path / "generated.png"
    Image.new("RGB", (8, 8), "navy").save(source)
    original_bytes = source.read_bytes()
    controller = PromptWorkspaceController.__new__(PromptWorkspaceController)

    with pytest.raises(ValueError, match="Unsupported RealESRGAN scale: 3"):
        controller.upscale_generated_image(str(source), 3)

    assert source.read_bytes() == original_bytes


def test_controller_upscale_failure_preserves_generated_original(tmp_path, monkeypatch):
    source = tmp_path / "generated.png"
    Image.new("RGB", (8, 8), "navy").save(source)
    original_bytes = source.read_bytes()

    class Adapter:
        def run(self, _skill, **_kwargs):
            raise RuntimeError("QNN unavailable")

    monkeypatch.setattr("engine.phoenix_adapter.PhoenixAdapter", Adapter)
    controller = PromptWorkspaceController.__new__(PromptWorkspaceController)

    with pytest.raises(RuntimeError, match="QNN unavailable"):
        controller.upscale_generated_image(str(source), 4)

    assert source.read_bytes() == original_bytes


def test_controller_rejects_original_path_as_upscale_output(tmp_path, monkeypatch):
    source = tmp_path / "generated.png"
    Image.new("RGB", (8, 8), "navy").save(source)
    original_bytes = source.read_bytes()

    class Adapter:
        def run(self, _skill, **_kwargs):
            return {"output_path": str(source)}

    monkeypatch.setattr("engine.phoenix_adapter.PhoenixAdapter", Adapter)
    controller = PromptWorkspaceController.__new__(PromptWorkspaceController)

    with pytest.raises(RuntimeError, match="separate output file"):
        controller.upscale_generated_image(str(source), 4)

    assert source.read_bytes() == original_bytes


def test_controller_legacy_2x_wrapper_delegates_to_profile_method(tmp_path):
    controller = PromptWorkspaceController.__new__(PromptWorkspaceController)
    calls = []
    controller.upscale_generated_image = lambda path, scale: calls.append((path, scale)) or str(tmp_path / "result.png")

    assert controller.upscale_generated_image_2x("generated.png") == str(tmp_path / "result.png")
    assert calls == [("generated.png", 2)]


def test_plugin_routes_image_upscale_to_overlap_tiled_pipeline(tmp_path, monkeypatch):
    source = tmp_path / "generated.png"
    output = tmp_path / "generated_tile_upscaled_x4.png"
    Image.new("RGB", (512, 512), "navy").save(source)
    output.touch()
    calls = []

    def tiled(path):
        calls.append(path)
        return output

    monkeypatch.setattr(realesrgan_plugin_module, "upscale_tiled", tiled)
    monkeypatch.setattr(
        QNNBackend,
        "upscale",
        lambda *_args, **_kwargs: pytest.fail("image.upscale must not use QNNBackend.upscale"),
    )

    result = RealESRGANPlugin().execute("image.upscale", input_path=str(source))

    assert calls == [source]
    assert result == {
        "status": "success",
        "plugin": "RealESRGAN",
        "skill": "image.upscale",
        "input_path": str(source),
        "output_path": str(output),
        "backend": "QNN",
    }


def test_plugin_propagates_tiled_upscale_errors(tmp_path, monkeypatch):
    source = tmp_path / "generated.png"
    Image.new("RGB", (512, 512), "navy").save(source)

    def tiled(_path):
        raise RuntimeError("QNN tile failed")

    monkeypatch.setattr(realesrgan_plugin_module, "upscale_tiled", tiled)

    with pytest.raises(RuntimeError, match="QNN tile failed"):
        RealESRGANPlugin().execute("image.upscale", input_path=str(source))


def test_plugin_tiled_pipeline_uses_25_tiles_for_512_square_image():
    positions = realesrgan_core.tile_positions(512)

    assert len(positions) == 5
    assert len(positions) * len(positions) == 25


def test_plugin_and_controller_contracts_remain_qnn_upscale_connections():
    assert RealESRGANPlugin.id == "realesrgan"
    assert RealESRGANPlugin.skills == ["image.upscale"]
    controller_source = Path("controllers/prompt_workspace_controller.py").read_text(encoding="utf-8")
    assert 'PhoenixAdapter().run("image.upscale", input_path=str(source_path))' in controller_source
