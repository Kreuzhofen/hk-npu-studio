"""
HK NPU STUDIO

Plugin Base

Created by Holger Kreuzhofen
Phoenix Engine
"""


class PluginBase:
    id = ""
    name = ""
    skills = []

    def can_handle(self, skill_name: str) -> bool:
        return skill_name in self.skills

    def execute(self, skill_name: str, **kwargs):
        raise NotImplementedError("Plugin must implement execute().")