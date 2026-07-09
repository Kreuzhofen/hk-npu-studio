from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger("SDXLSchedulerService")


class SDXLSchedulerService:
    """Small SDXL scheduler foundation for future real denoising schedulers."""

    def build_timesteps(self, steps: int, scheduler_name: str = "Normal") -> list[int]:
        step_count = max(1, int(steps or 1))
        if scheduler_name.lower() in {"karras", "exponential"}:
            values = np.geomspace(1000, 1, num=step_count)
            return [int(round(value)) for value in values]
        return [int(round(value)) for value in np.linspace(999, 0, num=step_count)]

    def build_time_ids(self, width: int, height: int) -> np.ndarray:
        # SDXL convention: original_size, crop_coords_top_left, target_size.
        values = [height, width, 0, 0, height, width]
        return np.array([values], dtype=np.float32)

    def step(self, latents: np.ndarray, predicted_latents: np.ndarray, timestep: int | float, step_index: int, total_steps: int) -> np.ndarray:
        del timestep
        denominator = max(total_steps, 1)
        strength = 1.0 / denominator
        if predicted_latents.shape != latents.shape:
            logger.warning("Scheduler step skipped because latent shapes differ: %s vs %s", predicted_latents.shape, latents.shape)
            return latents
        return latents + (predicted_latents - latents) * strength

    def describe(self, steps: int, scheduler_name: str, width: int, height: int) -> dict[str, Any]:
        timesteps = self.build_timesteps(steps, scheduler_name)
        return {
            "scheduler": scheduler_name,
            "steps": len(timesteps),
            "first_timestep": timesteps[0] if timesteps else None,
            "last_timestep": timesteps[-1] if timesteps else None,
            "time_ids_shape": list(self.build_time_ids(width, height).shape),
        }
