"""
Snapdragon AI Studio

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

        plugin = self.plugin_manager.get_plugin_for_skill(skill)

        return plugin.execute(skill, **kwargs)