"""
Snapdragon AI Studio

Plugin Manager

Created by Holger Kreuzhofen
"""

import importlib
import json
from pathlib import Path

from config import PLUGINS_DIR
from engine.logging_config import get_logger
from engine.plugin_info import PluginInfo


logger = get_logger("PluginManager")


class PluginManager:

    def __init__(self, plugin_folder: str | Path = PLUGINS_DIR):
        self.plugin_folder = Path(plugin_folder)

    def scan(self) -> list[PluginInfo]:
        plugins: list[PluginInfo] = []
        if not self.plugin_folder.exists():
            return plugins

        for plugin_json in sorted(self.plugin_folder.glob("*/plugin.json")):
            try:
                data = json.loads(plugin_json.read_text(encoding="utf-8"))
                info = PluginInfo.from_json(data)
                if info.id != plugin_json.parent.name:
                    raise ValueError(
                        f"Manifest-ID '{info.id}' stimmt nicht mit Ordner "
                        f"'{plugin_json.parent.name}' überein."
                    )
                plugins.append(info)
            except Exception:
                logger.exception("Plugin-Manifest übersprungen | path=%s", plugin_json)
        return plugins

    def load_plugin(self, plugin_name: str):
        """Load one validated and enabled plugin instance."""
        manifests = {plugin.id: plugin for plugin in self.scan()}
        if plugin_name not in manifests:
            raise ValueError(f"Plugin ist nicht registriert: {plugin_name}")
        if not self._is_enabled(plugin_name):
            raise RuntimeError(f"Plugin ist deaktiviert: {plugin_name}")
        module = importlib.import_module(f"plugins.{plugin_name}.plugin")
        plugin_type = getattr(module, "Plugin", None)
        if not isinstance(plugin_type, type):
            raise TypeError(f"Plugin-Einstiegspunkt fehlt: {plugin_name}.Plugin")
        instance = plugin_type()
        if str(getattr(instance, "id", "")) != plugin_name:
            raise ValueError(f"Plugin-Instanz meldet eine abweichende ID: {plugin_name}")
        return instance

    def get_plugin_for_skill(self, skill: str):
        """
        Lädt das passende Plugin für einen Skill.
        """

        for plugin_info in self.scan():
            if skill in plugin_info.skills:
                return self.load_plugin(plugin_info.id)
        raise ValueError(f"No plugin found for skill: {skill}")

    def _is_enabled(self, plugin_name: str) -> bool:
        config_path = self.plugin_folder / "plugins_config.json"
        if not config_path.is_file():
            return True
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            return bool(data.get(plugin_name, True)) if isinstance(data, dict) else True
        except (OSError, UnicodeError, json.JSONDecodeError):
            logger.warning("Plugin-Aktivierungskonfiguration ungültig | path=%s", config_path)
            return True
