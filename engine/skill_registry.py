"""
HK NPU STUDIO

Skill Registry

Created by Holger Kreuzhofen
Phoenix Engine
"""

from engine.plugin_manager import PluginManager


class SkillRegistry:
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.skills = {}

    def build(self):
        self.skills = {}

        for plugin in self.plugin_manager.scan():
            for skill in plugin.skills:
                if skill not in self.skills:
                    self.skills[skill] = []

                self.skills[skill].append(plugin)

        return self.skills

    def get_skills(self):
        if not self.skills:
            self.build()

        return self.skills

    def find_plugins_for_skill(self, skill_name):
        if not self.skills:
            self.build()

        return self.skills.get(skill_name, [])