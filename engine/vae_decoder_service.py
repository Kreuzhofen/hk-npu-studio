from __future__ import annotations
import logging
from engine.logging_config import get_logger
from pathlib import Path
from typing import Any
import numpy as np
from PIL import Image
from engine.model_runtime_package import ModelRuntimePackage
from engine.onnx_component_inspector import OnnxComponentInspector
from engine.onnx_provider_service import OnnxProviderService

logger = get_logger("VAEDecoderService")

class VAEDecoderService:
    """
    Model-independent service that wraps the VAE Decoder component.
    Receives latent tensors from the UNet step, decodes them to RGB pixel arrays
    via ONNX Runtime. Missing or invalid production components fail closed.
    """
    def __init__(self, package: ModelRuntimePackage) -> None:
        self.package = package

    def decode_latents(self, latents: np.ndarray, prompt: str = "") -> dict[str, Any]:
        """
        Decode a latent tensor of shape (1, 4, latent_h, latent_w) to an RGB image.
        """
        vae_path = self.package.get_component_path("vae_decoder")
        metadata = OnnxComponentInspector.inspect("vae_decoder", vae_path)
        logger.info(f"[VAEDecoderService] Resolving VAE Decoder from: '{vae_path}'")
        
        latent_shape = list(latents.shape)
        img_h = latent_shape[2] * 8
        img_w = latent_shape[3] * 8
        
        if not self.package.is_fully_ready() or not vae_path or not Path(vae_path).is_file():
            raise RuntimeError(f"Realer VAE-Decoder ist nicht verfügbar: {vae_path}")

        session = None
        try:
                logger.info(f"[VAEDecoderService] Loading VAE Decoder InferenceSession for: '{vae_path}'")
                print(f"[VAEDecoderService] Loading VAE Decoder InferenceSession for: '{vae_path}'")
                
                session = OnnxProviderService.create_session(vae_path, "vae_decoder")
                input_name = session.get_inputs()[0].name
                print(f"[VAEDecoderService] VAE mapped input: {input_name}")
                
                # Run VAE decoding
                outputs = session.run(None, {input_name: latents})
                vae_output = outputs[0]
                
                logger.info(f"[VAEDecoderService] VAE ONNX run successful. Output shape: {vae_output.shape}")
                print(f"[VAEDecoderService] VAE ONNX run successful. Output shape: {vae_output.shape}")
                metadata["session_providers"] = OnnxProviderService.session_providers(session)
                
                # Postprocess VAE output tensor: shape (1, 3, H, W)
                image_arr = vae_output[0]
                image_arr = np.clip((image_arr + 1.0) / 2.0 * 255.0, 0.0, 255.0).astype(np.uint8)
                image_arr = np.transpose(image_arr, (1, 2, 0))
                
                pil_image = Image.fromarray(image_arr)
                return {
                    "image": pil_image,
                    "image_shape": [1, 3, img_h, img_w],
                    "is_mock": False,
                    "backend": OnnxProviderService.runtime_label([metadata.get("session_providers", [])]),
                    "metadata": metadata
                }
        except Exception as exc:
            logger.exception("[VAEDecoderService] Real VAE execution failed")
            raise RuntimeError(f"Reale CPU-Ausführung des VAE-Decoders fehlgeschlagen: {exc}") from exc
        finally:
            OnnxProviderService.release_session(session)
