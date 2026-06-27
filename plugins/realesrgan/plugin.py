"""
SnapdragonAI Studio

RealESRGAN Plugin

Created by Holger Kreuzhofen
Phoenix Plugin
"""

from pathlib import Path

from engine.plugin_base import PluginBase
from engine.backends.qnn_backend import QNNBackend


class RealESRGANPlugin(PluginBase):
    id = "realesrgan"
    name = "RealESRGAN"
    skills = ["image.upscale"]

    def __init__(self):
        self.backend = QNNBackend()

    def execute(self, skill_name: str, **kwargs):
        if not self.can_handle(skill_name):
            raise ValueError(f"Skill not supported: {skill_name}")

        input_path = Path(kwargs.get("input_path", ""))

        if not input_path.exists():
            raise FileNotFoundError(input_path)

        result = self.backend.upscale(input_path)

        return {
            "status": "success",
            "plugin": self.name,
            "skill": skill_name,
            "input_path": str(input_path),
            "output_path": result["output"],
            "backend": result["backend"],
        }


# Compatibility alias for the plugin loader
Plugin = RealESRGANPlugin