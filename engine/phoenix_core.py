"""
HK NPU STUDIO

Phoenix Core

Created by Holger Kreuzhofen
Phoenix Engine
"""

from engine.hardware_manager import HardwareManager
from engine.plugin_manager import PluginManager
from engine.skill_registry import SkillRegistry
from engine.skill_manager import SkillManager
from engine.system_manager import SystemManager
from engine.phoenix_api import PhoenixAPI


class PhoenixCore:
    """
    Zentrale Schnittstelle zur Phoenix Engine.
    """

    def __init__(self):
        self.hardware = HardwareManager()
        self.plugins = PluginManager()
        self.registry = SkillRegistry()
        self.skills = SkillManager()
        self.api = PhoenixAPI()

        self.system = SystemManager(
            hardware=self.hardware,
            plugins=self.plugins,
            skills=self.skills,
        )

    def run(self, skill: str, **kwargs):
        """
        Führt einen Skill über die PhoenixAPI aus.
        """

        return self.api.run(skill, **kwargs)