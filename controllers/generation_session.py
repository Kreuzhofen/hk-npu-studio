from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class GenerationSessionModel:
    """
    Central model serving as the Single Source of Truth for all AI image and video generations.
    Holds model configuration, prompts, resolution and sampling parameters.
    """
    prompt: str = ""
    negative_prompt: str = ""
    model_name: str = "sd_xl_base_1.0"
    width: int = 512
    height: int = 512
    steps: int = 20
    cfg_scale: float = 7.0
    seed: int = -1
    sampler: str = "Euler a"
    scheduler: str = "Normal"
    batch_size: int = 1
    output_directory: str = "output"
    output_prefix: str = "generate"

    def reset(self) -> None:
        """Reset all parameters to default values."""
        self.prompt = ""
        self.negative_prompt = ""
        self.model_name = "sd_xl_base_1.0"
        self.width = 512
        self.height = 512
        self.steps = 20
        self.cfg_scale = 7.0
        self.seed = -1
        self.sampler = "Euler a"
        self.scheduler = "Normal"
        self.batch_size = 1
        self.output_directory = "output"
        self.output_prefix = "generate"

    def update(self, **kwargs: Any) -> None:
        """Update fields dynamically."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        """Serialize session model parameters to a dict."""
        return asdict(self)
