from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from engine.release_config import RELEASE
from tools import build_app
from tools.build_app import BUILD_ROOT, build_arguments
from tools.build_installer import build_command


def test_packaging_uses_arm64_release_identity_and_required_resources():
    arguments = build_arguments()
    joined = "\n".join(arguments)

    assert "--onedir" in arguments
    assert "--windowed" in arguments
    assert "--contents-directory" in arguments
    assert "release.json" in joined
    assert "resources" in joined
    assert "locales" in joined
    assert "plugins" in joined
    assert RELEASE.architecture == "arm64"

    # QAI AppBuilder is optional for this RC3 package. Its dependency closure is
    # collected only when an explicitly configured or local development package exists.
    expected_packages = [
        "requests",
        "filelock",
        "tqdm",
        "packaging",
        "huggingface_hub",
        "qai_hub",
        "diffusers",
        "py3_wget",
        "torchgen",
        "functorch",
        "yaml",
    ]
    collect_indices = [i for i, x in enumerate(arguments) if x == "--collect-all"]
    collected_packages = [arguments[i + 1] for i in collect_indices]
    hidden_indices = [i for i, x in enumerate(arguments) if x == "--hidden-import"]
    hidden_packages = [arguments[i + 1] for i in hidden_indices]

    if build_app._find_optional_qai_appbuilder() is None:
        assert "qai_appbuilder" not in collected_packages
        assert "qai_appbuilder" not in hidden_packages
        return

    for pkg in expected_packages:
        assert pkg in collected_packages
        assert pkg in hidden_packages


def test_packaged_model_metadata_does_not_leak_local_install_paths():
    build_arguments()
    definitions = BUILD_ROOT / "release_data" / "resources" / "models"

    for definition in definitions.glob("*.json"):
        data = json.loads(definition.read_text(encoding="utf-8"))
        assert data["installed"] is False
        assert data["downloaded"] is False
        assert data["path"] == ""
        assert data["status"] == "Not Installed"


def test_packaging_includes_only_the_product_real_esrgan_model():
    arguments = build_arguments()
    add_data_values = [
        arguments[index + 1]
        for index, argument in enumerate(arguments[:-1])
        if argument == "--add-data"
    ]
    expected = f"{build_app.REALESRGAN_PRODUCT_MODEL}{os.pathsep}models"

    assert add_data_values.count(expected) == 1
    assert all(
        value.split(os.pathsep, 1)[0] != str(build_app.PROJECT_ROOT / "models")
        for value in add_data_values
    )
    assert all(
        destination != "models" or source == str(build_app.REALESRGAN_PRODUCT_MODEL)
        for source, destination in (
            value.split(os.pathsep, 1) for value in add_data_values
        )
    )


def test_packaging_includes_fidesr_qnn_runtime_and_current_documentation():
    arguments = build_arguments()
    add_data_values = {
        arguments[index + 1]
        for index, argument in enumerate(arguments[:-1])
        if argument == "--add-data"
    }

    for source, destination in build_app.FIDESR_PRODUCT_FILES:
        assert f"{source}{os.pathsep}{destination}" in add_data_values
    for source, destination in build_app.RELEASE_DOCUMENTS:
        assert f"{source}{os.pathsep}{destination}" in add_data_values
    for source, destination in build_app._resolve_fidesr_qnn_runtime_files():
        assert f"{source}{os.pathsep}{destination}" in add_data_values

    joined = "\n".join(add_data_values).lower()
    assert "ddcolor" not in joined
    assert "rorem" not in joined
    assert "rc3_release_notes.md" in joined


def test_fidesr_runner_uses_portable_resource_and_qnn_runtime_contracts():
    project_root = build_app.PROJECT_ROOT
    runner = (
        project_root / "engine" / "backends" / "fidesr_strong_runner_template.py"
    ).read_text(encoding="utf-8")
    backend = (
        project_root / "engine" / "backends" / "fidesr_photo_restore_backend.py"
    ).read_text(encoding="utf-8")
    entrypoint = (project_root / "gui_v2.py").read_text(encoding="utf-8")

    assert r"C:\SnapdragonAI" not in runner
    assert r"C:\Qualcomm\AIStack" not in runner
    assert 'os.environ["HK_NPU_FIDESR_ROOT"]' in runner
    assert 'os.environ["HK_NPU_FIDESR_QNN_RUNNER"]' in runner
    assert 'packaged = ROOT / "qnn_runtime"' in backend
    assert '"--fidesr-runner"' in backend
    assert '"--fidesr-runner"' in entrypoint


def test_packaging_fails_when_product_real_esrgan_model_is_missing(tmp_path, monkeypatch):
    missing_model = tmp_path / "real_esrgan_x4plus.bin"
    monkeypatch.setattr(build_app, "REALESRGAN_PRODUCT_MODEL", missing_model)

    with pytest.raises(FileNotFoundError, match="Produktgebundenes RealESRGAN-Modell fehlt"):
        build_app.build_arguments()


def test_installer_command_uses_final_executable_and_package_version():
    command = build_command("ISCC.exe")

    assert f"/DExecutableName={RELEASE.executable_name}" in command
    assert f"/DAppVersion={RELEASE.package_version}" in command


def test_installer_keeps_fidesr_contexts_but_does_not_recompress_them():
    installer = build_app.PROJECT_ROOT / "installer" / "snapdragon_ai_studio.iss"
    text = installer.read_text(encoding="utf-8")
    file_lines = [line.strip() for line in text.splitlines() if line.startswith("Source:")]

    general = next(
        line for line in file_lines
        if line.startswith('Source: "..\\dist\\HKNPUStudio\\*";')
    )
    contexts = next(
        line for line in file_lines
        if line.startswith(
            'Source: "..\\dist\\HKNPUStudio\\models\\photo_restore_context\\*";'
        )
    )

    assert "Compression=lzma2" in text
    assert "SolidCompression=yes" in text
    assert "models\\photo_restore_context\\*" in general
    assert "nocompression" not in general
    assert 'DestDir: "{app}\\models\\photo_restore_context"' in contexts
    assert "recursesubdirs" in contexts
    assert "createallsubdirs" in contexts
    assert "nocompression" in contexts
    assert "qnn_runtime" not in general.partition("Excludes:")[2]


def test_development_launcher_targets_the_phoenix_entrypoint_without_legacy_gui():
    project_root = build_app.PROJECT_ROOT
    launcher = (project_root / "start_gui.bat").read_text(encoding="utf-8")

    assert "%~dp0" in launcher
    assert "gui_v2.py" in launcher
    assert "C:\\sd-compile-x64" not in launcher
    assert "python gui.py" not in launcher.lower()
    assert not (project_root / "gui.py").exists()

    tracked_files = subprocess.check_output(
        ["git", "-C", str(project_root), "ls-files", "*.py", "*.bat"], text=True
    ).splitlines()
    product_sources = [
        project_root / relative for relative in tracked_files if not relative.startswith("tests/")
    ]
    product_text = "\n".join(
        path.read_text(encoding="utf-8") for path in product_sources if path.is_file()
    )
    assert "Studio v1.1 Identity" not in product_text
    assert "ComfyUI Backend" not in product_text
