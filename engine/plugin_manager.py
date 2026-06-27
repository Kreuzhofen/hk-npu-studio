"""
SnapdragonAI Studio

Plugin Manager

Created by Holger Kreuzhofen
"""

import importlib
import json
from pathlib import Path

from engine.plugin_info import PluginInfo


class PluginManager:

    def __init__(self):
        self.plugin_folder = Path("plugins")

    def scan(self):

        plugins: list[PluginInfo] = []

        if not self.plugin_folder.exists():
            return plugins

        for plugin_json in self.plugin_folder.glob("*/plugin.json"):

            try:

                with open(plugin_json, "r", encoding="utf-8") as f:

                    data = json.load(f)

                plugins.append(
                    PluginInfo.from_json(data)
                )

            except Exception as e:
                print(e)

        return plugins

    def load_plugin(self, plugin_name: str):
        """
        Lädt eine Plugin-Instanz.
        """

        module = importlib.import_module(
            f"plugins.{plugin_name}.plugin"
        )

        return module.Plugin()

    def get_plugin_for_skill(self, skill: str):
        """
        Lädt das passende Plugin für einen Skill.
        """

        for plugin_info in self.scan():

            if skill in plugin_info.skills:
                return self.load_plugin(plugin_info.id)

        raise ValueError(f"No plugin found for skill: {skill}")