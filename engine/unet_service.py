# engine/unet_service.py
from __future__ import annotations

import logging
import datetime
import threading
import time
from engine.logging_config import get_logger
from pathlib import Path
from typing import Any, Callable

import numpy as np

from engine.model_runtime_package import ModelRuntimePackage
from engine.onnx_component_inspector import OnnxComponentInspector
from engine.onnx_provider_service import OnnxProviderService
from engine.sdxl_scheduler_service import SDXLSchedulerService
from engine.cpu_pipeline_diagnostics import current_diagnostics, diagnostic_session_run

logger = get_logger("UNetService")


class UNetService:
    """Model-independent UNet wrapper with SDXL scheduler and CFG core."""

    def __init__(self, package: ModelRuntimePackage) -> None:
        self.package = package
        self.scheduler = SDXLSchedulerService(package.get_component_path("scheduler"))

    def _onnx_type_to_numpy(self, item_type: str) -> np.dtype:
        if not item_type or not isinstance(item_type, str):
            return np.float32
        lowered = item_type.lower()
        if "float" in lowered:
            return np.float32
        if "int64" in lowered:
            return np.int64
        if "int32" in lowered:
            return np.int32
        if "double" in lowered:
            return np.float64
        if "bool" in lowered:
            return np.bool_
        return np.float32

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
        diagnostic_phase: str = "UNet",
        session: Any | None = None,
    ) -> dict[str, Any]:
        unet_path = self.package.get_component_path("unet")
        metadata = OnnxComponentInspector.inspect("unet", unet_path)
        logger.info(f"[UNetService] Resolving UNet component from: '{unet_path}'")

        if not self.package.is_fully_ready() or not unet_path or not Path(unet_path).is_file():
            raise RuntimeError(f"Reales UNet-Modell ist nicht verfügbar: {unet_path}")

        owns_session = session is None
        try:
            if owns_session:
                logger.info(f"[UNetService] Loading UNet InferenceSession for: '{unet_path}'")
                print(f"[UNetService] Loading UNet InferenceSession for: '{unet_path}'")
                session = OnnxProviderService.create_session(unet_path, "unet")
            if session is None:
                raise RuntimeError("UNet InferenceSession konnte nicht erstellt werden.")
            inputs = self._build_unet_inputs(session, latents, timestep, encoder_hidden_states, additional_inputs or {})
            logger.debug("[UNetService] UNet mapped inputs: %s", list(inputs.keys()))
            outputs = diagnostic_session_run(
                session, None, inputs, phase=diagnostic_phase,
                component_name="unet", model_path=unet_path,
            )
            output_noise = self._normalize_noise_output(np.asarray(outputs[0]), latents)
            logger.debug("[UNetService] UNet ONNX run successful. Output shape: %s", output_noise.shape)
            metadata["session_providers"] = OnnxProviderService.session_providers(session)
            return {
                "noise_pred": output_noise,
                "latent_shape": list(latents.shape),
                "noise_shape": list(output_noise.shape),
                "is_mock": False,
                "metadata": metadata,
            }
        except Exception as exc:
            logger.exception("[UNetService] Real UNet execution failed")
            raise RuntimeError(f"Reale CPU-Ausführung des UNet fehlgeschlagen: {exc}") from exc
        finally:
            if owns_session:
                OnnxProviderService.release_session(session)

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
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        self.scheduler.prepare_timesteps(timesteps)
        current = self.scheduler.scale_initial_noise(latents.astype(np.float32))
        logger.info(
            "[UNetService] Initial latents scaled for Euler scheduler | "
            "sigma=%.8f | min=%.8f | max=%.8f | mean=%.8f | std=%.8f",
            self.scheduler.init_noise_sigma,
            float(np.min(current)),
            float(np.max(current)),
            float(np.mean(current)),
            float(np.std(current)),
        )
        any_mock = False
        last_result: dict[str, Any] | None = None
        step_records: list[dict[str, Any]] = []
        guidance_enabled = bool(negative_embeddings is not None and guidance_scale != 1.0)

        unet_path = self.package.get_component_path("unet")
        if not self.package.is_fully_ready() or not unet_path or not Path(unet_path).is_file():
            raise RuntimeError(f"Reales UNet-Modell ist nicht verfügbar: {unet_path}")

        logger.info(f"[UNetService] Loading shared UNet InferenceSession for denoising loop: '{unet_path}'")
        print(f"[UNetService] Loading shared UNet InferenceSession for denoising loop: '{unet_path}'")
        shared_session = OnnxProviderService.create_session(unet_path, "unet")
        try:
            total_steps = len(timesteps)
            for index, timestep in enumerate(timesteps):
                diagnostics = current_diagnostics()
                step_name = f"Step {index + 1}/{total_steps}"
                step_started = time.perf_counter()
                if diagnostics is not None:
                    diagnostics.current_phase = f"Denoise {step_name}"
                    logger.info(
                        "[DENOISE] %s started | Start: %s | Thread: %s | Provider: %s | "
                        "Model path: %s | Progress: %.1f%%",
                        step_name, datetime.datetime.now().astimezone().isoformat(timespec="milliseconds"),
                        threading.get_ident(), diagnostics.provider,
                        self.package.get_component_path("unet"), diagnostics.progress_percent(),
                    )
                next_timestep = timesteps[index + 1] if index + 1 < total_steps else None
                latent_model_input = self.scheduler.scale_model_input(current, timestep)
                negative_noise = None
                negative_result: dict[str, Any] | None = None

                if guidance_enabled:
                    cfg_latents = np.concatenate(
                        [latent_model_input, latent_model_input], axis=0
                    )
                    cfg_embeddings = np.concatenate(
                        [negative_embeddings, prompt_embeddings], axis=0
                    )
                    cfg_pooled = np.concatenate(
                        [negative_pooled_embeddings, pooled_prompt_embeddings], axis=0
                    )
                    cfg_time_ids = np.concatenate([time_ids, time_ids], axis=0)
                    cfg_inputs = {
                        "text_embeds": cfg_pooled,
                        "time_ids": cfg_time_ids,
                        "pooled_prompt_embeds": cfg_pooled,
                    }
                    positive_result = self.predict_noise(
                        cfg_latents, timestep, cfg_embeddings, cfg_inputs,
                        diagnostic_phase=f"Denoise {step_name} CFG",
                        session=shared_session,
                    )
                    negative_noise, positive_noise = np.split(
                        positive_result["noise_pred"], 2, axis=0
                    )
                else:
                    positive_inputs = {
                        "text_embeds": pooled_prompt_embeddings,
                        "time_ids": time_ids,
                        "pooled_prompt_embeds": pooled_prompt_embeddings,
                    }
                    positive_result = self.predict_noise(
                        latent_model_input, timestep, prompt_embeddings, positive_inputs,
                        diagnostic_phase=f"Denoise {step_name} positive",
                        session=shared_session,
                    )
                    positive_noise = positive_result["noise_pred"]

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
                if progress_callback:
                    progress_callback(index + 1, total_steps)
                if diagnostics is not None:
                    logger.info(
                        "[DENOISE] %s completed | End: %s | Duration: %.3fs | Thread: %s | "
                        "Provider: %s | Model path: %s | Progress: %.1f%%",
                        step_name, datetime.datetime.now().astimezone().isoformat(timespec="milliseconds"),
                        time.perf_counter() - step_started, threading.get_ident(),
                        diagnostics.provider, self.package.get_component_path("unet"),
                        diagnostics.progress_percent(),
                    )
        finally:
            OnnxProviderService.release_session(shared_session)

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
            
            item_type = getattr(item, "type", None) or "tensor(float)"
            dtype = self._onnx_type_to_numpy(item_type)
            
            if lowered in additional_inputs and additional_inputs[lowered] is not None:
                inputs[name] = np.asarray(additional_inputs[lowered]).astype(dtype)
            elif "sample" in lowered or "latent" in lowered:
                inputs[name] = latents.astype(dtype)
            elif "timestep" in lowered or lowered in {"t", "time"}:
                if item.shape == []:
                    inputs[name] = np.array(float(timestep), dtype=dtype)
                else:
                    inputs[name] = np.array([timestep], dtype=dtype)
            elif "encoder_hidden" in lowered or "hidden_states" in lowered or "encoder" in lowered:
                inputs[name] = encoder_hidden_states.astype(dtype)
            elif "text_embeds" in lowered or "pooled" in lowered:
                value = additional_inputs.get("text_embeds")
                if value is None:
                    value = additional_inputs.get("pooled_prompt_embeds")
                inputs[name] = np.asarray(value).astype(dtype) if value is not None else self._zeros_for_shape(item.shape, dtype)
            elif "time_ids" in lowered or "add_time" in lowered:
                value = additional_inputs.get("time_ids")
                inputs[name] = np.asarray(value).astype(dtype) if value is not None else self._zeros_for_shape(item.shape, dtype)
            else:
                inputs[name] = self._zeros_for_shape(item.shape, dtype)
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
