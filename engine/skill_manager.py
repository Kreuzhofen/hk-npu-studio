"""
SnapdragonAI Studio

Skill Manager

Created by Holger Kreuzhofen
Phoenix Engine
"""

from engine.skill_registry import SkillRegistry


class SkillManager:

    def __init__(self):
        self.registry = SkillRegistry()

    def get_plugin_for_skill(self, skill_name: str):

        plugins = self.registry.find_plugins_for_skill(skill_name)

        if not plugins:
            return None

        # Später können wir hier Prioritäten,
        # Benchmarks oder Benutzereinstellungen berücksichtigen.
        return plugins[0]

    def has_skill(self, skill_name: str) -> bool:
        return self.get_plugin_for_skill(skill_name) is not None

    def list_skills(self):
        return list(self.registry.get_skills().keys())