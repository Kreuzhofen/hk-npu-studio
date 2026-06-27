"""
SnapdragonAI Studio

RealESRGAN Plugin

Created by Holger Kreuzhofen
Phoenix Plugin
"""

from pathlib import Path

from engine.plugin_base import PluginBase


class RealESRGANPlugin(PluginBase):
    id = "realesrgan"
    name = "RealESRGAN"
    skills = ["image.upscale"]

    def execute(self, skill_name: str, **kwargs):
        if not self.can_handle(skill_name):
            raise ValueError(f"Skill not supported: {skill_name}")

        input_path = Path(kwargs.get("input_path", ""))

        if not input_path.exists():
            raise FileNotFoundError(input_path)

        return {
            "status": "prepared",
            "plugin": self.name,
            "skill": skill_name,
            "input_path": str(input_path),
            "message": "RealESRGAN Phoenix Plugin Runtime ist erreichbar."
        }
# Compatibility alias for the plugin loader
Plugin = RealESRGANPlugin