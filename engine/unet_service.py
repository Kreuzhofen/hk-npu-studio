from __future__ import annotations

import logging
from engine.logging_config import get_logger
from pathlib import Path
from typing import Any

import numpy as np

from engine.model_runtime_package import ModelRuntimePackage
from engine.onnx_component_inspector import OnnxComponentInspector
from engine.onnx_provider_service import OnnxProviderService
from engine.sdxl_scheduler_service import SDXLSchedulerService

logger = get_logger("UNetService")


class UNetService:
    """Model-independent UNet wrapper with SDXL scheduler and CFG core."""

    def __init__(self, package: ModelRuntimePackage) -> None:
        self.package = package
        self.scheduler = SDXLSchedulerService()

    def generate_initial_latents(self, width: int, height: int, seed: int = -1) -> np.ndarray:
        latent_h = max(1, (height if height > 0 else 512) // 8)
        latent_w = max(1, (width if width > 0 else 512) // 8)
        if seed >= 0:
            np.random.seed(seed)
        latents = np.random.randn(1, 4, latent_h, latent_w).astype(np.float32)
        logger.info(f"[UNetService] Generated initial random latents with shape: {latents.shape}")
        return latents

    def predict_noise(
        self,
        latents: np.ndarray,
        timestep: int | float,
        encoder_hidden_states: np.ndarray,
        additional_inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        unet_path = self.package.get_component_path("unet")
        metadata = OnnxComponentInspector.inspect("unet", unet_path)
        logger.info(f"[UNetService] Resolving UNet component from: '{unet_path}'")

        if self.package.is_fully_ready() and unet_path and Path(unet_path).exists():
            session = None
            try:
                logger.info(f"[UNetService] Loading UNet InferenceSession for: '{unet_path}'")
                print(f"[UNetService] Loading UNet InferenceSession for: '{unet_path}'")
                session = OnnxProviderService.create_session(unet_path, "unet")
                inputs = self._build_unet_inputs(session, latents, timestep, encoder_hidden_states, additional_inputs or {})
                logger.info(f"[UNetService] UNet mapped inputs: {list(inputs.keys())}")
                print(f"[UNetService] UNet mapped inputs: {list(inputs.keys())}")
                outputs = session.run(None, inputs)
                output_noise = self._normalize_noise_output(np.asarray(outputs[0]), latents)
                logger.info(f"[UNetService] UNet ONNX run successful. Output shape: {output_noise.shape}")
                print(f"[UNetService] UNet ONNX run successful. Output shape: {output_noise.shape}")
                metadata["session_providers"] = OnnxProviderService.session_providers(session)
                return {
                    "noise_pred": output_noise,
                    "latent_shape": list(latents.shape),
                    "noise_shape": list(output_noise.shape),
                    "is_mock": False,
                    "metadata": metadata,
                }
            except Exception as exc:
                logger.warning(f"[UNetService] UNet InferenceSession run failed/skipped: {exc}")
                print(f"[UNetService] UNet InferenceSession run failed/skipped: {exc}")
            finally:
                OnnxProviderService.release_session(session)
                session = None

        mock_noise = np.random.randn(*latents.shape).astype(np.float32)
        logger.info(f"[UNetService] Generated mock UNet noise prediction with shape: {mock_noise.shape}")
        print(f"[UNetService] Generated mock UNet noise prediction with shape: {mock_noise.shape}")
        return {
            "noise_pred": mock_noise,
            "latent_shape": list(latents.shape),
            "noise_shape": list(mock_noise.shape),
            "is_mock": True,
            "metadata": metadata,
        }

    def run_denoising_loop(
        self,
        latents: np.ndarray,
        timesteps: list[int],
        prompt_embeddings: np.ndarray,
        pooled_prompt_embeddings: np.ndarray | None = None,
        time_ids: np.ndarray | None = None,
        negative_embeddings: np.ndarray | None = None,
        negative_pooled_embeddings: np.ndarray | None = None,
        guidance_scale: float = 7.0,
    ) -> dict[str, Any]:
        current = latents.astype(np.float32)
        any_mock = False
        last_result: dict[str, Any] | None = None
        step_records: list[dict[str, Any]] = []
        guidance_enabled = bool(negative_embeddings is not None and guidance_scale != 1.0)

        for index, timestep in enumerate(timesteps):
            next_timestep = timesteps[index + 1] if index + 1 < len(timesteps) else None
            positive_inputs = {
                "text_embeds": pooled_prompt_embeddings,
                "time_ids": time_ids,
                "pooled_prompt_embeds": pooled_prompt_embeddings,
            }
            positive_result = self.predict_noise(current, timestep, prompt_embeddings, positive_inputs)
            positive_noise = positive_result["noise_pred"]
            negative_noise = None
            negative_result: dict[str, Any] | None = None

            if guidance_enabled:
                negative_inputs = {
                    "text_embeds": negative_pooled_embeddings,
                    "time_ids": time_ids,
                    "pooled_prompt_embeds": negative_pooled_embeddings,
                }
                negative_result = self.predict_noise(current, timestep, negative_embeddings, negative_inputs)
                negative_noise = negative_result["noise_pred"]

            guided_noise = self.scheduler.combine_classifier_free_guidance(
                positive_noise,
                negative_noise,
                guidance_scale,
            )
            current = self.scheduler.step(current, guided_noise, timestep, next_timestep)
            any_mock = any_mock or bool(positive_result.get("is_mock")) or bool(negative_result and negative_result.get("is_mock"))
            last_result = positive_result
            step_records.append({
                "index": index,
                "timestep": timestep,
                "next_timestep": next_timestep,
                "positive_noise_shape": list(positive_noise.shape),
                "negative_noise_shape": list(negative_noise.shape) if negative_noise is not None else None,
                "guided_noise_shape": list(guided_noise.shape),
                "latent_shape": list(current.shape),
                "guidance_applied": bool(guidance_enabled and negative_noise is not None),
                "mock_step": bool(positive_result.get("is_mock")) or bool(negative_result and negative_result.get("is_mock")),
            })

        return {
            "latents": current.astype(np.float32),
            "latent_shape": list(current.shape),
            "is_mock": any_mock,
            "timesteps": timesteps,
            "step_count": len(step_records),
            "step_records": step_records,
            "guidance_prepared": guidance_enabled,
            "guidance_applied": any(record["guidance_applied"] for record in step_records),
            "guidance_scale": float(guidance_scale),
            "last_unet_metadata": last_result.get("metadata") if last_result else {},
        }

    def _build_unet_inputs(
        self,
        session: Any,
        latents: np.ndarray,
        timestep: int | float,
        encoder_hidden_states: np.ndarray,
        additional_inputs: dict[str, Any],
    ) -> dict[str, np.ndarray]:
        inputs: dict[str, np.ndarray] = {}
        for item in session.get_inputs():
            name = item.name
            lowered = name.lower()
            if lowered in additional_inputs and additional_inputs[lowered] is not None:
                inputs[name] = np.asarray(additional_inputs[lowered]).astype(np.float32)
            elif "sample" in lowered or "latent" in lowered:
                inputs[name] = latents.astype(np.float32)
            elif "timestep" in lowered or lowered in {"t", "time"}:
                if item.shape == []:
                    inputs[name] = np.array(float(timestep), dtype=np.float32)
                else:
                    inputs[name] = np.array([timestep], dtype=np.float32)
            elif "encoder_hidden" in lowered or "hidden_states" in lowered or "encoder" in lowered:
                inputs[name] = encoder_hidden_states.astype(np.float32)
            elif "text_embeds" in lowered or "pooled" in lowered:
                value = additional_inputs.get("text_embeds")
                if value is None:
                    value = additional_inputs.get("pooled_prompt_embeds")
                inputs[name] = np.asarray(value).astype(np.float32) if value is not None else self._zeros_for_shape(item.shape, np.float32)
            elif "time_ids" in lowered or "add_time" in lowered:
                value = additional_inputs.get("time_ids")
                inputs[name] = np.asarray(value).astype(np.float32) if value is not None else self._zeros_for_shape(item.shape, np.float32)
            else:
                inputs[name] = self._zeros_for_shape(item.shape, np.float32)
        return inputs

    def _normalize_noise_output(self, output: np.ndarray, latents: np.ndarray) -> np.ndarray:
        output = output.astype(np.float32)
        if output.shape == latents.shape:
            return output
        if output.size == latents.size:
            return output.reshape(latents.shape).astype(np.float32)
        logger.warning("UNet output shape %s does not match latents %s; using zeros noise.", output.shape, latents.shape)
        return np.zeros_like(latents, dtype=np.float32)

    def _zeros_for_shape(self, shape: list[Any], dtype: Any) -> np.ndarray:
        resolved = [1 if isinstance(value, str) or value is None or value < 0 else int(value) for value in shape]
        return np.zeros(resolved, dtype=dtype)
