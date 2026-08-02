from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class PresetManager:
    """Manages creation, loading, saving and deletion of parameter presets."""

    def __init__(self, preset_dir: str | Path = "C:/SnapdragonAI/presets") -> None:
        self.preset_dir = Path(preset_dir)
        self.preset_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_default_presets()

    def _ensure_default_presets(self) -> None:
        """Ensures standard default, cyberpunk, and photorealistic presets exist on disk."""
        default_preset = {
            "name": "Default",
            "prompt": "A beautiful landscape photography",
            "negative_prompt": "ugly, blurry, distorted, low quality",
            "model_name": "Qualcomm Stable Diffusion 1.5 (HTP V73)",
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7.5,
            "sampler": "Euler",
            "scheduler": "Euler",
            "controlnet_enabled": False,
            "canny_low_threshold": 50,
            "canny_high_threshold": 150,
            "controlnet_conditioning_scale": 1.0,
            "reference_image_path": ""
        }
        if not (self.preset_dir / "default.json").exists():
            self.save_preset("Default", default_preset)

        cyberpunk_preset = {
            "name": "Cyberpunk",
            "prompt": "Cyberpunk city street, neon glowing signs, futuristic cars, rain, high detail",
            "negative_prompt": "daylight, natural, old, rustic, low quality",
            "model_name": "Qualcomm Stable Diffusion 1.5 (HTP V73)",
            "width": 512,
            "height": 512,
            "steps": 25,
            "cfg_scale": 8.0,
            "sampler": "Euler",
            "scheduler": "Euler",
            "controlnet_enabled": False,
            "canny_low_threshold": 50,
            "canny_high_threshold": 150,
            "controlnet_conditioning_scale": 1.0,
            "reference_image_path": ""
        }
        if not (self.preset_dir / "cyberpunk.json").exists():
            self.save_preset("Cyberpunk", cyberpunk_preset)

        photorealistic_preset = {
            "name": "Photorealistic",
            "prompt": "Portrait of an astronaut in space, hyperrealistic, 8k resolution, cinematic lighting",
            "negative_prompt": "cartoon, 3d render, illustration, ugly, bad anatomy",
            "model_name": "Qualcomm Stable Diffusion 1.5 (HTP V73)",
            "width": 512,
            "height": 512,
            "steps": 30,
            "cfg_scale": 7.0,
            "sampler": "Euler",
            "scheduler": "Euler",
            "controlnet_enabled": False,
            "canny_low_threshold": 50,
            "canny_high_threshold": 150,
            "controlnet_conditioning_scale": 1.0,
            "reference_image_path": ""
        }
        if not (self.preset_dir / "photorealistic.json").exists():
            self.save_preset("Photorealistic", photorealistic_preset)

    def list_presets(self) -> list[str]:
        """Returns a list of preset names (keys, without suffix)."""
        presets = []
        if self.preset_dir.exists():
            for p in self.preset_dir.glob("*.json"):
                presets.append(p.stem)
        return sorted(presets)

    def get_preset(self, name: str) -> dict[str, Any] | None:
        """Loads a preset by its file-name (stem)."""
        file_path = self.preset_dir / f"{name}.json"
        if file_path.is_file():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    @staticmethod
    def preset_key(name: str) -> str:
        """Return the normalized file key used for a preset display name."""
        safe_name = "".join(
            c for c in name if c.isalnum() or c in (" ", "_", "-")
        ).strip()
        return safe_name.lower().replace(" ", "_")

    def preset_exists(self, name: str) -> bool:
        """Return whether a preset with this normalized display name exists."""
        key = self.preset_key(name)
        return bool(key and (self.preset_dir / f"{key}.json").is_file())

    def save_preset(self, name: str, data: dict[str, Any]) -> bool:
        """Saves a preset under a given display name."""
        safe_name = "".join([c for c in name if c.isalnum() or c in (" ", "_", "-")]).strip()
        if not safe_name:
            return False

        filename = self.preset_key(safe_name)
        file_path = self.preset_dir / f"{filename}.json"

        preset_data = dict(data)
        preset_data["name"] = safe_name

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def delete_preset(self, name: str) -> bool:
        """Deletes a preset by its name."""
        file_path = self.preset_dir / f"{name}.json"
        if file_path.is_file():
            try:
                file_path.unlink()
                return True
            except Exception:
                pass
        return False
