from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger("SDXLSchedulerService")


class SDXLSchedulerService:
    """SDXL scheduler core foundation with deterministic timestep and latent updates."""

    DEFAULT_TRAIN_TIMESTEPS = 1000

    def build_timesteps(self, steps: int, scheduler_name: str = "Normal") -> list[int]:
        step_count = max(1, int(steps or 1))
        name = (scheduler_name or "Normal").lower()
        if name == "karras":
            ramp = np.linspace(0.0, 1.0, step_count)
            values = (1.0 - ramp**2) * (self.DEFAULT_TRAIN_TIMESTEPS - 1)
        elif name == "exponential":
            values = np.geomspace(self.DEFAULT_TRAIN_TIMESTEPS, 1, num=step_count) - 1
        elif name in {"sgm uniform", "sgm_uniform"}:
            values = np.linspace(self.DEFAULT_TRAIN_TIMESTEPS - 1, 0, num=step_count)
        else:
            values = np.linspace(self.DEFAULT_TRAIN_TIMESTEPS - 1, 0, num=step_count)
        return [max(0, min(self.DEFAULT_TRAIN_TIMESTEPS - 1, int(round(value)))) for value in values]

    def build_time_ids(self, width: int, height: int) -> np.ndarray:
        values = [height, width, 0, 0, height, width]
        return np.array([values], dtype=np.float32)

    def timestep_to_sigma(self, timestep: int | float) -> float:
        normalized = max(0.0, min(1.0, float(timestep) / float(self.DEFAULT_TRAIN_TIMESTEPS - 1)))
        return normalized

    def step(
        self,
        latents: np.ndarray,
        noise_pred: np.ndarray,
        timestep: int | float,
        next_timestep: int | float | None,
    ) -> np.ndarray:
        if noise_pred.shape != latents.shape:
            logger.warning("Scheduler step skipped because latent shapes differ: %s vs %s", noise_pred.shape, latents.shape)
            return latents.astype(np.float32)

        sigma = self.timestep_to_sigma(timestep)
        next_sigma = self.timestep_to_sigma(next_timestep if next_timestep is not None else 0)
        step_size = max(sigma - next_sigma, 1.0 / self.DEFAULT_TRAIN_TIMESTEPS)
        updated = latents - noise_pred * step_size
        return updated.astype(np.float32)

    def combine_classifier_free_guidance(
        self,
        positive_noise: np.ndarray,
        negative_noise: np.ndarray | None,
        guidance_scale: float,
    ) -> np.ndarray:
        if negative_noise is None or negative_noise.shape != positive_noise.shape or guidance_scale == 1.0:
            return positive_noise.astype(np.float32)
        guided = negative_noise + float(guidance_scale) * (positive_noise - negative_noise)
        return guided.astype(np.float32)

    def describe(self, steps: int, scheduler_name: str, width: int, height: int, guidance_scale: float | None = None) -> dict[str, Any]:
        timesteps = self.build_timesteps(steps, scheduler_name)
        sigmas = [self.timestep_to_sigma(timestep) for timestep in timesteps]
        return {
            "scheduler": scheduler_name,
            "steps": len(timesteps),
            "timesteps": timesteps,
            "sigmas": sigmas,
            "first_timestep": timesteps[0] if timesteps else None,
            "last_timestep": timesteps[-1] if timesteps else None,
            "time_ids_shape": list(self.build_time_ids(width, height).shape),
            "guidance_scale": guidance_scale,
        }
