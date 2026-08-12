from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import version
from engine.brand_manager import BrandManager
from engine.release_config import RELEASE, ReleaseConfig
from tools.build_installer import INSTALLER_SCRIPT, build_command
from widgets.phoenix import header


def test_release_configuration_is_the_shared_version_source():
    assert version.APP_NAME == RELEASE.app_name == BrandManager.APP_NAME
    assert version.VERSION == RELEASE.display_version == BrandManager.APP_VERSION
    assert version.PACKAGE_VERSION == RELEASE.package_version
    assert version.BUILD == RELEASE.build
    assert version.CODENAME == RELEASE.codename
    assert version.ARCHITECTURE == "arm64"


def test_main_header_uses_shared_release_version_without_rc1_literal():
    source = Path(header.__file__).read_text(encoding="utf-8")
    assert "self.brand.APP_VERSION" in source
    assert "Version 2.0.0 RC1" not in source


def test_window_icon_uses_the_canonical_main_window_resource():
    window = MagicMock()

    assert BrandManager.apply_window_icon(window) is True
    window.iconbitmap.assert_called_once_with(str(BrandManager.APP_ICON))


def test_release_configuration_rejects_missing_or_non_arm64_values(tmp_path):
    invalid = tmp_path / "release.json"
    invalid.write_text(json.dumps({"app_name": "App"}), encoding="utf-8")

    try:
        ReleaseConfig.load(invalid)
    except ValueError as error:
        assert "unvollständig" in str(error)
    else:
        raise AssertionError("Incomplete release config was accepted")


def test_installer_command_uses_release_configuration():
    command = build_command(Path("ISCC.exe"))

    assert f"/DAppVersion={RELEASE.package_version}" in command
    assert f"/DExecutableName={RELEASE.executable_name}" in command
    assert command[-1] == str(INSTALLER_SCRIPT)


def test_inno_setup_contract_is_arm64_and_requires_build_defines():
    content = INSTALLER_SCRIPT.read_text(encoding="utf-8")

    assert "ArchitecturesAllowed=arm64" in content
    assert "ArchitecturesInstallIn64BitMode=arm64" in content
    assert "#ifndef AppVersion" in content
    assert r'dist\SnapdragonAIStudio\*' in content
