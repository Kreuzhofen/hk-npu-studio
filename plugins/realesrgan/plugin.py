"""
Snapdragon AI Studio

RealESRGAN Plugin

Created by Holger Kreuzhofen
Phoenix Plugin
"""

from pathlib import Path

from engine.plugin_base import PluginBase
from modules.realesrgan_core import upscale_tiled


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

        output_path = upscale_tiled(input_path)

        return {
            "status": "success",
            "plugin": self.name,
            "skill": skill_name,
            "input_path": str(input_path),
            "output_path": str(output_path),
            "backend": "QNN",
        }


# Compatibility alias for the plugin loader
Plugin = RealESRGANPlugin
