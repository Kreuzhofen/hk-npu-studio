from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from controllers.plugin_controller import PluginController
from engine.plugin_manager import PluginManager


def manifest(plugin_id="demo"):
    return {
        "id": plugin_id,
        "name": "Demo",
        "version": "1.0.0",
        "author": "Test",
        "backend": "CPU",
        "skills": ["image.demo"],
    }


def write_plugin(root, folder="demo", data=None):
    directory = root / folder
    directory.mkdir()
    (directory / "plugin.json").write_text(
        json.dumps(data or manifest(folder)), encoding="utf-8"
    )
    (directory / "plugin.py").write_text("class Plugin: pass", encoding="utf-8")
    return directory


def test_scan_is_deterministic_and_skips_invalid_manifests(tmp_path):
    write_plugin(tmp_path, "valid")
    write_plugin(tmp_path, "mismatch", manifest("other"))
    write_plugin(tmp_path, "broken", {"id": "broken"})

    plugins = PluginManager(tmp_path).scan()

    assert [plugin.id for plugin in plugins] == ["valid"]


def test_disabled_plugin_cannot_be_loaded(tmp_path):
    write_plugin(tmp_path)
    (tmp_path / "plugins_config.json").write_text(
        json.dumps({"demo": False}), encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="deaktiviert"):
        PluginManager(tmp_path).load_plugin("demo")


def test_validated_plugin_entrypoint_is_loaded(tmp_path):
    write_plugin(tmp_path)
    plugin_type = type("Plugin", (), {"id": "demo"})

    with patch(
        "engine.plugin_manager.importlib.import_module",
        return_value=SimpleNamespace(Plugin=plugin_type),
    ):
        plugin = PluginManager(tmp_path).load_plugin("demo")

    assert plugin.id == "demo"


def test_plugin_activation_config_is_written_atomically(tmp_path):
    controller = PluginController(tmp_path)

    controller.toggle_plugin("demo", False)

    assert json.loads(controller.config_path.read_text(encoding="utf-8")) == {
        "demo": False
    }
    assert not list(tmp_path.glob(".*.tmp"))


def test_plugin_install_validates_manifest_and_commits_complete_directory(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    source = write_plugin(source_root, "package", manifest("installed"))
    target = tmp_path / "target"
    controller = PluginController(target)

    plugin_id = controller.install_plugin(source)

    assert plugin_id == "installed"
    assert (target / "installed" / "plugin.json").is_file()
    assert (target / "installed" / "plugin.py").is_file()
    assert not list(target.glob(".*.tmp"))


def test_invalid_plugin_install_leaves_no_partial_directory(tmp_path):
    source = tmp_path / "invalid"
    source.mkdir()
    (source / "plugin.py").write_text("class Plugin: pass", encoding="utf-8")
    target = tmp_path / "target"
    controller = PluginController(target)

    with pytest.raises(ValueError, match="plugin.json"):
        controller.install_plugin(source)

    assert not (target / "invalid").exists()
