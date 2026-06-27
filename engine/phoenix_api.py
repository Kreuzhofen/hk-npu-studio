"""
SnapdragonAI Studio

Phoenix API

Created by Holger Kreuzhofen
Phoenix Engine
"""

from plugins.realesrgan.plugin import RealESRGANPlugin


class PhoenixAPI:
    """
    Öffentliche API der Phoenix Engine.

    Diese Klasse dient als zentraler Einstiegspunkt
    für alle KI-Funktionen.
    """

    def __init__(self):
        self.realesrgan = RealESRGANPlugin()

    def run(self, skill: str, **kwargs):
        """
        Führt einen Skill über das passende Plugin aus.
        """

        if skill == "image.upscale":
            return self.realesrgan.execute(skill, **kwargs)

        raise ValueError(f"Unknown skill: {skill}")