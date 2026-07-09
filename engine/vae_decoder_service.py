from __future__ import annotations
import logging
from pathlib import Path
from typing import Any
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from engine.model_runtime_package import ModelRuntimePackage
from engine.onnx_component_inspector import OnnxComponentInspector
from engine.onnx_provider_service import OnnxProviderService

logger = logging.getLogger("VAEDecoderService")

class VAEDecoderService:
    """
    Model-independent service that wraps the VAE Decoder component.
    Receives latent tensors from the UNet step, decodes them to RGB pixel arrays
    via ONNX Runtime, and falls back to procedurally rendering a high-quality PIL Image
    if the model is missing or invalid.
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
        
        # Try to run VAE Decoder using ONNX Runtime if package is fully ready
        if self.package.is_fully_ready() and vae_path and Path(vae_path).exists():
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
                
                # Cleanup session
                del session
                
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
            except Exception as e:
                logger.warning(f"[VAEDecoderService] VAE InferenceSession run failed/skipped: {e}")
                print(f"[VAEDecoderService] VAE InferenceSession run failed/skipped: {e}")
                
        # Fallback Mock Decoding: Generate a stunning procedural diagnostic preview image
        logger.info(f"[VAEDecoderService] Fallback to procedural mock decoder. Shape: (1, 3, {img_h}, {img_w})")
        print(f"[VAEDecoderService] Fallback to procedural mock decoder. Shape: (1, 3, {img_h}, {img_w})")
        
        latent_mean = float(np.mean(latents))
        latent_std = float(np.std(latents))
        
        pil_image = Image.new("RGB", (img_w, img_h), color="#171d23")
        draw = ImageDraw.Draw(pil_image)
        
        # Draw nice concentric glowing rings or abstract curves to simulate latent decoding
        center_x, center_y = img_w // 2, img_h // 2
        max_r = min(img_w, img_h) // 2 - 20
        
        for r in range(max_r, 0, -8):
            factor = r / max_r
            r_val = int(23 + factor * 10 * abs(latent_mean))
            g_val = int(29 + factor * 120 * latent_std)
            b_val = int(35 + factor * 180)
            
            r_val = min(max(r_val, 0), 255)
            g_val = min(max(g_val, 0), 255)
            b_val = min(max(b_val, 0), 255)
            
            draw.ellipse(
                [(center_x - r, center_y - r), (center_x + r, center_y + r)],
                fill=f"#{r_val:02x}{g_val:02x}{b_val:02x}"
            )
            
        core_r = 15
        draw.ellipse(
            [(center_x - core_r, center_y - core_r), (center_x + core_r, center_y + core_r)],
            fill="#10b981"
        )
        
        return {
            "image": pil_image,
            "image_shape": [1, 3, img_h, img_w],
            "is_mock": True,
            "backend": "Mock VAE Decoder",
            "metadata": metadata
        }
