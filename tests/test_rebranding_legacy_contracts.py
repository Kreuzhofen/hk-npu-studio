from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.application_update_service import (
    ApplicationUpdateManifest,
    ApplicationUpdateService,
)
from engine.brand_manager import BrandManager
from engine.release_config import RELEASE, ReleaseConfig


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRODUCT_DIR = "HK NPU STUDIO"
LEGACY_PRODUCT_DIR = "Snapdragon AI Studio"
EXECUTABLE_NAME = "HKNPUStudio.exe"
INSTALLER_APP_ID = "{{8D9D455C-4C15-4A61-9685-21F67C5D4A44}"


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_rebranded_storage_target_preserves_legacy_source_contract():
    config_source = _read("config.py")

    assert f'PRODUCT_DATA_DIR_NAME = "{PRODUCT_DIR}"' in config_source
    assert f'LEGACY_PRODUCT_DATA_DIR_NAME = "{LEGACY_PRODUCT_DIR}"' in config_source
    assert "LOCAL_APP_DATA / PRODUCT_DATA_DIR_NAME" in config_source
    for contract in (
        'INPUT_DIR = USER_BASE / "input"',
        'OUTPUT_DIR = USER_BASE / "output"',
        'DATA_DIR = USER_BASE / "data"',
        'LOG_DIR = USER_BASE / "logs"',
        'ASSET_INDEX_DB = DATA_DIR / "asset_index.sqlite3"',
        'PREFERENCES_PATH = DATA_DIR / "preferences.json"',
        'PROMPT_HISTORY_PATH = DATA_DIR / "prompt_history.json"',
        'TEMP_DIR = USER_BASE / "temp"',
        'MODELS_DIR = USER_BASE / "models"',
        'REALESRGAN_MODEL = MODELS_DIR / "real_esrgan_x4plus.bin"',
    ):
        assert contract in config_source


def test_legacy_migration_sources_are_preserved():
    migration_source = _read("app/migration.py")

    assert "legacy_user_root = local_root / LEGACY_PRODUCT_DATA_DIR_NAME" in migration_source
    assert 'local_root / "Programs" / LEGACY_PRODUCT_DATA_DIR_NAME / "output"' in migration_source
    assert "not target.exists()" in migration_source


def test_early_generation_abort_log_uses_canonical_log_dir():
    generation_source = _read("controllers/generation_controller.py")

    assert 'Path(LOG_DIR) / "early_generation_abort.log"' in generation_source


def test_rebranded_executable_contract():
    assert RELEASE.executable_name == EXECUTABLE_NAME
    assert json.loads(_read("release.json"))["executable_name"] == EXECUTABLE_NAME


def test_installer_keeps_upgrade_identity_and_uses_new_paths():
    installer = _read("installer/snapdragon_ai_studio.iss")

    assert f"AppId={INSTALLER_APP_ID}" in installer
    assert (
        r"DefaultDirName={localappdata}\Programs\HK NPU STUDIO"
        in installer
    )
    assert (
        r"PreferencesDir := ExpandConstant('{localappdata}\HK NPU STUDIO\data');"
        in installer
    )
    assert r"{localappdata}\Snapdragon AI Studio\data\preferences.json" in installer


def test_rebranded_packaging_and_update_contracts(tmp_path):
    installer = _read("installer/snapdragon_ai_studio.iss")
    build_installer = _read("tools/build_installer.py")
    build_app = _read("tools/build_app.py")

    assert "OutputBaseFilename=HKNPUStudio-{#AppVersion}-ARM64-Setup" in installer
    assert r'Source: "..\dist\HKNPUStudio\*"; DestDir: "{app}"' in installer
    assert r'Filename: "{app}\{#ExecutableName}"' in installer
    assert 'RELEASE_STAGING_DIR = PROJECT_ROOT / "dist" / "HKNPUStudio"' in build_installer
    assert 'APP_DIST = DIST_ROOT / "HKNPUStudio"' in build_app
    assert 'StringStruct(\'InternalName\', \'HKNPUStudio\')' in build_app
    assert '"HKNPUStudio"' in build_app

    calls: list[tuple[str, dict[str, object]]] = []

    class Downloader:
        def download(self, url, **kwargs):
            calls.append((url, kwargs))
            target = tmp_path / str(kwargs["filename"])
            target.write_bytes(b"verified")
            return type("Result", (), {"success": True, "path": target, "message": "ok"})()

    service = ApplicationUpdateService(
        current_version="2.0.0-rc.1",
        download_service=Downloader(),
    )
    manifest = ApplicationUpdateManifest(
        version="2.0.0-rc.2",
        architecture="arm64",
        package_url="https://updates.example.test/update.exe",
        sha256="a" * 64,
    )

    result = service.stage_update(manifest)

    assert result.success is True
    assert calls[0][1]["filename"] == "HKNPUStudio-2.0.0-rc.2-ARM64-Setup.exe"


def test_rebranded_technical_user_agent_contracts():
    expected_user_agents = {
        "app/model_downloader.py": '"User-Agent": "HKNPUStudio/2.0"',
        "app/settings_manager.py": '"User-Agent": "HKNPUStudio/2.0"',
        "engine/application_update_service.py": (
            '"User-Agent": f"HKNPUStudio/{self.current_version}"'
        ),
        "engine/download_service.py": '"User-Agent": "HKNPUStudio/2.0"',
    }

    for relative_path, expected_contract in expected_user_agents.items():
        assert expected_contract in _read(relative_path)


