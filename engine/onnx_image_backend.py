from __future__ import annotations

import time
import datetime
import json
import logging
import traceback
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from controllers.generation_job import GenerationJob
from engine.generation_response import GenerationResponse
from engine.inference_backend import InferenceBackend
from engine.onnx_provider_service import OnnxProviderService
from engine.runtime_model import RuntimeModel

logger = logging.getLogger("OnnxImageBackend")


class OnnxImageBackend(InferenceBackend):
    """
    ONNX Runtime image generation backend with CPU fallback and optional QNN diagnostics.
    """

    def __init__(self, runtime_model: RuntimeModel | None = None) -> None:
        self.runtime_model = runtime_model

    def _build_save_diagnostic_log_path(self, job: GenerationJob) -> Path:
        logs_dir = Path("C:/SnapdragonAI/diagnostics/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return logs_dir / f"prompt_to_image_save_{timestamp}_{str(job.job_id)[:8]}.log"

    def _append_save_diagnostic(self, log_path: Path, step: str, details: str = "") -> None:
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        message = f"[{timestamp}] {step}"
        if details:
            message = f"{message} | {details}"
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(message + "\n")
        except Exception as error:
            logger.warning("[OnnxImageBackend] Failed to write save diagnostic log: %s", error)

    def _validate_output_image(self, image: object) -> dict[str, object]:
        if not isinstance(image, Image.Image):
            raise ValueError(f"VAE decoder returned invalid image type: {type(image).__name__}")
        if image.width <= 0 or image.height <= 0:
            raise ValueError(f"VAE decoder returned invalid image size: {image.size}")

        array = np.asarray(image)
        if array.size == 0:
            raise ValueError("VAE decoder returned empty image data.")
        if np.issubdtype(array.dtype, np.floating) and not np.isfinite(array).all():
            raise ValueError("VAE decoder returned image data containing NaN or Inf values.")

        return {
            "mode": image.mode,
            "size": list(image.size),
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "min": float(np.min(array)),
            "max": float(np.max(array)),
        }

    def _save_failure_response(
        self,
        message: str,
        model_name: str,
        backend_name: str,
        diagnostic_log_path: Path,
    ) -> GenerationResponse:
        return GenerationResponse(
            success=False,
            status="SaveError",
            message=message,
            backend_name=backend_name,
            model_name=model_name,
            metadata={"diagnostic_log_path": str(diagnostic_log_path)}
        )

    @staticmethod
    def discover_onnx_models(project_root: Path | str = "C:/SnapdragonAI") -> list[dict[str, any]]:
        """
        Discover ONNX models project-wide, prioritizing specific model folders.
        Returns a list of dicts with keys: path, filename, size_mb, modified_at.
        """
        root = Path(project_root)
        priorities = [
            root / "resources" / "models",
            root / "models",
            root / "assets" / "models"
        ]
        
        discovered_paths: set[Path] = set()
        
        # 1. Scan prioritized directories first
        for folder in priorities:
            if folder.exists() and folder.is_dir():
                try:
                    for f in folder.rglob("*.onnx"):
                        if f.is_file():
                            discovered_paths.add(f.resolve())
                except Exception as e:
                    logger.debug(f"[OnnxImageBackend] Error scanning prioritised folder '{folder}': {e}")
                    
        # 2. If nothing is found, search project-wide (excluding standard heavy/system folders)
        if not discovered_paths:
            logger.info("[OnnxImageBackend] No ONNX models found in prioritized folders. Scanning project-wide...")
            exclude_folders = {".git", "temp", "venv", ".venv", "__pycache__", "build", "dist", ".gemini"}
            try:
                for path in root.rglob("*.onnx"):
                    if path.is_file():
                        parts = path.parts
                        if not any(x in exclude_folders for x in parts):
                            discovered_paths.add(path.resolve())
            except Exception as e:
                logger.debug(f"[OnnxImageBackend] Error scanning project-wide: {e}")
                
        # 3. Compile metadata for found files
        results = []
        for p in sorted(list(discovered_paths)):
            try:
                stat = p.stat()
                size_mb = round(stat.st_size / (1024 * 1024), 2)
                modified_at = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                results.append({
                    "path": str(p.as_posix()),
                    "filename": p.name,
                    "size_mb": size_mb,
                    "modified_at": modified_at
                })
            except Exception as e:
                logger.warning(f"[OnnxImageBackend] Failed to read metadata for '{p}': {e}")
                
        return results

    def check_availability(self) -> tuple[bool, str]:
        """
        Check if onnxruntime library is importable and log its metadata.
        Returns a tuple of (is_available, status_message).
        """
        try:
            import onnxruntime
            version = getattr(onnxruntime, "__version__", "unknown")
            diagnostics = OnnxProviderService.diagnostics()
            try:
                providers = OnnxProviderService.available_providers()
            except Exception:
                providers = []
            
            # Verify CPUExecutionProvider
            cpu_available = "CPUExecutionProvider" in providers
            
            # Check QNNExecutionProvider presence (optional)
            qnn_available = "QNNExecutionProvider" in providers
            
            log_msg = f"ONNX Runtime v{version} detected."
            if cpu_available:
                log_msg += " CPUExecutionProvider is available."
            else:
                log_msg += " CPUExecutionProvider is NOT listed in available providers."
                
            if qnn_available:
                log_msg += " QNNExecutionProvider is available."
                logger.info(f"[OnnxImageBackend] {log_msg}")
                print(f"[OnnxImageBackend] {log_msg}")
            else:
                warn_msg = log_msg + " NOTE: QNNExecutionProvider is not available (this is normal if QNN SDK/EP is not installed)."
                logger.warning(f"[OnnxImageBackend] {warn_msg}")
                print(f"[OnnxImageBackend] {warn_msg}")
                
            msg = (
                f"ONNX Runtime v{version} available. Providers: {providers}. "
                f"QNN registration: {diagnostics.get('provider_registration_status')}"
            )
            return True, msg
        except ImportError as e:
            return False, f"ONNX Runtime is not installed on this system: {e}"

    def is_available(self) -> bool:
        available, _ = self.check_availability()
        return available

    def generate(self, job: GenerationJob) -> GenerationResponse:
        model_name = self.runtime_model.model_id if self.runtime_model else job.session.model_name
        backend_name = OnnxProviderService.runtime_label()
        save_diagnostic_log_path = self._build_save_diagnostic_log_path(job)
        self._append_save_diagnostic(
            save_diagnostic_log_path,
            "generation_start",
            f"job_id={job.job_id}, model={model_name}, size={job.session.width}x{job.session.height}, steps={job.session.steps}"
        )

        # 1. Check ONNX Runtime availability
        available, check_msg = self.check_availability()
        if not available:
            logger.error(f"[OnnxImageBackend] {check_msg}")
            print(f"[OnnxImageBackend] {check_msg}")
            return GenerationResponse(
                success=False,
                status="unavailable",
                message=check_msg,
                model_name=model_name
            )

        logger.info(f"[OnnxImageBackend] {check_msg}")
        print(f"[OnnxImageBackend] {check_msg}")

        # 1.5. Discover ONNX models project-wide and log their details
        discovered_models = self.discover_onnx_models()
        logger.info(f"[OnnxImageBackend] Discovered {len(discovered_models)} ONNX models:")
        print(f"[OnnxImageBackend] Discovered {len(discovered_models)} ONNX models:")
        for m in discovered_models:
            logger.info(f"  - Model: {m['filename']} (Size: {m['size_mb']} MB, Path: {m['path']}, Modified: {m['modified_at']})")
            print(f"  - Model: {m['filename']} (Size: {m['size_mb']} MB, Path: {m['path']}, Modified: {m['modified_at']})")

        # 2. Check if compatible ONNX model path and files exist
        if not self.runtime_model or not self.runtime_model.model_path:
            msg = "No runtime model metadata provided for ONNX generation."
            logger.error(f"[OnnxImageBackend] {msg}")
            print(f"[OnnxImageBackend] {msg}")
            return GenerationResponse(
                success=False,
                status="unavailable",
                message=msg,
                model_name=model_name
            )

        model_dir = Path(self.runtime_model.model_path)
        is_smp = (model_dir / "package.json").exists() if model_dir.exists() else False

        onnx_files = [f for f in self.runtime_model.files if f.lower().endswith(".onnx")]
        if not onnx_files and model_dir.exists() and model_dir.is_dir():
            try:
                onnx_files = [str(f.resolve()) for f in model_dir.rglob("*.onnx")]
            except Exception:
                pass

        if not onnx_files and not is_smp:
            msg = f"No compatible ONNX model files (*.onnx) found in directory '{self.runtime_model.model_path}'."
            logger.error(f"[OnnxImageBackend] {msg}")
            print(f"[OnnxImageBackend] {msg}")
            return GenerationResponse(
                success=False,
                status="unavailable",
                message=msg,
                model_name=model_name
            )

        # 3. Verify ONNX model paths and check if they are fundamentally loadable (non-fatal check)
        onnx_model_path = onnx_files[0] if onnx_files else ""
        if onnx_model_path:
            logger.info(f"[OnnxImageBackend] Found {len(onnx_files)} ONNX files. Verifying: '{onnx_model_path}'")
            print(f"[OnnxImageBackend] Found {len(onnx_files)} ONNX files. Verifying: '{onnx_model_path}'")
            try:
                session = OnnxProviderService.create_session(onnx_model_path, "root_model")
                inputs = [x.name for x in session.get_inputs()]
                outputs = [x.name for x in session.get_outputs()]
                session_providers = OnnxProviderService.session_providers(session)
                logger.info(f"[OnnxImageBackend] Root InferenceSession verified. Providers: {session_providers}, Inputs: {inputs}, Outputs: {outputs}")
                print(f"[OnnxImageBackend] Root InferenceSession verified. Providers: {session_providers}, Inputs: {inputs}, Outputs: {outputs}")
                del session
            except Exception as e:
                logger.warning(f"[OnnxImageBackend] Root model loadability check skipped/failed (will use components fallback): {e}")
                print(f"[OnnxImageBackend] Root model loadability check skipped/failed (will use components fallback): {e}")
        else:
            logger.info("[OnnxImageBackend] No root ONNX model file found (SMP components layout mode).")
            print("[OnnxImageBackend] No root ONNX model file found (SMP components layout mode).")

        # 4. Integrate ModelRuntimePackage & TextEmbeddingService for Prompt Processing
        from controllers.model_repository import ModelRepository
        from engine.onnx_component_inspector import OnnxComponentInspector
        from engine.sdxl_scheduler_service import SDXLSchedulerService
        from engine.text_embedding_service import TextEmbeddingService
        
        repo = ModelRepository()
        pkg = repo.build_runtime_package(model_name)
        if not pkg:
            msg = f"Failed to build ModelRuntimePackage for model '{model_name}'."
            logger.error(f"[OnnxImageBackend] {msg}")
            print(f"[OnnxImageBackend] {msg}")
            return GenerationResponse(
                success=False,
                status="Failed",
                message=msg,
                model_name=model_name
            )

        component_metadata = OnnxComponentInspector.inspect_package(
            pkg,
            ("text_encoder", "text_encoder_2", "unet", "vae_decoder"),
        )
        OnnxComponentInspector.log_metadata(component_metadata)

        # Verify package components and log status
        verification_status = pkg.verify_components()
        logger.info(f"[OnnxImageBackend] Component Verification Status: {verification_status}")
        print("[OnnxImageBackend] Component Verification Status:")
        for name, status in verification_status.items():
            print(f"  - {name:<15}: {status}")
            
        package_ready = pkg.is_fully_ready()
        if package_ready:
            msg = "[OnnxImageBackend] All components are READY. Activating real ONNX execution pipeline."
            logger.info(msg)
            print(msg)
        else:
            msg = "[OnnxImageBackend] Component validation failed (some components are MISSING/FOUND/INVALID). Activating Mock Pipeline fallback automatically."
            logger.info(msg)
            print(msg)
            for comp, status in verification_status.items():
                if status != "READY":
                    comp_path = pkg.get_component_path(comp)
                    logger.warning(f"  -> Component '{comp}' status is '{status}'. Expected path: '{comp_path}'")
                    print(f"  -> Component '{comp}' status is '{status}'. Expected path: '{comp_path}'")
            
        embedder = TextEmbeddingService(pkg)
        embed_res = embedder.embed_prompt_sdxl(job.session.prompt, job.session.negative_prompt)

        # 4.5. Integrate UNetService and scheduler foundation for latent denoising
        from engine.unet_service import UNetService
        unet_service = UNetService(pkg)
        scheduler_service = SDXLSchedulerService(pkg.get_component_path("scheduler"))
        w = job.session.width if job.session.width > 0 else 512
        h = job.session.height if job.session.height > 0 else 512
        timesteps = scheduler_service.build_timesteps(job.session.steps, job.session.scheduler)
        time_ids = scheduler_service.build_time_ids(w, h)
        scheduler_metadata = scheduler_service.describe(job.session.steps, job.session.scheduler, w, h, job.session.cfg_scale)
        
        init_latents = unet_service.generate_initial_latents(w, h, seed=job.session.seed)
        unet_res = unet_service.run_denoising_loop(
            init_latents,
            timesteps=timesteps,
            prompt_embeddings=embed_res["embeddings"],
            pooled_prompt_embeddings=embed_res["pooled_embeddings"],
            time_ids=time_ids,
            negative_embeddings=embed_res["negative_embeddings"],
            negative_pooled_embeddings=embed_res["negative_pooled_embeddings"],
            guidance_scale=job.session.cfg_scale,
        )

        # 4.7. Integrate VAEDecoderService for VAE Latent Decoding
        from engine.vae_decoder_service import VAEDecoderService
        vae_service = VAEDecoderService(pkg)
        try:
            self._append_save_diagnostic(save_diagnostic_log_path, "before_vae_decode")
            vae_res = vae_service.decode_latents(unet_res["latents"], prompt=job.session.prompt)
            self._append_save_diagnostic(
                save_diagnostic_log_path,
                "after_vae_decode",
                f"is_mock={vae_res.get('is_mock')}, backend={vae_res.get('backend')}, image_shape={vae_res.get('image_shape')}"
            )
        except Exception as error:
            self._append_save_diagnostic(save_diagnostic_log_path, "vae_decode_exception", traceback.format_exc())
            logger.exception("[OnnxImageBackend] VAE decode failed")
            return self._save_failure_response(
                f"VAE Decode fehlgeschlagen: {error}",
                model_name,
                backend_name,
                save_diagnostic_log_path,
            )
        session_provider_lists = [
            embed_res.get("encoder_metadata", {}).get("text_encoder", {}).get("session_providers", []),
            embed_res.get("encoder_metadata", {}).get("text_encoder_2", {}).get("session_providers", []),
            unet_res.get("last_unet_metadata", {}).get("session_providers", []),
            vae_res.get("metadata", {}).get("session_providers", []),
        ]
        backend_name = OnnxProviderService.runtime_label(session_provider_lists)
        provider_diagnostics = OnnxProviderService.diagnostics()
        alpha_fallback = bool(not package_ready or embed_res["is_mock"] or unet_res["is_mock"] or vae_res["is_mock"])

        # 5. Generate visual PNG and JSON output using the session and job parameters
        output_dir = Path(job.session.output_directory) if job.session.output_directory else Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        prefix = job.session.output_prefix if job.session.output_prefix else "generate"
        timestamp = int(time.time())
        filename = f"{prefix}_{timestamp}_{str(job.job_id)[:8]}.png"
        dummy_image_path = output_dir / filename

        try:
            self._append_save_diagnostic(save_diagnostic_log_path, "before_image_conversion")
            image_stats = self._validate_output_image(vae_res.get("image"))
            self._append_save_diagnostic(save_diagnostic_log_path, "after_image_validation", json.dumps(image_stats))

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

            # Copy VAE decoded image and draw overlay metadata on it
            img = vae_res["image"].copy()
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            self._append_save_diagnostic(
                save_diagnostic_log_path,
                "after_image_conversion",
                f"mode={img.mode}, size={img.size}"
            )
            if alpha_fallback:
                self._append_save_diagnostic(save_diagnostic_log_path, "before_diagnostic_renderer")
                draw = ImageDraw.Draw(img)
                img_w, img_h = img.size
                draw.rectangle([(2, 2), (img_w - 3, img_h - 3)], outline="#3e4b59", width=2)
                draw.line([(40, 100), (img_w - 40, 100)], fill="#10b981", width=3)

                draw.text((40, 50), "Snapdragon AI Studio", fill="#10b981", font=font_title)
                draw.text((40, 115), "ONNX Alpha Fallback Generation", fill="#e8edf2", font=font_subtitle)

                draw.text((40, 155), f"Model: {model_name}", fill="#9aa7b2", font=font_body)
                draw.text((40, 175), f"Backend: {backend_name}", fill="#9aa7b2", font=font_body)
                draw.text((40, 195), f"Seed: {job.session.seed} | Steps: {job.session.steps} | CFG: {job.session.cfg_scale}", fill="#9aa7b2", font=font_body)

                tokens_str = str(embed_res["tokens"][:8]) + "..." if len(embed_res["tokens"]) > 8 else str(embed_res["tokens"])
                draw.text((40, 215), f"Tokens: {tokens_str}", fill="#9aa7b2", font=font_body)
                draw.text((40, 235), f"Embedding Shape: {embed_res['embedding_shape']}", fill="#9aa7b2", font=font_body)
                draw.text((40, 255), f"Pooled Shape: {embed_res['pooled_embedding_shape']}", fill="#9aa7b2", font=font_body)
                draw.text((40, 275), f"Latent Shape: {unet_res['latent_shape']}", fill="#9aa7b2", font=font_body)
                draw.text((40, 295), f"Decoder: {vae_res['backend']}", fill="#9aa7b2", font=font_body)

                prompt_str = job.session.prompt
                truncated_prompt = prompt_str[:57] + "..." if len(prompt_str) > 60 else prompt_str
                draw.text((40, 325), "Prompt Preview:", fill="#e8edf2", font=font_body)
                draw.text((40, 350), f'"{truncated_prompt}"', fill="#10b981", font=font_prompt)

                timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                draw.text((40, img_h - 50), f"Generated: {timestamp_str}", fill="#9aa7b2", font=font_body)
                self._append_save_diagnostic(save_diagnostic_log_path, "after_diagnostic_renderer")
            else:
                self._append_save_diagnostic(
                    save_diagnostic_log_path,
                    "real_vae_output_selected",
                    "Saving decoded VAE image without diagnostic overlay."
                )
            self._append_save_diagnostic(save_diagnostic_log_path, "before_png_save", str(dummy_image_path))
            img.save(dummy_image_path, format="PNG")
            if not dummy_image_path.exists() or dummy_image_path.stat().st_size <= 0:
                raise IOError(f"PNG save completed but output file is missing or empty: {dummy_image_path}")
            self._append_save_diagnostic(
                save_diagnostic_log_path,
                "after_png_save",
                f"path={dummy_image_path}, bytes={dummy_image_path.stat().st_size}"
            )
        except Exception as e:
            self._append_save_diagnostic(save_diagnostic_log_path, "png_save_exception", traceback.format_exc())
            logger.exception("[OnnxImageBackend] Failed to create output image")
            return self._save_failure_response(
                f"PNG konnte nicht gespeichert werden: {e}",
                model_name,
                backend_name,
                save_diagnostic_log_path,
            )

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
            "created_at": datetime.datetime.now().isoformat(),
            "onnx_model_file": onnx_model_path,
            "prompt_tokens": embed_res["tokens"],
            "negative_prompt_tokens": embed_res["negative_tokens"],
            "embedding_shape": embed_res["embedding_shape"],
            "negative_embedding_shape": embed_res["negative_embedding_shape"],
            "pooled_embedding_shape": embed_res["pooled_embedding_shape"],
            "negative_pooled_embedding_shape": embed_res["negative_pooled_embedding_shape"],
            "is_mock_embedding": embed_res["is_mock"],
            "latent_shape": unet_res["latent_shape"],
            "is_mock_unet": unet_res["is_mock"],
            "guidance_prepared": unet_res.get("guidance_prepared", False),
            "guidance_applied": unet_res.get("guidance_applied", False),
            "guidance_scale": unet_res.get("guidance_scale", job.session.cfg_scale),
            "scheduler_metadata": scheduler_metadata,
            "timesteps": unet_res.get("timesteps", []),
            "step_count": unet_res.get("step_count", 0),
            "step_records": unet_res.get("step_records", []),
            "time_ids_shape": list(time_ids.shape),
            "initial_latent_shape": list(init_latents.shape),
            "final_latent_shape": unet_res.get("latent_shape", []),
            "component_metadata": component_metadata,
            "provider_diagnostics": provider_diagnostics,
            "session_provider_lists": session_provider_lists,
            "decoder_backend": vae_res["backend"],
            "is_mock_decoder": vae_res["is_mock"],
            "diagnostic_log_path": str(save_diagnostic_log_path),
            "image_stats": image_stats,
            "alpha_fallback": alpha_fallback,
            "alpha_fallback_reason": "Package contains placeholder or incomplete ONNX components." if not package_ready else "",
        }

        # Write sidecar JSON alongside the image
        metadata_path = dummy_image_path.with_suffix(".json")
        try:
            self._append_save_diagnostic(save_diagnostic_log_path, "before_json_sidecar_save", str(metadata_path))
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(response_metadata, f, indent=2, ensure_ascii=False)
            if not metadata_path.exists() or metadata_path.stat().st_size <= 0:
                raise IOError(f"JSON sidecar save completed but file is missing or empty: {metadata_path}")
            logger.info(f"[OnnxImageBackend] Saved sidecar metadata to: {metadata_path}")
            print(f"[OnnxImageBackend] Saved sidecar metadata to: {metadata_path}")
            self._append_save_diagnostic(
                save_diagnostic_log_path,
                "after_json_sidecar_save",
                f"path={metadata_path}, bytes={metadata_path.stat().st_size}"
            )
        except Exception as e:
            self._append_save_diagnostic(save_diagnostic_log_path, "json_sidecar_exception", traceback.format_exc())
            logger.exception("[OnnxImageBackend] Failed to save sidecar metadata")
            return self._save_failure_response(
                f"JSON-Metadaten konnten nicht gespeichert werden: {e}",
                model_name,
                backend_name,
                save_diagnostic_log_path,
            )

        # Simulate small generation latency
        time.sleep(0.05)

        logger.info(f"[OnnxImageBackend] Generation completed successfully. Image saved to: {dummy_image_path}")
        print(f"[OnnxImageBackend] Generation completed successfully. Image saved to: {dummy_image_path}")

        self._append_save_diagnostic(save_diagnostic_log_path, "before_finish_response")
        return GenerationResponse(
            success=True,
            status="FINISHED",
            message=(
                "ONNX local image generation completed successfully."
                if not response_metadata["alpha_fallback"]
                else "ONNX alpha fallback image generated successfully; no real model weights were used."
            ),
            image_path=str(dummy_image_path),
            thumbnail_path=str(dummy_image_path),
            backend_name=backend_name,
            model_name=model_name,
            metadata=response_metadata
        )
