"""
Snapdragon AI Studio

Phoenix Adapter

Created by Holger Kreuzhofen
Phoenix Engine
"""

from engine.phoenix_core import PhoenixCore


class PhoenixAdapter:
    """
    Adapter zwischen GUI und Phoenix Engine.
    """

    def __init__(self):
        self.core = PhoenixCore()

    def run(self, skill: str, **kwargs):
        """
        Führt einen Skill über die Phoenix Engine aus.
        """

        return self.core.run(skill, **kwargs)