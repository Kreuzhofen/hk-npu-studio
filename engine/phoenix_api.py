"""
SnapdragonAI Studio

Phoenix API

Created by Holger Kreuzhofen
Phoenix Engine
"""

from engine.plugin_manager import PluginManager


class PhoenixAPI:
    """
    Öffentliche API der Phoenix Engine.

    Diese Klasse dient als zentraler Einstiegspunkt
    für alle KI-Funktionen.
    """

    def __init__(self):
        self.plugin_manager = PluginManager()

    def run(self, skill: str, **kwargs):
        """
        Führt einen Skill über das passende Plugin aus.
        """

        if skill == "image.upscale":
            plugin = self.plugin_manager.load_plugin("realesrgan")
            return plugin.execute(skill, **kwargs)

        raise ValueError(f"Unknown skill: {skill}")