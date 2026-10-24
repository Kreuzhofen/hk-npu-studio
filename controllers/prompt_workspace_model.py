from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptWorkspaceState:
    prompt: str = ""
    negative_prompt: str = ""
    seed: int = -1
    steps: int = 20
    cfg: float = 7.0
    width: int = 512
    height: int = 512
    selected_model: str = "sd_xl_base_1.0"
    sampler: str = "Euler a"
    scheduler: str = "Normal"
    batch_count: int = 1
    status: str = "ready"
    input_image_path: str | None = None
    controlnet_enabled: bool = False
    canny_low_threshold: int = 50
    canny_high_threshold: int = 150
    controlnet_conditioning_scale: float = 1.0
    upscale_profile: str = "off"
    phoenix_boost_enabled: bool = False


class PromptWorkspaceModel:
    """State container for the Prompt Workspace."""

    def __init__(self) -> None:
        self.state = PromptWorkspaceState()

    def update_state(self, **kwargs) -> None:
        fields = {
            "prompt": kwargs.get("prompt", self.state.prompt),
            "negative_prompt": kwargs.get("negative_prompt", self.state.negative_prompt),
            "seed": kwargs.get("seed", self.state.seed),
            "steps": kwargs.get("steps", self.state.steps),
            "cfg": kwargs.get("cfg", kwargs.get("cfg_scale", self.state.cfg)),
            "width": kwargs.get("width", self.state.width),
            "height": kwargs.get("height", self.state.height),
            "selected_model": kwargs.get(
                "selected_model", kwargs.get("model_name", self.state.selected_model)
            ),
            "sampler": kwargs.get("sampler", self.state.sampler),
            "scheduler": kwargs.get("scheduler", self.state.scheduler),
            "batch_count": kwargs.get(
                "batch_count",
                kwargs.get("batch_size", kwargs.get("batch", self.state.batch_count)),
            ),
            "status": kwargs.get("status", self.state.status),
            "input_image_path": kwargs.get(
                "input_image_path",
                kwargs.get("reference_image_path", self.state.input_image_path),
            ),
            "controlnet_enabled": kwargs.get("controlnet_enabled", self.state.controlnet_enabled),
            "canny_low_threshold": kwargs.get("canny_low_threshold", self.state.canny_low_threshold),
            "canny_high_threshold": kwargs.get("canny_high_threshold", self.state.canny_high_threshold),
            "controlnet_conditioning_scale": kwargs.get(
                "controlnet_conditioning_scale", self.state.controlnet_conditioning_scale
            ),
            "upscale_profile": kwargs.get("upscale_profile", self.state.upscale_profile),
            "phoenix_boost_enabled": kwargs.get(
                "phoenix_boost_enabled", self.state.phoenix_boost_enabled
            ),
        }
        self.state = PromptWorkspaceState(**fields)
