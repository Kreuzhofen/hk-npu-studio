from __future__ import annotations

import json

from engine.release_config import RELEASE
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

    # Verify that all required dependencies are collected and included as hidden imports
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
    for pkg in expected_packages:
        # Check that it is collected via --collect-all
        collect_indices = [i for i, x in enumerate(arguments) if x == "--collect-all"]
        collected_packages = [arguments[i + 1] for i in collect_indices]
        assert pkg in collected_packages

        # Check that it is listed as a hidden import
        hidden_indices = [i for i, x in enumerate(arguments) if x == "--hidden-import"]
        hidden_packages = [arguments[i + 1] for i in hidden_indices]
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


def test_installer_command_uses_final_executable_and_package_version():
    command = build_command("ISCC.exe")

    assert f"/DExecutableName={RELEASE.executable_name}" in command
    assert f"/DAppVersion={RELEASE.package_version}" in command
