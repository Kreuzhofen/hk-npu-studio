from __future__ import annotations

import time
import datetime
import json
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from controllers.generation_job import GenerationJob
from engine.generation_response import GenerationResponse
from engine.inference_backend import InferenceBackend
from engine.runtime_model import RuntimeModel

logger = logging.getLogger("OnnxImageBackend")


class OnnxImageBackend(InferenceBackend):
    """
    ONNX Runtime stub image generation backend.
    Renders diagnostic text details indicating ONNX execution on a dark background using Pillow.
    """

    def __init__(self, runtime_model: RuntimeModel | None = None) -> None:
        self.runtime_model = runtime_model

    def generate(self, job: GenerationJob) -> GenerationResponse:
        model_name = self.runtime_model.model_id if self.runtime_model else job.session.model_name
        backend_name = "ONNX Runtime (Stub)"
        
        # Setup unique image path using prefix, timestamp and job ID
        output_dir = Path(job.session.output_directory) if job.session.output_directory else Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        prefix = job.session.output_prefix if job.session.output_prefix else "generate"
        timestamp = int(time.time())
        filename = f"{prefix}_{timestamp}_{str(job.job_id)[:8]}.png"
        dummy_image_path = output_dir / filename

        # Create a valid PNG image with visible diagnostic content using Pillow
        try:
            w = job.session.width if job.session.width > 0 else 512
            h = job.session.height if job.session.height > 0 else 512

            # Try to load standard TrueType fonts with fallback
            try:
                font_title = ImageFont.truetype("segoeui.ttf", 24)
                font_subtitle = ImageFont.truetype("segoeui.ttf", 18)
                font_body = ImageFont.truetype("segoeui.ttf", 14)
                font_prompt = ImageFont.truetype("segoeui.ttf", 12)
            except Exception:
                try:
                    font_title = ImageFont.truetype("arial.ttf", 24)
                    font_subtitle = ImageFont.truetype("arial.ttf", 18)
                    font_body = ImageFont.truetype("arial.ttf", 14)
                    font_prompt = ImageFont.truetype("arial.ttf", 12)
                except Exception:
                    font_title = ImageFont.load_default()
                    font_subtitle = ImageFont.load_default()
                    font_body = ImageFont.load_default()
                    font_prompt = ImageFont.load_default()

            # Create standard dark background matching Phoenix colors
            img = Image.new("RGB", (w, h), color="#171d23")
            draw = ImageDraw.Draw(img)

            # Draw border
            draw.rectangle([(2, 2), (w - 3, h - 3)], outline="#3e4b59", width=2)

            # Draw accent divider line
            draw.line([(40, 100), (w - 40, 100)], fill="#3b82f6", width=3)

            # Draw header labels
            draw.text((40, 50), "Snapdragon AI Studio", fill="#3b82f6", font=font_title)
            draw.text((40, 115), "ONNX Runtime Stub Generation", fill="#e8edf2", font=font_subtitle)

            # Draw metadata values
            draw.text((40, 165), f"Model: {model_name}", fill="#9aa7b2", font=font_body)
            draw.text((40, 195), f"Backend: {backend_name}", fill="#9aa7b2", font=font_body)
            draw.text((40, 225), f"Seed: {job.session.seed} | Steps: {job.session.steps} | CFG: {job.session.cfg_scale}", fill="#9aa7b2", font=font_body)

            # Draw truncated prompt preview
            prompt_str = job.session.prompt
            truncated_prompt = prompt_str[:57] + "..." if len(prompt_str) > 60 else prompt_str
            draw.text((40, 265), "Prompt Preview:", fill="#e8edf2", font=font_body)
            draw.text((40, 290), f'"{truncated_prompt}"', fill="#3b82f6", font=font_prompt)

            # Draw footer timestamp
            timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            draw.text((40, h - 50), f"Generated: {timestamp_str}", fill="#9aa7b2", font=font_body)

            img.save(dummy_image_path, format="PNG")
        except Exception as e:
            logger.error(f"[OnnxImageBackend] Failed to create dummy image with text using Pillow: {e}")

        # Prepare sidecar metadata dictionary
        response_metadata = {
            "prompt": job.session.prompt,
            "negative_prompt": job.session.negative_prompt,
            "model": model_name,
            "backend": backend_name,
            "seed": job.session.seed,
            "width": job.session.width,
            "height": job.session.height,
            "steps": job.session.steps,
            "cfg": job.session.cfg_scale,
            "sampler": job.session.sampler,
            "scheduler": job.session.scheduler,
            "batch_count": job.session.batch_size,
            "created_at": datetime.datetime.now().isoformat()
        }

        # Write sidecar JSON alongside the image
        metadata_path = dummy_image_path.with_suffix(".json")
        try:
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(response_metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"[OnnxImageBackend] Saved sidecar metadata to: {metadata_path}")
            print(f"[OnnxImageBackend] Saved sidecar metadata to: {metadata_path}")
        except Exception as e:
            logger.error(f"[OnnxImageBackend] Failed to save sidecar metadata: {e}")

        # Simulate small generation latency (e.g. 50ms)
        time.sleep(0.05)

        logger.info(f"[OnnxImageBackend] Generation completed successfully. Image saved to: {dummy_image_path}")
        print(f"[OnnxImageBackend] Generation completed successfully. Image saved to: {dummy_image_path}")

        return GenerationResponse(
            success=True,
            status="FINISHED",
            message="ONNX local image generation completed successfully.",
            image_path=str(dummy_image_path),
            thumbnail_path=str(dummy_image_path),
            backend_name=backend_name,
            model_name=model_name,
            metadata=response_metadata
        )
