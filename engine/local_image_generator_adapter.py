from __future__ import annotations

import os
import time
import logging
from pathlib import Path
from typing import Any
from controllers.generation_job import GenerationJob
from engine.generation_response import GenerationResponse

logger = logging.getLogger("LocalImageGeneratorAdapter")


class LocalImageGeneratorAdapter:
    """
    Adapter for local image generation. Resolves the target backend and runs the inference stub.
    Creates a dummy/stub output image if successful.
    """

    def __init__(self, backend_adapter: Any = None) -> None:
        self.backend_adapter = backend_adapter

    def get_backend_name(self) -> str:
        if self.backend_adapter:
            return self.backend_adapter.get_backend_name()
        return "Local CPU (Stub)"

    def generate(self, job: GenerationJob) -> GenerationResponse:
        backend_name = self.get_backend_name()
        logger.info(f"[Adapter] Starting generate() on backend: {backend_name}")
        print(f"[Adapter] Starting generate() on backend: {backend_name}")

        model_name = job.session.model_name
        
        # Setup dummy image directory and path
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        dummy_image_path = output_dir / f"dummy_{job.job_id}.png"

        # Create a dummy image file (1x1 black PNG bytes)
        try:
            png_bytes = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDAT\x08\xd7c`f`f"
                b"\x00\x00\x00\x05\x00\x01\xa5\xf6E@\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            with open(dummy_image_path, "wb") as f:
                f.write(png_bytes)
        except Exception as e:
            logger.error(f"[Adapter] Failed to create dummy image: {e}")

        # Simulate small generation latency (e.g. 50ms)
        time.sleep(0.05)

        logger.info(f"[Adapter] Generation completed successfully. Image saved to: {dummy_image_path}")
        print(f"[Adapter] Generation completed successfully. Image saved to: {dummy_image_path}")

        return GenerationResponse(
            success=True,
            status="FINISHED",
            message="Local image generation completed successfully.",
            image_path=str(dummy_image_path),
            thumbnail_path=str(dummy_image_path),
            backend_name=backend_name,
            model_name=model_name
        )
