from __future__ import annotations
import logging
from pathlib import Path
from typing import Any
import numpy as np
from engine.model_runtime_package import ModelRuntimePackage

logger = logging.getLogger("UNetService")

class UNetService:
    """
    Model-independent service that wraps the UNet (noise prediction) component.
    Receives text embeddings and latents, runs ONNX inference if the model is available,
    and falls back to generating/updating SDXL-shaped latent tensors when needed.
    """
    def __init__(self, package: ModelRuntimePackage) -> None:
        self.package = package

    def generate_initial_latents(self, width: int, height: int, seed: int = -1) -> np.ndarray:
        """
        Generate initial random latent noise in the shape of an SDXL latent tensor.
        SDXL downsamples resolution by a factor of 8 (e.g. 512x512 -> 64x64, 4 channels).
        """
        latent_h = (height if height > 0 else 512) // 8
        latent_w = (width if width > 0 else 512) // 8
        
        # Set random seed if provided
        if seed >= 0:
            np.random.seed(seed)
            
        # Shape: (batch_size=1, channels=4, height=latent_h, width=latent_w)
        latents = np.random.randn(1, 4, latent_h, latent_w).astype(np.float32)
        logger.info(f"[UNetService] Generated initial random latents with shape: {latents.shape}")
        return latents

    def predict_noise(
        self,
        latents: np.ndarray,
        timestep: int | float,
        encoder_hidden_states: np.ndarray,
        additional_inputs: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Predict noise / update latents using the UNet component.
        """
        unet_path = self.package.get_component_path("unet")
        logger.info(f"[UNetService] Resolving UNet component from: '{unet_path}'")
        
        # Try to run using ONNX Runtime if available
        if unet_path and Path(unet_path).exists():
            try:
                import onnxruntime as ort
                logger.info(f"[UNetService] Loading UNet InferenceSession for: '{unet_path}'")
                print(f"[UNetService] Loading UNet InferenceSession for: '{unet_path}'")
                
                session = ort.InferenceSession(unet_path)
                
                # Retrieve session input names
                input_names = [x.name for x in session.get_inputs()]
                logger.info(f"[UNetService] UNet input names: {input_names}")
                
                # Build inputs dictionary dynamically
                inputs = {}
                for name in input_names:
                    if "sample" in name or "latent" in name:
                        inputs[name] = latents
                    elif "timestep" in name or "time" in name:
                        inputs[name] = np.array([timestep], dtype=np.float32)
                    elif "hidden" in name or "encoder" in name:
                        inputs[name] = encoder_hidden_states
                    else:
                        # Provide fallback zero tensors for other inputs (e.g. text_embeds, time_ids in SDXL)
                        input_shape = session.get_inputs()[input_names.index(name)].shape
                        resolved_shape = [1 if isinstance(s, str) or s is None or s < 0 else s for s in input_shape]
                        inputs[name] = np.zeros(resolved_shape, dtype=np.float32)
                
                # Run session
                outputs = session.run(None, inputs)
                output_noise = outputs[0]
                
                logger.info(f"[UNetService] UNet ONNX run successful. Output shape: {output_noise.shape}")
                print(f"[UNetService] UNet ONNX run successful. Output shape: {output_noise.shape}")
                
                # Clean up session
                del session
                
                # Simulating one Euler step of denoising update
                updated_latents = latents - 0.1 * output_noise
                
                return {
                    "latents": updated_latents,
                    "latent_shape": list(updated_latents.shape),
                    "is_mock": False
                }
            except Exception as e:
                logger.warning(f"[UNetService] UNet InferenceSession run failed/skipped: {e}")
                print(f"[UNetService] UNet InferenceSession run failed/skipped: {e}")
                
        # Fallback Mock Denoising Step: apply a tiny noise reduction step mock
        # Simply reduce latent variance slightly or subtract a minor random noise
        # This keeps the shape exactly (1, 4, latent_h, latent_w)
        mock_noise = np.random.randn(*latents.shape).astype(np.float32)
        updated_latents = latents - 0.05 * mock_noise
        
        logger.info(f"[UNetService] Generated mock UNet latents update with shape: {updated_latents.shape}")
        print(f"[UNetService] Generated mock UNet latents update with shape: {updated_latents.shape}")
        
        return {
            "latents": updated_latents,
            "latent_shape": list(updated_latents.shape),
            "is_mock": True
        }
