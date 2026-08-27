"""
HK NPU STUDIO

Skill Manager

Created by Holger Kreuzhofen
Phoenix Engine
"""

import importlib

from engine.skill_registry import SkillRegistry


class SkillManager:
    def __init__(self):
        self.registry = SkillRegistry()

    def get_plugin_for_skill(self, skill_name: str):
        plugins = self.registry.find_plugins_for_skill(skill_name)

        if not plugins:
            return None

        return plugins[0]

    def has_skill(self, skill_name: str) -> bool:
        return self.get_plugin_for_skill(skill_name) is not None

    def list_skills(self):
        return list(self.registry.get_skills().keys())

    def execute(self, skill_name: str, **kwargs):
        plugin_info = self.get_plugin_for_skill(skill_name)

        if plugin_info is None:
            raise ValueError(f"No plugin found for skill: {skill_name}")

        module_name = f"plugins.{plugin_info.id}.plugin"
        module = importlib.import_module(module_name)

        plugin_class = getattr(module, "Plugin")
        plugin = plugin_class()

        if not plugin.can_handle(skill_name):
            raise ValueError(f"Plugin cannot handle skill: {skill_name}")

        return plugin.execute(skill_name, **kwargs)