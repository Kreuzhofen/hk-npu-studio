from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from engine.model_runtime_package import ModelRuntimePackage
from engine.onnx_component_inspector import OnnxComponentInspector
from engine.sdxl_scheduler_service import SDXLSchedulerService

logger = logging.getLogger("UNetService")


class UNetService:
    """
    Model-independent UNet wrapper with SDXL input mapping preparation.
    It supports existing fallback generation and prepares a multi-step denoising loop.
    """

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
            try:
                import onnxruntime as ort
                logger.info(f"[UNetService] Loading UNet InferenceSession for: '{unet_path}'")
                print(f"[UNetService] Loading UNet InferenceSession for: '{unet_path}'")
                session = ort.InferenceSession(unet_path)
                inputs = self._build_unet_inputs(session, latents, timestep, encoder_hidden_states, additional_inputs or {})
                logger.info(f"[UNetService] UNet mapped inputs: {list(inputs.keys())}")
                print(f"[UNetService] UNet mapped inputs: {list(inputs.keys())}")
                outputs = session.run(None, inputs)
                output_noise = np.asarray(outputs[0]).astype(np.float32)
                logger.info(f"[UNetService] UNet ONNX run successful. Output shape: {output_noise.shape}")
                print(f"[UNetService] UNet ONNX run successful. Output shape: {output_noise.shape}")
                del session
                updated_latents = latents - 0.1 * output_noise if output_noise.shape == latents.shape else output_noise
                return {
                    "latents": updated_latents.astype(np.float32),
                    "noise_pred": output_noise,
                    "latent_shape": list(updated_latents.shape),
                    "is_mock": False,
                    "metadata": metadata,
                }
            except Exception as exc:
                logger.warning(f"[UNetService] UNet InferenceSession run failed/skipped: {exc}")
                print(f"[UNetService] UNet InferenceSession run failed/skipped: {exc}")

        mock_noise = np.random.randn(*latents.shape).astype(np.float32)
        updated_latents = latents - 0.05 * mock_noise
        logger.info(f"[UNetService] Generated mock UNet latents update with shape: {updated_latents.shape}")
        print(f"[UNetService] Generated mock UNet latents update with shape: {updated_latents.shape}")
        return {
            "latents": updated_latents.astype(np.float32),
            "noise_pred": mock_noise,
            "latent_shape": list(updated_latents.shape),
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
        current = latents
        any_mock = False
        last_result: dict[str, Any] | None = None
        total = max(1, len(timesteps))

        for index, timestep in enumerate(timesteps):
            additional_inputs = {
                "text_embeds": pooled_prompt_embeddings,
                "time_ids": time_ids,
                "pooled_prompt_embeds": pooled_prompt_embeddings,
            }
            if negative_embeddings is not None:
                additional_inputs["negative_embeddings"] = negative_embeddings
            if negative_pooled_embeddings is not None:
                additional_inputs["negative_pooled_embeddings"] = negative_pooled_embeddings

            result = self.predict_noise(current, timestep, prompt_embeddings, additional_inputs)
            current = self.scheduler.step(current, result["latents"], timestep, index, total)
            any_mock = any_mock or bool(result.get("is_mock"))
            last_result = result

        return {
            "latents": current.astype(np.float32),
            "latent_shape": list(current.shape),
            "is_mock": any_mock,
            "timesteps": timesteps,
            "guidance_prepared": bool(negative_embeddings is not None and guidance_scale != 1.0),
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

    def _zeros_for_shape(self, shape: list[Any], dtype: Any) -> np.ndarray:
        resolved = [1 if isinstance(value, str) or value is None or value < 0 else int(value) for value in shape]
        return np.zeros(resolved, dtype=dtype)
