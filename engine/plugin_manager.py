import json
from pathlib import Path


class PluginManager:
    def __init__(self):
        self.plugin_folder = Path("plugins")

    def scan(self):
        plugins = []

        if not self.plugin_folder.exists():
            return plugins

        for plugin_json in self.plugin_folder.glob("*/plugin.json"):
            try:
                with open(plugin_json, "r", encoding="utf-8") as f:
                    plugins.append(json.load(f))
            except Exception as e:
                print(e)

        return plugins