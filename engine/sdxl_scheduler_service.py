from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from engine.logging_config import get_logger

logger = get_logger("SDXLSchedulerService")


class SDXLSchedulerService:
    """
    NumPy implementation of the Diffusers EulerDiscreteScheduler core used by
    SDXL. It reads the model's scheduler_config.json and provides the exact
    operations needed by this project's CPU ONNX denoising loop.
    """

    DEFAULT_TRAIN_TIMESTEPS = 1000

    def __init__(self, scheduler_path: str | Path | None = None) -> None:
        self.config = self._load_config(scheduler_path)

        self.train_timesteps = int(
            self.config.get("num_train_timesteps", self.DEFAULT_TRAIN_TIMESTEPS)
        )
        self.beta_start = float(self.config.get("beta_start", 0.0001))
        self.beta_end = float(self.config.get("beta_end", 0.02))
        self.beta_schedule = str(self.config.get("beta_schedule", "linear"))
        self.timestep_spacing = str(self.config.get("timestep_spacing", "linspace"))
        self.steps_offset = int(self.config.get("steps_offset", 0) or 0)
        self.prediction_type = str(self.config.get("prediction_type", "epsilon"))
        self.interpolation_type = str(self.config.get("interpolation_type", "linear"))
        self.final_sigmas_type = str(self.config.get("final_sigmas_type", "zero"))
        self.scheduler_class = str(
            self.config.get("_class_name", "EulerDiscreteScheduler")
        )

        if self.scheduler_class != "EulerDiscreteScheduler":
            raise ValueError(
                f"Unsupported scheduler class: {self.scheduler_class}. "
                "Expected EulerDiscreteScheduler."
            )

        self.betas = self._build_betas()
        self.alphas = np.float32(1.0) - self.betas
        self.alphas_cumprod = np.cumprod(
            self.alphas, axis=0, dtype=np.float32
        )
        self.training_sigmas = np.sqrt(
            (np.float32(1.0) - self.alphas_cumprod) / self.alphas_cumprod
        ).astype(np.float32)

        self.timesteps = np.array([], dtype=np.float32)
        self.sigmas = np.array([], dtype=np.float32)
        self._step_index: int | None = None

    def _load_config(self, scheduler_path: str | Path | None) -> dict[str, Any]:
        if not scheduler_path:
            logger.warning(
                "[SCHEDULER] No scheduler path supplied; using Euler defaults."
            )
            return {}

        path = Path(scheduler_path)
        config_path = path / "scheduler_config.json" if path.is_dir() else path

        if not config_path.exists():
            logger.warning(
                "[SCHEDULER] scheduler_config.json not found at %s; using defaults.",
                config_path,
            )
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as handle:
                config = json.load(handle)
            logger.info("[SCHEDULER] Loaded configuration from %s", config_path)
            return config
        except Exception as exc:
            raise RuntimeError(
                f"Scheduler configuration could not be read: {config_path}: {exc}"
            ) from exc

    def _build_betas(self) -> np.ndarray:
        if self.beta_schedule == "linear":
            return np.linspace(
                self.beta_start,
                self.beta_end,
                self.train_timesteps,
                dtype=np.float32,
            )

        if self.beta_schedule == "scaled_linear":
            return np.linspace(
                np.float32(np.sqrt(self.beta_start)),
                np.float32(np.sqrt(self.beta_end)),
                self.train_timesteps,
                dtype=np.float32,
            ) ** np.float32(2.0)

        raise NotImplementedError(
            f"Unsupported beta_schedule: {self.beta_schedule}"
        )

    def build_timesteps(
        self,
        steps: int,
        scheduler_name: str = "Normal",
    ) -> list[int]:
        step_count = max(1, int(steps or 1))

        if self.timestep_spacing == "linspace":
            values = np.linspace(
                0,
                self.train_timesteps - 1,
                step_count,
                dtype=np.float32,
            )[::-1].copy()

        elif self.timestep_spacing == "leading":
            step_ratio = self.train_timesteps // step_count
            values = (
                (np.arange(0, step_count) * step_ratio)
                .round()[::-1]
                .copy()
                .astype(np.float32)
            )
            values += self.steps_offset

        elif self.timestep_spacing == "trailing":
            step_ratio = self.train_timesteps / step_count
            values = (
                np.arange(self.train_timesteps, 0, -step_ratio)
                .round()
                .copy()
                .astype(np.float32)
            )
            values -= 1

        else:
            raise ValueError(
                f"Unsupported timestep_spacing: {self.timestep_spacing}"
            )

        values = np.clip(values, 0, self.train_timesteps - 1)
        self.prepare_timesteps(values.tolist())

        result = [int(round(value)) for value in values]
        logger.info(
            "[SCHEDULER] Euler schedule prepared | steps=%d | timesteps=%s | "
            "sigmas=%s | init_noise_sigma=%.8f",
            step_count,
            result,
            [round(float(value), 8) for value in self.sigmas],
            self.init_noise_sigma,
        )
        return result

    def prepare_timesteps(self, timesteps: list[int | float]) -> None:
        """
        Prepare Euler sigmas for an externally supplied timestep list.

        This is required because OnnxImageBackend builds the timestep list with
        one scheduler instance while UNetService owns the instance that performs
        scale_model_input() and step().
        """
        values = np.asarray(timesteps, dtype=np.float32)
        if values.size == 0:
            raise ValueError("At least one scheduler timestep is required.")

        if self.interpolation_type != "linear":
            raise NotImplementedError(
                f"Unsupported interpolation_type: {self.interpolation_type}"
            )

        inference_sigmas = np.interp(
            values.astype(np.float64),
            np.arange(self.train_timesteps, dtype=np.float64),
            self.training_sigmas,
        )

        if self.final_sigmas_type == "zero":
            final_sigma = 0.0
        elif self.final_sigmas_type == "sigma_min":
            final_sigma = float(self.training_sigmas[0])
        else:
            raise ValueError(
                f"Unsupported final_sigmas_type: {self.final_sigmas_type}"
            )

        self.timesteps = values
        self.sigmas = np.concatenate(
            [inference_sigmas, np.array([final_sigma], dtype=np.float64)]
        ).astype(np.float32)
        self._step_index = None

    def _index_for_timestep(self, timestep: int | float) -> int:
        indices = np.nonzero(self.timesteps == np.float32(timestep))[0]
        if indices.size == 0:
            raise ValueError(f"Timestep {timestep} is not in the scheduler schedule.")
        return int(indices[1] if indices.size > 1 else indices[0])

    def _init_step_index(self, timestep: int | float) -> None:
        if self._step_index is None:
            self._step_index = self._index_for_timestep(timestep)

    @property
    def init_noise_sigma(self) -> float:
        if self.sigmas.size:
            max_sigma = np.max(self.sigmas)
        else:
            max_sigma = np.max(self.training_sigmas)

        if self.timestep_spacing in {"linspace", "trailing"}:
            return float(max_sigma)

        return float(
            np.sqrt(max_sigma * max_sigma + np.float32(1.0))
        )

    def scale_initial_noise(self, latents: np.ndarray) -> np.ndarray:
        return (
            np.asarray(latents, dtype=np.float32)
            * np.float32(self.init_noise_sigma)
        ).astype(np.float32)

    def scale_model_input(
        self,
        sample: np.ndarray,
        timestep: int | float,
    ) -> np.ndarray:
        if self.sigmas.size == 0:
            raise RuntimeError(
                "Scheduler timesteps were not prepared before scale_model_input()."
            )
        self._init_step_index(timestep)
        assert self._step_index is not None
        if self._step_index >= len(self.sigmas) - 1:
            raise IndexError("Scheduler step index is outside the sigma schedule.")

        sigma = np.float32(self.sigmas[self._step_index])
        scale = np.sqrt(sigma * sigma + np.float32(1.0))
        return (
            np.asarray(sample, dtype=np.float32) / np.float32(scale)
        ).astype(np.float32)

    def step(
        self,
        latents: np.ndarray,
        noise_pred: np.ndarray,
        timestep: int | float,
        next_timestep: int | float | None = None,
    ) -> np.ndarray:
        if noise_pred.shape != latents.shape:
            raise ValueError(
                "Scheduler cannot update latents because shapes differ: "
                f"{noise_pred.shape} vs {latents.shape}"
            )
        if self.sigmas.size == 0:
            raise RuntimeError("Scheduler timesteps were not prepared before step().")
        self._init_step_index(timestep)
        assert self._step_index is not None
        if self._step_index >= len(self.sigmas) - 1:
            raise IndexError("Scheduler step index is outside the sigma schedule.")

        sample = np.asarray(latents, dtype=np.float32)
        model_output = np.asarray(noise_pred, dtype=np.float32)

        sigma = np.float32(self.sigmas[self._step_index])
        sigma_next = np.float32(self.sigmas[self._step_index + 1])

        if self.prediction_type in {"sample", "original_sample"}:
            pred_original_sample = model_output
        elif self.prediction_type == "epsilon":
            pred_original_sample = sample - sigma * model_output
        elif self.prediction_type == "v_prediction":
            denominator = np.float32(np.sqrt(float(sigma * sigma + 1.0)))
            pred_original_sample = (
                model_output * (-sigma / denominator)
                + sample / (sigma * sigma + np.float32(1.0))
            )
        else:
            raise ValueError(
                f"Unsupported prediction_type: {self.prediction_type}"
            )

        if float(sigma) == 0.0:
            derivative = np.zeros_like(sample, dtype=np.float32)
        else:
            derivative = (sample - pred_original_sample) / sigma

        dt = sigma_next - sigma
        previous_sample = sample + derivative * dt
        self._step_index += 1

        return previous_sample.astype(np.float32)

    def combine_classifier_free_guidance(
        self,
        positive_noise: np.ndarray,
        negative_noise: np.ndarray | None,
        guidance_scale: float,
    ) -> np.ndarray:
        if (
            negative_noise is None
            or negative_noise.shape != positive_noise.shape
            or guidance_scale == 1.0
        ):
            return positive_noise.astype(np.float32)

        guided = negative_noise + float(guidance_scale) * (
            positive_noise - negative_noise
        )
        return guided.astype(np.float32)

    def build_time_ids(self, width: int, height: int) -> np.ndarray:
        values = [height, width, 0, 0, height, width]
        return np.array([values], dtype=np.float32)

    def timestep_to_sigma(self, timestep: int | float) -> float:
        return float(
            np.interp(
                float(timestep),
                np.arange(self.train_timesteps, dtype=np.float64),
                self.training_sigmas,
            )
        )

    def describe(
        self,
        steps: int,
        scheduler_name: str,
        width: int,
        height: int,
        guidance_scale: float | None = None,
    ) -> dict[str, Any]:
        timesteps = self.build_timesteps(steps, scheduler_name)
        return {
            "scheduler": scheduler_name,
            "scheduler_class": self.scheduler_class,
            "prediction_type": self.prediction_type,
            "beta_schedule": self.beta_schedule,
            "beta_start": self.beta_start,
            "beta_end": self.beta_end,
            "timestep_spacing": self.timestep_spacing,
            "steps_offset": self.steps_offset,
            "train_timesteps": self.train_timesteps,
            "steps": len(timesteps),
            "timesteps": timesteps,
            "sigmas": [float(value) for value in self.sigmas],
            "initial_noise_sigma": self.init_noise_sigma,
            "first_timestep": timesteps[0] if timesteps else None,
            "last_timestep": timesteps[-1] if timesteps else None,
            "time_ids_shape": list(self.build_time_ids(width, height).shape),
            "guidance_scale": guidance_scale,
        }
