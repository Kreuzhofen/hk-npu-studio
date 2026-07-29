from __future__ import annotations

import json
import logging
from engine.logging_config import get_logger
from pathlib import Path
from typing import Any

import numpy as np

logger = get_logger("SDXLSchedulerService")


class SDXLSchedulerService:
    """SDXL scheduler core foundation aligned with local Euler scheduler metadata."""

    DEFAULT_TRAIN_TIMESTEPS = 1000

    def __init__(self, scheduler_path: str | Path | None = None) -> None:
        self.config = self._load_config(scheduler_path)
        self.train_timesteps = int(self.config.get("num_train_timesteps", self.DEFAULT_TRAIN_TIMESTEPS))
        self.timestep_spacing = str(self.config.get("timestep_spacing", "leading"))
        self.steps_offset = int(self.config.get("steps_offset", 0) or 0)
        self.prediction_type = str(self.config.get("prediction_type", "epsilon"))
        self.scheduler_class = str(self.config.get("_class_name", "EulerDiscreteScheduler"))

    def _load_config(self, scheduler_path: str | Path | None) -> dict[str, Any]:
        if not scheduler_path:
            return {}
        path = Path(scheduler_path)
        config_path = path / "scheduler_config.json" if path.is_dir() else path
        if not config_path.exists():
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception as exc:
            logger.warning("Failed to read scheduler config %s: %s", config_path, exc)
            return {}

    def build_timesteps(self, steps: int, scheduler_name: str = "Normal") -> list[int]:
        step_count = max(1, int(steps or 1))
        name = (scheduler_name or self.scheduler_class or "Normal").lower()
        max_timestep = max(0, self.train_timesteps - 1)

        if name == "karras" or bool(self.config.get("use_karras_sigmas", False)):
            ramp = np.linspace(0.0, 1.0, step_count)
            values = (1.0 - ramp**2) * max_timestep
        elif name == "exponential" or bool(self.config.get("use_exponential_sigmas", False)):
            values = np.geomspace(max(self.train_timesteps, 1), 1, num=step_count) - 1
        else:
            if self.timestep_spacing == "trailing":
                values = np.linspace(max_timestep, 0, num=step_count, endpoint=False)
            else:
                values = np.linspace(max_timestep, 0, num=step_count)

        values = values + self.steps_offset
        return [max(0, min(max_timestep, int(round(value)))) for value in values]

    def build_time_ids(self, width: int, height: int) -> np.ndarray:
        values = [height, width, 0, 0, height, width]
        return np.array([values], dtype=np.float32)

    def timestep_to_sigma(self, timestep: int | float) -> float:
        denominator = max(1, self.train_timesteps - 1)
        normalized = max(0.0, min(1.0, float(timestep) / float(denominator)))
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
        step_size = max(sigma - next_sigma, 1.0 / max(1, self.train_timesteps))
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
            "scheduler_class": self.scheduler_class,
            "prediction_type": self.prediction_type,
            "timestep_spacing": self.timestep_spacing,
            "steps_offset": self.steps_offset,
            "train_timesteps": self.train_timesteps,
            "steps": len(timesteps),
            "timesteps": timesteps,
            "sigmas": sigmas,
            "first_timestep": timesteps[0] if timesteps else None,
            "last_timestep": timesteps[-1] if timesteps else None,
            "time_ids_shape": list(self.build_time_ids(width, height).shape),
            "guidance_scale": guidance_scale,
        }