def test_phase1_phoenix_boost_brand_preserved():
    required_locale_keys = {
        "home_ollama_optional",
        "boost_button",
        "boost_title",
        "boost_preview_title",
        "boost_ai_available",
        "boost_ai_title",
        "boost_ai_optional_info",
        "boost_ai_setup_ready",
        "boost_ai_status_not_ready",
        "boost_ai_status_ready",
        "boost_ai_ready_button",
    }
    for locale in ("de_DE", "en_US", "es_ES"):
        values = json.loads(_read(f"locales/{locale}.json"))
        assert required_locale_keys <= values.keys()
        for key in required_locale_keys:
            assert "Phoenix Boost" in values[key]

    for relative_path in (
        "dialogs/ollama_setup_dialog.py",
        "dialogs/qwen_setup_dialog.py",
        "widgets/phoenix/views/prompt_view.py",
    ):
        assert "Phoenix Boost" in _read(relative_path)


def test_phase1_phoenix_technical_contracts_preserved():
    required_modules = (
        "engine/phoenix_adapter.py",
        "engine/phoenix_api.py",
        "engine/phoenix_core.py",
        "engine/phoenix_queue.py",
        "engine/phoenix_scheduler.py",
        "engine/phoenix_worker.py",
        "widgets/phoenix/theme.py",
        "widgets/phoenix/workspace.py",
    )
    assert (PROJECT_ROOT / "widgets/phoenix").is_dir()
    for relative_path in required_modules:
        assert (PROJECT_ROOT / relative_path).is_file()

    prompt_view = _read("widgets/phoenix/views/prompt_view.py")
    theme = _read("widgets/phoenix/theme.py")
    assert "PHOENIX_THEME" in prompt_view
    assert "PHOENIX_THEME" in theme
    assert 'style="Phoenix.' in prompt_view


def test_phase1_phoenix_asset_paths_preserved():
    expected = {
        "MASTER_LOGO": "assets/brand/master/phoenix_master.svg",
        "SVG_BLACK": "assets/brand/svg/phoenix_black.svg",
        "SVG_WHITE": "assets/brand/svg/phoenix_white.svg",
        "SVG_BLUE": "assets/brand/svg/phoenix_blue.svg",
        "PHOENIX_ICON": "assets/brand/icons/phoenix.ico",
        "HEADER_DARK": "assets/brand/header/phoenix_header_dark.png",
        "HEADER_LIGHT": "assets/brand/header/phoenix_header_light.png",
        "SPLASH": "assets/brand/splash/phoenix_splash.png",
        "ABOUT_IMAGE": "assets/brand/about/phoenix_about.png",
    }
    for attribute, relative_path in expected.items():
        actual = getattr(BrandManager, attribute)
        assert actual == PROJECT_ROOT / relative_path
        assert actual.is_file()

    assert BrandManager.png(128) == PROJECT_ROOT / "assets/brand/png/phoenix_128.png"
    assert BrandManager.png(128).is_file()


def test_phase1_app_icon_contract_preserved():
    expected_icon = PROJECT_ROOT / "assets/brand/icons/app.ico"
    build_app = _read("tools/build_app.py")
    installer = _read("installer/snapdragon_ai_studio.iss")

    assert BrandManager.APP_ICON == expected_icon
    assert expected_icon.is_file()
    assert 'str(PROJECT_ROOT / "assets" / "brand" / "icons" / "app.ico")' in build_app
    assert r"SetupIconFile=..\assets\brand\icons\app.ico" in installer


def test_phase1_approved_brand_master_hash_preserved():
    master = PROJECT_ROOT / "assets/brand/hk_npu_studio_banner_master.png"

    assert master.is_file()
    actual_hash = hashlib.sha256(master.read_bytes()).hexdigest().upper()
    assert actual_hash == "FE9CFD4A393BE39B0F9FAA13DB1AECACD0B8BC38E079C781E5C9E9D92E3CE8A8"


def test_phase1_snapdragon_hardware_terms_preserved():
    sources = "\n".join(
        _read(relative_path)
        for relative_path in (
            "README.md",
            "gui_v2.py",
            "installer/snapdragon_ai_studio.iss",
            "locales/en_US.json",
            "resources/package_catalog.json",
            "engine/sd15_qai_appbuilder_backend.py",
        )
    )

    for hardware_term in (
        "Snapdragon X Elite",
        "Snapdragon X Plus",
        "Snapdragon NPU",
        "Windows on Snapdragon",
        "QNN",
        "QAI AppBuilder",
    ):
        assert hardware_term in sources


def test_help_uses_rebranded_storage_paths():
    expected_paths = (
        rf"%LOCALAPPDATA%\{PRODUCT_DIR}\output",
        rf"%LOCALAPPDATA%\{PRODUCT_DIR}\models",
        rf"%LOCALAPPDATA%\{PRODUCT_DIR}\data",
        rf"%LOCALAPPDATA%\{PRODUCT_DIR}\logs",
    )
    for locale in ("de_DE", "en_US", "es_ES"):
        help_text = _read(f"locales/help_{locale}.txt")
        for expected_path in expected_paths:
            assert expected_path in help_text


def test_phase1_visible_branding_can_change_independently(tmp_path):
    release_values = json.loads(_read("release.json"))
    release_values["app_name"] = "HK NPU STUDIO"
    candidate = tmp_path / "release.json"
    candidate.write_text(
        json.dumps(release_values, ensure_ascii=False),
        encoding="utf-8",
    )

    branded = ReleaseConfig.load(candidate)

    assert branded.app_name == "HK NPU STUDIO"
    assert branded.executable_name == EXECUTABLE_NAME
    assert branded.package_version == RELEASE.package_version
    assert branded.architecture == "arm64"
