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

    assert build_app._find_optional_qai_appbuilder() is not None

    for pkg in expected_packages:
        assert pkg in collected_packages
        assert pkg in hidden_packages
    for module_name in build_app.SD35_FROZEN_MODULES:
        assert module_name in hidden_packages


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
    for source, destination in build_app._resolve_sd35_dependency_files():
        assert f"{source}{os.pathsep}{destination}" in add_data_values

    sd35_dependencies = build_app._resolve_sd35_dependency_files()
    dependency_destinations = {
        source.name: destination for source, destination in sd35_dependencies
    }
    for package_name in build_app.SD35_DEPENDENCY_DIRS:
        assert dependency_destinations[package_name] == package_name
    assert not any(
        source.name == "types.py" and destination == "."
        for source, destination in sd35_dependencies
    )

    joined = "\n".join(add_data_values).lower()
    assert "ddcolor" not in joined
    assert "rorem" not in joined
    assert "rc3_release_notes.md" in joined


def test_sd35_dependency_payload_preserves_package_namespaces():
    dependencies = build_app._resolve_sd35_dependency_files()
    package_mappings = {
        source.name: (source, Path(destination))
        for source, destination in dependencies
        if source.name in build_app.SD35_DEPENDENCY_DIRS
    }

    expected_entries = (
        ("torch", "types.py"),
        ("torch", "__init__.py"),
        ("torchgen", "__init__.py"),
        ("functorch", "__init__.py"),
        ("yaml", "__init__.py"),
    )
    staged_paths = set()
    for package_name, relative_entry in expected_entries:
        source, destination = package_mappings[package_name]
        assert destination == Path(package_name)
        assert (source / relative_entry).is_file()
        staged_paths.add(destination / relative_entry)

    assert Path("torch/types.py") in staged_paths
    assert Path("types.py") not in staged_paths
    assert Path("torch/__init__.py") in staged_paths
    assert Path("torchgen/__init__.py") in staged_paths
    assert Path("functorch/__init__.py") in staged_paths
    assert Path("yaml/__init__.py") in staged_paths
    assert not any(path.parent == Path(".") for path in staged_paths)


def test_sd35_qai_payload_and_helper_keep_frozen_namespaces():
    arguments = build_app.build_arguments()
    add_data_values = {
        arguments[index + 1]
        for index, argument in enumerate(arguments[:-1])
        if argument == "--add-data"
    }
    qai_package, qai_common = build_app._find_optional_qai_appbuilder()

    assert f"{qai_package}{os.pathsep}qai_appbuilder" in add_data_values
    assert f"{qai_common}{os.pathsep}qai_appbuilder_common" in add_data_values
    for relative_path in build_app.QAI_APPBUILDER_REQUIRED_FILES:
        assert (qai_package / relative_path).is_file()
        assert Path("qai_appbuilder") / relative_path != Path(relative_path)
    assert (qai_common / "_stable_diffusion.py").is_file()
    assert Path("qai_appbuilder_common/_stable_diffusion.py") != Path(
        "_stable_diffusion.py"
    )


def test_release_build_fails_without_sd35_qai_payload(monkeypatch):
    monkeypatch.setattr(build_app, "_find_optional_qai_appbuilder", lambda: None)

    with pytest.raises(FileNotFoundError, match="SD3.5 release backend"):
        build_app.build_arguments()


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
